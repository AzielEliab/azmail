"""Layer 8 — metadata scrubbing (tracking pixels, scripts, hidden redirects)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "_hsenc",
        "_hsmi",
    }
)
TRACKER_HINTS = (
    "pixel",
    "tracking",
    "/track",
    "open.gif",
    "beacon",
    "doubleclick",
    "list-manage.com",
    "mailchimp",
    "mandrillapp",
    "sendgrid.net/wf",
)
SHORTENERS = frozenset(
    {"bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rb.gy"}
)

SCRIPT_RE = re.compile(r"(?is)<script\b[^>]*>.*?</script\s*>")
IFRAME_RE = re.compile(r"(?is)<(?:iframe|object|embed|form)\b[^>]*>.*?</(?:iframe|object|embed|form)\s*>")
IFRAME_VOID_RE = re.compile(r"(?is)<(?:iframe|object|embed|form)\b[^>]*/?>")
ON_ATTR_RE = re.compile(r'(?is)\s+on[a-z]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)')
META_REFRESH_RE = re.compile(r'(?is)<meta\b[^>]*http-equiv\s*=\s*[\'"]?refresh[^>]*>')
JS_HREF_RE = re.compile(r'(?is)href\s*=\s*[\'"]\s*javascript:[^\'"]*[\'"]')
DATA_HREF_RE = re.compile(r'(?is)href\s*=\s*[\'"]\s*data:text/html[^\'"]*[\'"]')
IMG_RE = re.compile(r"(?is)<img\b[^>]*>")
HIDDEN_A_RE = re.compile(
    r'(?is)<a\b[^>]*(?:style\s*=\s*[\'"][^\'"]*(?:display\s*:\s*none|font-size\s*:\s*0|opacity\s*:\s*0)[^\'"]*[\'"])[^>]*>.*?</a\s*>'
)
HREF_RE = re.compile(r'(?is)href\s*=\s*[\'"]([^\'"]+)[\'"]')


def _strip_tracking_query(url: str) -> tuple[str, bool]:
    try:
        parsed = urlparse(url)
    except ValueError:
        return url, False
    if not parsed.query:
        return url, False
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    if len(kept) == len(parse_qsl(parsed.query, keep_blank_values=True)):
        return url, False
    clean = urlunparse(parsed._replace(query=urlencode(kept)))
    return clean, True


def _is_pixel(tag: str) -> bool:
    low = tag.lower()
    if re.search(r'(?:width|height)\s*=\s*[\'"]?1\b', low):
        return True
    if "1x1" in low or "1px" in low:
        return True
    if any(hint in low for hint in TRACKER_HINTS):
        return True
    return False


def _rewrite_hrefs(html: str, stripped: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        url = match.group(1)
        host = urlparse(url).hostname or ""
        if host.lower() in SHORTENERS:
            stripped.append(f"shortener:{host}")
            return 'href="#azmail-isolated-shortener" data-original="' + url.replace('"', "") + '"'
        clean, changed = _strip_tracking_query(url)
        if changed:
            stripped.append("tracking_query")
            return match.group(0).replace(url, clean)
        return match.group(0)

    return HREF_RE.sub(repl, html)


def scrub_html(html: str) -> dict[str, Any]:
    """Strip scripts, tracking pixels, event handlers, and hidden redirects."""
    original = html or ""
    text = original
    stripped: list[str] = []

    def drop(pattern: re.Pattern[str], label: str) -> None:
        nonlocal text
        found = pattern.findall(text)
        if found:
            stripped.extend([label] * len(found))
            text = pattern.sub("", text)

    drop(SCRIPT_RE, "script")
    drop(IFRAME_RE, "embed")
    drop(IFRAME_VOID_RE, "embed")
    drop(META_REFRESH_RE, "meta_refresh")
    if ON_ATTR_RE.search(text):
        count = len(ON_ATTR_RE.findall(text))
        stripped.extend(["event_handler"] * count)
        text = ON_ATTR_RE.sub("", text)
    if JS_HREF_RE.search(text):
        stripped.append("javascript_href")
        text = JS_HREF_RE.sub('href="#azmail-blocked-javascript"', text)
    if DATA_HREF_RE.search(text):
        stripped.append("data_html_href")
        text = DATA_HREF_RE.sub('href="#azmail-blocked-data"', text)
    drop(HIDDEN_A_RE, "hidden_redirect")

    def img_repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if _is_pixel(tag):
            stripped.append("tracking_pixel")
            return "<!-- azmail: tracking pixel stripped -->"
        return tag

    text = IMG_RE.sub(img_repl, text)
    text = _rewrite_hrefs(text, stripped)

    # Collapse leftover empty script-ish residue.
    text = re.sub(r"(?is)<!--\s*azmail:[^>]*-->\s*", lambda m: m.group(0), text)

    return {
        "layer": "scrub",
        "html": text,
        "original_bytes": len(original.encode("utf-8")),
        "scrubbed_bytes": len(text.encode("utf-8")),
        "stripped": stripped,
        "stripped_kinds": sorted(set(stripped)),
        "changed": text != original,
        "note": "Local HTML rewrite. Not a full browser isolation VM.",
    }
