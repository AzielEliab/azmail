"""DMARC evaluation (RFC 7489) on a record and auth results already in hand.

Alignment is exact when the authenticated domain equals the From domain.
Relaxed organizational alignment runs only when the operator supplies the
public suffix. A missing suffix does not become a pass. This module does
not query DNS and does not sample `pct`.
"""

from __future__ import annotations

import re
from typing import Any

_TAG = re.compile(r"([A-Za-z]+)\s*=\s*([^;]+)")
_POLICIES = {"none", "quarantine", "reject"}


def organizational_domain(domain: str, public_suffix: str | None) -> str | None:
    host = (domain or "").strip().lower().rstrip(".")
    suffix = (public_suffix or "").strip().lower().rstrip(".")
    if not host or not suffix:
        return None
    if host == suffix:
        return None
    if host.endswith("." + suffix):
        label = host[: -(len(suffix) + 1)].split(".")[-1]
        if not label:
            return None
        return f"{label}.{suffix}"
    return None


def evaluate_dmarc(
    *,
    from_domain: str,
    record: str | None,
    spf_domain: str | None = None,
    spf_result: str | None = None,
    dkim: list[dict[str, str]] | None = None,
    public_suffix: str | None = None,
) -> dict[str, Any]:
    mail_from = (from_domain or "").strip().lower().rstrip(".")
    out: dict[str, Any] = {
        "result": "none",
        "disposition": "none",
        "policy": None,
        "from_domain": mail_from,
        "aligned_spf": False,
        "aligned_dkim": False,
        "dns_queried": False,
        "sampling": "not_applied",
        "reason": "",
        "advisory": False,
    }
    text = " ".join(str(record or "").split())
    if not text:
        out["reason"] = "no_record"
        return out
    tags = {key.lower(): value.strip() for key, value in _TAG.findall(text)}
    if tags.get("v", "").upper() != "DMARC1":
        out["result"] = "permerror"
        out["reason"] = "not_dmarc"
        return out
    policy = (tags.get("p") or "").lower()
    if policy not in _POLICIES:
        out["result"] = "permerror"
        out["reason"] = "bad_policy"
        return out
    subdomain = (tags.get("sp") or policy).lower()
    if subdomain not in _POLICIES:
        out["result"] = "permerror"
        out["reason"] = "bad_policy"
        return out
    adkim = (tags.get("adkim") or "r").lower()
    aspf = (tags.get("aspf") or "r").lower()
    if adkim not in {"r", "s"} or aspf not in {"r", "s"}:
        out["result"] = "permerror"
        out["reason"] = "bad_alignment_mode"
        return out
    try:
        pct = int(tags["pct"]) if "pct" in tags else 100
    except ValueError:
        out["result"] = "permerror"
        out["reason"] = "bad_pct"
        return out
    if pct < 0 or pct > 100:
        out["result"] = "permerror"
        out["reason"] = "bad_pct"
        return out
    out["policy"] = policy
    out["subdomain_policy"] = subdomain
    out["pct"] = pct
    out["adkim"] = adkim
    out["aspf"] = aspf
    if not mail_from:
        out["result"] = "permerror"
        out["reason"] = "bad_from"
        return out

    spf_state: bool | None = False
    if (spf_result or "").lower() == "pass":
        spf_state = _aligned(spf_domain or "", mail_from, aspf, public_suffix)
    dkim_align = False
    dkim_unresolved = False
    dkim_temperror = False
    for entry in dkim or []:
        result = (entry.get("result") or "").lower()
        if result == "temperror":
            dkim_temperror = True
            continue
        if result != "pass":
            continue
        aligned = _aligned(entry.get("domain") or "", mail_from, adkim, public_suffix)
        if aligned is None:
            dkim_unresolved = True
            continue
        if aligned:
            dkim_align = True
    out["aligned_spf"] = spf_state is True
    out["aligned_dkim"] = dkim_align
    if spf_state is True or dkim_align:
        out["result"] = "pass"
        out["disposition"] = "none"
        return out
    if spf_state is None or dkim_unresolved or (spf_result or "").lower() == "temperror" or dkim_temperror:
        out["result"] = "temperror"
        out["reason"] = "alignment_unresolved" if dkim_unresolved else "temporary"
        return out
    published = _disposition_policy(mail_from, policy, subdomain, public_suffix)
    out["result"] = "fail"
    if published is None:
        out["disposition"] = "none"
        out["reason"] = "organizational_domain_unspecified"
        return out
    if pct != 100:
        out["disposition"] = "none"
        out["reason"] = "pct_not_applied"
        return out
    out["disposition"] = published
    return out


def _aligned(auth_domain: str, from_domain: str, mode: str, public_suffix: str | None) -> bool | None:
    auth = (auth_domain or "").strip().lower().rstrip(".")
    sender = (from_domain or "").strip().lower().rstrip(".")
    if not auth or not sender:
        return False
    if auth == sender:
        return True
    if mode == "s":
        return False
    if not public_suffix:
        return None
    left = organizational_domain(auth, public_suffix)
    right = organizational_domain(sender, public_suffix)
    if left is None or right is None:
        return False
    return left == right


def _disposition_policy(
    from_domain: str,
    policy: str,
    subdomain_policy: str,
    public_suffix: str | None,
) -> str | None:
    if subdomain_policy == policy:
        return policy
    org = organizational_domain(from_domain, public_suffix)
    if org is None:
        return None
    if from_domain == org:
        return policy
    return subdomain_policy
