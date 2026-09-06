"""AZMail command line. Local airlock + compose + mesh helpers. Not an MTA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from azmail import DEFAULT_PORT, LIMITATION, LOOPBACK, SPEC_STRING, __version__
from azmail.airlock import classify, process
from azmail.doctor import run_doctor
from azmail.mesh import (
    match_keywords,
    mesh_broadcast,
    mesh_disable,
    mesh_enable,
    mesh_keywords,
    mesh_listen,
    mesh_session,
    mesh_status,
)
from azmail.scrub import scrub_html
from azmail.store import confirm_release, default_mailbox, ingest, load, save

DEFAULT_BOX = Path.home() / ".azmail" / "mailbox.json"


def _print(data: Any, as_json: bool) -> None:
    if as_json or isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)


def _box_path(ns: argparse.Namespace) -> Path:
    return Path(getattr(ns, "mailbox", None) or DEFAULT_BOX)


def cmd_version(_ns: argparse.Namespace) -> int:
    print(f"azmail {__version__} ({SPEC_STRING})")
    print(LIMITATION)
    return 0


def cmd_doctor(ns: argparse.Namespace) -> int:
    return run_doctor(as_json=bool(getattr(ns, "json", False)))


def cmd_ui(ns: argparse.Namespace) -> int:
    from azmail.ui import serve

    return serve(host=LOOPBACK, port=int(ns.port), mailbox=_box_path(ns))


def cmd_classify(ns: argparse.Namespace) -> int:
    payload = json.loads(Path(ns.file).read_text(encoding="utf-8")) if ns.file else {
        "from": ns.sender,
        "to": ns.to,
        "subject": ns.subject,
        "body_text": ns.body,
        "body_html": ns.html or "",
        "headers": json.loads(ns.headers) if ns.headers else {},
    }
    result = classify(payload).as_dict()
    _print(result, True)
    return 0


def cmd_receive(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    box = load(path)
    msg = {
        "from": ns.sender,
        "to": ns.to,
        "subject": ns.subject,
        "body_text": ns.body,
        "body_html": ns.html or "",
        "headers": json.loads(ns.headers) if ns.headers else {},
    }
    env = ingest(box, msg, confirmed=bool(ns.confirm))
    save(path, box)
    _print(env.as_dict(), True)
    return 0


def cmd_release(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    box = load(path)
    row = confirm_release(box, ns.id)
    if not row:
        print(json.dumps({"ok": False, "error": "not in airlock", "id": ns.id}, indent=2))
        return 1
    save(path, box)
    _print({"ok": True, "released": row}, True)
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    box = load(_box_path(ns))
    which = ns.which
    _print({which: box.get(which, [])}, True)
    return 0


def cmd_scrub(ns: argparse.Namespace) -> int:
    html = Path(ns.file).read_text(encoding="utf-8") if ns.file else ns.html
    _print(scrub_html(html or ""), True)
    return 0


def cmd_process(ns: argparse.Namespace) -> int:
    payload = json.loads(Path(ns.file).read_text(encoding="utf-8"))
    env = process(payload, confirmed=bool(ns.confirm))
    _print(env.as_dict(), True)
    return 0


def cmd_import(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    incoming = json.loads(Path(ns.file).read_text(encoding="utf-8"))
    box = load(path)
    if incoming.get("schema") == box.get("schema"):
        box = incoming
    elif isinstance(incoming, dict) and "from" in incoming:
        ingest(box, incoming)
    elif isinstance(incoming, list):
        for item in incoming:
            ingest(box, item)
    else:
        print(json.dumps({"ok": False, "error": "unrecognized import"}, indent=2))
        return 1
    save(path, box)
    _print({"ok": True, "inbox": len(box["inbox"]), "airlock": len(box["airlock"])}, True)
    return 0


def cmd_export(ns: argparse.Namespace) -> int:
    box = load(_box_path(ns))
    text = json.dumps(box, indent=2, ensure_ascii=False)
    if ns.file:
        Path(ns.file).write_text(text + "\n", encoding="utf-8")
        print(ns.file)
    else:
        print(text)
    return 0


def cmd_verify(ns: argparse.Namespace) -> int:
    box = load(_box_path(ns))
    ok = box.get("schema") == "azmail-mailbox-v0"
    report = {
        "ok": ok,
        "schema": box.get("schema"),
        "inbox": len(box.get("inbox") or []),
        "airlock": len(box.get("airlock") or []),
        "quarantine": len(box.get("quarantine") or []),
        "mesh_enabled": bool((box.get("mesh") or {}).get("enabled")),
        "limitation": LIMITATION,
    }
    _print(report, True)
    return 0 if ok else 1


def cmd_mesh(ns: argparse.Namespace) -> int:
    action = ns.action
    if action == "enable":
        _print(mesh_enable(), True)
        return 0
    if action == "disable":
        _print(mesh_disable(), True)
        return 0
    if action == "status":
        _print(mesh_status(), True)
        return 0
    if action == "broadcast":
        _print(mesh_broadcast(ns.text or ""), True)
        return 0
    if action == "listen":
        _print(mesh_listen(), True)
        return 0
    return 1


def cmd_keywords(ns: argparse.Namespace) -> int:
    session = mesh_session()
    if ns.action == "list":
        _print({"keywords": session.keywords, "note": "Alerts do not reveal identity."}, True)
        return 0
    if ns.action == "set":
        _print(mesh_keywords(ns.words or []), True)
        return 0
    if ns.action == "match":
        _print({"alerts": match_keywords(ns.text or "", session.keywords)}, True)
        return 0
    return 1


def cmd_compose(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    box = load(path) if path.exists() else default_mailbox()
    draft = {
        "from": ns.sender or "local@azmail.demo",
        "to": ns.to,
        "subject": ns.subject,
        "body_text": ns.body,
        "demo": True,
        "note": "v0.1 compose is local only. It does not send internet email.",
    }
    box.setdefault("drafts", []).append(draft)
    save(path, box)
    _print(draft, True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="azmail", description="AZMail APP 1.0 — local Mail Airlock. Not an MTA.")
    p.add_argument("--mailbox", default=str(DEFAULT_BOX), help="Local mailbox JSON path")
    p.add_argument("--json", action="store_true", help="JSON output where applicable")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version")
    d = sub.add_parser("doctor")
    d.add_argument("--json", action="store_true")
    u = sub.add_parser("ui")
    u.add_argument("--port", type=int, default=DEFAULT_PORT)
    u.add_argument("--mailbox", default=str(DEFAULT_BOX))

    c = sub.add_parser("classify")
    c.add_argument("--file")
    c.add_argument("--from", dest="sender", default="")
    c.add_argument("--to", default="")
    c.add_argument("--subject", default="")
    c.add_argument("--body", default="")
    c.add_argument("--html", default="")
    c.add_argument("--headers", default="")

    r = sub.add_parser("receive")
    r.add_argument("--from", dest="sender", required=True)
    r.add_argument("--to", default="you@local")
    r.add_argument("--subject", default="")
    r.add_argument("--body", default="")
    r.add_argument("--html", default="")
    r.add_argument("--headers", default="")
    r.add_argument("--confirm", action="store_true")

    rel = sub.add_parser("release")
    rel.add_argument("id")

    lst = sub.add_parser("list")
    lst.add_argument("which", choices=("inbox", "airlock", "quarantine", "drafts"))

    s = sub.add_parser("scrub")
    s.add_argument("--file")
    s.add_argument("--html", default="")

    pr = sub.add_parser("process")
    pr.add_argument("file")
    pr.add_argument("--confirm", action="store_true")

    imp = sub.add_parser("import")
    imp.add_argument("file")
    exp = sub.add_parser("export")
    exp.add_argument("--file")
    sub.add_parser("verify")

    m = sub.add_parser("mesh")
    m.add_argument("action", choices=("enable", "disable", "status", "broadcast", "listen"))
    m.add_argument("--text", default="")

    k = sub.add_parser("keywords")
    k.add_argument("action", choices=("list", "set", "match"))
    k.add_argument("words", nargs="*")
    k.add_argument("--text", default="")

    co = sub.add_parser("compose")
    co.add_argument("--from", dest="sender", default="")
    co.add_argument("--to", required=True)
    co.add_argument("--subject", default="")
    co.add_argument("--body", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    handlers = {
        "version": cmd_version,
        "doctor": cmd_doctor,
        "ui": cmd_ui,
        "classify": cmd_classify,
        "receive": cmd_receive,
        "release": cmd_release,
        "list": cmd_list,
        "scrub": cmd_scrub,
        "process": cmd_process,
        "import": cmd_import,
        "export": cmd_export,
        "verify": cmd_verify,
        "mesh": cmd_mesh,
        "keywords": cmd_keywords,
        "compose": cmd_compose,
    }
    return handlers[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main())
