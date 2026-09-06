"""Local JSON mailbox (inbox / airlock / quarantine). Not an MTA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from azmail.airlock import Envelope, process
from azmail.mesh import MeshClient, anonymous_handle

SCHEMA = "azmail-mailbox-v0"


def default_mailbox() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "inbox": [],
        "airlock": [],
        "quarantine": [],
        "drafts": [],
        "contacts": {},
        "history": [],
        "mesh": {
            "enabled": False,
            "handle": anonymous_handle("mailbox"),
            "keywords": [],
        },
    }


def load(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return default_mailbox()
    data = json.loads(path.read_text(encoding="utf-8"))
    base = default_mailbox()
    base.update(data)
    return base


def save(path: Path, box: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(box, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ingest(box: dict[str, Any], message: dict[str, Any], *, confirmed: bool = False) -> Envelope:
    msg = dict(message)
    msg.setdefault("contacts", box.get("contacts") or {})
    msg.setdefault("history", box.get("history") or [])
    env = process(msg, confirmed=confirmed)
    row = env.as_dict()
    verdict = (env.classification or {}).get("verdict")
    if env.released:
        box["inbox"].append(row)
        addr = env.message.get("from")
        if addr and addr not in box["history"]:
            box["history"].append(addr)
    elif verdict == "quarantine":
        box["quarantine"].append(row)
    else:
        box["airlock"].append(row)
    return env


def confirm_release(box: dict[str, Any], envelope_id: str) -> dict[str, Any] | None:
    kept: list[dict[str, Any]] = []
    found = None
    for row in box.get("airlock") or []:
        if row.get("id") == envelope_id:
            found = row
        else:
            kept.append(row)
    if not found:
        return None
    found["released"] = True
    found["confirmed"] = True
    found["stage"] = "release"
    box["airlock"] = kept
    box["inbox"].append(found)
    addr = (found.get("message") or {}).get("from")
    if addr and addr not in box["history"]:
        box["history"].append(addr)
    return found


def mesh_from_box(box: dict[str, Any]) -> MeshClient:
    mesh = box.setdefault("mesh", {})
    client = MeshClient(
        enabled=bool(mesh.get("enabled")),
        handle=str(mesh.get("handle") or anonymous_handle("mailbox")),
        keywords=list(mesh.get("keywords") or []),
    )
    return client


def mesh_into_box(box: dict[str, Any], client: MeshClient) -> None:
    box["mesh"] = {
        "enabled": client.enabled,
        "handle": client.handle,
        "keywords": list(client.keywords),
    }
