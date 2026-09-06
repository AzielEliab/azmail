"""Self-check for AZMail. Offline. No telemetry. No MTA."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Callable

from azmail import LIMITATION, LOOPBACK, SPEC_STRING, __version__
from azmail.airlock import classify, process
from azmail.mesh import MeshClient, match_keywords, refuse_reason
from azmail.scrub import scrub_html
from azmail.ui import make_server

Check = tuple[str, bool, str]


def _ok(name: str, detail: str = "") -> Check:
    return name, True, detail


def _fail(name: str, detail: str) -> Check:
    return name, False, detail


def _check_version() -> Check:
    if __version__ == "0.1.0" and SPEC_STRING == "azmail-app-1.0":
        return _ok("version", __version__)
    return _fail("version", f"{__version__} {SPEC_STRING}")


def _check_clean_release() -> Check:
    result = classify(
        {
            "from": "billing@paypal.com",
            "subject": "Your monthly statement",
            "body_text": "Statement attached as PDF.",
            "headers": {
                "Authentication-Results": "mx.example; spf=pass smtp.mailfrom=paypal.com; dkim=pass header.d=paypal.com; dmarc=pass"
            },
            "attachments": [{"name": "statement.pdf", "text": "pdf-bytes"}],
            "history": ["billing@paypal.com"],
            "contacts": {"paypal billing": ["billing@paypal.com"]},
        }
    )
    if result.verdict == "release" and result.badge == "verified" and not result.requires_confirmation:
        return _ok("clean classify", result.verdict)
    return _fail("clean classify", f"{result.verdict}/{result.badge}/{result.risk}")


def _check_phish_confirm() -> Check:
    result = classify(
        {
            "from": "PayPal Billing <help@paypa1-verify.com>",
            "from_display": "PayPal Billing",
            "subject": "URGENT: verify your account immediately",
            "body_text": "Your account will be closed. Reset your password and send a gift card.",
            "body_html": '<a href="https://paypa1-verify.com/login">login</a>',
            "contacts": {"paypal billing": ["billing@paypal.com"]},
            "history": ["billing@paypal.com"],
        }
    )
    if result.requires_confirmation and result.badge in {"high-risk", "quarantined"}:
        return _ok("phish classify", f"{result.verdict}/{result.badge}")
    return _fail("phish classify", f"{result.verdict}/{result.badge}/{result.flags}")


def _check_known_phish_quarantine() -> Check:
    result = classify(
        {
            "from": "alert@secure-paypal-login.tk",
            "subject": "Verify your account",
            "body_text": "Login now and send your password.",
        }
    )
    if result.verdict == "quarantine" and result.badge == "quarantined":
        return _ok("known-phish quarantine", result.verdict)
    return _fail("known-phish quarantine", f"{result.verdict}/{result.badge}")


def _check_airlock_hold() -> Check:
    env = process(
        {
            "from": "newfriend@unknown-startup.io",
            "subject": "hello",
            "body_text": "Nice to meet you.",
        }
    )
    if env.stage in {"classify", "release"} and not env.released:
        if (env.classification or {}).get("badge") == "unverified":
            return _ok("airlock hold", env.stage)
    if (env.classification or {}).get("verdict") == "hold":
        return _ok("airlock hold", env.stage)
    return _fail("airlock hold", json.dumps(env.classification))


def _check_confirm_gate() -> Check:
    env = process(
        {
            "from": "cfo@g00gle-account.net",
            "subject": "Act now — wire transfer",
            "body_text": "Urgent. Send payment via bitcoin immediately.",
        },
        confirmed=False,
    )
    if env.released:
        return _fail("confirm gate", "released without confirmation")
    env2 = process(env.message, confirmed=True)
    if env2.classification.get("verdict") == "quarantine":
        return _ok("confirm gate", "quarantine stays quarantined")
    if env2.released or env2.confirmed:
        return _ok("confirm gate", env2.stage)
    return _fail("confirm gate", str(env2.as_dict()))


def _check_scrub() -> Check:
    html = (
        '<html><head><script>alert(1)</script><meta http-equiv="refresh" content="0;url=https://evil.example"></head>'
        '<body><img src="https://track.example/pixel.gif" width="1" height="1">'
        '<a href="javascript:steal()">x</a>'
        '<a href="https://good.example/?utm_source=mail">ok</a>'
        '<a style="display:none" href="https://hidden.example/redir">hidden</a>'
        "</body></html>"
    )
    out = scrub_html(html)
    kinds = set(out["stripped_kinds"])
    need = {"script", "tracking_pixel", "javascript_href", "hidden_redirect"}
    if not need <= kinds:
        return _fail("scrub", str(kinds))
    if "<script" in out["html"].lower():
        return _fail("scrub", "script remains")
    if "utm_source" in out["html"]:
        return _fail("scrub", "utm remains")
    return _ok("scrub", ",".join(sorted(kinds)))


def _check_mesh_off() -> Check:
    client = MeshClient()
    if client.enabled:
        return _fail("mesh off", "enabled by default")
    refused = client.broadcast("hello mesh")
    if refused.get("code") != "MESH_DISABLED":
        return _fail("mesh off", str(refused))
    off = client.disable()
    if off.get("enabled") is not False:
        return _fail("mesh disable", str(off))
    return _ok("mesh off-switch", "disabled by default; disable is easy")


def _check_keyword_alerts() -> Check:
    alerts = match_keywords("Project lighthouse update tonight", ["lighthouse", "payroll"])
    if len(alerts) != 1 or alerts[0]["keyword"] != "lighthouse":
        return _fail("keywords", str(alerts))
    if alerts[0].get("identity") is not None:
        return _fail("keywords identity", str(alerts))
    return _ok("keyword alerts", "lighthouse")


def _check_mesh_refuse() -> Check:
    if not refuse_reason("password: hunter2"):
        return _fail("mesh refuse", "missed credential")
    if not refuse_reason("doxx this person, lives at 1 Main St"):
        return _fail("mesh refuse", "missed doxxing")
    client = MeshClient()
    client.enable()
    bad = client.broadcast("send your password: hunter2")
    if bad.get("ok"):
        return _fail("mesh refuse", str(bad))
    return _ok("mesh refuse", bad.get("reason", "refused"))


def _check_loopback() -> Check:
    try:
        make_server("0.0.0.0", 9)
    except ValueError as exc:
        if "loopback" in str(exc).lower() and LOOPBACK == "127.0.0.1":
            return _ok("loopback", "rejects 0.0.0.0")
        return _fail("loopback", str(exc))
    return _fail("loopback", "accepted 0.0.0.0")


def _check_no_mta() -> Check:
    root = Path(__file__).parent
    banned = ("import smtplib", "smtp.SMTP", "sendmail(", "IMAP4", "import socks")
    for path in root.glob("*.py"):
        if path.name == "doctor.py":
            continue
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                return _fail("no mta", f"{path.name}: {token}")
    return _ok("no mta", "stdlib airlock only")


def _check_independence() -> Check:
    root = Path(__file__).parent
    for path in root.glob("*.py"):
        if path.name == "doctor.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "import azos" in text or "import lumen" in text:
            return _fail("independence", path.name)
    return _ok("independence", "no AZ-OS / Lumen import")


CHECKS: tuple[Callable[[], Check], ...] = (
    _check_version,
    _check_clean_release,
    _check_phish_confirm,
    _check_known_phish_quarantine,
    _check_airlock_hold,
    _check_confirm_gate,
    _check_scrub,
    _check_mesh_off,
    _check_keyword_alerts,
    _check_mesh_refuse,
    _check_loopback,
    _check_no_mta,
    _check_independence,
)


def run_doctor(*, as_json: bool = False) -> int:
    results = []
    failed = 0
    for fn in CHECKS:
        name, ok, detail = fn()
        results.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            failed += 1
        mark = "ok" if ok else "FAIL"
        if not as_json:
            print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    payload = {
        "ok": failed == 0,
        "failed": failed,
        "checks": results,
        "version": __version__,
        "spec": SPEC_STRING,
        "limitation": LIMITATION,
        "network": False,
        "telemetry": False,
        "mta": False,
        "mesh_default": False,
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("limitation:", LIMITATION)
        print("doctor", "passed" if failed == 0 else "failed")
    return 0 if failed == 0 else 1
