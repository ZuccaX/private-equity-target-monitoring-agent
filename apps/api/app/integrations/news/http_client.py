from dataclasses import dataclass
from time import monotonic, sleep
from collections.abc import Callable
from urllib.parse import urljoin, urlsplit

import httpx

from app.integrations.news.base import NewsFetchError
from app.integrations.news.url_safety import URLSafetyPolicy


ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/atom+xml",
        "application/rss+xml",
        "application/xhtml+xml",
        "application/xml",
        "text/html",
        "text/xml",
    }
)
RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class FetchedDocument:
    url: str
    status: int
    content_type: str
    body: bytes


class BoundedNewsHttpClient:
    def __init__(
        self,
        *,
        policy: URLSafetyPolicy,
        transport: httpx.BaseTransport | None = None,
        max_response_bytes: int = 2_000_000,
        max_redirects: int = 3,
        max_retries: int = 2,
        min_host_interval_seconds: float = 0.5,
        timeout_seconds: float = 10,
        connect_timeout_seconds: float = 5,
        clock: Callable[[], float] = monotonic,
        sleep: Callable[[float], None] = sleep,
    ) -> None:
        self.policy = policy
        self.max_response_bytes = max_response_bytes
        self.max_redirects = max_redirects
        self.max_retries = max_retries
        self.min_host_interval_seconds = min_host_interval_seconds
        self.clock = clock
        self.sleep = sleep
        self._last_request_by_host: dict[str, float] = {}
        self._client = httpx.Client(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            timeout=httpx.Timeout(
                timeout_seconds, connect=connect_timeout_seconds
            ),
            headers={"user-agent": "pe-agent-news-sync/1.0"},
        )

    def close(self) -> None:
        self._client.close()

    def get(self, url: str) -> FetchedDocument:
        current_url = self._validate(url)
        redirects = 0
        attempts = 0
        while True:
            self._rate_limit(current_url)
            try:
                outcome = self._request_once(current_url)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempts < self.max_retries:
                    self._backoff(attempts)
                    attempts += 1
                    continue
                raise NewsFetchError("timeout", retryable=True) from exc

            if isinstance(outcome, FetchedDocument):
                return outcome
            status, location = outcome
            if 300 <= status < 400:
                if not location:
                    raise NewsFetchError("redirect_missing_location")
                if redirects >= self.max_redirects:
                    raise NewsFetchError("redirect_limit")
                current_url = self._validate(urljoin(current_url, location))
                redirects += 1
                attempts = 0
                continue
            if status in RETRYABLE_STATUSES and attempts < self.max_retries:
                self._backoff(attempts)
                attempts += 1
                continue
            raise NewsFetchError(
                "http_error",
                retryable=status in RETRYABLE_STATUSES,
                http_status=status,
            )

    def _request_once(
        self, url: str
    ) -> FetchedDocument | tuple[int, str | None]:
        with self._client.stream("GET", url) as response:
            if not (200 <= response.status_code < 300):
                return response.status_code, response.headers.get("location")

            content_type = response.headers.get("content-type", "")
            normalized_type = content_type.split(";", 1)[0].strip().lower()
            if normalized_type not in ALLOWED_CONTENT_TYPES:
                raise NewsFetchError("unsupported_content_type")
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError as exc:
                    raise NewsFetchError("invalid_content_length") from exc
                if declared_length > self.max_response_bytes:
                    raise NewsFetchError("response_too_large")

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > self.max_response_bytes:
                    raise NewsFetchError("response_too_large")
                chunks.append(chunk)
            return FetchedDocument(
                url=str(response.url),
                status=response.status_code,
                content_type=normalized_type,
                body=b"".join(chunks),
            )

    def _validate(self, url: str) -> str:
        try:
            return self.policy.validate(url)
        except (ValueError, OSError) as exc:
            raise NewsFetchError("unsafe_url") from exc

    def _rate_limit(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        now = self.clock()
        previous = self._last_request_by_host.get(host)
        if previous is not None:
            remaining = self.min_host_interval_seconds - (now - previous)
            if remaining > 0:
                self.sleep(remaining)
                now = self.clock()
        self._last_request_by_host[host] = now

    def _backoff(self, attempt: int) -> None:
        self.sleep(min(2**attempt, 4))
