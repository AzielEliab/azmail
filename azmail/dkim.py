"""DKIM verification (RFC 6376) with a public key the operator supplied.

RSA SHA-256 and SHA-1 only. There is no DNS lookup: a missing key is
`permerror` / `public_key_not_supplied`, never `pass`. Ed25519 and other
algorithms are `permerror` rather than an invented success.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from typing import Any

_SHA256_INFO = bytes.fromhex("3031300d060960864801650304020105000420")
_SHA1_INFO = bytes.fromhex("3021300906052b0e03021a05000414")
_RSA_OID = bytes.fromhex("2a864886f70d010101")
_B_TAG = re.compile(r"(?i)(?<![A-Za-z])b\s*=\s*[^;]*")
_TAG = re.compile(r"([A-Za-z0-9]+)\s*=\s*([^;]*)")


def canonical_body(body: bytes, method: str) -> bytes:
    if method not in {"simple", "relaxed"}:
        raise ValueError(method)
    if body == b"":
        return b""
    lines = body.split(b"\r\n")
    if method == "relaxed":
        folded: list[bytes] = []
        for line in lines:
            line = re.sub(rb"[ \t]+", b" ", line).rstrip(b" ")
            folded.append(line)
        lines = folded
    while lines and lines[-1] == b"":
        lines.pop()
    if not lines:
        return b""
    return b"\r\n".join(lines) + b"\r\n"


def canon_header(block: bytes, method: str) -> bytes:
    if method == "simple":
        return block if block.endswith(b"\r\n") else block + b"\r\n"
    if method != "relaxed":
        raise ValueError(method)
    text = block.decode("ascii")
    if text.endswith("\r\n"):
        text = text[:-2]
    text = re.sub(r"\r\n([ \t])", r"\1", text)
    name, sep, value = text.partition(":")
    if not sep:
        raise ValueError("header")
    value = re.sub(r"[ \t]+", " ", value.strip(" \t"))
    return f"{name.strip().lower()}:{value}\r\n".encode("ascii")


def verify_dkim(
    message: bytes | str,
    *,
    public_key: str | None = None,
    public_keys: dict[tuple[str, str], str] | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    raw = _as_crlf_bytes(message)
    out: dict[str, Any] = {
        "result": "none",
        "verified": False,
        "dns_queried": False,
        "signatures": [],
        "reason": "",
        "advisory": False,
    }
    if raw is None:
        out["result"] = "permerror"
        out["reason"] = "crlf_required"
        return out
    split = raw.split(b"\r\n\r\n", 1)
    header_blob = split[0]
    body = split[1] if len(split) == 2 else b""
    if len(split) == 1:
        out["result"] = "permerror"
        out["reason"] = "missing_body_separator"
        return out
    try:
        blocks = _header_blocks(header_blob)
    except ValueError:
        out["result"] = "permerror"
        out["reason"] = "bad_header"
        return out
    signatures = [block for block in blocks if _field_name(block) == "dkim-signature"]
    if not signatures:
        out["reason"] = "no_signature"
        return out
    clock = time.time() if now is None else float(now)
    results = [
        _verify_one(block, blocks, body, public_key, public_keys or {}, clock) for block in signatures
    ]
    out["signatures"] = results
    if any(item["result"] == "pass" for item in results):
        out["result"] = "pass"
        out["verified"] = True
        return out
    if results and all(item["result"] == "permerror" for item in results):
        out["result"] = "permerror"
        out["reason"] = results[0]["reason"]
        return out
    out["result"] = "fail"
    out["reason"] = results[0]["reason"]
    return out


def _as_crlf_bytes(message: bytes | str) -> bytes | None:
    raw = message.encode("utf-8") if isinstance(message, str) else bytes(message)
    if b"\r\n" not in raw:
        return None
    if b"\n" in raw.replace(b"\r\n", b""):
        return None
    return raw


def _header_blocks(header_blob: bytes) -> list[bytes]:
    lines = header_blob.split(b"\r\n")
    blocks: list[bytes] = []
    current: list[bytes] = []
    for line in lines:
        if line.startswith((b" ", b"\t")):
            if not current:
                raise ValueError("orphan")
            current.append(line)
            continue
        if current:
            blocks.append(b"\r\n".join(current) + b"\r\n")
        if line == b"":
            current = []
            continue
        current = [line]
    if current:
        blocks.append(b"\r\n".join(current) + b"\r\n")
    return blocks


def _field_name(block: bytes) -> str:
    first = block.split(b"\r\n", 1)[0]
    name = first.split(b":", 1)[0]
    return name.decode("ascii").strip().lower()


def _tags(block: bytes) -> dict[str, str]:
    text = block.decode("ascii")
    if text.lower().startswith("dkim-signature:"):
        text = text.split(":", 1)[1]
    text = text.replace("\r\n", "")
    found: dict[str, str] = {}
    for name, value in _TAG.findall(text):
        found[name.lower()] = value.strip()
    return found


def _blank_b(block: bytes) -> bytes:
    text = block.decode("ascii")
    blanked, count = _B_TAG.subn("b=", text, count=1)
    if count != 1:
        raise ValueError("missing b")
    return blanked.encode("ascii")


def _verify_one(
    block: bytes,
    blocks: list[bytes],
    body: bytes,
    public_key: str | None,
    public_keys: dict[tuple[str, str], str],
    now: float,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "result": "permerror",
        "reason": "",
        "domain": None,
        "selector": None,
        "algorithm": None,
        "body_hash_ok": False,
        "verified": False,
        "dns_queried": False,
    }
    try:
        tags = _tags(block)
    except UnicodeError:
        item["reason"] = "bad_header"
        return item
    item["domain"] = (tags.get("d") or "").lower().rstrip(".") or None
    item["selector"] = tags.get("s") or None
    item["algorithm"] = (tags.get("a") or "").lower() or None
    if tags.get("v", "1") != "1":
        item["reason"] = "bad_version"
        return item
    algo = item["algorithm"] or ""
    if algo not in {"rsa-sha256", "rsa-sha1"}:
        item["reason"] = "algorithm_unsupported"
        return item
    if not item["domain"] or not item["selector"] or not tags.get("bh") or not tags.get("b") or not tags.get("h"):
        item["reason"] = "missing_tag"
        return item
    query = (tags.get("q") or "dns/txt").lower().replace(" ", "")
    if query != "dns/txt":
        item["reason"] = "query_unsupported"
        return item
    identity = (tags.get("i") or "").lower()
    if identity:
        ident_domain = identity.split("@", 1)[-1].rstrip(".")
        if ident_domain != item["domain"] and not ident_domain.endswith("." + item["domain"]):
            item["reason"] = "identity_mismatch"
            return item
    try:
        signed_at = int(tags["t"]) if "t" in tags and tags["t"] != "" else None
        expires = int(tags["x"]) if "x" in tags and tags["x"] != "" else None
        length = int(tags["l"]) if "l" in tags and tags["l"] != "" else None
    except ValueError:
        item["reason"] = "bad_tag"
        return item
    if signed_at is not None and signed_at > now:
        item["reason"] = "future_timestamp"
        return item
    if expires is not None and (signed_at is not None and expires < signed_at or expires < now):
        item["reason"] = "expired"
        return item
    if length is not None and length < 0:
        item["reason"] = "bad_tag"
        return item
    canon_name = (tags.get("c") or "simple/simple").lower().replace(" ", "")
    if "/" not in canon_name:
        canon_name = canon_name + "/simple"
    header_method, _, body_method = canon_name.partition("/")
    if header_method not in {"simple", "relaxed"} or body_method not in {"simple", "relaxed"}:
        item["reason"] = "bad_canonicalization"
        return item
    try:
        hashed = canonical_body(body, body_method)
    except ValueError:
        item["reason"] = "bad_canonicalization"
        return item
    if length is not None:
        if len(hashed) < length:
            item["reason"] = "body_truncated"
            item["result"] = "fail"
            return item
        hashed = hashed[:length]
        item["body_length_limited"] = True
    digest_mod = hashlib.sha256 if algo == "rsa-sha256" else hashlib.sha1
    body_digest = digest_mod(hashed).digest()
    try:
        expected = base64.b64decode(re.sub(r"\s+", "", tags["bh"]), validate=False)
    except Exception:
        item["reason"] = "bad_body_hash"
        return item
    if len(body_digest) != len(expected) or not hmac.compare_digest(body_digest, expected):
        item["result"] = "fail"
        item["reason"] = "body_hash"
        return item
    item["body_hash_ok"] = True
    names = [part.strip().lower() for part in tags["h"].split(":") if part.strip()]
    if not names:
        item["reason"] = "missing_tag"
        return item
    selected = _select(blocks, names, skip=block)
    if selected is None:
        item["reason"] = "signed_header_missing"
        return item
    try:
        signature_header = canon_header(_blank_b(block), header_method)
        signed = b"".join(canon_header(piece, header_method) for piece in selected) + signature_header
    except (UnicodeError, ValueError):
        item["reason"] = "bad_header"
        return item
    key_text = public_keys.get((str(item["selector"]), str(item["domain"]))) or public_key
    if not key_text:
        item["reason"] = "public_key_not_supplied"
        return item
    loaded = _parse_public_key(key_text)
    if loaded is None:
        item["reason"] = "public_key_unparsed"
        return item
    if loaded.get("revoked"):
        item["reason"] = "revoked"
        return item
    hash_name = "sha256" if algo == "rsa-sha256" else "sha1"
    if loaded["hashes"] and hash_name not in loaded["hashes"]:
        item["reason"] = "algorithm_unsupported"
        return item
    if loaded["services"] and "email" not in loaded["services"] and "*" not in loaded["services"]:
        item["reason"] = "service_unsupported"
        return item
    try:
        signature = base64.b64decode(re.sub(r"\s+", "", tags["b"]), validate=False)
    except Exception:
        item["reason"] = "bad_signature"
        return item
    info = (_SHA256_INFO if algo == "rsa-sha256" else _SHA1_INFO) + digest_mod(signed).digest()
    if not _rsa_pkcs1_verify(int(loaded["n"]), int(loaded["e"]), signature, info):
        item["result"] = "fail"
        item["reason"] = "signature"
        return item
    item["result"] = "pass"
    item["verified"] = True
    item["reason"] = ""
    if loaded.get("testing"):
        item["testing"] = True
    return item


def _select(blocks: list[bytes], names: list[str], *, skip: bytes) -> list[bytes] | None:
    pools: dict[str, list[int]] = {}
    for index, block in enumerate(blocks):
        if block is skip:
            continue
        try:
            name = _field_name(block)
        except UnicodeError:
            return None
        pools.setdefault(name, []).append(index)
    chosen: list[bytes] = []
    for name in names:
        stack = pools.get(name)
        if not stack:
            return None
        chosen.append(blocks[stack.pop()])
    return chosen


def _parse_public_key(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    hashes: set[str] = set()
    services: set[str] = set()
    testing = False
    if "BEGIN PUBLIC KEY" in stripped or "BEGIN RSA PUBLIC KEY" in stripped:
        der = _pem_der(stripped)
    else:
        tags = {key.lower(): value.strip() for key, value in _TAG.findall(stripped.replace("\n", " "))}
        if "p" in tags and tags["p"] == "":
            return {"revoked": True}
        if "p" in tags:
            if tags.get("k", "rsa").lower() != "rsa":
                return None
            if tags.get("v", "DKIM1").upper() not in {"DKIM1", ""}:
                return None
            payload = tags["p"]
            hashes = {part.strip().lower() for part in tags.get("h", "").split(":") if part.strip()}
            services = {part.strip().lower() for part in tags.get("s", "").split(":") if part.strip()}
            testing = "y" in {part.strip().lower() for part in tags.get("t", "").split(":") if part.strip()}
        else:
            payload = re.sub(r"\s+", "", stripped)
        try:
            der = base64.b64decode(payload, validate=False)
        except Exception:
            return None
    if not der:
        return None
    try:
        modulus, exponent = _rsa_spki(der)
    except (ValueError, IndexError):
        return None
    return {
        "revoked": False,
        "n": modulus,
        "e": exponent,
        "hashes": hashes,
        "services": services,
        "testing": testing,
    }


def _pem_der(text: str) -> bytes:
    lines = [line.strip() for line in text.splitlines() if not line.startswith("-----")]
    return base64.b64decode("".join(lines), validate=False)


def _read_len(data: bytes, index: int) -> tuple[int, int]:
    first = data[index]
    index += 1
    if first < 0x80:
        return first, index
    count = first & 0x7F
    if count == 0 or count > 4:
        raise ValueError("length")
    length = int.from_bytes(data[index : index + count], "big")
    return length, index + count


def _read_tlv(data: bytes, index: int) -> tuple[int, bytes, int]:
    tag = data[index]
    length, index = _read_len(data, index + 1)
    end = index + length
    if end > len(data):
        raise ValueError("truncated")
    return tag, data[index:end], end


def _read_int(data: bytes, index: int) -> tuple[int, int]:
    tag, value, index = _read_tlv(data, index)
    if tag != 0x02 or not value:
        raise ValueError("integer")
    return int.from_bytes(value, "big"), index


def _rsa_spki(der: bytes) -> tuple[int, int]:
    tag, seq, end = _read_tlv(der, 0)
    if tag != 0x30 or end != len(der):
        raise ValueError("spki")
    tag, alg, index = _read_tlv(seq, 0)
    if tag != 0x30 or _RSA_OID not in alg:
        raise ValueError("oid")
    tag, bit, index = _read_tlv(seq, index)
    if tag != 0x03 or index != len(seq) or not bit or bit[0] != 0:
        raise ValueError("bitstring")
    pk = bit[1:]
    tag, body, pk_end = _read_tlv(pk, 0)
    if tag != 0x30 or pk_end != len(pk):
        raise ValueError("pkcs1")
    modulus, index = _read_int(body, 0)
    exponent, index = _read_int(body, index)
    if index != len(body) or modulus <= 0 or exponent <= 0:
        raise ValueError("rsa")
    return modulus, exponent


def _rsa_pkcs1_verify(modulus: int, exponent: int, signature: bytes, digest_info: bytes) -> bool:
    k = (modulus.bit_length() + 7) // 8
    if len(signature) > k or k < 11:
        return False
    padded = signature.rjust(k, b"\x00")
    value = int.from_bytes(padded, "big")
    if value <= 0 or value >= modulus:
        return False
    encoded = pow(value, exponent, modulus).to_bytes(k, "big")
    if len(digest_info) > k - 11:
        return False
    expected = b"\x00\x01" + (b"\xff" * (k - len(digest_info) - 3)) + b"\x00" + digest_info
    return hmac.compare_digest(encoded, expected)
