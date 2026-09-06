"""Layer 5 — link / attachment isolation (sandbox UX + hashes)."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import quote

URL_RE = re.compile(r"""(?i)\b((?:https?|ftp)://[^\s<>"']+|www\.[^\s<>"']+)""")


def sha256_hex(data: bytes | str) -> str:
    raw = data if isinstance(data, bytes) else data.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def extract_urls(text: str) -> list[str]:
    found: list[str] = []
    for match in URL_RE.findall(text or ""):
        url = match.rstrip(").,;]")
        if url not in found:
            found.append(url)
    return found


def sandbox_url(url: str) -> str:
    return "sandbox:preview?u=" + quote(url, safe="")


def hash_attachment(name: str, data: bytes | str = b"") -> dict[str, Any]:
    raw = data if isinstance(data, bytes) else str(data).encode("utf-8")
    return {
        "name": name,
        "bytes": len(raw),
        "sha256": sha256_hex(raw),
        "isolated": True,
        "opened": False,
        "note": "Hashed locally. Not detonated. Open only in a contained preview.",
    }


def isolate_message(
    subject: str = "",
    body_text: str = "",
    body_html: str = "",
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    urls = extract_urls("\n".join([subject, body_text, body_html]))
    hashed = []
    for att in attachments or []:
        name = str(att.get("name") or att.get("filename") or "attachment")
        data = att.get("data") or att.get("bytes") or att.get("text") or b""
        if isinstance(data, int):
            data = b""
        hashed.append(hash_attachment(name, data if not isinstance(data, str) else data.encode("utf-8")))
    return {
        "layer": "isolation",
        "urls": [{"url": u, "sandbox": sandbox_url(u)} for u in urls],
        "attachments": hashed,
        "note": "Links stay in a contained preview. Attachments are hashed, not executed.",
    }
