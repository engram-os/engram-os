import ipaddress
import os
import socket
import logging
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Internal Docker service names that should never be reachable from user input.
_BLOCKED_HOSTNAMES = {"qdrant", "redis", "ai_os_api", "localhost"}

# Private/reserved IPv4 networks that must never be the target of a user-supplied URL.
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("169.254.0.0/16"),    # link-local / cloud metadata (AWS, GCP)
    ipaddress.ip_network("100.64.0.0/10"),     # shared address space
    ipaddress.ip_network("0.0.0.0/8"),
]

# Cloud metadata hostnames that resolve to link-local addresses but should be
# explicitly blocked regardless of their resolved IP.
_BLOCKED_METADATA_HOSTS = {
    "169.254.169.254",          # AWS / GCP / Azure instance metadata
    "metadata.google.internal", # GCP metadata
}


def is_safe_url(url: str) -> bool:
    """
    Returns True if the URL is safe to fetch externally.
    Returns False (and logs the reason) if the URL targets any internal,
    private, or cloud-metadata resource.

    Checks performed (in order):
      1. Scheme must be http or https
      2. Hostname must not be in the blocked hostnames set
      3. Hostname must not be in the blocked metadata hosts set
      4. Hostname resolves to an IP that is not in any private network range
    """
    try:
        parsed = urlparse(url)
    except Exception:
        logger.warning(f"SSRF guard: could not parse URL '{url}'")
        return False

    # 1. Scheme check
    if parsed.scheme not in ("http", "https"):
        logger.warning(f"SSRF guard: blocked non-http scheme '{parsed.scheme}' in '{url}'")
        return False

    hostname = parsed.hostname
    if not hostname:
        logger.warning(f"SSRF guard: no hostname found in '{url}'")
        return False

    # 2. Blocked Docker-internal and loopback hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        logger.warning(f"SSRF guard: blocked internal hostname '{hostname}' in '{url}'")
        return False

    # 3. Cloud metadata hostnames
    if hostname.lower() in _BLOCKED_METADATA_HOSTS:
        logger.warning(f"SSRF guard: blocked metadata hostname '{hostname}' in '{url}'")
        return False

    # 4. Resolve hostname to IP and check against private ranges.
    #    This prevents DNS rebinding: a public hostname that resolves to a private IP.
    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
    except (socket.gaierror, ValueError) as e:
        logger.warning(f"SSRF guard: could not resolve hostname '{hostname}': {e}")
        return False

    for network in _PRIVATE_NETWORKS:
        if ip_obj in network:
            logger.warning(
                f"SSRF guard: '{hostname}' resolved to private IP '{resolved_ip}' "
                f"(matches {network}). Blocked."
            )
            return False

    return True


# ── NetworkGateway ────────────────────────────────────────────────────────────

# All outbound HTTP destinations. Values are callables so env vars are resolved
# at call time, not module import time (important for tests that set env vars).
_DESTINATIONS: dict[str, callable] = {
    "ollama":       lambda: os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"),
    "brain":        lambda: os.getenv("BRAIN_API_URL", "http://localhost:8000"),
    "linear":       lambda: "https://api.linear.app",
    "jira":         lambda: os.getenv("JIRA_URL", ""),
    "qdrant_admin": lambda: f"http://{os.getenv('QDRANT_HOST', 'localhost')}:6334",
    # "crawler" has no base URL — caller supplies the full URL,
    # which is validated by is_safe_url before the request is sent.
    "crawler":      None,
}


class NetworkGateway:
    """Central enforcement point for all outbound HTTP calls.

    All modules MUST use this class instead of calling `requests` directly.
    Direct `import requests` is prohibited outside this module.

    Usage:
        from core.network_gateway import gateway

        gateway.post("ollama", "/api/chat", json=payload, timeout=60)
        gateway.get("brain", "/api/matters")
        gateway.get("crawler", full_url)   # is_safe_url checked automatically
    """

    def _resolve_url(self, destination_label: str, path: str) -> str:
        if destination_label not in _DESTINATIONS:
            raise ValueError(f"NetworkGateway: unknown destination '{destination_label}'. "
                             f"Allowed: {list(_DESTINATIONS)}")

        base_fn = _DESTINATIONS[destination_label]

        if base_fn is None:
            # "crawler" — path IS the full URL
            if not is_safe_url(path):
                raise PermissionError(f"NetworkGateway: URL blocked by SSRF guard: {path!r}")
            return path

        base = base_fn().rstrip("/")
        return base + (path if path.startswith("/") else f"/{path}" if path else "")

    def _log(self, method: str, label: str, url: str, status: int | str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"[{ts}] {method.upper()} {label} {url} → {status}")

    def get(self, destination_label: str, path: str = "", **kwargs) -> requests.Response:
        url = self._resolve_url(destination_label, path)
        try:
            resp = requests.get(url, **kwargs)
            self._log("GET", destination_label, url, resp.status_code)
            return resp
        except Exception as e:
            self._log("GET", destination_label, url, type(e).__name__)
            raise

    def post(self, destination_label: str, path: str = "", **kwargs) -> requests.Response:
        url = self._resolve_url(destination_label, path)
        try:
            resp = requests.post(url, **kwargs)
            self._log("POST", destination_label, url, resp.status_code)
            return resp
        except Exception as e:
            self._log("POST", destination_label, url, type(e).__name__)
            raise

    def delete(self, destination_label: str, path: str = "", **kwargs) -> requests.Response:
        url = self._resolve_url(destination_label, path)
        try:
            resp = requests.delete(url, **kwargs)
            self._log("DELETE", destination_label, url, resp.status_code)
            return resp
        except Exception as e:
            self._log("DELETE", destination_label, url, type(e).__name__)
            raise


# Module-level singleton — import and use this everywhere.
gateway = NetworkGateway()
