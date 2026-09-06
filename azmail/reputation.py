"""Layer 2 — domain reputation (lookalike / new domain / known-phish)."""

from __future__ import annotations

import re
from typing import Any

BRANDS = (
    "paypal",
    "apple",
    "microsoft",
    "google",
    "gmail",
    "amazon",
    "bankofamerica",
    "wellsfargo",
    "chase",
    "irs",
    "netflix",
    "facebook",
    "instagram",
    "whatsapp",
    "docusign",
    "adobe",
    "outlook",
    "office365",
    "icloud",
    "dropbox",
)

# Demo / fixture list only. Not a live feed.
KNOWN_PHISH = frozenset(
    {
        "secure-paypal-login.tk",
        "paypa1-verify.com",
        "g00gle-account.net",
        "micros0ft-support.xyz",
        "amaz0n-billing.cc",
        "phish.example",
        "login-appleid-secure.top",
    }
)

LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a"})
HOST_RE = re.compile(r"^[a-z0-9.-]+$")


def domain_of(addr_or_host: str) -> str:
    text = (addr_or_host or "").strip().lower()
    if "@" in text:
        text = text.rsplit("@", 1)[-1]
    text = text.strip("<> \t\"'")
    if text.startswith("www."):
        text = text[4:]
    return text


def registrable_name(domain: str) -> str:
    host = domain_of(domain)
    parts = [p for p in host.split(".") if p]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else ""


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins, delete, sub = prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def lookalike(domain: str) -> dict[str, Any]:
    host = domain_of(domain)
    name = registrable_name(host)
    folded = name.translate(LEET)
    compact = name.replace("-", "").translate(LEET)
    tokens = [t for t in re.split(r"[-_]", name) if t]
    folded_tokens = [t.translate(LEET) for t in tokens]
    hits: list[dict[str, Any]] = []
    for brand in BRANDS:
        if name == brand:
            continue
        if brand in folded_tokens or folded == brand or compact == brand:
            hits.append({"brand": brand, "reason": "homoglyph_or_leet", "distance": 0})
            continue
        if brand in name or brand in compact:
            hits.append({"brand": brand, "reason": "brand_plus_extra", "distance": _levenshtein(compact, brand)})
            continue
        dists = [_levenshtein(name, brand), _levenshtein(folded, brand), _levenshtein(compact, brand)]
        dists.extend(_levenshtein(t, brand) for t in folded_tokens if len(t) >= 4)
        dist = min(dists)
        if 0 < dist <= 2 and len(name) >= 4:
            hits.append({"brand": brand, "reason": "edit_distance", "distance": dist})
    return {
        "domain": host,
        "registrable": name,
        "lookalike": bool(hits),
        "matches": hits[:5],
    }


def new_domain_flags(domain: str, age_days: int | None = None) -> dict[str, Any]:
    host = domain_of(domain)
    name = registrable_name(host)
    hyphen_count = name.count("-")
    digit_ratio = (sum(ch.isdigit() for ch in name) / len(name)) if name else 0.0
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    risky_tld = tld in {"tk", "ml", "ga", "cf", "gq", "xyz", "top", "click", "zip", "mov"}
    looks_new = hyphen_count >= 2 or digit_ratio >= 0.3 or risky_tld
    if age_days is not None:
        looks_new = looks_new or age_days < 30
    return {
        "domain": host,
        "age_days": age_days,
        "hyphen_count": hyphen_count,
        "digit_ratio": round(digit_ratio, 3),
        "risky_tld": risky_tld,
        "new_or_suspicious": looks_new,
        "note": "Heuristic only. Live WHOIS/RDAP is not queried in v0.1.",
    }


def reputation(domain: str, *, age_days: int | None = None) -> dict[str, Any]:
    host = domain_of(domain)
    known = host in KNOWN_PHISH
    alike = lookalike(host)
    fresh = new_domain_flags(host, age_days)
    risk = 0
    flags: list[str] = []
    if known:
        risk += 80
        flags.append("known_phish")
    if alike["lookalike"]:
        risk += 40
        flags.append("lookalike")
    if fresh["new_or_suspicious"]:
        risk += 20
        flags.append("new_or_suspicious_domain")
    return {
        "layer": "reputation",
        "domain": host,
        "known_phish": known,
        "lookalike": alike,
        "new_domain": fresh,
        "flags": flags,
        "risk": min(risk, 100),
        "advisory": True,
    }
