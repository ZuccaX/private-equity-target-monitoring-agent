from app.core.content_identity import (
    LEGACY_FILE_VERSION,
    canonical_content_hash,
    canonicalize_content,
)


def test_canonical_content_normalizes_only_line_endings() -> None:
    assert canonicalize_content(" A\r\nB\rC \n") == " A\nB\nC \n"


def test_canonical_hash_is_stable_and_distinguishes_other_whitespace() -> None:
    assert canonical_content_hash("a\r\nb") == canonical_content_hash("a\nb")
    assert canonical_content_hash(" a\nb") != canonical_content_hash("a\nb")
    assert len(canonical_content_hash(None)) == 64


def test_legacy_file_version_sentinel_is_explicit() -> None:
    assert LEGACY_FILE_VERSION == "legacy-unversioned"
