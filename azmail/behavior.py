"""Layer 4 — behavioral anomaly (urgency, credentials, attachments, payment)."""

from __future__ import annotations

import re
from typing import Any

URGENCY = (
    "urgent",
    "immediately",
    "act now",
    "account suspended",
    "verify within",
    "final notice",
    "within 24 hours",
    "within 24 hrs",
    "your account will be closed",
    "limited time",
    "respond now",
)
CREDENTIALS = (
    "password",
    "passcode",
    "login",
    "sign in",
    "ssn",
    "social security",
    "one-time code",
    "otp",
    "2fa",
    "verify your account",
    "confirm your identity",
    "update your billing",
    "reset your password",
    "security code",
)
PAYMENT = (
    "wire transfer",
    "gift card",
    "bitcoin",
    "crypto",
    "invoice overdue",
    "payment required",
    "send payment",
    "western union",
    "zelle",
    "routing number",
    "account number",
)
DANGEROUS_EXT = frozenset(
    {"exe", "scr", "js", "jse", "bat", "cmd", "vbs", "vbe", "ps1", "hta", "iso", "img", "lnk"}
)
HTML_ATTACH = frozenset({"html", "htm", "shtml"})


def _hits(text: str, phrases: tuple[str, ...]) -> list[str]:
    low = (text or "").lower()
    return [p for p in phrases if p in low]


def _ext(name: str) -> str:
    if "." not in (name or ""):
        return ""
    return name.rsplit(".", 1)[-1].lower()


def analyze_behavior(
    subject: str = "",
    body: str = "",
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    blob = f"{subject}\n{body}"
    urgency = _hits(blob, URGENCY)
    creds = _hits(blob, CREDENTIALS)
    payment = _hits(blob, PAYMENT)
    unexpected: list[str] = []
    for att in attachments or []:
        name = str(att.get("name") or att.get("filename") or "")
        ext = _ext(name)
        if ext in DANGEROUS_EXT or ext in HTML_ATTACH:
            unexpected.append(name or ext)

    flags: list[str] = []
    risk = 0
    if urgency:
        flags.append("urgency")
        risk += 20
    if creds:
        flags.append("credentials")
        risk += 35
    if payment:
        flags.append("payment_language")
        risk += 25
    if unexpected:
        flags.append("unexpected_attachment")
        risk += 30
    if urgency and creds:
        risk += 15
    if payment and urgency:
        risk += 10

    return {
        "layer": "behavior",
        "urgency": urgency,
        "credentials": creds,
        "payment": payment,
        "unexpected_attachments": unexpected,
        "flags": flags,
        "risk": min(risk, 100),
        "advisory": True,
        "note": "Keyword heuristics. Not a content-intent model.",
    }


# Keep a named export used by tests / doctor without pulling re into callers.
WORD_BOUNDARY = re.compile(r"\w+")
