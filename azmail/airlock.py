"""Layer 7 — Mail Airlock: receive → isolate → analyze → classify → release."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from azmail.behavior import analyze_behavior
from azmail.identity import continuity, split_from
from azmail.isolate import isolate_message
from azmail.reputation import domain_of, reputation
from azmail.scrub import scrub_html
from azmail.source_auth import advise_source_auth

STAGES = ("receive", "isolate", "analyze", "classify", "release")
BADGES = ("verified", "unverified", "high-risk", "quarantined")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _mid() -> str:
    return "AM-" + uuid.uuid4().hex[:12]


@dataclass
class Classification:
    verdict: str
    badge: str
    risk: int
    requires_confirmation: bool
    layers: dict[str, Any]
    flags: list[str]
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "badge": self.badge,
            "risk": self.risk,
            "requires_confirmation": self.requires_confirmation,
            "layers": self.layers,
            "flags": self.flags,
            "note": self.note,
            "aspirational": {
                "inbox_delay": "<1s (target, not a measured SLA in v0.1)",
                "scan": "parallel layers",
                "link_analysis": "real-time sandbox rewrite",
            },
        }


@dataclass
class Envelope:
    id: str
    stage: str
    message: dict[str, Any]
    isolation: dict[str, Any] = field(default_factory=dict)
    classification: dict[str, Any] = field(default_factory=dict)
    scrubbed_html: str = ""
    released: bool = False
    confirmed: bool = False
    received_at: str = field(default_factory=_now)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "stage": self.stage,
            "message": self.message,
            "isolation": self.isolation,
            "classification": self.classification,
            "scrubbed_html": self.scrubbed_html,
            "released": self.released,
            "confirmed": self.confirmed,
            "received_at": self.received_at,
        }


def normalize_message(raw: dict[str, Any]) -> dict[str, Any]:
    display, addr = split_from(str(raw.get("from") or raw.get("from_addr") or ""))
    return {
        "from": addr or str(raw.get("from") or ""),
        "from_display": str(raw.get("from_display") or display),
        "to": str(raw.get("to") or raw.get("to_addr") or ""),
        "subject": str(raw.get("subject") or ""),
        "body_text": str(raw.get("body_text") or raw.get("body") or ""),
        "body_html": str(raw.get("body_html") or raw.get("html") or ""),
        "headers": dict(raw.get("headers") or {}),
        "attachments": list(raw.get("attachments") or []),
        "spf_record": raw.get("spf_record"),
        "dmarc_record": raw.get("dmarc_record"),
        "domain_age_days": raw.get("domain_age_days"),
        "contacts": raw.get("contacts") or {},
        "history": list(raw.get("history") or []),
    }


def classify(message: dict[str, Any]) -> Classification:
    msg = normalize_message(message)
    headers = dict(msg["headers"])
    if msg["from"] and "from" not in {k.lower() for k in headers}:
        headers["From"] = msg["from"]

    auth = advise_source_auth(
        headers,
        spf_record=msg.get("spf_record"),
        dmarc_record=msg.get("dmarc_record"),
    )
    host = domain_of(msg["from"])
    rep = reputation(host, age_days=msg.get("domain_age_days"))
    ident = continuity(
        msg["from"],
        msg["from_display"],
        contacts=msg.get("contacts") or {},
        history=msg.get("history") or [],
    )
    behav = analyze_behavior(msg["subject"], msg["body_text"] + "\n" + msg["body_html"], msg["attachments"])
    iso = isolate_message(msg["subject"], msg["body_text"], msg["body_html"], msg["attachments"])
    scrub = scrub_html(msg["body_html"]) if msg["body_html"] else {"stripped": [], "changed": False, "html": ""}

    flags: list[str] = []
    for layer in (rep, ident, behav):
        flags.extend(layer.get("flags") or [])
    if auth["verdict"] in {"fail", "unverified", "unknown"}:
        flags.append("source_unverified")
    if scrub.get("stripped"):
        flags.append("html_scrubbed")

    risk = min(
        100,
        int(rep.get("risk") or 0)
        + int(ident.get("risk") or 0)
        + int(behav.get("risk") or 0)
        + (25 if auth["verdict"] == "fail" else 0)
        + (10 if auth["verdict"] in {"unverified", "unknown"} else 0),
    )

    known_phish = bool(rep.get("known_phish"))
    cred_phish = "credentials" in behav.get("flags", []) and (
        "urgency" in behav.get("flags", []) or bool(rep.get("lookalike", {}).get("lookalike"))
    )

    if known_phish or (cred_phish and risk >= 70):
        verdict, badge, confirm = "quarantine", "quarantined", True
    elif risk >= 45 or "lookalike" in flags or "display_name_address_mismatch" in flags:
        verdict, badge, confirm = "confirm", "high-risk", True
    elif auth["verdict"] == "pass" and risk < 20 and not flags:
        verdict, badge, confirm = "release", "verified", False
    elif auth["verdict"] == "pass" and risk < 25 and flags == ["html_scrubbed"]:
        verdict, badge, confirm = "release", "verified", False
    else:
        verdict, badge, confirm = "hold", "unverified", False

    # Clean, authenticated mail with no flags.
    if auth["verdict"] == "pass" and risk < 20 and not any(
        f in flags for f in ("known_phish", "lookalike", "credentials", "urgency", "display_name_address_mismatch")
    ):
        verdict, badge, confirm = "release", "verified", False

    note = "No message is trusted until verified across identity, origin, structure, and behavior."
    return Classification(
        verdict=verdict,
        badge=badge,
        risk=risk,
        requires_confirmation=confirm,
        layers={
            "source_auth": auth,
            "reputation": rep,
            "identity": ident,
            "behavior": behav,
            "isolation": iso,
            "scrub": {k: scrub[k] for k in ("stripped", "stripped_kinds", "changed") if k in scrub},
        },
        flags=sorted(set(flags)),
        note=note,
    )


def receive(message: dict[str, Any]) -> Envelope:
    msg = normalize_message(message)
    return Envelope(id=_mid(), stage="receive", message=msg)


def isolate(envelope: Envelope) -> Envelope:
    msg = envelope.message
    envelope.isolation = isolate_message(
        msg["subject"], msg["body_text"], msg["body_html"], msg["attachments"]
    )
    if msg["body_html"]:
        scrubbed = scrub_html(msg["body_html"])
        envelope.scrubbed_html = scrubbed["html"]
    envelope.stage = "isolate"
    return envelope


def analyze(envelope: Envelope) -> Envelope:
    envelope.classification = classify(envelope.message).as_dict()
    envelope.stage = "analyze"
    return envelope


def classify_envelope(envelope: Envelope) -> Envelope:
    if not envelope.classification:
        envelope.classification = classify(envelope.message).as_dict()
    envelope.stage = "classify"
    return envelope


def release(envelope: Envelope, *, confirmed: bool = False) -> Envelope:
    cls = envelope.classification or classify(envelope.message).as_dict()
    envelope.classification = cls
    verdict = cls.get("verdict")
    if verdict == "quarantine":
        envelope.stage = "quarantine"
        envelope.released = False
        envelope.confirmed = False
        return envelope
    if verdict == "hold":
        envelope.stage = "classify"
        envelope.released = False
        envelope.confirmed = False
        return envelope
    if cls.get("requires_confirmation") and not confirmed:
        envelope.stage = "classify"
        envelope.released = False
        envelope.confirmed = False
        return envelope
    envelope.confirmed = confirmed or not cls.get("requires_confirmation")
    envelope.released = True
    envelope.stage = "release"
    return envelope


def process(message: dict[str, Any], *, confirmed: bool = False) -> Envelope:
    """Full airlock: receive → isolate → analyze → classify → release."""
    env = receive(message)
    isolate(env)
    analyze(env)
    classify_envelope(env)
    release(env, confirmed=confirmed)
    return env
