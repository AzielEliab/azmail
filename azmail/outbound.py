"""Operator-gated SMTP submission (RFC 5321 / RFC 6409).

This is not a public MTA and it does not listen. `mta` is true only after
`handshake` sees a real greeting, EHLO, STARTTLS when required, and a 235
from AUTH on the transport the caller passed in. Nothing here opens a
socket unless `open_submission` is called with `allow_network=True`.
Secrets stay on the config object and are omitted from status dicts.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import os
import re
import socket
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate, make_msgid
from typing import Any

_ADDR = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
_HOST = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
_HELO = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
_MAX_MESSAGE = 10_000_000
_MAX_RECIPIENTS = 100
_ISSUED = object()


@dataclass
class RelayConfig:
    host: str
    port: int
    username: str
    secret: str
    envelope_from: str
    require_starttls: bool = True
    auth: str = "plain"
    helo_name: str = "localhost"

    def __repr__(self) -> str:
        return (
            "RelayConfig("
            f"host={self.host!r}, port={self.port!r}, username={self.username!r}, "
            f"envelope_from={self.envelope_from!r}, require_starttls={self.require_starttls!r}, "
            f"auth={self.auth!r}, helo_name={self.helo_name!r}, secret='***')"
        )


class RelaySession:
    """Issued only by `handshake`. A hand-built session cannot authorize a send."""

    def __init__(self, issued: object, config_id: str, public: dict[str, Any]) -> None:
        if issued is not _ISSUED:
            raise TypeError("RelaySession is issued only by handshake")
        self.config_id = config_id
        self.public = dict(public)


class ScriptedTransport:
    """In-memory SMTP peer. Each entry is one server reply, possibly multiline."""

    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self._lines: list[bytes] = []
        self.written = bytearray()
        self.tls_active = False
        self.certificate_verified = False
        self.tls_mode = "clear"

    def readline(self) -> bytes:
        if not self._lines:
            if not self._replies:
                raise TimeoutError("script exhausted")
            block = self._replies.pop(0)
            if not block.endswith("\n"):
                block += "\r\n"
            self._lines = [line.encode("utf-8") + b"\r\n" for line in block.splitlines()]
        return self._lines.pop(0)

    def write(self, data: bytes) -> None:
        self.written += data

    def starttls(self, server_hostname: str) -> None:
        del server_hostname
        self.tls_active = True
        self.tls_mode = "scripted"

    def push(self, *replies: str) -> None:
        self._replies.extend(replies)

    def close(self) -> None:
        return None


class SocketTransport:
    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._pending = b""
        self.tls_active = False
        self.certificate_verified = False
        self.tls_mode = "clear"

    def readline(self) -> bytes:
        while b"\n" not in self._pending:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("smtp closed")
            self._pending += chunk
            if len(self._pending) > 65536:
                raise ConnectionError("smtp reply too long")
        line, self._pending = self._pending.split(b"\n", 1)
        return line + b"\n"

    def write(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            sent = self._sock.send(view)
            if sent <= 0:
                raise ConnectionError("smtp write failed")
            view = view[sent:]

    def starttls(self, server_hostname: str) -> None:
        context = ssl.create_default_context()
        self._sock = context.wrap_socket(self._sock, server_hostname=server_hostname)
        self.tls_active = True
        self.certificate_verified = True
        self.tls_mode = "starttls"
        self._pending = b""

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            return None


def config_from_env(env: dict[str, str] | None = None) -> RelayConfig | None:
    source = os.environ if env is None else env
    host = (source.get("AZMAIL_RELAY_HOST") or "").strip()
    if not host and not (source.get("AZMAIL_RELAY_USER") or source.get("AZMAIL_RELAY_SECRET") or source.get("AZMAIL_RELAY_FROM")):
        return None
    port_text = (source.get("AZMAIL_RELAY_PORT") or "").strip()
    try:
        port = int(port_text) if port_text else 0
    except ValueError:
        port = 0
    starttls = (source.get("AZMAIL_RELAY_STARTTLS") or "1").strip().lower()
    return RelayConfig(
        host=host,
        port=port,
        username=(source.get("AZMAIL_RELAY_USER") or "").strip(),
        secret=source.get("AZMAIL_RELAY_SECRET") or "",
        envelope_from=(source.get("AZMAIL_RELAY_FROM") or "").strip(),
        require_starttls=starttls not in {"0", "false", "no", "off"},
        auth=((source.get("AZMAIL_RELAY_AUTH") or "plain").strip().lower() or "plain"),
        helo_name=(source.get("AZMAIL_RELAY_HELO") or "localhost").strip() or "localhost",
    )


def validate_config(config: RelayConfig | None) -> str | None:
    if config is None:
        return "not_configured"
    if not isinstance(config.port, int) or isinstance(config.port, bool) or not 1 <= config.port <= 65535:
        return "bad_port"
    if not _good_host(config.host or ""):
        return "bad_host"
    if not _ADDR.match(config.envelope_from or ""):
        return "bad_envelope_from"
    if not config.username or _has_break(config.username) or "\x00" in config.username:
        return "username_missing" if not config.username else "bad_username"
    if not config.secret or _has_break(config.secret) or "\x00" in config.secret:
        return "secret_missing" if not config.secret else "bad_secret"
    if config.auth not in {"plain", "login"}:
        return "bad_auth"
    if not _HELO.match(config.helo_name or ""):
        return "bad_helo"
    return None


def relay_status(config: RelayConfig | None = None, session: RelaySession | None = None) -> dict[str, Any]:
    problem = validate_config(config)
    if problem or config is None:
        return {
            "ok": problem is None,
            "configured": False,
            "verified": False,
            "mta": False,
            "reason": problem or "not_configured",
            "connected": False,
            "dns_queried": False,
        }
    public = _config_public(config)
    if not isinstance(session, RelaySession) or session.config_id != _config_id(config):
        public.update({"ok": True, "configured": True, "verified": False, "mta": False, "reason": "not_verified"})
        return public
    view = dict(session.public)
    view["mta"] = bool(view.get("verified"))
    return view


def handshake(config: RelayConfig | None, transport: Any) -> tuple[dict[str, Any], RelaySession | None]:
    problem = validate_config(config)
    if problem or config is None:
        return (
            {
                "ok": False,
                "configured": False,
                "verified": False,
                "mta": False,
                "reason": problem or "not_configured",
                "connected": False,
                "dns_queried": False,
            },
            None,
        )
    try:
        return _handshake(config, transport)
    except _SmtpDone as done:
        return _denied(config, "smtp_rejected", smtp_code=done.code, smtp_reply=done.text), None
    except Exception as exc:
        failed = _config_public(config)
        failed.update(
            {
                "ok": False,
                "configured": True,
                "verified": False,
                "mta": False,
                "reason": "smtp_error",
                "detail": type(exc).__name__,
            }
        )
        return failed, None


def submit_message(
    config: RelayConfig | None,
    message: bytes | str,
    recipients: list[str],
    *,
    transport: Any = None,
    session: RelaySession | None = None,
) -> dict[str, Any]:
    status = relay_status(config, session)
    if config is None or session is None or not status.get("mta"):
        return {
            "ok": False,
            "sent": False,
            "mta": False,
            "configured": bool(status.get("configured")),
            "verified": False,
            "reason": status.get("reason") or "not_verified",
            "smtp_data_reply": None,
            "dns_queried": False,
        }
    if transport is None:
        return {
            "ok": False,
            "sent": False,
            "mta": False,
            "configured": True,
            "verified": True,
            "reason": "transport_missing",
            "smtp_data_reply": None,
            "dns_queried": False,
        }
    targets = []
    for item in recipients:
        if not isinstance(item, str) or not _ADDR.match(item) or _has_break(item):
            return _unsent("bad_recipient")
        targets.append(item)
    if not targets:
        return _unsent("no_recipient")
    if len(targets) > _MAX_RECIPIENTS:
        return _unsent("too_many_recipients")
    payload = message.encode("utf-8") if isinstance(message, str) else bytes(message)
    if not payload:
        return _unsent("empty_message")
    if len(payload) > _MAX_MESSAGE:
        return _unsent("message_too_large")
    if _has_break(config.envelope_from):
        return _unsent("bad_envelope_from")
    try:
        mail = _read_ok(transport, _command(transport, f"MAIL FROM:<{config.envelope_from}>"), {250})
        accepted = []
        for target in targets:
            reply = _read_ok(transport, _command(transport, f"RCPT TO:<{target}>"), {250, 251})
            accepted.append({"recipient": target, "code": reply[0], "text": reply[1]})
        data = _read_ok(transport, _command(transport, "DATA"), {354})
        transport.write(_dot_stuff(payload))
        done = _read_reply(transport)
        quit_code = None
        try:
            _command(transport, "QUIT")
            quit_reply = _read_reply(transport)
            quit_code = quit_reply[0]
        except Exception:
            quit_code = None
        sent = done[0] == 250
        return {
            "ok": sent,
            "sent": sent,
            "mta": True,
            "configured": True,
            "verified": True,
            "reason": "" if sent else "data_rejected",
            "smtp_mail_code": mail[0],
            "recipients": accepted,
            "smtp_data_code": data[0],
            "smtp_data_reply": done[1],
            "smtp_data_status": done[0],
            "quit_code": quit_code,
            "dns_queried": False,
        }
    except _SmtpDone as done:
        return {
            "ok": False,
            "sent": False,
            "mta": True,
            "configured": True,
            "verified": True,
            "reason": "smtp_rejected",
            "smtp_code": done.code,
            "smtp_reply": done.text,
            "smtp_data_reply": None,
            "dns_queried": False,
        }
    except Exception as exc:
        return {
            "ok": False,
            "sent": False,
            "mta": True,
            "configured": True,
            "verified": True,
            "reason": "smtp_error",
            "detail": type(exc).__name__,
            "smtp_data_reply": None,
            "dns_queried": False,
        }


def build_message(*, sender: str, recipients: list[str], subject: str, body: str) -> dict[str, Any]:
    if not _ADDR.match(sender or "") or any(not _ADDR.match(item) for item in recipients):
        return {"ok": False, "reason": "bad_address"}
    if any(_has_break(item) for item in (sender, subject, *recipients)):
        return {"ok": False, "reason": "header_rejected"}
    msg = EmailMessage(policy=SMTP)
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg["Date"] = formatdate(usegmt=True)
    local_id = make_msgid(domain="azmail.invalid")
    msg["Message-ID"] = local_id
    msg.set_content(body or "")
    raw = msg.as_bytes(policy=SMTP)
    return {"ok": True, "message": raw, "local_message_id": local_id.strip("<>"), "domain": "azmail.invalid"}


def open_submission(
    config: RelayConfig | None,
    *,
    allow_network: bool = False,
    timeout: float = 30.0,
) -> tuple[dict[str, Any], SocketTransport | None]:
    problem = validate_config(config)
    if problem or config is None:
        return (
            {
                "ok": False,
                "configured": False,
                "verified": False,
                "mta": False,
                "reason": problem or "not_configured",
                "connected": False,
                "dns_queried": False,
            },
            None,
        )
    if allow_network is not True:
        public = _config_public(config)
        public.update({"ok": False, "configured": True, "verified": False, "mta": False, "reason": "network_disabled"})
        return public, None
    try:
        sock = socket.create_connection((config.host, int(config.port)), timeout)
    except OSError as exc:
        public = _config_public(config)
        public.update(
            {
                "ok": False,
                "configured": True,
                "verified": False,
                "mta": False,
                "reason": "connect_failed",
                "detail": exc.strerror or type(exc).__name__,
                "connected": False,
            }
        )
        return public, None
    public = _config_public(config)
    public.update({"ok": True, "configured": True, "verified": False, "mta": False, "reason": "connected_not_verified", "connected": True})
    return public, SocketTransport(sock)


def _handshake(config: RelayConfig, transport: Any) -> tuple[dict[str, Any], RelaySession | None]:
    greeting = _read_reply(transport)
    if greeting[0] != 220:
        return _denied(config, "greeting_rejected", smtp_code=greeting[0], smtp_reply=greeting[1]), None
    ehlo = _expect(_command(transport, f"EHLO {config.helo_name}"), transport, {250})
    caps = _capabilities(ehlo[1])
    tls = False
    certificate_verified = False
    if config.require_starttls:
        if "starttls" not in caps:
            return _denied(config, "starttls_not_advertised", capabilities=sorted(caps)), None
        ready = _expect(_command(transport, "STARTTLS"), transport, {220})
        try:
            transport.starttls(config.host)
        except Exception:
            return _denied(config, "tls_failed"), None
        if not getattr(transport, "tls_active", False):
            return _denied(config, "tls_not_established"), None
        tls = True
        certificate_verified = bool(getattr(transport, "certificate_verified", False))
        ehlo = _expect(_command(transport, f"EHLO {config.helo_name}"), transport, {250})
        caps = _capabilities(ehlo[1])
    mechanisms = caps.get("auth", [])
    wanted = config.auth.upper()
    if wanted not in mechanisms:
        return _denied(config, "auth_not_advertised", capabilities=sorted(caps)), None
    if config.auth == "plain":
        token = base64.b64encode(b"\x00" + config.username.encode("utf-8") + b"\x00" + config.secret.encode("utf-8")).decode("ascii")
        auth = _expect(_command(transport, f"AUTH PLAIN {token}"), transport, {235})
    else:
        _expect(_command(transport, "AUTH LOGIN"), transport, {334})
        _expect(_command(transport, base64.b64encode(config.username.encode("utf-8")).decode("ascii")), transport, {334})
        auth = _expect(
            _command(transport, base64.b64encode(config.secret.encode("utf-8")).decode("ascii")),
            transport,
            {235},
        )
    public = _config_public(config)
    public.update(
        {
            "ok": True,
            "configured": True,
            "verified": True,
            "mta": True,
            "reason": "",
            "tls": tls,
            "tls_mode": getattr(transport, "tls_mode", "starttls" if tls else "clear"),
            "certificate_verified": certificate_verified,
            "capabilities": sorted(caps),
            "banner": greeting[1].splitlines()[0][:200],
            "auth_reply": auth[1][:200],
            "connected": True,
        }
    )
    return public, RelaySession(_ISSUED, _config_id(config), public)


def _config_public(config: RelayConfig) -> dict[str, Any]:
    return {
        "ok": True,
        "configured": True,
        "verified": False,
        "mta": False,
        "host": config.host,
        "port": config.port,
        "username": config.username,
        "envelope_from": config.envelope_from,
        "require_starttls": config.require_starttls,
        "auth": config.auth,
        "helo_name": config.helo_name,
        "connected": False,
        "dns_queried": False,
        "reason": "",
    }


def _config_id(config: RelayConfig) -> str:
    material = "\n".join(
        [
            config.host.lower(),
            str(config.port),
            config.username,
            config.envelope_from.lower(),
            config.auth,
            "1" if config.require_starttls else "0",
            config.helo_name.lower(),
            hashlib.sha256(config.secret.encode("utf-8")).hexdigest(),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _denied(config: RelayConfig, reason: str, **extra: Any) -> dict[str, Any]:
    public = _config_public(config)
    public.update({"ok": False, "configured": True, "verified": False, "mta": False, "reason": reason})
    public.update(extra)
    return public


def _unsent(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "sent": False,
        "mta": True,
        "configured": True,
        "verified": True,
        "reason": reason,
        "smtp_data_reply": None,
        "dns_queried": False,
    }


class _SmtpDone(Exception):
    def __init__(self, code: int, text: str) -> None:
        super().__init__(text)
        self.code = code
        self.text = text


def _command(transport: Any, line: str) -> None:
    if "\r" in line or "\n" in line:
        raise ValueError("smtp newline")
    transport.write((line + "\r\n").encode("ascii"))


def _expect(command: None, transport: Any, codes: set[int]) -> tuple[int, str]:
    del command
    return _read_ok(transport, None, codes)


def _read_ok(transport: Any, command: None, codes: set[int]) -> tuple[int, str]:
    del command
    code, text = _read_reply(transport)
    if code not in codes:
        raise _SmtpDone(code, text)
    return code, text


def _read_reply(transport: Any) -> tuple[int, str]:
    lines: list[str] = []
    code: int | None = None
    while True:
        raw = transport.readline()
        if not isinstance(raw, (bytes, bytearray)):
            raise TypeError("reply")
        if len(raw) > 8192:
            raise ConnectionError("smtp line too long")
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if len(line) < 4 or not line[:3].isdigit() or line[3] not in {" ", "-"}:
            raise ConnectionError("bad smtp reply")
        this = int(line[:3])
        if code is None:
            code = this
        elif this != code:
            raise ConnectionError("smtp code changed")
        lines.append(line[4:])
        if line[3] == " ":
            return code, "\n".join(lines)


def _capabilities(text: str) -> dict[str, list[str]]:
    caps: dict[str, list[str]] = {}
    for line in text.splitlines()[1:]:
        parts = line.strip().split()
        if not parts:
            continue
        name = parts[0].lower()
        args: list[str] = []
        for part in parts[1:]:
            args.extend(piece.upper() for piece in part.split("=") if piece)
        caps[name] = args
    return caps


def _dot_stuff(message: bytes) -> bytes:
    text = message.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    lines = text.split(b"\n")
    stuffed = [b"." + line if line.startswith(b".") else line for line in lines]
    body = b"\r\n".join(stuffed)
    if not body.endswith(b"\r\n"):
        body += b"\r\n"
    return body + b".\r\n"


def _has_break(value: str) -> bool:
    return any(char in value for char in ("\r", "\n", "\x00"))


def _good_host(host: str) -> bool:
    if _HOST.match(host) and not host.startswith(".") and ".." not in host and not host.endswith("."):
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            labels = host.split(".")
            return all(labels) and all(not label.startswith("-") and not label.endswith("-") for label in labels)
    if ":" in host:
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False
    return False
