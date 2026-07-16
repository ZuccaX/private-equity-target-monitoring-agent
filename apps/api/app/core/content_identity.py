import hashlib


LEGACY_FILE_VERSION = "legacy-unversioned"


def canonicalize_content(content: str | None) -> str:
    return (content or "").replace("\r\n", "\n").replace("\r", "\n")


def canonical_content_hash(content: str | None) -> str:
    return hashlib.sha256(canonicalize_content(content).encode("utf-8")).hexdigest()
