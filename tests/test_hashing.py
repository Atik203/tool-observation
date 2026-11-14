"""Hash stability tests for freeze integrity."""

from __future__ import annotations

from toolobs.hashing import (
    canonical_json,
    sha256_bytes,
    sha256_file,
    sha256_record,
    sha256_text,
    sha256_text_file,
)


def test_sha256_bytes_known_value() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_text_hash_normalizes_newlines() -> None:
    assert sha256_text("a\r\nb") == sha256_text("a\nb")


def test_canonical_json_ignores_key_order() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_record_hash_is_stable() -> None:
    first = {"b": [2, 3], "a": {"y": True, "x": None}}
    second = {"a": {"x": None, "y": True}, "b": [2, 3]}
    assert sha256_record(first) == sha256_record(second)


def test_file_hash_reads_bytes(tmp_path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == sha256_bytes(b"abc")


def test_text_file_hash_normalizes_line_endings(tmp_path) -> None:
    crlf = tmp_path / "crlf.txt"
    lf = tmp_path / "lf.txt"
    crlf.write_bytes(b"a\r\nb\r\n")
    lf.write_bytes(b"a\nb\n")
    assert sha256_text_file(crlf) == sha256_text_file(lf)
    assert sha256_text_file(crlf) == sha256_text("a\nb\n")
