"""Anonymous MCP mesh — product-side contract + local client helpers.

Live broadcast/listen runs via aziel-runtime FragGate (engine lands in a
sibling PR). This module is the local contract: off by default, easy off
switch, keyword alerts without identity, no PII in handles, rate limits,
refuse doxxing / credential-harvest content.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Any

from azmail.reputation import domain_of

MESH_OFF_BY_DEFAULT = True
RATE_LIMIT = 10
RATE_WINDOW_SEC = 60
HANDLE_PREFIX = "anon-"

# Product refuses to carry these on the mesh. Not a content-moderation API
# for the public internet — a local refuse list so the microphone stays clean.
DOX_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-shaped
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),  # PAN-shaped
    re.compile(r"\blives at\b", re.I),
    re.compile(r"\bhome address\b", re.I),
    re.compile(r"\breal name is\b", re.I),
    re.compile(r"\bphone number is\b", re.I),
    re.compile(r"\bdox\b", re.I),
    re.compile(r"\bdoxx", re.I),
)
CRED_PATTERNS = (
    re.compile(r"\bpassword\s*[:=]", re.I),
    re.compile(r"\bpasswd\s*[:=]", re.I),
    re.compile(r"\bapi[_-]?key\s*[:=]", re.I),
    re.compile(r"\bsecret\s*[:=]", re.I),
    re.compile(r"\bbearer\s+[a-z0-9._\-]+", re.I),
    re.compile(r"\bharvest(?:ing)? (?:passwords|credentials|logins)\b", re.I),
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I)

RUNTIME_HINT = {
    "door": "fraggate",
    "runtime": "https://aziel-runtime.vibelock.workers.dev",
    "kernel": "https://github.com/AzielEliab/fraggate",
    "call": "fraggate_call name=azmail op=<mesh_enable|mesh_disable|broadcast|listen|keyword_alerts>",
    "note": "Engine lands in a sibling aziel-runtime PR. Local helpers implement the contract only.",
}


def anonymous_handle(seed: str | None = None) -> str:
    """Non-PII mesh handle. Never an email, never a legal name."""
    raw = (seed or str(time.time_ns())).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:10]
    return HANDLE_PREFIX + digest


def refuse_reason(text: str) -> str | None:
    blob = text or ""
    if EMAIL_RE.search(blob):
        return "mesh_refuse_pii: email-shaped handle or body (no PII on the mesh)"
    if any(p.search(blob) for p in DOX_PATTERNS):
        return "mesh_refuse_doxxing"
    if any(p.search(blob) for p in CRED_PATTERNS):
        return "mesh_refuse_credential_harvest"
    if "@" in blob and domain_of(blob):
        # bare name@host without TLD still treated as identity leak
        if re.search(r"\b\S+@\S+\b", blob):
            return "mesh_refuse_pii: mailbox-shaped token"
    return None


@dataclass
class MeshClient:
    enabled: bool = False
    handle: str = field(default_factory=anonymous_handle)
    keywords: list[str] = field(default_factory=list)
    inbox: list[dict[str, Any]] = field(default_factory=list)
    _stamps: list[float] = field(default_factory=list)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "handle": self.handle,
            "keywords": list(self.keywords),
            "off_by_default": MESH_OFF_BY_DEFAULT,
            "rate_limit": RATE_LIMIT,
            "rate_window_sec": RATE_WINDOW_SEC,
            "runtime": RUNTIME_HINT,
            "limitation": "Local contract. Live mesh is FragGate, not this process.",
        }

    def enable(self) -> dict[str, Any]:
        self.enabled = True
        return {"ok": True, "enabled": True, "handle": self.handle, **self.status()}

    def disable(self) -> dict[str, Any]:
        self.enabled = False
        return {"ok": True, "enabled": False, "handle": self.handle, "note": "Mesh off. Easy off-switch. No further broadcasts."}

    def _rate_ok(self) -> bool:
        now = time.time()
        self._stamps = [t for t in self._stamps if now - t < RATE_WINDOW_SEC]
        return len(self._stamps) < RATE_LIMIT

    def broadcast(self, text: str) -> dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "code": "MESH_DISABLED",
                "enabled": False,
                "note": "Mesh is off (default). Call mesh_enable first. Easy off-switch: mesh_disable.",
                "runtime": RUNTIME_HINT,
            }
        reason = refuse_reason(text)
        if reason:
            return {"ok": False, "code": "MESH_REFUSE", "reason": reason, "enabled": True}
        if not self._rate_ok():
            return {"ok": False, "code": "MESH_RATE_LIMIT", "limit": RATE_LIMIT, "window_sec": RATE_WINDOW_SEC}
        self._stamps.append(time.time())
        item = {
            "handle": self.handle,
            "text": text,
            "ts": time.time(),
        }
        self.inbox.append(item)
        alerts = match_keywords(text, self.keywords)
        return {"ok": True, "enabled": True, "handle": self.handle, "queued": True, "keyword_alerts": alerts, "runtime": RUNTIME_HINT}

    def listen(self) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "code": "MESH_DISABLED", "items": [], "enabled": False}
        return {"ok": True, "enabled": True, "handle": self.handle, "items": list(self.inbox), "runtime": RUNTIME_HINT}

    def set_keywords(self, keywords: list[str]) -> dict[str, Any]:
        cleaned = []
        for raw in keywords:
            token = str(raw).strip().lower()
            if not token:
                continue
            if refuse_reason(token):
                continue
            if token not in cleaned:
                cleaned.append(token)
        self.keywords = cleaned
        return {"ok": True, "keywords": list(self.keywords), "note": "Alerts fire without revealing subscriber identity."}


def match_keywords(text: str, keywords: list[str]) -> list[dict[str, Any]]:
    """Keyword alerts. The alert names the keyword, never a legal identity."""
    blob = (text or "").lower()
    alerts: list[dict[str, Any]] = []
    for key in keywords:
        token = key.strip().lower()
        if token and token in blob:
            alerts.append(
                {
                    "keyword": token,
                    "matched": True,
                    "identity": None,
                    "note": "Alert without revealing identity.",
                }
            )
    return alerts


# Module-level session used by CLI / doctor (off by default).
_SESSION = MeshClient()


def mesh_enable() -> dict[str, Any]:
    return _SESSION.enable()


def mesh_disable() -> dict[str, Any]:
    return _SESSION.disable()


def mesh_status() -> dict[str, Any]:
    return _SESSION.status()


def mesh_broadcast(text: str) -> dict[str, Any]:
    return _SESSION.broadcast(text)


def mesh_listen() -> dict[str, Any]:
    return _SESSION.listen()


def mesh_keywords(keywords: list[str]) -> dict[str, Any]:
    return _SESSION.set_keywords(keywords)


def mesh_session() -> MeshClient:
    return _SESSION
