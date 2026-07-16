import pytest

from app.integrations.news.url_safety import URLSafetyPolicy


def _policy(*addresses: str) -> URLSafetyPolicy:
    return URLSafetyPolicy(
        allowed_hosts={"news.example.com"},
        resolver=lambda _host: list(addresses or ("93.184.216.34",)),
    )


def test_accepts_allowlisted_https_global_destination() -> None:
    assert _policy().validate("https://news.example.com/feed") == (
        "https://news.example.com/feed"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://news.example.com/feed",
        "https://user:pass@news.example.com/feed",
        "https://news.example.com/feed#fragment",
        "https://news.example.com:444/feed",
        "https://127.0.0.1/feed",
        "https://localhost/feed",
        "https://service.local/feed",
        "https://other.example.com/feed",
    ],
)
def test_rejects_unsafe_url_shapes(url: str) -> None:
    with pytest.raises(ValueError):
        _policy().validate(url)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "224.0.0.1",
        "192.0.2.1",
        "::1",
        "fc00::1",
    ],
)
def test_rejects_any_non_global_dns_answer(address: str) -> None:
    with pytest.raises(ValueError, match="global"):
        _policy("93.184.216.34", address).validate(
            "https://news.example.com/feed"
        )
