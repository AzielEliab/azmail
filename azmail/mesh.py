"""Anonymous MCP mesh — product-side contract + local client helpers.

Live broadcast/listen runs via aziel-runtime FragGate (engine lands in a
sibling PR). This module is the local contract: off by default, easy off
switch, keyword alerts without identity, no PII in handles, rate limits,
refuse doxxing / credential-harvest content.

SPLIT THE WIRES (STW-1.0) and COLD-COPY SURVIVAL (CCS-1.0) are locked
product-local mesh law. Mesh hop stays default-off. Author: Aziel Eliab only.
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
    "call": "POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call {\"slug\":\"azmail\",\"op\":\"<mesh_enable|mesh_disable|broadcast|listen|keyword_alerts>\",\"payload\":{}}",
    "note": "Engine lands in a sibling aziel-runtime PR. Local helpers implement the contract only.",
}

# --- SPLIT THE WIRES (STW-1.0) locked law ---------------------------------
# Tip-only 0.5–1s tick (presence + tip hash, fixed-size).
# Pull-only payload plane.
# Update = proof, not a timer (cite prev + lockset, fail-closed;
# 777s dwell after a valid cite; clock desync ≠ yes; ambiguous = isolate).
# Equivocation ends the peer. Emit last locally. Phoenix local only.
# Partition: no auto-splice. Heartbeat loss ≠ poison ≠ apply last packet.
# 1s tick socket ≠ 777s dwell socket. Mesh hop default-off stays.

STW_SPEC = "STW-1.0"
STW_TITLE = "SPLIT THE WIRES"
STW_AUTHOR = "Aziel Eliab"
TICK_MIN_SEC = 0.5
TICK_MAX_SEC = 1.0
DWELL_SEC = 777
TIP_HASH_HEX_LEN = 64
TIP_TICK_BYTES = 65  # 1 presence code + 64 hex tip hash
PLANE_TIP = "tip"
PLANE_PAYLOAD = "payload"
SOCKET_TICK = "tick_1s"
SOCKET_DWELL = "dwell_777s"
MESH_HOP_DEFAULT_OFF = True
PRESENCE_WIRE = {"live": "L", "locked": "K", "isolated": "I"}
PRESENCE_CODES = {code: name for name, code in PRESENCE_WIRE.items()}

STW_LAW: dict[str, Any] = {
    "spec": STW_SPEC,
    "title": STW_TITLE,
    "author": STW_AUTHOR,
    "identity": STW_AUTHOR,
    "hop_default": False,
    "hop_default_off": True,
    "tick_min_sec": TICK_MIN_SEC,
    "tick_max_sec": TICK_MAX_SEC,
    "dwell_sec": DWELL_SEC,
    "tip_only": True,
    "tip_fields": ("presence", "tip_hash"),
    "tip_tick_bytes": TIP_TICK_BYTES,
    "tip_hash_hex_len": TIP_HASH_HEX_LEN,
    "payload_plane": "pull",
    "update": "proof",
    "cite": "prev+lockset",
    "fail_closed": True,
    "clock_desync_is_yes": False,
    "ambiguous": "isolate",
    "equivocation": "ends_peer",
    "emit_last": "local",
    "phoenix": "local_only",
    "auto_splice": False,
    "heartbeat_loss_is_poison": False,
    "heartbeat_loss_applies_last_packet": False,
    "sockets": {SOCKET_TICK: TICK_MAX_SEC, SOCKET_DWELL: DWELL_SEC},
    "note": (
        "SPLIT THE WIRES STW-1.0. Tip-only 0.5–1s tick (presence+tip hash "
        "fixed-size). Pull-only payload plane. Update is proof, not a timer "
        "(cite prev+lockset fail-closed; 777s dwell after valid cite; clock "
        "desync is not yes; ambiguous isolates). Equivocation ends peer. "
        "Emit last locally. Phoenix local only. Partition does not auto-splice. "
        "Heartbeat loss is not poison and does not apply the last packet. "
        "1s tick socket is not the 777s dwell socket. Mesh hop default-off stays. "
        "Author: Aziel Eliab only."
    ),
}

# --- COLD-COPY SURVIVAL (CCS-1.0) locked law ------------------------------
# Multiply cold copies. Refuse live body sync. Tip is expensive to erase.
# Server pull cannot wipe cold replicas. Hash-absolute poison refuse.
# Data outlives creators. Keeps SPLIT THE WIRES.

CCS_SPEC = "CCS-1.0"
CCS_TITLE = "COLD-COPY SURVIVAL"
COLD_COPY_MIN = 2

CCS_LAW: dict[str, Any] = {
    "spec": CCS_SPEC,
    "title": CCS_TITLE,
    "author": STW_AUTHOR,
    "identity": STW_AUTHOR,
    "multiply": True,
    "min_copies": COLD_COPY_MIN,
    "live_body_sync": False,
    "tip_erase": "expensive",
    "server_pull_wipes_cold": False,
    "poison": "hash_absolute_refuse",
    "data_outlives_creators": True,
    "keeps_split_the_wires": True,
    "hop_default_off": True,
    "note": (
        "COLD-COPY SURVIVAL CCS-1.0. Multiply cold copies. Refuse live body "
        "sync. Tip is expensive to erase. Server pull cannot wipe cold replicas. "
        "Hash-absolute poison refuse (not interpret). Data outlives creators. "
        "Keeps SPLIT THE WIRES. Mesh hop default-off stays. Author: Aziel Eliab only."
    ),
}


def _hex64(value: str) -> str | None:
    digest = str(value or "").strip().lower()
    if len(digest) != TIP_HASH_HEX_LEN:
        return None
    if any(ch not in "0123456789abcdef" for ch in digest):
        return None
    return digest


def encode_tip_tick(presence: str, tip_hash: str, *, payload: Any = None) -> dict[str, Any]:
    """Tip-only 0.5–1s tick: presence + tip hash, fixed size. No payload."""
    if payload not in (None, "", b""):
        return {"ok": False, "code": "STW_TIP_ONLY", "plane": PLANE_TIP, "payload": None}
    if presence not in PRESENCE_WIRE:
        return {"ok": False, "code": "STW_PRESENCE_UNKNOWN", "presence": presence}
    digest = _hex64(tip_hash)
    if digest is None:
        return {"ok": False, "code": "STW_TIP_HASH_SIZE", "want": TIP_HASH_HEX_LEN}
    wire = PRESENCE_WIRE[presence] + digest
    return {
        "ok": True,
        "code": "STW_OK",
        "plane": PLANE_TIP,
        "socket": SOCKET_TICK,
        "presence": presence,
        "tip_hash": digest,
        "wire": wire,
        "bytes": len(wire),
        "payload": None,
    }


def decode_tip_tick(wire: str) -> dict[str, Any]:
    raw = str(wire or "")
    if len(raw) != TIP_TICK_BYTES:
        return {"ok": False, "code": "STW_TIP_HASH_SIZE", "bytes": len(raw)}
    presence = PRESENCE_CODES.get(raw[0])
    digest = _hex64(raw[1:])
    if presence is None or digest is None:
        return {"ok": False, "code": "STW_TIP_ONLY"}
    return encode_tip_tick(presence, digest)


def tick_interval_ok(seconds: float) -> bool:
    try:
        dt = float(seconds)
    except (TypeError, ValueError):
        return False
    return TICK_MIN_SEC <= dt <= TICK_MAX_SEC


def admit_payload(
    *,
    direction: str,
    plane: str = PLANE_PAYLOAD,
    socket: str = SOCKET_DWELL,
    hop_enabled: bool = False,
) -> dict[str, Any]:
    """Pull-only payload plane. Hop default-off stays. 1s ≠ 777s sockets."""
    if hop_enabled:
        return {"ok": False, "code": "STW_HOP_DEFAULT_OFF", "hop": False, "enabled": False}
    if plane != PLANE_PAYLOAD:
        return {"ok": False, "code": "STW_PLANE_SPLIT", "plane": plane}
    if socket != SOCKET_DWELL:
        return {"ok": False, "code": "STW_SOCKET_SPLIT", "note": "1s tick socket is not the 777s dwell socket"}
    if str(direction).strip().lower() != "pull":
        return {"ok": False, "code": "STW_PULL_ONLY", "direction": direction, "payload_plane": "pull"}
    return {
        "ok": True,
        "code": "STW_OK",
        "plane": PLANE_PAYLOAD,
        "direction": "pull",
        "socket": SOCKET_DWELL,
        "hop": False,
    }


def decide_update(event: dict[str, Any] | None) -> dict[str, Any]:
    """Update is proof, not a timer. Cite prev+lockset fail-closed."""
    ev = event if isinstance(event, dict) else {}
    kind = str(ev.get("kind") or ev.get("reason") or "").strip().lower()
    if ev.get("clock_desync") or kind in {"clock_desync", "desync"}:
        return {"ok": False, "apply": False, "yes": False, "code": "STW_CLOCK_DESYNC_NOT_YES"}
    if ev.get("ambiguous") or kind == "ambiguous":
        return {"ok": False, "apply": False, "isolate": True, "code": "STW_AMBIGUOUS_ISOLATE"}
    if kind == "heartbeat_loss" or ev.get("heartbeat_loss"):
        return heartbeat_loss()
    timer_only = bool(ev.get("timer")) or kind == "timer"
    prev = ev.get("prev") or ev.get("cite_prev")
    lockset = ev.get("lockset")
    if timer_only and not (prev and lockset):
        return {"ok": False, "apply": False, "code": "STW_UPDATE_NOT_TIMER"}
    if not prev or not lockset or ev.get("valid_cite") is False:
        return {"ok": False, "apply": False, "fail_closed": True, "code": "STW_CITE_FAIL_CLOSED"}
    return {
        "ok": True,
        "apply": True,
        "dwell_sec": DWELL_SEC,
        "fail_closed": False,
        "code": "STW_OK",
        "cite": "prev+lockset",
    }


def equivocation_ends_peer(peer: str, tips: list[str]) -> dict[str, Any]:
    unique = {str(t).strip().lower() for t in tips if t}
    if len(unique) > 1:
        return {"ok": True, "peer": peer, "ended": True, "apply": False, "code": "STW_EQUIVOCATION_ENDS_PEER"}
    return {"ok": True, "peer": peer, "ended": False, "code": "STW_OK"}


def emit_last(*, scope: str = "local") -> dict[str, Any]:
    if str(scope).strip().lower() != "local":
        return {"ok": False, "relay": False, "code": "STW_EMIT_LAST_LOCAL"}
    return {"ok": True, "emit": "last", "scope": "local", "relay": False, "code": "STW_OK"}


def phoenix(*, scope: str = "local") -> dict[str, Any]:
    if str(scope).strip().lower() != "local":
        return {"ok": False, "public_restore": False, "code": "STW_PHOENIX_LOCAL_ONLY"}
    return {"ok": True, "scope": "local", "public_restore": False, "code": "STW_PHOENIX_LOCAL"}


def partition_heal(*, auto_splice: bool = False) -> dict[str, Any]:
    if auto_splice:
        return {"ok": False, "splice": False, "code": "STW_NO_AUTO_SPLICE"}
    return {"ok": True, "splice": False, "code": "STW_PARTITION_HOLD"}


def heartbeat_loss() -> dict[str, Any]:
    return {
        "ok": True,
        "poison": False,
        "apply": False,
        "apply_last_packet": False,
        "code": "STW_HEARTBEAT_LOSS_NOT_POISON",
    }


def sockets_are_split(tick_socket: str, dwell_socket: str) -> dict[str, Any]:
    if tick_socket == dwell_socket or tick_socket != SOCKET_TICK or dwell_socket != SOCKET_DWELL:
        return {"ok": False, "code": "STW_SOCKET_SPLIT", "note": "1s ≠ 777s sockets"}
    return {"ok": True, "tick": SOCKET_TICK, "dwell": SOCKET_DWELL, "code": "STW_OK"}


def hop_status() -> dict[str, Any]:
    return {"enabled": False, "default_off": True, "code": "STW_HOP_DEFAULT_OFF"}


def hop_enable() -> dict[str, Any]:
    return {
        "ok": False,
        "enabled": False,
        "default_off": True,
        "code": "STW_HOP_DEFAULT_OFF",
        "note": "Mesh hop default-off stays.",
    }


def split_the_wires() -> dict[str, Any]:
    return dict(STW_LAW)


def cold_copy_survival() -> dict[str, Any]:
    return dict(CCS_LAW)


def multiply_cold_copies(copies: list[Any] | None) -> dict[str, Any]:
    """Cold replicas must be multiplied. A single copy is not survival."""
    rows = [c for c in (copies or []) if c is not None]
    live = []
    hashes: list[str] = []
    for raw in rows:
        if isinstance(raw, dict):
            if raw.get("cold") is False or raw.get("live") is True:
                live.append(raw)
            digest = raw.get("hash") or raw.get("body_hash") or raw.get("tip_hash")
        else:
            digest = raw
        if digest:
            hashes.append(str(digest))
    if live:
        return {"ok": False, "code": "CCS_LIVE_BODY_SYNC_REFUSED", "copies": len(rows)}
    if len(rows) < COLD_COPY_MIN:
        return {"ok": False, "code": "CCS_MULTIPLY", "min_copies": COLD_COPY_MIN, "copies": len(rows)}
    return {
        "ok": True,
        "code": "CCS_OK",
        "copies": len(rows),
        "min_copies": COLD_COPY_MIN,
        "distinct": len(set(hashes)) if hashes else len(rows),
        "cold": True,
    }


def live_body_sync(*, source: str = "live", target: str = "cold") -> dict[str, Any]:
    return {
        "ok": False,
        "synced": False,
        "source": source,
        "target": target,
        "code": "CCS_LIVE_BODY_SYNC_REFUSED",
        "note": "Refuse live body sync. Cold copies stay cold.",
    }


def erase_tip(*, expensive: bool = False) -> dict[str, Any]:
    return {
        "ok": False,
        "erased": False,
        "expensive": bool(expensive),
        "code": "CCS_TIP_ERASE_EXPENSIVE",
        "note": "Tip is expensive to erase. Cheap wipe is refused.",
    }


def server_pull(*, wipe_cold: bool = False, replicas: list[Any] | None = None) -> dict[str, Any]:
    kept = list(replicas or [])
    if wipe_cold:
        return {
            "ok": False,
            "wiped": False,
            "replicas": kept,
            "copies": len(kept),
            "code": "CCS_SERVER_PULL_NO_WIPE",
            "note": "Server pull cannot wipe cold replicas.",
        }
    return {
        "ok": True,
        "wiped": False,
        "replicas": kept,
        "copies": len(kept),
        "direction": "pull",
        "code": "CCS_OK",
    }


def poison_refuse(digest: str, poison: list[str] | set[str] | None = None) -> dict[str, Any]:
    """Hash-absolute poison refuse. No interpret. Exact 64-hex only."""
    want = _hex64(digest)
    if want is None:
        return {"ok": False, "apply": False, "code": "CCS_POISON_HASH_ABSOLUTE"}
    marked = {_hex64(str(h)) for h in (poison or [])}
    marked.discard(None)
    if want in marked:
        return {
            "ok": False,
            "apply": False,
            "interpret": False,
            "hash": want,
            "code": "CCS_POISON_HASH_ABSOLUTE",
            "note": "Hash-absolute poison refuse. Not interpreted.",
        }
    return {"ok": True, "apply": False, "interpret": False, "hash": want, "poison": False, "code": "CCS_OK"}


def creator_gone(creator: str, replicas: list[Any] | None = None) -> dict[str, Any]:
    kept = list(replicas or [])
    return {
        "ok": True,
        "creator": creator,
        "gone": True,
        "wiped": False,
        "replicas": kept,
        "copies": len(kept),
        "data_remains": True,
        "code": "CCS_DATA_OUTLIVES_CREATORS",
        "note": "Data outlives creators.",
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
            "hop": hop_status(),
            "split_the_wires": split_the_wires(),
            "cold_copy_survival": cold_copy_survival(),
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
