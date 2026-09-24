"""AZMail command line. Human text by default. --json keeps the machine record."""

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

WELCOME = """AZMail checks a message before it lands in your inbox, and holds anything risky until you release it.

Open the app:
  azmail ui

Check this install:
  azmail doctor

More commands:
  azmail --help

Author: Aziel Eliab
"""

TOP_HELP = f"""azmail — check a message before it lands in your inbox

usage:
  azmail [--mailbox PATH] [--json] <command> [<args>]

Author: Aziel Eliab

Common commands:
  ui         Open the local app at http://{LOOPBACK}:{DEFAULT_PORT}/
  doctor     Check this install
  classify   Judge a message without saving it
  receive    Hold a message in the airlock
  list       Show inbox, airlock, quarantine, or drafts
  release    Move a held message into the inbox

Advanced commands:
  scrub      Strip tracking and scripts from HTML
  process    Run the airlock on a JSON file
  import     Load a mailbox or a message file
  export     Write the mailbox
  verify     Check the mailbox file
  mesh       Local anonymous ring (off until you turn it on)
  keywords   Alert words for that ring
  compose    Save a draft on this computer
  version    Print the version

Add --json for the machine record. People get the sentences above.

Examples:
  azmail ui
  azmail doctor
  azmail classify --from 'a@b.com' --subject hello --body hi
  azmail receive --from 'a@b.com' --subject hello --body hi
  azmail list airlock
"""

FLAG_WORDS = {
    "urgency": "Urgent wording",
    "credentials": "Asks for a password or login",
    "payment_language": "Payment wording",
    "unexpected_attachment": "Unexpected attachment",
    "first_seen_sender": "Sender not in your history",
    "display_name_address_mismatch": "Display name does not match the address",
    "unexpected_domain_for_known_name": "Known name on a different domain",
    "known_phish": "Known phishing pattern",
    "lookalike": "Lookalike domain",
    "new_or_suspicious_domain": "New or unusual domain",
    "source_unverified": "Sender authentication was not a pass",
    "html_scrubbed": "Something was removed from the HTML",
}

BADGE_LINE = {
    "verified": "Verified",
    "unverified": "Unverified",
    "high-risk": "High risk",
    "quarantined": "Quarantined",
}

VERDICT_LINE = {
    "release": "Ready for the inbox",
    "hold": "Held in the airlock",
    "confirm": "Waiting for your OK",
    "quarantine": "Set aside in quarantine",
}

LIST_LABEL = {
    "inbox": "Inbox",
    "airlock": "Airlock",
    "quarantine": "Quarantine",
    "drafts": "Drafts",
}


class CliStop(Exception):
    def __init__(
        self,
        text: str,
        hint: str,
        *,
        code: int = 1,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(text)
        self.text = text
        self.hint = hint
        self.code = code
        self.body = body


class FriendlyParser(argparse.ArgumentParser):
    raw_argv: list[str]
    as_json: bool

    def error(self, message: str) -> None:
        text, hint = explain_error(message, getattr(self, "raw_argv", []))
        if getattr(self, "as_json", False):
            print(json.dumps({"ok": False, "error": text, "hint": hint}, indent=2, ensure_ascii=False))
        else:
            print(f"{text} Try: {hint}", file=sys.stderr)
        self.exit(2)


def _box_path(ns: argparse.Namespace) -> Path:
    return Path(getattr(ns, "mailbox", None) or DEFAULT_BOX)


def _as_json(ns: argparse.Namespace) -> bool:
    return bool(getattr(ns, "json", False))


def _emit(ns: argparse.Namespace, data: Any, human: str) -> None:
    if _as_json(ns):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(human)


def _emit_error(
    ns: argparse.Namespace,
    text: str,
    hint: str,
    code: int = 1,
    body: dict[str, Any] | None = None,
) -> int:
    if _as_json(ns):
        payload = body if body is not None else {"ok": False, "error": text, "hint": hint}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"{text} Try: {hint}", file=sys.stderr)
    return code


def _flag_line(flags: list[str] | None) -> str:
    if not flags:
        return ""
    words = [FLAG_WORDS.get(flag, flag) for flag in flags]
    return "Notes: " + "; ".join(words)


def _first_command(argv: list[str]) -> str:
    skip_value = False
    for arg in argv:
        if skip_value:
            skip_value = False
            continue
        if arg == "--mailbox":
            skip_value = True
            continue
        if arg.startswith("--mailbox="):
            continue
        if arg.startswith("-"):
            continue
        return arg
    return ""


def explain_error(message: str, argv: list[str]) -> tuple[str, str]:
    cmd = _first_command(argv)
    choice = ""
    if "invalid choice:" in message:
        start = message.find("invalid choice: '")
        if start >= 0:
            rest = message[start + len("invalid choice: '") :]
            choice = rest.split("'", 1)[0]
    known = {"list", "mesh", "keywords", "ui", "doctor", "classify", "receive", "release", "scrub", "process", "import", "export", "verify", "compose", "version"}
    if "invalid choice" in message and cmd not in known:
        name = choice or cmd or "that"
        return (f'Unknown command "{name}".', "azmail ui   or   azmail --help")
    if "invalid choice" in message and cmd == "list":
        return ("That list name is not one AZMail keeps.", "azmail list airlock")
    if "invalid choice" in message and cmd == "mesh":
        return ("Say status, enable, disable, broadcast, or listen.", "azmail mesh status")
    if "invalid choice" in message and cmd == "keywords":
        return ("Say list, set, or match.", "azmail keywords list")
    if "required" in message and "--from" in message:
        return (
            "Receive needs the sender.",
            "azmail receive --from 'name@example.com' --subject 'Hello' --body 'Message'",
        )
    if "required" in message and "--to" in message:
        return (
            "Compose needs --to.",
            "azmail compose --to 'name@example.com' --subject 'Hello' --body 'Message'",
        )
    if cmd == "release" and "required" in message:
        return ("Release needs the message id.", "azmail list airlock")
    if cmd == "list" and "required" in message:
        return ("Name the list: inbox, airlock, quarantine, or drafts.", "azmail list airlock")
    if cmd == "process" and "required" in message:
        return ("Process needs a JSON file.", "azmail process message.json")
    if cmd == "import" and "required" in message:
        return ("Import needs a file.", "azmail import mailbox.json")
    if cmd == "mesh" and "required" in message:
        return ("Say what the ring should do.", "azmail mesh status")
    if cmd == "keywords" and "required" in message:
        return ("Say list, set, or match.", "azmail keywords list")
    if "expected one argument" in message and "--mailbox" in message:
        return ("Add a path after --mailbox.", "azmail --mailbox ~/.azmail/mailbox.json ui")
    if "invalid int value" in message:
        return ("The port needs to be a number.", "azmail ui --port 8876")
    if message.startswith("unrecognized arguments"):
        return ("Those options are not used here.", "azmail --help")
    return ("Could not run that.", "azmail --help")


def _load_json_file(path: str) -> Any:
    file = Path(path)
    if not file.is_file():
        raise CliStop(f"No file at {path}.", "Check the path and try again.")
    try:
        text = file.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise CliStop(f"{path} is not UTF-8 text.", "Save the file as UTF-8 JSON.") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CliStop(f"{path} is not JSON.", "Use a .json mailbox or message file.") from exc


def _headers(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliStop(
            "The headers value is not JSON.",
            'azmail classify --headers \'{"Authentication-Results":"spf=pass"}\'',
        ) from exc
    if not isinstance(data, dict):
        raise CliStop("Headers must be a JSON object.", "azmail classify --help")
    return data


def _message_from_flags(ns: argparse.Namespace) -> dict[str, Any]:
    return {
        "from": ns.sender,
        "to": ns.to,
        "subject": ns.subject,
        "body_text": ns.body,
        "body_html": ns.html or "",
        "headers": _headers(ns.headers) if getattr(ns, "headers", "") else {},
    }


def format_classification(result: dict[str, Any], *, saved: str | None = None) -> str:
    badge = str(result.get("badge") or "")
    verdict = str(result.get("verdict") or "")
    lines = [
        BADGE_LINE.get(badge, badge or "Checked"),
        VERDICT_LINE.get(verdict, verdict),
    ]
    flags = _flag_line(list(result.get("flags") or []))
    if flags:
        lines.append(flags)
    if saved:
        lines.append(saved)
    lines.append("Next: azmail receive --from 'name@example.com' --subject 'Hello' --body 'Message'")
    return "\n".join(line for line in lines if line)


def format_envelope(env: dict[str, Any]) -> str:
    cls = env.get("classification") or {}
    msg = env.get("message") or {}
    verdict = cls.get("verdict")
    if env.get("released"):
        place = "In your inbox."
        nxt = "azmail list inbox"
    elif verdict == "quarantine":
        place = "Set aside in quarantine."
        nxt = "azmail list quarantine"
    else:
        place = "Held in the airlock."
        nxt = f"azmail release {env.get('id')}"
    lines = [place, f"Id: {env.get('id')}", BADGE_LINE.get(cls.get("badge"), cls.get("badge") or "")]
    if msg.get("from"):
        lines.append(f"From: {msg['from']}")
    if msg.get("subject"):
        lines.append(f"Subject: {msg['subject']}")
    flags = _flag_line(list(cls.get("flags") or []))
    if flags:
        lines.append(flags)
    lines.append(f"Next: {nxt}")
    return "\n".join(line for line in lines if line)


def format_list(which: str, rows: list[dict[str, Any]]) -> str:
    title = LIST_LABEL.get(which, which)
    if not rows:
        empty = {
            "inbox": "Inbox is empty.",
            "airlock": "Airlock is empty.",
            "quarantine": "Quarantine is empty.",
            "drafts": "No drafts yet.",
        }.get(which, f"{title} is empty.")
        nxt = {
            "inbox": "azmail ui",
            "airlock": "azmail receive --from 'name@example.com' --subject 'Hello' --body 'Message'",
            "quarantine": "azmail list inbox",
            "drafts": "azmail compose --to 'name@example.com' --subject 'Hello' --body 'Message'",
        }.get(which, "azmail --help")
        return f"{empty}\nTry: {nxt}"
    lines = [f"{title} ({len(rows)})"]
    for row in rows:
        if which == "drafts":
            lines.append(f"  {row.get('to') or '(no recipient)'}  {row.get('subject') or '(no subject)'}")
            continue
        msg = row.get("message") or {}
        cls = row.get("classification") or {}
        badge = BADGE_LINE.get(cls.get("badge"), cls.get("badge") or "")
        lines.append(f"  {row.get('id')}  {badge}")
        lines.append(f"    {msg.get('subject') or '(no subject)'} — {msg.get('from') or ''}")
    if which == "airlock":
        lines.append(f"Next: azmail release {rows[0].get('id')}")
    return "\n".join(lines)


def format_scrub(out: dict[str, Any]) -> str:
    kinds = out.get("stripped_kinds") or []
    if out.get("changed"):
        head = "HTML rewritten."
        if kinds:
            head += "\nRemoved: " + ", ".join(kinds)
    else:
        head = "HTML unchanged."
    return head + "\n" + str(out.get("html") or "")


def _refuse_plain(reason: str) -> str:
    if reason == "mesh_refuse_credential_harvest":
        return "That text looks like a password or a credential."
    if reason == "mesh_refuse_doxxing":
        return "That text looks like it identifies a person."
    if reason.startswith("mesh_refuse_pii"):
        return "That text looks like an email address or other identity. The ring does not carry it."
    return reason or "That text was refused."


def format_mesh_problem(data: dict[str, Any]) -> str:
    code = data.get("code")
    if code == "MESH_DISABLED":
        return "The anonymous ring is off.\nTry: azmail mesh enable"
    if code == "MESH_RATE_LIMIT":
        limit = data.get("limit")
        window = data.get("window_sec")
        if limit and window:
            return (
                f"Not sent. This computer is over the local limit ({limit} in {window} seconds).\n"
                "Try: wait, then azmail mesh broadcast --text 'hello' again"
            )
        return "Not sent. This computer is over the local limit.\nTry: wait, then try again"
    if code == "MESH_REFUSE":
        return "Not sent. " + _refuse_plain(str(data.get("reason") or ""))
    note = data.get("note")
    if note:
        return str(note)
    return "The ring did not accept that.\nTry: azmail mesh status"


def format_mesh(action: str, data: dict[str, Any]) -> str:
    if action == "status":
        state = "on" if data.get("enabled") else "off"
        keys = data.get("keywords") or []
        key_line = ", ".join(keys) if keys else "none"
        lines = [
            f"Anonymous ring: {state}",
            f"Handle: {data.get('handle')}" if data.get("handle") else "",
            f"Alert words: {key_line}",
            "This switch is the local ring on this computer.",
            "Next: azmail mesh disable" if data.get("enabled") else "Next: azmail mesh enable",
        ]
        return "\n".join(line for line in lines if line)
    if action == "enable":
        return f"Anonymous ring is on.\nHandle: {data.get('handle') or ''}\nNext: azmail mesh disable"
    if action == "disable":
        return "Anonymous ring is off.\nNext: azmail mesh status"
    if action == "broadcast":
        if not data.get("ok"):
            return format_mesh_problem(data)
        alerts = data.get("keyword_alerts") or []
        lines = ["Queued on this computer.", f"Handle: {data.get('handle') or ''}"]
        if alerts:
            lines.append("Matched: " + ", ".join(str(item.get("keyword") or "") for item in alerts))
        return "\n".join(lines)
    if action == "listen":
        if not data.get("ok"):
            return format_mesh_problem(data)
        items = list(data.get("items") or [])
        if not items:
            return "No messages queued on this computer."
        noun = "message" if len(items) == 1 else "messages"
        lines = [f"{len(items)} {noun} on this computer."]
        for item in items:
            lines.append(f"- {item.get('handle')}: {item.get('text')}")
        return "\n".join(lines)
    return "Try: azmail mesh status"


def format_keywords(action: str, data: dict[str, Any], asked: list[str] | None = None) -> str:
    keys = list(data.get("keywords") or [])
    if action == "list":
        if not keys:
            return "No alert words yet.\nTry: azmail keywords set lighthouse"
        return "Alert words: " + ", ".join(keys) + "\nAlerts name the word only."
    if action == "set":
        shown = ", ".join(keys) if keys else "none"
        lines = [f"Saved alert words: {shown}", "Alerts name the word only."]
        cleaned = []
        for word in asked or []:
            token = str(word).strip().lower()
            if token and token not in cleaned:
                cleaned.append(token)
        if len(keys) < len(cleaned):
            lines.append("Some words were skipped because they look like a password, an email, or an identity.")
        return "\n".join(lines)
    alerts = list(data.get("alerts") or [])
    if not alerts:
        return "No alert word matched."
    return "Matched: " + ", ".join(str(item.get("keyword") or "") for item in alerts)


def cmd_version(ns: argparse.Namespace) -> int:
    if _as_json(ns):
        print(
            json.dumps(
                {
                    "version": __version__,
                    "spec": SPEC_STRING,
                    "author": "Aziel Eliab",
                    "limitation": LIMITATION,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    print(f"azmail {__version__} ({SPEC_STRING})")
    print("Author: Aziel Eliab")
    return 0


def cmd_doctor(ns: argparse.Namespace) -> int:
    return run_doctor(as_json=_as_json(ns))


def cmd_ui(ns: argparse.Namespace) -> int:
    from azmail.ui import serve

    return serve(host=LOOPBACK, port=int(ns.port), mailbox=_box_path(ns))


def cmd_classify(ns: argparse.Namespace) -> int:
    if ns.file:
        payload = _load_json_file(ns.file)
        if not isinstance(payload, dict):
            raise CliStop("That file is not a message object.", "Pass one JSON object with a from field.")
    else:
        payload = _message_from_flags(ns)
    result = classify(payload).as_dict()
    _emit(ns, result, format_classification(result))
    return 0


def cmd_receive(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    box = load(path)
    env = ingest(box, _message_from_flags(ns), confirmed=bool(ns.confirm))
    save(path, box)
    row = env.as_dict()
    _emit(ns, row, format_envelope(row))
    return 0


def cmd_release(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    box = load(path)
    row = confirm_release(box, ns.id)
    if not row:
        return _emit_error(
            ns,
            "That message is not in the airlock.",
            "azmail list airlock",
            body={"ok": False, "error": "not in airlock", "id": ns.id},
        )
    save(path, box)
    subject = (row.get("message") or {}).get("subject") or "(no subject)"
    _emit(ns, {"ok": True, "released": row}, f"Released to your inbox.\nId: {ns.id}\nSubject: {subject}")
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    box = load(_box_path(ns))
    which = ns.which
    rows = list(box.get(which) or [])
    _emit(ns, {which: rows}, format_list(which, rows))
    return 0


def cmd_scrub(ns: argparse.Namespace) -> int:
    if ns.file:
        html = Path(ns.file).read_text(encoding="utf-8") if Path(ns.file).is_file() else None
        if html is None:
            raise CliStop(f"No file at {ns.file}.", "Check the path and try again.")
    else:
        html = ns.html
    out = scrub_html(html or "")
    _emit(ns, out, format_scrub(out))
    return 0


def cmd_process(ns: argparse.Namespace) -> int:
    payload = _load_json_file(ns.file)
    if not isinstance(payload, dict):
        raise CliStop("That file is not a message object.", "Pass one JSON object.")
    env = process(payload, confirmed=bool(ns.confirm))
    row = env.as_dict()
    _emit(ns, row, format_envelope(row))
    return 0


def cmd_import(ns: argparse.Namespace) -> int:
    path = _box_path(ns)
    incoming = _load_json_file(ns.file)
    box = load(path)
    if isinstance(incoming, dict) and incoming.get("schema") == box.get("schema"):
        box = incoming
    elif isinstance(incoming, dict) and "from" in incoming:
        ingest(box, incoming)
    elif isinstance(incoming, list):
        for item in incoming:
            ingest(box, item)
    else:
        return _emit_error(
            ns,
            "This file is not a mailbox or a message.",
            "azmail import --help",
            body={"ok": False, "error": "unrecognized import"},
        )
    save(path, box)
    summary = {"ok": True, "inbox": len(box["inbox"]), "airlock": len(box["airlock"])}
    _emit(ns, summary, f"Imported.\nInbox: {summary['inbox']}\nAirlock: {summary['airlock']}")
    return 0


def cmd_export(ns: argparse.Namespace) -> int:
    box = load(_box_path(ns))
    text = json.dumps(box, indent=2, ensure_ascii=False)
    if ns.file:
        Path(ns.file).write_text(text + "\n", encoding="utf-8")
        if _as_json(ns):
            print(ns.file)
        else:
            print(f"Wrote {ns.file}")
        return 0
    if _as_json(ns):
        print(text)
        return 0
    mesh = box.get("mesh") or {}
    ring = "on" if mesh.get("enabled") else "off"
    print(
        "Mailbox on this computer.\n"
        f"Inbox {len(box.get('inbox') or [])} · "
        f"Airlock {len(box.get('airlock') or [])} · "
        f"Quarantine {len(box.get('quarantine') or [])} · "
        f"Drafts {len(box.get('drafts') or [])}\n"
        f"Anonymous ring: {ring}\n"
        "Add --json to print the mailbox, or --file PATH to save it."
    )
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
    if ok:
        ring = "on" if report["mesh_enabled"] else "off"
        human = (
            "Mailbox file looks right.\n"
            f"Inbox {report['inbox']} · Airlock {report['airlock']} · Quarantine {report['quarantine']}\n"
            f"Anonymous ring: {ring}"
        )
    else:
        human = "This mailbox file is not one AZMail can read.\nTry: azmail doctor"
    _emit(ns, report, human)
    return 0 if ok else 1


def cmd_mesh(ns: argparse.Namespace) -> int:
    action = ns.action
    if action == "enable":
        data = mesh_enable()
    elif action == "disable":
        data = mesh_disable()
    elif action == "status":
        data = mesh_status()
    elif action == "broadcast":
        data = mesh_broadcast(ns.text or "")
    elif action == "listen":
        data = mesh_listen()
    else:
        return _emit_error(ns, "Say what the ring should do.", "azmail mesh status")
    _emit(ns, data, format_mesh(action, data))
    if action in {"broadcast", "listen"} and not data.get("ok"):
        return 1
    return 0


def cmd_keywords(ns: argparse.Namespace) -> int:
    session = mesh_session()
    if ns.action == "list":
        data = {"keywords": session.keywords, "note": "Alerts do not reveal identity."}
        _emit(ns, data, format_keywords("list", data))
        return 0
    if ns.action == "set":
        data = mesh_keywords(ns.words or [])
        _emit(ns, data, format_keywords("set", data, list(ns.words or [])))
        return 0
    if ns.action == "match":
        data = {"alerts": match_keywords(ns.text or "", session.keywords)}
        _emit(ns, data, format_keywords("match", data))
        return 0
    return _emit_error(ns, "Say list, set, or match.", "azmail keywords list")


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
    human = (
        "Draft saved on this computer.\n"
        f"To: {draft['to']}\n"
        f"Subject: {draft['subject'] or '(no subject)'}\n"
        "It stays in Drafts.\n"
        "Next: azmail list drafts"
    )
    _emit(ns, draft, human)
    return 0


def _welcome_json() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "azmail",
        "version": __version__,
        "spec": SPEC_STRING,
        "author": "Aziel Eliab",
        "next": ["azmail ui", "azmail doctor", "azmail --help"],
    }


def build_parser() -> FriendlyParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--mailbox", default=argparse.SUPPRESS, help="Local mailbox JSON path")
    parser = FriendlyParser(prog="azmail", parents=[common], add_help=False)
    sub = parser.add_subparsers(dest="cmd", required=False)

    def add(name: str, help_line: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, parents=[common], help=help_line, description=help_line)

    add("version", "Print the version")
    add("doctor", "Check this install")
    ui = add("ui", f"Open the local app at http://{LOOPBACK}:{DEFAULT_PORT}/")
    ui.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Loopback port (default {DEFAULT_PORT})")

    classify_p = add("classify", "Judge a message without saving it")
    classify_p.add_argument("--file", help="JSON message file")
    classify_p.add_argument("--from", dest="sender", default="")
    classify_p.add_argument("--to", default="")
    classify_p.add_argument("--subject", default="")
    classify_p.add_argument("--body", default="")
    classify_p.add_argument("--html", default="")
    classify_p.add_argument("--headers", default="", help="JSON object of headers you already have")

    receive = add("receive", "Hold a message in the airlock")
    receive.add_argument("--from", dest="sender", required=True)
    receive.add_argument("--to", default="you@local")
    receive.add_argument("--subject", default="")
    receive.add_argument("--body", default="")
    receive.add_argument("--html", default="")
    receive.add_argument("--headers", default="")
    receive.add_argument("--confirm", action="store_true")

    release = add("release", "Move a held message into the inbox")
    release.add_argument("id")

    listing = add("list", "Show inbox, airlock, quarantine, or drafts")
    listing.add_argument("which", choices=("inbox", "airlock", "quarantine", "drafts"))

    scrub = add("scrub", "Strip tracking and scripts from HTML")
    scrub.add_argument("--file")
    scrub.add_argument("--html", default="")

    proc = add("process", "Run the airlock on a JSON file")
    proc.add_argument("file")
    proc.add_argument("--confirm", action="store_true")

    imported = add("import", "Load a mailbox or a message file")
    imported.add_argument("file")
    exported = add("export", "Write the mailbox")
    exported.add_argument("--file")
    add("verify", "Check the mailbox file")

    mesh = add("mesh", "Local anonymous ring (off until you turn it on)")
    mesh.add_argument("action", choices=("enable", "disable", "status", "broadcast", "listen"))
    mesh.add_argument("--text", default="")

    keywords = add("keywords", "Alert words for the local ring")
    keywords.add_argument("action", choices=("list", "set", "match"))
    keywords.add_argument("words", nargs="*")
    keywords.add_argument("--text", default="")

    compose = add("compose", "Save a draft on this computer")
    compose.add_argument("--from", dest="sender", default="")
    compose.add_argument("--to", required=True)
    compose.add_argument("--subject", default="")
    compose.add_argument("--body", default="")
    return parser


def _argv_kind(argv: list[str]) -> str:
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in {"-h", "--help"}:
            return "help"
        if arg == "help":
            return "help"
        if arg == "--mailbox":
            if i + 1 >= len(argv):
                return "command"
            i += 2
            continue
        if arg.startswith("--mailbox="):
            i += 1
            continue
        if arg.startswith("-"):
            return "command"
        return "command"
    return "bare"


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in raw
    args = [item for item in raw if item != "--json"]
    kind = _argv_kind(args)
    if kind == "bare":
        if as_json:
            print(json.dumps(_welcome_json(), indent=2, ensure_ascii=False))
        else:
            print(WELCOME, end="")
        return 0
    if args in (["--version"], ["-V"]):
        return cmd_version(argparse.Namespace(json=as_json))
    if kind == "help" and _first_command(args) in {"", "help"}:
        print(TOP_HELP, end="")
        return 0
    parser = build_parser()
    parser.raw_argv = args
    parser.as_json = as_json
    try:
        ns = parser.parse_args(args)
    except SystemExit as exc:
        code = exc.code
        return int(code) if code else 0
    ns.json = as_json
    if not ns.cmd:
        if as_json:
            print(json.dumps(_welcome_json(), indent=2, ensure_ascii=False))
        else:
            print(WELCOME, end="")
        return 0
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
    try:
        return handlers[ns.cmd](ns)
    except CliStop as exc:
        return _emit_error(ns, exc.text, exc.hint, exc.code, exc.body)
    except FileNotFoundError as exc:
        return _emit_error(ns, f"No file at {exc.filename}.", "Check the path and try again.")
    except json.JSONDecodeError:
        return _emit_error(ns, "That value is not JSON.", "azmail --help")


if __name__ == "__main__":
    sys.exit(main())
