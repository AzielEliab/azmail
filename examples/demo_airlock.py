#!/usr/bin/env python3
"""Classify a clean statement and a lookalike phish. Offline."""

from azmail.airlock import classify

clean = classify(
    {
        "from": "billing@paypal.com",
        "subject": "Your monthly statement",
        "body_text": "Statement attached as PDF.",
        "headers": {
            "Authentication-Results": "mx; spf=pass; dkim=pass header.d=paypal.com; dmarc=pass"
        },
        "history": ["billing@paypal.com"],
    }
)
phish = classify(
    {
        "from": "PayPal Billing <help@paypa1-verify.com>",
        "subject": "URGENT: verify your account immediately",
        "body_text": "Reset your password now or your account will be closed.",
    }
)
print("clean:", clean.verdict, clean.badge, clean.risk)
print("phish:", phish.verdict, phish.badge, phish.risk)
print("limitation: v0.1 does not send internet email. Author: Aziel Eliab.")
