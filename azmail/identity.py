"""Layer 3 — identity continuity (pattern deviation flags)."""

from __future__ import annotations

import re
from typing import Any

from azmail.reputation import domain_of

DISPLAY_RE = re.compile(r'^\s*"?([^"<]+)"?\s*<([^>]+)>')


def split_from(value: str) -> tuple[str, str]:
    text = (value or "").strip()
    m = DISPLAY_RE.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip().lower()
    if "@" in text:
        return "", text.strip("<> ").lower()
    return text, ""


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def continuity(
    from_addr: str,
    display_name: str = "",
    *,
    contacts: dict[str, list[str]] | None = None,
    history: list[str] | None = None,
) -> dict[str, Any]:
    parsed_name, parsed_addr = split_from(from_addr)
    name = _norm_name(display_name or parsed_name)
    addr = (parsed_addr or from_addr or "").strip().lower()
    if "<" in addr or ">" in addr:
        _, addr = split_from(addr if "@" in addr else from_addr)
    host = domain_of(addr)
    contacts = contacts or {}
    history = [h.lower() for h in (history or [])]

    flags: list[str] = []
    first_seen = addr not in history if addr else True
    if first_seen:
        flags.append("first_seen_sender")

    mismatch = False
    expected: list[str] = []
    if name:
        for key, addrs in contacts.items():
            if _norm_name(key) == name:
                expected = [a.lower() for a in addrs]
                if addr and addr not in expected:
                    mismatch = True
                    flags.append("display_name_address_mismatch")
                break

    unusual = False
    prior_hosts = {domain_of(h) for h in history if h}
    if host and prior_hosts and host not in prior_hosts and name and expected:
        unusual = True
        flags.append("unexpected_domain_for_known_name")

    return {
        "layer": "identity",
        "from_addr": addr,
        "display_name": name,
        "domain": host,
        "first_seen": first_seen,
        "display_mismatch": mismatch,
        "unexpected_domain": unusual,
        "expected_addrs": expected,
        "flags": flags,
        "risk": (35 if mismatch else 0) + (15 if first_seen else 0) + (25 if unusual else 0),
        "advisory": True,
    }
