"""Airlock classify + pipeline."""

from azmail.airlock import classify, process, release


def test_clean_authenticated_mail_releases_verified():
    result = classify(
        {
            "from": "billing@paypal.com",
            "subject": "Your monthly statement",
            "body_text": "Statement attached as PDF.",
            "headers": {
                "Authentication-Results": (
                    "mx.example; spf=pass smtp.mailfrom=paypal.com; "
                    "dkim=pass header.d=paypal.com; dmarc=pass"
                )
            },
            "attachments": [{"name": "statement.pdf", "text": "pdf-bytes"}],
            "history": ["billing@paypal.com"],
            "contacts": {"paypal billing": ["billing@paypal.com"]},
        }
    )
    assert result.verdict == "release"
    assert result.badge == "verified"
    assert result.requires_confirmation is False


def test_lookalike_urgency_requires_confirmation():
    result = classify(
        {
            "from": "PayPal Billing <help@paypa1-verify.com>",
            "from_display": "PayPal Billing",
            "subject": "URGENT: verify your account immediately",
            "body_text": "Your account will be closed. Reset your password now.",
            "contacts": {"paypal billing": ["billing@paypal.com"]},
            "history": ["billing@paypal.com"],
        }
    )
    assert result.requires_confirmation is True
    assert result.badge in {"high-risk", "quarantined"}
    assert "lookalike" in result.flags or "known_phish" in result.layers["reputation"]["flags"]


def test_known_phish_quarantine():
    result = classify(
        {
            "from": "alert@secure-paypal-login.tk",
            "subject": "Verify your account",
            "body_text": "Login now and send your password.",
        }
    )
    assert result.verdict == "quarantine"
    assert result.badge == "quarantined"


def test_unknown_sender_holds_unverified():
    result = classify(
        {
            "from": "newfriend@unknown-startup.io",
            "subject": "hello",
            "body_text": "Nice to meet you.",
        }
    )
    assert result.verdict == "hold"
    assert result.badge == "unverified"
    assert result.requires_confirmation is False


def test_process_does_not_release_high_risk_without_confirm():
    env = process(
        {
            "from": "cfo@g00gle-account.net",
            "subject": "Act now — wire transfer",
            "body_text": "Urgent. Send payment via bitcoin immediately.",
        },
        confirmed=False,
    )
    assert env.released is False
    assert env.classification["requires_confirmation"] is True


def test_release_gate_respects_confirmation():
    env = process(
        {
            "from": "help@paypa1-verify.com",
            "subject": "Act now verify your account",
            "body_text": "Urgent password reset required immediately.",
        },
        confirmed=False,
    )
    blocked = release(env, confirmed=False)
    assert blocked.released is False
    if blocked.classification["verdict"] != "quarantine":
        opened = release(env, confirmed=True)
        assert opened.confirmed is True


def test_layers_present():
    result = classify({"from": "a@b.com", "subject": "x", "body_text": "y"})
    for key in ("source_auth", "reputation", "identity", "behavior", "isolation", "scrub"):
        assert key in result.layers
