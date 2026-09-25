"""Local contacts: nicknames, mailbox file, and --json records."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

from azmail.cli import main
from azmail.store import load
from azmail.ui import make_server


def test_contact_round_trip_and_nickname_resolution(tmp_path: Path, capsys):
    box = tmp_path / "mailbox.json"
    code = main(
        ["--mailbox", str(box), "contact", "add", "--nickname", "Sam", "--address", "Sam@Example.com"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Sam" in out
    assert "sam@example.com" in out
    assert str(box) in out

    saved = json.loads(box.read_text(encoding="utf-8"))
    assert saved["contact_book"][0]["nickname"] == "Sam"
    assert saved["contact_book"][0]["address"] == "sam@example.com"
    assert saved["contacts"]["Sam"] == ["sam@example.com"]

    code = main(["--json", "--mailbox", str(box), "contact", "list"])
    listed = json.loads(capsys.readouterr().out)
    assert code == 0
    assert listed["ok"] is True
    assert listed["contacts"][0]["nickname"] == "Sam"
    assert listed["contacts"][0]["address"] == "sam@example.com"

    code = main(
        [
            "--mailbox",
            str(box),
            "contact",
            "edit",
            "--nickname",
            "Sam",
            "--rename",
            "Sammy",
            "--address",
            "sammy@example.com",
        ]
    )
    assert code == 0
    assert "Sammy" in capsys.readouterr().out

    code = main(
        ["--json", "--mailbox", str(box), "receive", "--from", "Sammy", "--subject", "Hi", "--body", "Hello"]
    )
    env = json.loads(capsys.readouterr().out)
    assert code == 0
    assert env["message"]["from"] == "sammy@example.com"
    assert env["message"]["from_display"] == "Sammy"

    code = main(
        ["--json", "--mailbox", str(box), "compose", "--to", "Sammy", "--subject", "Hi", "--body", "Hello"]
    )
    draft = json.loads(capsys.readouterr().out)
    assert code == 0
    assert draft["to"] == "sammy@example.com"
    assert draft["to_nickname"] == "Sammy"

    code = main(
        ["--json", "--mailbox", str(box), "compose", "--to", "other@example.com", "--subject", "Hi", "--body", "Hello"]
    )
    plain = json.loads(capsys.readouterr().out)
    assert plain["to"] == "other@example.com"
    assert "to_nickname" not in plain
    assert set(plain) == {"from", "to", "subject", "body_text", "demo", "note"}

    code = main(["--mailbox", str(box), "contact", "add", "--nickname", "Sammy", "--address", "a@b.com"])
    err = capsys.readouterr().err
    assert code == 1
    assert "already a contact" in err
    assert "azmail contact edit" in err

    code = main(["--mailbox", str(box), "contact", "remove", "--nickname", "Sammy"])
    assert code == 0
    assert load(box)["contact_book"] == []


def test_legacy_contact_dict_becomes_a_book(tmp_path: Path):
    path = tmp_path / "mailbox.json"
    path.write_text(
        json.dumps({"schema": "azmail-mailbox-v0", "contacts": {"paypal billing": ["billing@paypal.com"]}}),
        encoding="utf-8",
    )
    box = load(path)
    assert box["contact_book"][0]["nickname"] == "paypal billing"
    assert box["contact_book"][0]["address"] == "billing@paypal.com"
    assert box["contacts"]["paypal billing"] == ["billing@paypal.com"]


def test_contact_api_and_page(tmp_path: Path):
    page = Path(__file__).resolve().parents[1] / "azmail" / "web" / "index.html"
    text = page.read_text(encoding="utf-8")
    assert text.index('data-view="contacts"') < text.index('id="advanced"')

    server = make_server("127.0.0.1", 0, tmp_path / "mailbox.json")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        conn = HTTPConnection(host, port, timeout=5)
        body = json.dumps({"action": "add", "nickname": "Sam", "address": "sam@example.com"}).encode()
        conn.request(
            "POST",
            "/api/contacts",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        saved = json.loads(conn.getresponse().read().decode())
        conn.close()
        assert saved["ok"] is True
        assert saved["contact"]["nickname"] == "Sam"

        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", "/api/contacts")
        listed = json.loads(conn.getresponse().read().decode())
        conn.close()
        assert listed["contacts"][0]["address"] == "sam@example.com"

        conn = HTTPConnection(host, port, timeout=5)
        check = json.dumps({"from": "Sam", "subject": "Hi", "body_text": "Hello"}).encode()
        conn.request(
            "POST",
            "/api/receive",
            body=check,
            headers={"Content-Type": "application/json", "Content-Length": str(len(check))},
        )
        env = json.loads(conn.getresponse().read().decode())
        conn.close()
        assert env["message"]["from"] == "sam@example.com"
        assert env["resolved"]["nickname"] == "Sam"
    finally:
        server.shutdown()
        server.server_close()
