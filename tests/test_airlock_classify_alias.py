"""Local UI leftover /api/classify aliases FragGate op airlock_classify."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

from azmail.ui import make_server


def test_local_airlock_classify_and_classify_alias(tmp_path: Path) -> None:
    mailbox = tmp_path / "mailbox.json"
    server = make_server("127.0.0.1", 0, mailbox)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    payload = json.dumps(
        {
            "from": "help@paypa1-verify.com",
            "subject": "URGENT verify your account",
            "body_text": "reset your password immediately",
        }
    ).encode("utf-8")
    try:
        bodies = {}
        for path in ("/api/airlock_classify", "/api/classify"):
            conn = HTTPConnection(host, port, timeout=5)
            conn.request(
                "POST",
                path,
                body=payload,
                headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
            )
            res = conn.getresponse()
            bodies[path] = json.loads(res.read().decode("utf-8"))
            conn.close()
            assert res.status == 200
            assert bodies[path]["op"] == "airlock_classify"
            assert bodies[path]["verdict"]
        assert bodies["/api/airlock_classify"]["verdict"] == bodies["/api/classify"]["verdict"]
    finally:
        server.shutdown()
        server.server_close()
