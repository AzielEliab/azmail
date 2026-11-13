"""Operator SMTP submission. Scripted replies and loopback only — no relay."""

from __future__ import annotations

import base64
import json
import socket
import ssl
import threading
from pathlib import Path

import pytest

from azmail.cli import main
from azmail.outbound import (
    RelayConfig,
    RelaySession,
    ScriptedTransport,
    build_message,
    config_from_env,
    handshake,
    open_submission,
    relay_status,
    submit_message,
)

SECRET = "relay-secret-value"
SENDER = "operator@example.com"


def _config(**overrides) -> RelayConfig:
    values = dict(
        host="127.0.0.1",
        port=2525,
        username="operator",
        secret=SECRET,
        envelope_from=SENDER,
        require_starttls=True,
        auth="plain",
        helo_name="localhost",
    )
    values.update(overrides)
    return RelayConfig(**values)


def _script(*replies: str) -> ScriptedTransport:
    return ScriptedTransport(list(replies))


def _verified_script() -> ScriptedTransport:
    return _script(
        "220 relay.example ESMTP",
        "250-relay.example\r\n250-STARTTLS\r\n250 AUTH PLAIN LOGIN",
        "220 ready",
        "250-relay.example\r\n250 AUTH PLAIN LOGIN",
        "235 ok",
    )


def test_unconfigured_status_is_not_an_mta():
    status = relay_status(None)
    assert status["mta"] is False
    assert status["configured"] is False
    assert status["verified"] is False
    refused = submit_message(None, b"Subject: x\r\n\r\n", ["person@example.com"])
    assert refused["sent"] is False
    assert refused["mta"] is False
    try:
        RelaySession(object(), "x", {})
    except TypeError as exc:
        assert "handshake" in str(exc)
    else:
        raise AssertionError("a session must come from handshake")


def test_complete_config_stays_false_until_handshake():
    status = relay_status(_config())
    assert status["configured"] is True
    assert status["verified"] is False
    assert status["mta"] is False
    assert SECRET not in json.dumps(status)
    assert "secret" not in status
    blocked, transport = open_submission(_config(), allow_network=False)
    assert transport is None
    assert blocked["reason"] == "network_disabled"
    assert blocked["mta"] is False
    assert blocked["connected"] is False


def test_open_submission_does_not_connect_without_permission(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "create_connection", explode)
    blocked, transport = open_submission(_config(), allow_network=False)
    assert transport is None
    assert blocked["mta"] is False
    missing, _transport = open_submission(
        _config(secret=""),
        allow_network=True,
    )
    assert missing["connected"] is False
    assert missing["reason"] == "secret_missing"


def test_connect_failure_is_not_verification():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    status, transport = open_submission(_config(port=port), allow_network=True, timeout=2)
    assert transport is None
    assert status["ok"] is False
    assert status["mta"] is False
    assert status["verified"] is False
    assert status["reason"] == "connect_failed"


def test_handshake_arms_mta_only_after_starttls_and_auth():
    transport = _verified_script()
    status, session = handshake(_config(), transport)
    assert status["mta"] is True
    assert status["verified"] is True
    assert status["tls"] is True
    assert status["tls_mode"] == "scripted"
    assert status["certificate_verified"] is False
    assert status["banner"] == "relay.example ESMTP"
    assert SECRET not in json.dumps(status)
    written = bytes(transport.written)
    assert written.count(b"EHLO localhost\r\n") == 2
    assert b"STARTTLS\r\n" in written
    assert b"MAIL FROM:" not in written
    assert SECRET.encode() not in written
    token = written.split(b"AUTH PLAIN ", 1)[1].split(b"\r\n", 1)[0]
    assert base64.b64decode(token) == b"\x00operator\x00" + SECRET.encode()
    assert session is not None
    assert relay_status(_config(), session)["mta"] is True
    changed = relay_status(_config(secret=SECRET + "-other"), session)
    assert changed["mta"] is False
    assert changed["reason"] == "not_verified"


def test_missing_starttls_or_auth_does_not_arm_mta():
    no_tls, session = handshake(
        _config(),
        _script("220 relay.example ESMTP", "250-relay.example\r\n250 AUTH PLAIN"),
    )
    assert session is None
    assert no_tls["mta"] is False
    assert no_tls["reason"] == "starttls_not_advertised"
    rejected, session = handshake(
        _config(),
        _script(
            "220 relay.example ESMTP",
            "250-relay.example\r\n250-STARTTLS\r\n250 AUTH PLAIN",
            "220 ready",
            "250-relay.example\r\n250 AUTH PLAIN",
            "535 no",
        ),
    )
    assert session is None
    assert rejected["mta"] is False
    assert rejected["reason"] == "smtp_rejected"
    assert rejected["smtp_code"] == 535
    assert SECRET not in json.dumps(rejected)


def test_submit_sends_only_the_named_recipients_and_keeps_the_server_reply():
    transport = _verified_script()
    _status, session = handshake(_config(), transport)
    built = build_message(
        sender=SENDER,
        recipients=["person@example.com"],
        subject="Hello",
        body="Line\r\n.hidden",
    )
    assert built["ok"] is True
    assert built["local_message_id"].endswith("@azmail.invalid")
    transport.push(
        "250 sender ok",
        "250 recipient ok",
        "354 go ahead",
        "250 queued as server-queue-id",
        "221 bye",
    )
    result = submit_message(
        _config(),
        built["message"],
        ["person@example.com"],
        transport=transport,
        session=session,
    )
    assert result["sent"] is True
    assert result["smtp_data_reply"] == "queued as server-queue-id"
    assert result["smtp_data_reply"] != built["local_message_id"]
    written = bytes(transport.written)
    assert b"MAIL FROM:<operator@example.com>\r\n" in written
    assert written.count(b"RCPT TO:") == 1
    assert b"RCPT TO:<person@example.com>\r\n" in written
    assert b"\r\n..hidden\r\n" in written
    assert b"other@example.com" not in written
    refused = submit_message(_config(), built["message"], ["person@example.com"])
    assert refused["sent"] is False
    assert refused["reason"] == "not_verified"


def test_recipient_rejection_is_not_a_sent_message():
    transport = _verified_script()
    _status, session = handshake(_config(), transport)
    transport.push("550 denied")
    result = submit_message(
        _config(),
        b"Subject: hi\r\n\r\nbody\r\n",
        ["person@example.com"],
        transport=transport,
        session=session,
    )
    assert result["sent"] is False
    assert result["reason"] == "smtp_rejected"
    assert result["smtp_code"] == 550
    assert b"DATA\r\n" not in bytes(transport.written).split(b"AUTH PLAIN ", 1)[-1]


def test_header_injection_and_cleartext_auth_are_explicit():
    injected = build_message(sender=SENDER, recipients=["person@example.com"], subject="hi\r\nBcc: x", body="n")
    assert injected["ok"] is False
    clear = _script(
        "220 relay.example ESMTP",
        "250-relay.example\r\n250 AUTH LOGIN",
        "334 VXNlcm5hbWU6",
        "334 UGFzc3dvcmQ6",
        "235 ok",
    )
    status, session = handshake(_config(require_starttls=False, auth="login"), clear)
    assert status["mta"] is True
    assert status["tls"] is False
    assert status["certificate_verified"] is False
    assert session is not None
    assert SECRET.encode() not in bytes(clear.written)


def test_untrusted_certificate_does_not_arm_mta_or_send_the_secret(tmp_path: Path):
    key = tmp_path / "key.pem"
    cert = tmp_path / "cert.pem"
    if not _write_cert(key, cert):
        pytest.skip("openssl unavailable")
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(5)
    port = server.getsockname()[1]
    received: list[bytes] = []

    def serve() -> None:
        try:
            conn, _addr = server.accept()
        except OSError:
            return
        conn.settimeout(5)
        try:
            conn.sendall(b"220 local ESMTP\r\n")
            data = b""

            def read_line() -> bytes:
                nonlocal data
                while b"\n" not in data:
                    chunk = conn.recv(4096)
                    if not chunk:
                        return b""
                    data += chunk
                line, rest = data.split(b"\n", 1)
                data = rest
                received.append(line + b"\n")
                return line

            read_line()
            conn.sendall(b"250-localhost\r\n250 STARTTLS\r\n")
            read_line()
            conn.sendall(b"220 go\r\n")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert, key)
            try:
                tls = context.wrap_socket(conn, server_side=True)
                tls.settimeout(2)
                chunk = tls.recv(4096)
                if chunk:
                    received.append(chunk)
                tls.close()
            except ssl.SSLError:
                return
        except OSError:
            return
        finally:
            try:
                conn.close()
            except OSError:
                return

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        status, transport = open_submission(_config(port=port), allow_network=True, timeout=5)
        assert transport is not None
        armed, session = handshake(_config(port=port), transport)
        transport.close()
    finally:
        server.close()
        thread.join(timeout=5)
    assert status["connected"] is True
    assert status["mta"] is False
    assert session is None
    assert armed["mta"] is False
    assert armed["reason"] == "tls_failed"
    blob = b"".join(received)
    assert SECRET.encode() not in blob
    assert b"AUTH" not in blob


def _write_cert(key: Path, cert: Path) -> bool:
    import subprocess

    try:
        subprocess.check_call(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "1",
                "-nodes",
                "-subj",
                "/CN=localhost",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def test_relay_status_command_never_connects(monkeypatch, capsys, tmp_path: Path):
    for name in (
        "AZMAIL_RELAY_HOST",
        "AZMAIL_RELAY_PORT",
        "AZMAIL_RELAY_USER",
        "AZMAIL_RELAY_SECRET",
        "AZMAIL_RELAY_FROM",
    ):
        monkeypatch.delenv(name, raising=False)

    def explode(*_args, **_kwargs):
        raise AssertionError("socket opened")

    monkeypatch.setattr(socket, "create_connection", explode)
    code = main(["relay", "status"])
    out = capsys.readouterr().out
    assert code == 0
    assert "mta: false" in out
    monkeypatch.setenv("AZMAIL_RELAY_HOST", "127.0.0.1")
    monkeypatch.setenv("AZMAIL_RELAY_PORT", "2525")
    monkeypatch.setenv("AZMAIL_RELAY_USER", "operator")
    monkeypatch.setenv("AZMAIL_RELAY_SECRET", SECRET)
    monkeypatch.setenv("AZMAIL_RELAY_FROM", SENDER)
    code = main(["--json", "relay", "status"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["configured"] is True
    assert payload["verified"] is False
    assert payload["mta"] is False
    assert SECRET not in json.dumps(payload)
    assert config_from_env() is not None
    assert tmp_path is not None
