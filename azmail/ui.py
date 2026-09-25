"""Loopback-only AZMail UI. 127.0.0.1 only. No CDN. No telemetry."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from azmail import DEFAULT_PORT, LIMITATION, LOOPBACK, SIGIL_URL, SPEC_STRING, __version__
from azmail.airlock import classify
from azmail.contacts import (
    ContactError,
    add_contact,
    apply_sender,
    edit_contact,
    list_contacts,
    remove_contact,
    resolve_recipient,
)
from azmail.mesh import MeshClient, match_keywords
from azmail.scrub import scrub_html
from azmail.store import confirm_release, ingest, load, mesh_from_box, mesh_into_box, save

WEB = Path(__file__).with_name("web")


def make_server(host: str, port: int, mailbox: Path | None = None) -> ThreadingHTTPServer:
    if host not in {LOOPBACK, "localhost"}:
        raise ValueError("AZMail UI binds loopback only (127.0.0.1). Refusing " + host)
    box_path = Path(mailbox or Path.home() / ".azmail" / "mailbox.json")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _json(self, payload: Any, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self) -> None:
            path = WEB / "index.html"
            text = path.read_text(encoding="utf-8")
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            return json.loads(raw.decode("utf-8") or "{}")

        def _wants_json(self) -> bool:
            accept = (self.headers.get("Accept") or "").lower()
            json_at = accept.find("application/json")
            if json_at < 0:
                return False
            html_at = accept.find("text/html")
            if html_at < 0:
                return True
            return json_at < html_at

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                if self._wants_json():
                    self._json(_health())
                    return
                self._html()
                return
            box = load(box_path)
            if path == "/api/box":
                self._json(box)
                return
            if path == "/api/health":
                self._json(_health())
                return
            if path == "/api/contacts":
                self._json({"ok": True, "contacts": list_contacts(box)})
                return
            if path == "/api/doctor":
                from azmail.doctor import run_doctor
                import io
                import contextlib

                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    code = run_doctor(as_json=True)
                try:
                    payload = json.loads(buf.getvalue())
                except json.JSONDecodeError:
                    payload = {"ok": code == 0, "raw": buf.getvalue()}
                self._json(payload)
                return
            self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            body = self._read_json()
            box = load(box_path)
            if path == "/api/receive":
                payload, note = apply_sender(box, body)
                if payload.get("to"):
                    target, nick = resolve_recipient(list_contacts(box), str(payload.get("to") or ""))
                    payload["to"] = target
                    if nick:
                        payload["to_nickname"] = nick
                env = ingest(box, payload, confirmed=bool(body.get("confirmed")))
                save(box_path, box)
                out = env.as_dict()
                if note:
                    out["resolved"] = note
                self._json(out)
                return
            if path in {"/api/classify", "/api/airlock_classify"}:
                payload, note = apply_sender(box, body)
                out = classify(payload).as_dict()
                out["op"] = "airlock_classify"
                if note:
                    out["resolved"] = note
                self._json(out)
                return
            if path == "/api/contacts":
                action = str(body.get("action") or "list")
                try:
                    if action == "list":
                        self._json({"ok": True, "contacts": list_contacts(box)})
                        return
                    if action == "add":
                        contact = add_contact(
                            box,
                            nickname=str(body.get("nickname") or ""),
                            address=str(body.get("address") or ""),
                            handle=str(body.get("handle") or ""),
                            name=str(body.get("name") or ""),
                        )
                    elif action == "edit":
                        contact = edit_contact(
                            box,
                            contact_id=str(body.get("id") or ""),
                            nickname=str(body.get("nickname") or ""),
                            address=body.get("address") if "address" in body else None,
                            handle=body.get("handle") if "handle" in body else None,
                            name=body.get("name") if "name" in body else None,
                            rename=body.get("rename") if "rename" in body else None,
                        )
                    elif action == "remove":
                        removed = remove_contact(
                            box,
                            contact_id=str(body.get("id") or ""),
                            nickname=str(body.get("nickname") or ""),
                        )
                        save(box_path, box)
                        self._json({"ok": True, "removed": removed})
                        return
                    else:
                        self._json(
                            {
                                "ok": False,
                                "error": "Say list, add, edit, or remove.",
                                "hint": "azmail contact list",
                            },
                            400,
                        )
                        return
                except ContactError as exc:
                    self._json({"ok": False, "error": exc.text, "hint": exc.hint}, 400)
                    return
                save(box_path, box)
                self._json({"ok": True, "contact": contact})
                return
            if path == "/api/scrub":
                self._json(scrub_html(str(body.get("html") or "")))
                return
            if path == "/api/release":
                row = confirm_release(box, str(body.get("id") or ""))
                save(box_path, box)
                self._json({"ok": bool(row), "row": row})
                return
            if path == "/api/compose":
                target, nick = resolve_recipient(list_contacts(box), str(body.get("to") or ""))
                draft = {
                    "from": body.get("from") or "local@azmail.demo",
                    "to": target,
                    "subject": body.get("subject") or "",
                    "body_text": body.get("body") or body.get("body_text") or "",
                    "demo": True,
                    "note": "v0.1 compose is local only. It does not send internet email.",
                }
                if nick:
                    draft["to_nickname"] = nick
                box.setdefault("drafts", []).append(draft)
                save(box_path, box)
                self._json(draft)
                return
            if path == "/api/import":
                incoming = body.get("mailbox") or body
                if incoming.get("schema") == "azmail-mailbox-v0":
                    box = incoming
                    save(box_path, box)
                    self._json({"ok": True, "imported": "mailbox"})
                    return
                self._json({"ok": False, "error": "schema"}, 400)
                return
            if path == "/api/mesh":
                client = mesh_from_box(box)
                action = str(body.get("action") or "")
                if action == "enable":
                    out = client.enable()
                elif action == "disable":
                    out = client.disable()
                elif action == "broadcast":
                    out = client.broadcast(str(body.get("text") or ""))
                elif action == "listen":
                    out = client.listen()
                elif action == "keywords":
                    out = client.set_keywords(list(body.get("keywords") or []))
                else:
                    out = client.status()
                mesh_into_box(box, client)
                save(box_path, box)
                self._json(out)
                return
            if path == "/api/keywords/match":
                client = mesh_from_box(box)
                self._json({"alerts": match_keywords(str(body.get("text") or ""), client.keywords)})
                return
            self._json({"error": "not found"}, 404)

    return ThreadingHTTPServer((host, port), Handler)


def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "azmail",
        "version": __version__,
        "spec": SPEC_STRING,
        "limitation": LIMITATION,
        "sigil": SIGIL_URL,
        "loopback": True,
        "mta": False,
    }


def open_line(port: int) -> str:
    return f"Open http://{LOOPBACK}:{port}/"


def serve(host: str = LOOPBACK, port: int = DEFAULT_PORT, mailbox: Path | None = None) -> int:
    try:
        server = make_server(host, port, mailbox)
    except ValueError as exc:
        print(f"{exc}\nTry: azmail ui", file=sys.stderr)
        return 1
    except OSError:
        print(
            f"Port {port} is already in use.\nTry: azmail ui --port {int(port) + 1}",
            file=sys.stderr,
        )
        return 1
    bound = int(server.server_address[1])
    print(open_line(bound))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    return 0


# Imported by doctor for the unused-import-safe type check.
_ = MeshClient
