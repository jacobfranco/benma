"""Credential-free raw provider evidence encoding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StoredRawPayload:
    json_value: Any | None
    text_value: str | None
    sha256: str


def encode_raw_payload(payload: object) -> StoredRawPayload:
    if isinstance(payload, str):
        encoded = payload.encode()
        return StoredRawPayload(None, payload, hashlib.sha256(encoded).hexdigest())
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        text = repr(payload)
        return StoredRawPayload(None, text, hashlib.sha256(text.encode()).hexdigest())
    return StoredRawPayload(payload, None, hashlib.sha256(text.encode()).hexdigest())
