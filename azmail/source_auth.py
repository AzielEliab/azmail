"""Layer 1 — source authentication (SPF / DKIM / DMARC).

Advisory parsers and validators. No live DNS in v0.1 unless the caller
already supplied the record text. Honest: pass/fail here is header- or
record-shaped, not a mailbox-provider verdict.
"""

from __future__ import annotations

import re
from typing import Any

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

    return {
        "layer": "source_auth",
        "advisory": True,
        "verdict": verdict,
        "authentication_results": auth,
        "spf_record": spf,
        "dmarc_record": dmarc,
        "dkim_signature": dkim,
        "dkim_aligned": aligned,
        "limitation": "Advisory parser only. Live mailbox SPF/DKIM/DMARC needs DNS + keys the operator already has.",
    }
