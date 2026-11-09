"""Stable hashing helpers for manifests, prefixes, and observations.

Freeze integrity depends on canonical serialization: the same logical record
must hash to the same digest on every machine.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CHUNK_SIZE = 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Return the hex SHA-256 digest of UTF-8 text with normalized newlines."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_bytes(normalized.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    """Return the hex SHA-256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically: sorted keys, compact, UTF-8 text."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_record(record: Any) -> str:
    """Hash a JSON-serializable record using its canonical form."""
    return sha256_text(canonical_json(record))
