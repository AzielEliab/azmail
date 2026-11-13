"""Layer 1 — source authentication (SPF / DKIM / DMARC).

Advisory parsers and validators. No live DNS in v0.1 unless the caller
already supplied the record text. Honest: pass/fail here is header- or
record-shaped, not a mailbox-provider verdict.
"""

from __future__ import annotations

import re
from typing import Any

from azmail.dkim import verify_dkim
from azmail.dmarc import evaluate_dmarc
from azmail.spf import evaluate_spf, sender_domain

AUTH_RESULTS_RE = re.compile(
    r"\b(spf|dkim|dmarc)=(pass|fail|softfail|neutral|none|temperror|permerror|unknown)\b",
    re.IGNORECASE,
)
SPF_MECH_RE = re.compile(
    r"(?P<qual>[+\-~?])?(?P<mech>all|include|a|mx|ptr|ip4|ip6|exists|redirect)(?::(?P<val>\S+))?",
    re.IGNORECASE,
)
DKIM_TAG_RE = re.compile(r"([a-zA-Z])\s*=\s*([^;]+)")
DMARC_TAG_RE = re.compile(r"([a-zA-Z]+)\s*=\s*([^;]+)")


def _norm(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_spf_record(record: str) -> dict[str, Any]:
    text = _norm(record)
    out: dict[str, Any] = {
        "ok": text.lower().startswith("v=spf1"),
        "version": None,
        "mechanisms": [],
        "qualifier_all": None,
        "advisory": True,
        "note": "Parsed locally. Not a live DNS SPF check.",
    }
    if not text:
        return out
    parts = text.split()
    if parts:
        out["version"] = parts[0]
    for token in parts[1:]:
        m = SPF_MECH_RE.match(token)
        if not m:
            continue
        mech = {
            "qualifier": m.group("qual") or "+",
            "mechanism": (m.group("mech") or "").lower(),
            "value": m.group("val"),
        }
        out["mechanisms"].append(mech)
        if mech["mechanism"] == "all":
            out["qualifier_all"] = mech["qualifier"]
    return out


def parse_dmarc_record(record: str) -> dict[str, Any]:
    text = _norm(record)
    tags: dict[str, str] = {}
    for key, val in DMARC_TAG_RE.findall(text):
        tags[key.lower()] = val.strip()
    return {
        "ok": tags.get("v", "").upper() == "DMARC1",
        "tags": tags,
        "policy": tags.get("p"),
        "subdomain_policy": tags.get("sp"),
        "rua": tags.get("rua"),
        "advisory": True,
        "note": "Parsed locally. Not a live DNS DMARC check.",
    }


def parse_dkim_signature(header: str) -> dict[str, Any]:
    text = _norm(header)
    tags: dict[str, str] = {}
    for key, val in DKIM_TAG_RE.findall(text):
        tags[key.lower()] = val.strip()
    return {
        "ok": tags.get("v") == "1" and bool(tags.get("d")) and bool(tags.get("b")),
        "tags": {k: ("<redacted>" if k == "b" else v) for k, v in tags.items()},
        "domain": tags.get("d"),
        "selector": tags.get("s"),
        "algorithm": tags.get("a"),
        "advisory": True,
        "note": "Parsed locally. Signature bytes are not cryptographically verified in v0.1 without a supplied public key.",
    }


def parse_authentication_results(header: str) -> dict[str, Any]:
    text = _norm(header)
    results: dict[str, str] = {}
    for proto, verdict in AUTH_RESULTS_RE.findall(text):
        results[proto.lower()] = verdict.lower()
    return {
        "ok": bool(results),
        "results": results,
        "spf": results.get("spf", "unknown"),
        "dkim": results.get("dkim", "unknown"),
        "dmarc": results.get("dmarc", "unknown"),
        "advisory": True,
        "note": "Read from Authentication-Results. AZMail does not query DNS.",
    }


def advise_source_auth(
    headers: dict[str, Any] | None = None,
    *,
    spf_record: str | None = None,
    dmarc_record: str | None = None,
    dkim_signature: str | None = None,
    client_ip: str | None = None,
    mail_from: str | None = None,
    spf_records: dict[str, str] | None = None,
    dns_answers: dict[str, Any] | None = None,
    raw_message: bytes | str | None = None,
    dkim_public_key: str | None = None,
    dkim_public_keys: dict[tuple[str, str], str] | None = None,
    public_suffix: str | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    headers = headers or {}
    lowered = {str(k).lower(): v for k, v in headers.items()}
    auth_header = _norm(
        lowered.get("authentication-results") or lowered.get("authentication_results")
    )
    received_spf = _norm(lowered.get("received-spf") or lowered.get("received_spf"))
    dkim_header = dkim_signature or _norm(
        lowered.get("dkim-signature") or lowered.get("dkim_signature")
    )

    auth = parse_authentication_results(auth_header) if auth_header else {
        "ok": False,
        "results": {},
        "spf": "unknown",
        "dkim": "unknown",
        "dmarc": "unknown",
        "advisory": True,
        "note": "No Authentication-Results header.",
    }
    if received_spf and auth["spf"] == "unknown":
        low = received_spf.lower()
        for token in ("pass", "fail", "softfail", "neutral", "none"):
            if token in low:
                auth["spf"] = token
                auth["ok"] = True
                break

    spf = parse_spf_record(spf_record) if spf_record else None
    dmarc = parse_dmarc_record(dmarc_record) if dmarc_record else None
    dkim = parse_dkim_signature(dkim_header) if dkim_header else None

    aligned = False
    if dkim and dkim.get("domain"):
        from_addr = _norm(lowered.get("from"))
        if dkim["domain"].lower() in from_addr.lower():
            aligned = True

    verdict = "unknown"
    if auth["spf"] == "pass" and auth.get("dmarc") in {"pass", "unknown"}:
        verdict = "pass"
    if auth["spf"] == "fail" or auth.get("dmarc") == "fail" or auth.get("dkim") == "fail":
        verdict = "fail"
    if not auth_header and not received_spf and not dkim_header:
        verdict = "unverified"

    evaluation = _evaluate(
        headers=lowered,
        spf_record=spf_record,
        dmarc_record=dmarc_record,
        client_ip=client_ip,
        mail_from=mail_from,
        spf_records=spf_records,
        dns_answers=dns_answers,
        raw_message=raw_message,
        dkim_public_key=dkim_public_key,
        dkim_public_keys=dkim_public_keys,
        public_suffix=public_suffix,
        now=now,
    )
    limitation = "Advisory parser only. Live mailbox SPF/DKIM/DMARC needs DNS + keys the operator already has."
    advisory = True
    if evaluation is not None:
        verdict = evaluation["verdict"]
        advisory = bool(evaluation["advisory"])
        limitation = (
            "Verdict is from the records and keys supplied to this call. "
            "DNS was not queried. Authentication-Results was not treated as a pass."
        )

    result = {
        "layer": "source_auth",
        "advisory": advisory,
        "verdict": verdict,
        "authentication_results": auth,
        "spf_record": spf,
        "dmarc_record": dmarc,
        "dkim_signature": dkim,
        "dkim_aligned": aligned,
        "limitation": limitation,
    }
    if evaluation is not None:
        result["evaluation"] = evaluation
    return result


def _evaluate(
    *,
    headers: dict[str, Any],
    spf_record: str | None,
    dmarc_record: str | None,
    client_ip: str | None,
    mail_from: str | None,
    spf_records: dict[str, str] | None,
    dns_answers: dict[str, Any] | None,
    raw_message: bytes | str | None,
    dkim_public_key: str | None,
    dkim_public_keys: dict[tuple[str, str], str] | None,
    public_suffix: str | None,
    now: float | None,
) -> dict[str, Any] | None:
    if client_ip is None and raw_message is None:
        return None
    spf_eval = None
    dkim_eval = None
    if client_ip is not None:
        domain = sender_domain(str(mail_from or headers.get("from") or ""))
        spf_eval = evaluate_spf(
            str(client_ip),
            domain,
            spf_record if isinstance(spf_record, str) else None,
            records=spf_records,
            answers=dns_answers,
        )
    if raw_message is not None:
        dkim_eval = verify_dkim(
            raw_message,
            public_key=dkim_public_key,
            public_keys=dkim_public_keys,
            now=now,
        )
    dmarc_eval = None
    if dmarc_record and (spf_eval is not None or dkim_eval is not None):
        signatures = []
        for item in (dkim_eval or {}).get("signatures") or []:
            signatures.append({"domain": str(item.get("domain") or ""), "result": str(item.get("result") or "")})
        dmarc_eval = evaluate_dmarc(
            from_domain=sender_domain(str(headers.get("from") or "")),
            record=str(dmarc_record),
            spf_domain=(spf_eval or {}).get("domain"),
            spf_result=(spf_eval or {}).get("result"),
            dkim=signatures,
            public_suffix=public_suffix,
        )
    verdict = _checked_verdict(spf_eval, dkim_eval, dmarc_eval)
    return {
        "spf": spf_eval,
        "dkim": dkim_eval,
        "dmarc": dmarc_eval,
        "verdict": verdict,
        "authoritative": verdict in {"pass", "fail"},
        "dns_queried": False,
        "advisory": verdict not in {"pass", "fail"},
    }


def _checked_verdict(
    spf_eval: dict[str, Any] | None,
    dkim_eval: dict[str, Any] | None,
    dmarc_eval: dict[str, Any] | None,
) -> str:
    if dmarc_eval is not None:
        if dmarc_eval.get("result") == "pass":
            return "pass"
        if dmarc_eval.get("result") == "fail":
            return "fail"
        return "unverified"
    spf_result = (spf_eval or {}).get("result")
    dkim_result = (dkim_eval or {}).get("result")
    if spf_result == "pass" or dkim_result == "pass":
        return "pass"
    if spf_result == "fail" or dkim_result == "fail":
        return "fail"
    return "unverified"
