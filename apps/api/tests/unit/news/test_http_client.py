from collections.abc import Callable

import httpx
import pytest

from app.integrations.news.base import NewsFetchError
from app.integrations.news.http_client import BoundedNewsHttpClient
from app.integrations.news.url_safety import URLSafetyPolicy


def _client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    max_bytes: int = 1024,
    retries: int = 0,
    resolver=lambda _host: ["93.184.216.34"],
    sleep=lambda _seconds: None,
) -> BoundedNewsHttpClient:
    policy = URLSafetyPolicy(
        allowed_hosts={"news.example.com", "redirect.example.com"},
        resolver=resolver,
    )
    return BoundedNewsHttpClient(
        policy=policy,
        transport=httpx.MockTransport(handler),
        max_response_bytes=max_bytes,
        max_redirects=2,
        max_retries=retries,
        min_host_interval_seconds=0,
        sleep=sleep,
    )


def test_get_accepts_bounded_xml() -> None:
    client = _client(
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "application/rss+xml"},
            content=b"<rss />",
        )
    )

    fetched = client.get("https://news.example.com/feed")

    assert fetched.status == 200
    assert fetched.content_type == "application/rss+xml"
    assert fetched.body == b"<rss />"


def test_rejects_wrong_mime_and_oversized_body() -> None:
    wrong_mime = _client(
        lambda _request: httpx.Response(
            200, headers={"content-type": "image/png"}, content=b"png"
        )
    )
    with pytest.raises(NewsFetchError) as exc:
        wrong_mime.get("https://news.example.com/feed")
    assert exc.value.category == "unsupported_content_type"

    oversized = _client(
        lambda _request: httpx.Response(
            200, headers={"content-type": "text/html"}, content=b"12345"
        ),
        max_bytes=4,
    )
    with pytest.raises(NewsFetchError) as exc:
        oversized.get("https://news.example.com/feed")
    assert exc.value.category == "response_too_large"


def test_redirect_is_revalidated() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302, headers={"location": "https://redirect.example.com/private"}
        )

    client = _client(
        handler,
        resolver=lambda host: (
            ["10.0.0.1"] if host == "redirect.example.com" else ["93.184.216.34"]
        ),
    )
    with pytest.raises(NewsFetchError) as exc:
        client.get("https://news.example.com/feed")
    assert exc.value.category == "unsafe_url"


def test_retries_retryable_status_without_leaking_body() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(502, content=b"sensitive upstream output")
        return httpx.Response(
            200, headers={"content-type": "text/html"}, content=b"ok"
        )

    client = _client(handler, retries=1)
    assert client.get("https://news.example.com/feed").body == b"ok"
    assert calls == 2


def test_non_retryable_4xx_returns_safe_error() -> None:
    client = _client(
        lambda _request: httpx.Response(404, content=b"private details"),
        retries=2,
    )
    with pytest.raises(NewsFetchError) as exc:
        client.get("https://news.example.com/feed")
    assert exc.value.category == "http_error"
    assert exc.value.http_status == 404
    assert "private" not in str(exc.value)
