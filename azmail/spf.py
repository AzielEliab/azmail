"""SPF evaluation on records the operator already supplied.

RFC 7208 mechanisms that need DNS (`include`, `a`, `mx`, `ptr`, `exists`,
`redirect`) match only when the answer is in the supplied maps. A missing
answer is `temperror`. This module does not query DNS and does not report
`pass` for a lookup it did not receive.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any

_MECH = re.compile(
    r"^(?P<qual>[+\-~?])?(?P<name>all|include|a|mx|ptr|ip4|ip6|exists)(?:[:/](?P<arg>.*))?$",
    re.IGNORECASE,
)
_MOD = re.compile(r"^(?P<name>[a-z][a-z0-9_.-]*)=(?P<value>\S*)$", re.IGNORECASE)
_LOOKUP_LIMIT = 10


class _Stop(Exception):
    def __init__(self, result: str, reason: str, **extra: Any) -> None:
        super().__init__(reason)
        self.result = result
        self.reason = reason
        self.extra = extra


def sender_domain(value: str) -> str:
    text = (value or "").strip().lower()
    if "@" in text:
        text = text.rsplit("@", 1)[1]
    return text.strip("<> \t").rstrip(".")


def evaluate_spf(
    ip: str,
    domain: str,
    record: str | None,
    *,
    records: dict[str, str] | None = None,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one supplied SPF record against one client IP."""
    host = sender_domain(domain)
    base: dict[str, Any] = {
        "result": "none",
        "domain": host,
        "ip": str(ip or ""),
        "record": record if isinstance(record, str) else None,
        "matched": None,
        "dns_queried": False,
        "lookups": 0,
        "reason": "",
        "advisory": False,
    }
    try:
        client = ipaddress.ip_address(str(ip or "").strip())
    except ValueError:
        base["result"] = "permerror"
        base["reason"] = "bad_ip"
        return base
    if not host:
        base["result"] = "permerror"
        base["reason"] = "bad_domain"
        return base
    if record is None or str(record).strip() == "":
        base["reason"] = "no_record"
        return base
    text = " ".join(str(record).split())
    parts = text.split(" ")
    if parts[0].lower() != "v=spf1":
        base["reason"] = "not_spf"
        return base
    state = {
        "lookups": 0,
        "records": {k.lower().rstrip("."): v for k, v in (records or {}).items()},
        "answers": answers or {},
        "seen": set(),
    }
    try:
        result, matched, reason = _eval(host, text, client, state)
    except _Stop as stop:
        base.update(stop.extra)
        base["result"] = stop.result
        base["reason"] = stop.reason
        base["lookups"] = state["lookups"]
        return base
    base["result"] = result
    base["matched"] = matched
    base["reason"] = reason
    base["lookups"] = state["lookups"]
    return base


def _eval(
    domain: str,
    record: str,
    client: ipaddress.IPv4Address | ipaddress.IPv6Address,
    state: dict[str, Any],
) -> tuple[str, str | None, str]:
    key = domain.lower().rstrip(".")
    if key in state["seen"]:
        raise _Stop("permerror", "include_loop", domain=key)
    state["seen"].add(key)
    try:
        return _eval_terms(key, record, client, state)
    finally:
        state["seen"].discard(key)


def _eval_terms(
    domain: str,
    record: str,
    client: ipaddress.IPv4Address | ipaddress.IPv6Address,
    state: dict[str, Any],
) -> tuple[str, str | None, str]:
    parts = " ".join(record.split()).split(" ")
    if not parts or parts[0].lower() != "v=spf1":
        raise _Stop("permerror", "included_record_not_spf", domain=domain)
    redirect: str | None = None
    redirects = 0
    for term in parts[1:]:
        if not term:
            continue
        if "%" in term:
            raise _Stop("permerror", "macro_unsupported", term=term)
        mod = _MOD.match(term)
        if mod:
            name = mod.group("name").lower()
            if name == "redirect":
                redirects += 1
                redirect = mod.group("value").lower().rstrip(".")
                if redirects > 1:
                    raise _Stop("permerror", "duplicate_redirect")
            continue
        mech = _MECH.match(term)
        if not mech:
            raise _Stop("permerror", "bad_term", term=term)
        name = mech.group("name").lower()
        arg = mech.group("arg")
        qual = mech.group("qual") or "+"
        if name in {"include", "a", "mx", "ptr", "exists"}:
            state["lookups"] += 1
            if state["lookups"] > _LOOKUP_LIMIT:
                raise _Stop("permerror", "lookup_limit")
        matched = _mechanism(name, arg, domain, client, state)
        if matched:
            return _qualifier(qual), term, ""
    if redirect:
        state["lookups"] += 1
        if state["lookups"] > _LOOKUP_LIMIT:
            raise _Stop("permerror", "lookup_limit")
        target = redirect
        included = state["records"].get(target)
        if included is None:
            raise _Stop("temperror", "record_not_supplied", missing=target)
        return _eval(target, included, client, state)
    return "neutral", None, "no_match"


def _qualifier(qual: str) -> str:
    return {"+": "pass", "-": "fail", "~": "softfail", "?": "neutral"}[qual]


def _mechanism(
    name: str,
    arg: str | None,
    domain: str,
    client: ipaddress.IPv4Address | ipaddress.IPv6Address,
    state: dict[str, Any],
) -> bool:
    if name == "all":
        if arg:
            raise _Stop("permerror", "bad_term", term=f"all:{arg}")
        return True
    if name == "ip4":
        return _ip_match(arg, client, 4)
    if name == "ip6":
        return _ip_match(arg, client, 6)
    if name == "include":
        if not arg:
            raise _Stop("permerror", "bad_term", term="include")
        target = arg.lower().rstrip(".")
        if target not in state["records"]:
            raise _Stop("temperror", "record_not_supplied", missing=target)
        included = state["records"].get(target)
        if included is None or str(included).strip() == "":
            raise _Stop("permerror", "include_none", domain=target)
        result, _, _ = _eval(target, str(included), client, state)
        if result == "pass":
            return True
        if result in {"fail", "softfail", "neutral"}:
            return False
        raise _Stop(result, "include_" + result, domain=target)
    if name == "a":
        return _name_ip_match(arg, domain, client, state, kind="a")
    if name == "mx":
        return _mx_match(arg, domain, client, state)
    if name == "exists":
        if not arg:
            raise _Stop("permerror", "bad_term", term="exists")
        target = arg.lower().rstrip(".")
        exists = (state["answers"].get("exists") or {}).get(target)
        if exists is None:
            raise _Stop("temperror", "record_not_supplied", missing=target)
        return bool(exists)
    if name == "ptr":
        return _ptr_match(arg, domain, client, state)
    raise _Stop("permerror", "bad_term", term=name)


def _ip_match(arg: str | None, client: Any, version: int) -> bool:
    if not arg:
        raise _Stop("permerror", "bad_term", term="ip" + str(version))
    if client.version != version:
        return False
    try:
        network = ipaddress.ip_network(arg, strict=False)
    except ValueError as exc:
        raise _Stop("permerror", "bad_ip_mechanism", term=arg) from exc
    if network.version != version:
        raise _Stop("permerror", "bad_ip_mechanism", term=arg)
    return client in network


def _split_domain_cidr(arg: str | None, domain: str) -> tuple[str, str | None]:
    host = domain.lower().rstrip(".")
    if not arg:
        return host, None
    # `a/24` reaches here as arg "24" because the mechanism grammar ate the slash.
    if re.fullmatch(r"\d{1,3}", arg):
        return host, arg
    left, sep, right = arg.partition("/")
    name = (left or domain).lower().rstrip(".")
    if not sep:
        return name, None
    return name, right


def _name_ip_match(arg: str | None, domain: str, client: Any, state: dict[str, Any], *, kind: str) -> bool:
    host, cidr = _split_domain_cidr(arg, domain)
    family = "a" if client.version == 4 else "aaaa"
    table = state["answers"].get(family) or {}
    if host not in table:
        raise _Stop("temperror", "record_not_supplied", missing=host)
    addresses = table[host] or []
    prefix = cidr or ("32" if client.version == 4 else "128")
    for item in addresses:
        try:
            network = ipaddress.ip_network(f"{item}/{prefix}", strict=False)
        except ValueError as exc:
            raise _Stop("permerror", "bad_answer", missing=host) from exc
        if client in network:
            return True
    return False


def _mx_match(arg: str | None, domain: str, client: Any, state: dict[str, Any]) -> bool:
    host, cidr = _split_domain_cidr(arg, domain)
    mx_table = state["answers"].get("mx") or {}
    if host not in mx_table:
        raise _Stop("temperror", "record_not_supplied", missing=host)
    for exchanger in mx_table[host] or []:
        state["lookups"] += 1
        if state["lookups"] > _LOOKUP_LIMIT:
            raise _Stop("permerror", "lookup_limit")
        name = str(exchanger).lower().rstrip(".")
        if _name_ip_match(name + (f"/{cidr}" if cidr else ""), name, client, state, kind="a"):
            return True
    return False


def _ptr_match(arg: str | None, domain: str, client: Any, state: dict[str, Any]) -> bool:
    target = (arg or domain).lower().rstrip(".")
    ptr_table = state["answers"].get("ptr") or {}
    ip_key = str(client)
    if ip_key not in ptr_table:
        raise _Stop("temperror", "record_not_supplied", missing=ip_key)
    names = [str(item).lower().rstrip(".") for item in ptr_table[ip_key] or []]
    matched_name = None
    for name in names:
        if name == target or name.endswith("." + target):
            matched_name = name
            break
    if not matched_name:
        return False
    state["lookups"] += 1
    if state["lookups"] > _LOOKUP_LIMIT:
        raise _Stop("permerror", "lookup_limit")
    return _name_ip_match(matched_name, matched_name, client, state, kind="a")
