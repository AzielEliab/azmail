"""Local contacts with nicknames. Stored in the mailbox file on this computer."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from azmail.identity import split_from

PUBLIC_FIELDS = ("id", "nickname", "address", "handle", "name", "addresses")


class ContactError(Exception):
    def __init__(self, text: str, hint: str) -> None:
        super().__init__(text)
        self.text = text
        self.hint = hint


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _key(value: str) -> str:
    return _clean(value).casefold()


def _new_id() -> str:
    return "C-" + uuid.uuid4().hex[:12]


def _legacy_id(name: str, address: str) -> str:
    digest = hashlib.sha256(f"{name}\n{address}".encode("utf-8")).hexdigest()[:12]
    return "C-" + digest


def public_contact(raw: dict[str, Any]) -> dict[str, Any]:
    nickname = _clean(raw.get("nickname") or raw.get("name") or "")
    name = _clean(raw.get("name") or "")
    address = _clean(raw.get("address") or "")
    if "@" in address:
        address = address.lower()
    handle = _clean(raw.get("handle") or "")
    addresses: list[str] = []
    for item in list(raw.get("addresses") or []):
        token = _clean(item)
        if "@" in token:
            token = token.lower()
        if token and token not in addresses:
            addresses.append(token)
    if address and address not in addresses:
        addresses.insert(0, address)
    if not address and addresses:
        address = addresses[0]
    contact_id = _clean(raw.get("id") or "") or _new_id()
    return {
        "id": contact_id,
        "nickname": nickname,
        "address": address,
        "handle": handle,
        "name": name,
        "addresses": addresses,
    }


def book_from_legacy(legacy: dict[str, Any]) -> list[dict[str, Any]]:
    book: list[dict[str, Any]] = []
    for name, addrs in legacy.items():
        if isinstance(addrs, str):
            values = [addrs]
        elif isinstance(addrs, list):
            values = [str(item) for item in addrs]
        else:
            continue
        cleaned = public_contact(
            {
                "id": _legacy_id(str(name), values[0] if values else ""),
                "nickname": str(name),
                "name": str(name),
                "address": values[0] if values else "",
                "addresses": values,
            }
        )
        if cleaned["nickname"] or cleaned["address"] or cleaned["handle"]:
            book.append(cleaned)
    return book


def identity_map(book: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapped: dict[str, list[str]] = {}
    for contact in book:
        addrs = [item for item in contact.get("addresses") or [] if item]
        if not addrs and contact.get("address"):
            addrs = [contact["address"]]
        for label in (contact.get("nickname"), contact.get("name")):
            if not label:
                continue
            bucket = mapped.setdefault(str(label), [])
            for addr in addrs:
                if addr not in bucket:
                    bucket.append(addr)
    return mapped


def normalize_contacts(box: dict[str, Any]) -> dict[str, Any]:
    legacy = box.get("contacts")
    book = box.get("contact_book")
    if isinstance(book, list) and book:
        cleaned = [public_contact(item) for item in book if isinstance(item, dict)]
        cleaned = [item for item in cleaned if item["nickname"] or item["address"] or item["handle"]]
        box["contact_book"] = cleaned
        box["contacts"] = identity_map(cleaned)
        return box
    if isinstance(legacy, dict) and legacy:
        migrated = book_from_legacy(legacy)
        box["contact_book"] = migrated
        box["contacts"] = identity_map(migrated)
        return box
    box["contact_book"] = []
    if not isinstance(legacy, dict):
        box["contacts"] = {}
    return box


def list_contacts(box: dict[str, Any]) -> list[dict[str, Any]]:
    normalize_contacts(box)
    return [public_contact(item) for item in box.get("contact_book") or []]


def _find(book: list[dict[str, Any]], *, contact_id: str = "", nickname: str = "") -> dict[str, Any] | None:
    if contact_id:
        want = _key(contact_id)
        for contact in book:
            if _key(contact.get("id") or "") == want:
                return contact
        return None
    want_nick = _key(nickname)
    if not want_nick:
        return None
    for contact in book:
        if _key(contact.get("nickname") or "") == want_nick:
            return contact
    return None


def _nickname_taken(book: list[dict[str, Any]], nickname: str, *, except_id: str = "") -> bool:
    want = _key(nickname)
    for contact in book:
        if except_id and contact.get("id") == except_id:
            continue
        if _key(contact.get("nickname") or "") == want:
            return True
    return False


def add_contact(
    box: dict[str, Any],
    *,
    nickname: str,
    address: str = "",
    handle: str = "",
    name: str = "",
) -> dict[str, Any]:
    normalize_contacts(box)
    nick = _clean(nickname)
    if not nick:
        raise ContactError(
            "Add needs a nickname.",
            "azmail contact add --nickname Sam --address sam@example.com",
        )
    if len(nick) > 80:
        raise ContactError("That nickname is too long.", "Use a shorter nickname, then try again.")
    addr = _clean(address)
    handle_text = _clean(handle)
    if not addr and not handle_text:
        raise ContactError(
            "Add an address or a handle for that nickname.",
            "azmail contact add --nickname Sam --address sam@example.com",
        )
    book = list(box.get("contact_book") or [])
    if _nickname_taken(book, nick):
        raise ContactError(
            f'"{nick}" is already a contact.',
            f"azmail contact edit --nickname {nick} --address {addr or 'name@example.com'}",
        )
    contact = public_contact(
        {
            "id": _new_id(),
            "nickname": nick,
            "address": addr,
            "handle": handle_text,
            "name": name,
            "addresses": [addr] if addr else [],
        }
    )
    book.append(contact)
    box["contact_book"] = book
    box["contacts"] = identity_map(book)
    return contact


def edit_contact(
    box: dict[str, Any],
    *,
    contact_id: str = "",
    nickname: str = "",
    address: str | None = None,
    handle: str | None = None,
    name: str | None = None,
    rename: str | None = None,
) -> dict[str, Any]:
    normalize_contacts(box)
    book = list(box.get("contact_book") or [])
    found = _find(book, contact_id=contact_id, nickname=nickname)
    if not found:
        raise ContactError("No contact with that nickname.", "azmail contact list")
    updated = public_contact(found)
    new_nick = _clean(rename) if rename is not None else ""
    if contact_id and nickname and rename is None:
        new_nick = _clean(nickname)
    if new_nick:
        if len(new_nick) > 80:
            raise ContactError("That nickname is too long.", "Use a shorter nickname, then try again.")
        if _nickname_taken(book, new_nick, except_id=updated["id"]):
            raise ContactError(
                f'"{new_nick}" is already a contact.',
                "azmail contact list",
            )
        updated["nickname"] = new_nick
    if address is not None:
        updated["address"] = _clean(address)
        if "@" in updated["address"]:
            updated["address"] = updated["address"].lower()
        updated["addresses"] = [updated["address"]] if updated["address"] else []
    if handle is not None:
        updated["handle"] = _clean(handle)
    if name is not None:
        updated["name"] = _clean(name)
    updated = public_contact(updated)
    if not updated["nickname"]:
        raise ContactError("A contact needs a nickname.", "azmail contact edit --nickname Sam --rename Sam")
    if not updated["address"] and not updated["handle"]:
        raise ContactError(
            "Keep an address or a handle so the nickname can be used.",
            "azmail contact edit --nickname Sam --address sam@example.com",
        )
    replaced = [updated if item.get("id") == updated["id"] else item for item in book]
    box["contact_book"] = replaced
    box["contacts"] = identity_map(replaced)
    return updated


def remove_contact(box: dict[str, Any], *, contact_id: str = "", nickname: str = "") -> dict[str, Any]:
    normalize_contacts(box)
    book = list(box.get("contact_book") or [])
    found = _find(book, contact_id=contact_id, nickname=nickname)
    if not found:
        raise ContactError("No contact with that nickname.", "azmail contact list")
    box["contact_book"] = [item for item in book if item.get("id") != found.get("id")]
    box["contacts"] = identity_map(box["contact_book"])
    return public_contact(found)


def find_nickname(book: list[dict[str, Any]], token: str) -> dict[str, Any] | None:
    want = _key(token)
    if not want:
        return None
    for contact in book:
        if _key(contact.get("nickname") or "") == want:
            return contact
        if contact.get("name") and _key(contact.get("name") or "") == want:
            return contact
        if contact.get("handle") and _key(contact.get("handle") or "") == want and "@" not in token:
            return contact
    return None


def nickname_for_address(book: list[dict[str, Any]], address: str) -> str:
    want = _clean(address).lower()
    if not want:
        return ""
    for contact in book:
        addrs = [str(item).lower() for item in contact.get("addresses") or []]
        if contact.get("address"):
            addrs.append(str(contact["address"]).lower())
        if want in addrs:
            return str(contact.get("nickname") or "")
    return ""


def resolve_recipient(book: list[dict[str, Any]], raw: str) -> tuple[str, str]:
    text = _clean(raw)
    if not text:
        return "", ""
    _display, addr = split_from(text)
    if addr:
        return addr, nickname_for_address(book, addr)
    contact = find_nickname(book, text)
    if not contact:
        return text, ""
    target = contact.get("address") or contact.get("handle") or text
    return str(target), str(contact.get("nickname") or "")


def apply_sender(box: dict[str, Any], message: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve a bare nickname in From. Leave a typed address as typed."""
    normalize_contacts(box)
    book = list_contacts(box)
    msg = dict(message)
    raw = str(msg.get("from") or "")
    display, addr = split_from(raw)
    note: dict[str, str] = {}
    if addr:
        nick = nickname_for_address(book, addr)
        if nick and not msg.get("from_display"):
            msg["from_display"] = nick
            note = {"nickname": nick, "address": addr}
        return msg, note
    token = _clean(raw)
    if not token:
        return msg, note
    contact = find_nickname(book, token)
    if not contact:
        note = {"unmatched": token}
        return msg, note
    target = str(contact.get("address") or contact.get("handle") or "")
    nick = str(contact.get("nickname") or "")
    if target and "@" in target:
        msg["from"] = f"{nick} <{target}>" if nick else target
        msg["from_display"] = nick or display
        note = {"nickname": nick, "address": target}
    elif target:
        msg["from"] = target
        msg["from_display"] = nick or display
        note = {"nickname": nick, "handle": target}
    return msg, note
