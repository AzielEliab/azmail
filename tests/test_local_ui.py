"""Local loopback UI: human page, JSON when asked, same health record."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

from azmail import __version__
from azmail.ui import make_server

PAGE = Path(__file__).resolve().parents[1] / "azmail" / "web" / "index.html"


def test_page_meets_the_human_layout():
    text = PAGE.read_text(encoding="utf-8")
    assert 'name="viewport"' in text
    assert "prefers-color-scheme" in text
    assert ":focus-visible" in text
    assert ">Advanced</summary>" in text
    assert "Check this message" in text
    assert "Aziel Eliab" in text
    assert "THIS IS NOT" not in text
    assert "Not an MTA" not in text


def test_root_is_html_unless_json_is_asked(tmp_path: Path):
    server = make_server("127.0.0.1", 0, tmp_path / "mailbox.json")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        page = HTTPConnection(host, port, timeout=5)
        page.request("GET", "/", headers={"Accept": "text/html"})
        html = page.getresponse()
        body = html.read().decode("utf-8")
        page.close()
        assert html.status == 200
        assert "text/html" in html.getheader("Content-Type")
        assert "Check this message" in body

        machine = HTTPConnection(host, port, timeout=5)
        machine.request("GET", "/", headers={"Accept": "application/json"})
        raw = machine.getresponse()
        payload = json.loads(raw.read().decode("utf-8"))
        machine.close()
        assert raw.status == 200
        assert payload["ok"] is True
        assert payload["product"] == "azmail"
        assert payload["version"] == __version__
        assert payload["loopback"] is True
        assert "limitation" in payload
        assert payload["mta"] is False

        health = HTTPConnection(host, port, timeout=5)
        health.request("GET", "/api/health")
        health_body = json.loads(health.getresponse().read().decode("utf-8"))
        health.close()
        assert health_body == payload
    finally:
        server.shutdown()
        server.server_close()
