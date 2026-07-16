import ipaddress
import socket
from collections.abc import Callable, Iterable
from urllib.parse import urlsplit, urlunsplit


Resolver = Callable[[str], Iterable[str]]


def _default_resolver(host: str) -> list[str]:
    return sorted(
        {
            item[4][0]
            for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        }
    )


class URLSafetyPolicy:
    def __init__(
        self,
        *,
        allowed_hosts: set[str] | frozenset[str],
        resolver: Resolver | None = None,
    ) -> None:
        self.allowed_hosts = {
            host.encode("idna").decode("ascii").lower().rstrip(".")
            for host in allowed_hosts
        }
        self.resolver = resolver or _default_resolver

    def validate(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https":
            raise ValueError("only HTTPS destinations are allowed")
        if parsed.username or parsed.password:
            raise ValueError("URL credentials are not allowed")
        if parsed.fragment:
            raise ValueError("URL fragments are not allowed")
        if parsed.port not in (None, 443):
            raise ValueError("unsupported HTTPS port")
        if not parsed.hostname:
            raise ValueError("URL host is required")

        host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
        if host == "localhost" or host.endswith(".local"):
            raise ValueError("local destinations are not allowed")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("IP literal destinations are not allowed")
        if host not in self.allowed_hosts:
            raise ValueError("destination host is not allowlisted")

        addresses = list(self.resolver(host))
        if not addresses:
            raise ValueError("destination did not resolve")
        for address in addresses:
            try:
                parsed_address = ipaddress.ip_address(address)
            except ValueError as exc:
                raise ValueError("resolver returned an invalid address") from exc
            if (
                not parsed_address.is_global
                or parsed_address.is_multicast
                or parsed_address.is_reserved
                or parsed_address.is_unspecified
                or parsed_address.is_loopback
                or parsed_address.is_link_local
                or parsed_address.is_private
            ):
                raise ValueError("every resolved address must be global")

        netloc = host if parsed.port is None else f"{host}:443"
        return urlunsplit(("https", netloc, parsed.path or "/", parsed.query, ""))
