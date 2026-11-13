"""SPF, DKIM, and DMARC on supplied records and keys. No DNS, no network."""

from __future__ import annotations

import base64
import hashlib
import socket
import subprocess
from pathlib import Path

import pytest

from azmail.airlock import classify
from azmail.dkim import canon_header, canonical_body, verify_dkim
from azmail.dmarc import evaluate_dmarc, organizational_domain
from azmail.source_auth import advise_source_auth
from azmail.spf import evaluate_spf


def test_spf_ip4_pass_fail_and_softfail():
    record = "v=spf1 ip4:192.0.2.0/24 -all"
    passed = evaluate_spf("192.0.2.10", "example.com", record)
    assert passed["result"] == "pass"
    assert passed["dns_queried"] is False
    assert passed["matched"] == "ip4:192.0.2.0/24"
    failed = evaluate_spf("203.0.113.5", "example.com", record)
    assert failed["result"] == "fail"
    assert failed["dns_queried"] is False
    soft = evaluate_spf("203.0.113.5", "example.com", "v=spf1 ip4:192.0.2.0/24 ~all")
    assert soft["result"] == "softfail"
    neutral = evaluate_spf("203.0.113.5", "example.com", "v=spf1 ?all")
    assert neutral["result"] == "neutral"


def test_spf_missing_include_is_not_a_pass(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("SPF must not open a socket")

    monkeypatch.setattr(socket, "create_connection", explode)
    checked = evaluate_spf(
        "192.0.2.10",
        "example.com",
        "v=spf1 include:missing.example +all",
    )
    assert checked["result"] == "temperror"
    assert checked["reason"] == "record_not_supplied"
    assert checked["missing"] == "missing.example"
    assert checked["dns_queried"] is False


def test_spf_include_uses_only_the_supplied_record():
    passed = evaluate_spf(
        "192.0.2.1",
        "example.com",
        "v=spf1 include:good.example -all",
        records={"good.example": "v=spf1 ip4:192.0.2.1 -all"},
    )
    assert passed["result"] == "pass"
    assert passed["dns_queried"] is False
    failed = evaluate_spf(
        "192.0.2.2",
        "example.com",
        "v=spf1 include:good.example -all",
        records={"good.example": "v=spf1 ip4:192.0.2.1 -all"},
    )
    assert failed["result"] == "fail"
    empty = evaluate_spf(
        "192.0.2.1",
        "example.com",
        "v=spf1 include:good.example -all",
        records={"good.example": ""},
    )
    assert empty["result"] == "permerror"
    assert empty["reason"] == "include_none"


def test_spf_redirect_and_lookup_limit_and_absent_record():
    redirected = evaluate_spf(
        "2001:db8::1",
        "example.com",
        "v=spf1 redirect=other.example",
        records={"other.example": "v=spf1 ip6:2001:db8::1 -all"},
    )
    assert redirected["result"] == "pass"
    assert evaluate_spf("203.0.113.9", "example.com", None)["result"] == "none"
    assert evaluate_spf("203.0.113.9", "example.com", "v=spf2 -all")["result"] == "none"
    nested = "v=spf1 include:hop0.example -all"
    records = {f"hop{i}.example": f"v=spf1 include:hop{i + 1}.example -all" for i in range(11)}
    records["hop11.example"] = "v=spf1 +all"
    limited = evaluate_spf("192.0.2.1", "example.com", nested, records=records)
    assert limited["result"] == "permerror"
    assert limited["reason"] == "lookup_limit"


def test_spf_mx_matches_only_a_supplied_address():
    answers = {"mx": {"example.com": ["mail.example.com"]}, "a": {"mail.example.com": ["192.0.2.8"]}}
    hit = evaluate_spf("192.0.2.8", "example.com", "v=spf1 mx -all", answers=answers)
    assert hit["result"] == "pass"
    missing = evaluate_spf("192.0.2.8", "example.com", "v=spf1 mx -all")
    assert missing["result"] == "temperror"
    assert missing["dns_queried"] is False


def test_header_pass_does_not_override_a_supplied_spf_fail():
    advised = advise_source_auth(
        {
            "From": "billing@example.com",
            "Authentication-Results": "mx; spf=pass; dkim=pass; dmarc=pass",
        },
        spf_record="v=spf1 ip4:192.0.2.0/24 -all",
        client_ip="203.0.113.5",
        mail_from="billing@example.com",
    )
    assert advised["advisory"] is False
    assert advised["verdict"] == "fail"
    assert advised["evaluation"]["spf"]["result"] == "fail"
    assert advised["evaluation"]["dns_queried"] is False
    assert advised["authentication_results"]["spf"] == "pass"


def test_header_only_parser_stays_advisory():
    advised = advise_source_auth({"Authentication-Results": "mx; spf=pass; dkim=fail; dmarc=pass"})
    assert advised["advisory"] is True
    assert advised["verdict"] == "fail"
    assert "evaluation" not in advised


def test_classify_does_not_verify_a_forged_authentication_results_header():
    result = classify(
        {
            "from": "billing@paypal.com",
            "subject": "Your monthly statement",
            "body_text": "Statement attached as PDF.",
            "headers": {
                "Authentication-Results": "mx; spf=pass; dkim=pass; dmarc=pass",
            },
            "client_ip": "203.0.113.5",
            "mail_from": "billing@paypal.com",
            "spf_record": "v=spf1 ip4:192.0.2.0/24 -all",
            "history": ["billing@paypal.com"],
            "contacts": {"paypal billing": ["billing@paypal.com"]},
        }
    )
    assert result.layers["source_auth"]["verdict"] == "fail"
    assert result.badge != "verified"
    assert result.verdict != "release"


def test_body_and_header_canonicalization():
    assert canonical_body(b"", "simple") == b""
    assert canonical_body(b"hello  world \r\n\r\n", "simple") == b"hello  world \r\n"
    assert canonical_body(b"hello  world \r\n\r\n", "relaxed") == b"hello world\r\n"
    assert hashlib.sha256(canonical_body(b"", "relaxed")).hexdigest() == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    folded = canon_header(b"Subject: hello\r\n world\r\n", "relaxed")
    assert folded == b"subject:hello world\r\n"
    assert canon_header(b"From:  Alice   <a@example.com>  \r\n", "relaxed") == (
        b"from:Alice <a@example.com>\r\n"
    )


def test_dkim_without_a_key_is_not_a_pass():
    message = b"From: Alice <alice@example.com>\r\nSubject: hi\r\n\r\nHello\r\n"
    checked = verify_dkim(message, public_key=None)
    assert checked["result"] == "none"
    assert checked["verified"] is False
    assert checked["dns_queried"] is False
    body = b"Hello\r\n"
    bh = base64.b64encode(hashlib.sha256(canonical_body(body, "simple")).digest()).decode("ascii")
    signed = (
        b"From: Alice <alice@example.com>\r\n"
        b"DKIM-Signature: v=1; a=rsa-sha256; c=simple/simple; d=example.com; s=sel; h=from; bh="
        + bh.encode("ascii")
        + b"; b=AAAA\r\n\r\n"
        + body
    )
    missing = verify_dkim(signed)
    assert missing["verified"] is False
    assert missing["result"] == "permerror"
    assert missing["signatures"][0]["reason"] == "public_key_not_supplied"
    revoked = verify_dkim(signed, public_key="v=DKIM1; p=")
    assert revoked["result"] != "pass"
    assert revoked["verified"] is False
    ed25519 = (
        b"From: Alice <alice@example.com>\r\n"
        b"DKIM-Signature: v=1; a=ed25519-sha256; d=example.com; s=sel; h=from; bh=abc; b=abc\r\n"
        b"\r\nHello\r\n"
    )
    unsupported = verify_dkim(ed25519, public_key="v=DKIM1; k=rsa; p=AAAA")
    assert unsupported["result"] == "permerror"
    assert unsupported["signatures"][0]["reason"] == "algorithm_unsupported"


def _openssl(*args: str, input_bytes: bytes | None = None) -> bytes:
    try:
        return subprocess.check_output(["openssl", *args], input=input_bytes, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"openssl unavailable: {exc}")
        return b""


def _signed_message(tmp_path: Path, *, body: bytes, key_path: Path | None = None) -> tuple[bytes, str]:
    key = key_path or (tmp_path / "dkim.pem")
    if key_path is None:
        _openssl("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:1024", "-out", str(key))
    der = _openssl("pkey", "-in", str(key), "-pubout", "-outform", "DER")
    txt = "v=DKIM1; k=rsa; p=" + base64.b64encode(der).decode("ascii")
    bh = base64.b64encode(hashlib.sha256(canonical_body(body, "relaxed")).digest()).decode("ascii")
    from_header = b"From: Alice <alice@example.com>\r\n"
    subject = b"Subject: hi\r\n"
    signature = (
        "DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=sel; "
        f"h=from:subject; bh={bh}; b=\r\n"
    ).encode("ascii")
    signing = (
        canon_header(from_header, "relaxed")
        + canon_header(subject, "relaxed")
        + canon_header(signature, "relaxed")
    )
    raw_sig = _openssl("dgst", "-sha256", "-sign", str(key), input_bytes=signing)
    stamped = signature.replace(b"b=", b"b=" + base64.b64encode(raw_sig), 1)
    return from_header + subject + stamped + b"\r\n" + body, txt


def test_dkim_rsa_sha256_verifies_and_a_changed_body_fails(tmp_path: Path):
    message, txt = _signed_message(tmp_path, body=b"Hello\r\n")
    checked = verify_dkim(message, public_key=txt, now=1_700_000_000)
    assert checked["dns_queried"] is False
    assert checked["verified"] is True
    assert checked["result"] == "pass"
    assert checked["signatures"][0]["domain"] == "example.com"
    tampered = message.replace(b"Hello", b"Helli", 1)
    failed = verify_dkim(tampered, public_key=txt, now=1_700_000_000)
    assert failed["verified"] is False
    assert failed["result"] == "fail"
    assert failed["signatures"][0]["reason"] == "body_hash"
    other = tmp_path / "other.pem"
    _openssl("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:1024", "-out", str(other))
    other_txt = "v=DKIM1; k=rsa; p=" + base64.b64encode(
        _openssl("pkey", "-in", str(other), "-pubout", "-outform", "DER")
    ).decode("ascii")
    mismatch = verify_dkim(message, public_key=other_txt, now=1_700_000_000)
    assert mismatch["result"] == "fail"
    assert mismatch["signatures"][0]["reason"] == "signature"


def test_dmarc_pass_fail_and_unresolved_alignment():
    passed = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=reject; adkim=s; aspf=s",
        spf_domain="example.com",
        spf_result="pass",
    )
    assert passed["result"] == "pass"
    assert passed["disposition"] == "none"
    assert passed["dns_queried"] is False
    rejected = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=reject",
        spf_domain="example.com",
        spf_result="fail",
        dkim=[{"domain": "example.com", "result": "fail"}],
    )
    assert rejected["result"] == "fail"
    assert rejected["disposition"] == "reject"
    unresolved = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=reject; aspf=r",
        spf_domain="mail.example.com",
        spf_result="pass",
    )
    assert unresolved["result"] == "temperror"
    assert unresolved["disposition"] == "none"
    assert unresolved["result"] != "pass"
    relaxed = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=quarantine; aspf=r",
        spf_domain="mail.example.com",
        spf_result="pass",
        public_suffix="com",
    )
    assert relaxed["result"] == "pass"
    assert organizational_domain("mail.example.com", "com") == "example.com"
    strict = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=reject; aspf=s",
        spf_domain="mail.example.com",
        spf_result="pass",
        public_suffix="com",
    )
    assert strict["result"] == "fail"
    assert strict["disposition"] == "reject"
    sampled = evaluate_dmarc(
        from_domain="example.com",
        record="v=DMARC1; p=reject; pct=0",
        spf_domain="example.com",
        spf_result="fail",
    )
    assert sampled["result"] == "fail"
    assert sampled["disposition"] == "none"
    assert sampled["sampling"] == "not_applied"
    assert evaluate_dmarc(from_domain="example.com", record=None)["result"] == "none"


def test_supplied_dmarc_beats_a_passing_authentication_results_header():
    advised = advise_source_auth(
        {"From": "alice@example.com", "Authentication-Results": "mx; spf=pass; dkim=pass; dmarc=pass"},
        client_ip="203.0.113.5",
        mail_from="alice@example.com",
        spf_record="v=spf1 -all",
        dmarc_record="v=DMARC1; p=reject",
        public_suffix="com",
    )
    assert advised["verdict"] == "fail"
    assert advised["evaluation"]["dmarc"]["disposition"] == "reject"
    assert advised["evaluation"]["dns_queried"] is False
