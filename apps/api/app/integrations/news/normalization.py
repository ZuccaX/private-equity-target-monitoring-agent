import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup


TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalize_text(value: str | None, *, max_length: int) -> str:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    return normalized[:max_length].rstrip()


def sanitize_html(value: str | None, *, max_length: int) -> str:
    soup = BeautifulSoup(value or "", "html.parser")
    for tag in soup(["script", "style", "template", "noscript"]):
        tag.decompose()
    return normalize_text(soup.get_text(" "), max_length=max_length)


def normalize_url(
    value: str | None,
    *,
    allowed_query_keys: set[str] | frozenset[str] = frozenset(),
) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("article URL must use HTTP or HTTPS")
    host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    port = parsed.port
    include_port = port is not None and not (
        (parsed.scheme.lower() == "https" and port == 443)
        or (parsed.scheme.lower() == "http" and port == 80)
    )
    netloc = f"{host}:{port}" if include_port else host
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    query = []
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key.startswith(TRACKING_QUERY_PREFIXES):
            continue
        if lower_key in TRACKING_QUERY_KEYS:
            continue
        if key in allowed_query_keys:
            query.append((key, item))
    return urlunsplit(
        (parsed.scheme.lower(), netloc, path, urlencode(sorted(query)), "")
    )


def parse_datetime_utc(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        candidate = value.strip()
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(candidate)
            except (TypeError, ValueError) as exc:
                raise ValueError("unsupported publication datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def content_hash(title: str, content: str | None) -> str:
    identity = "\n".join(
        (
            normalize_text(title, max_length=500).casefold(),
            normalize_text(content, max_length=20_000).casefold(),
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def detect_language(value: str, *, default: str = "und") -> str:
    if not value.strip():
        return default
    ascii_letters = sum(character.isascii() and character.isalpha() for character in value)
    letters = sum(character.isalpha() for character in value)
    if letters and ascii_letters / letters >= 0.9:
        return "en"
    return default
