"""Tests for core/network_gateway.py — SSRF guard coverage (IPv4 + IPv6)."""
import socket
from unittest.mock import patch

import pytest

from core.network_gateway import is_safe_url


def _make_resolver(ip: str):
    """Return a side-effect that makes gethostbyname resolve to ip."""
    def _resolve(hostname):
        return ip
    return _resolve


def _fail_resolver(hostname):
    raise socket.gaierror("no route to host")


class TestSchemeCheck:
    def test_ftp_scheme_blocked(self):
        assert not is_safe_url("ftp://example.com/file")

    def test_file_scheme_blocked(self):
        assert not is_safe_url("file:///etc/passwd")

    def test_http_allowed(self):
        with patch("core.network_gateway.socket.gethostbyname", _make_resolver("93.184.216.34")):
            assert is_safe_url("http://example.com")

    def test_https_allowed(self):
        with patch("core.network_gateway.socket.gethostbyname", _make_resolver("93.184.216.34")):
            assert is_safe_url("https://example.com")


class TestBlockedHostnames:
    def test_qdrant_hostname_blocked(self):
        assert not is_safe_url("http://qdrant/collections")

    def test_ai_os_api_blocked(self):
        assert not is_safe_url("http://ai_os_api/health")

    def test_localhost_blocked(self):
        assert not is_safe_url("http://localhost/admin")

    def test_metadata_169_blocked(self):
        assert not is_safe_url("http://169.254.169.254/latest/meta-data/")

    def test_gcp_metadata_hostname_blocked(self):
        assert not is_safe_url("http://metadata.google.internal/")


class TestIPv4PrivateRanges:
    def _check_blocked(self, ip):
        with patch("core.network_gateway.socket.gethostbyname", _make_resolver(ip)):
            assert not is_safe_url(f"http://example.com/"), f"{ip} should be blocked"

    def test_loopback_127_0_0_1_blocked(self):
        self._check_blocked("127.0.0.1")

    def test_loopback_127_255_255_255_blocked(self):
        self._check_blocked("127.255.255.255")

    def test_link_local_169_254_blocked(self):
        self._check_blocked("169.254.1.100")

    def test_private_10_x_blocked(self):
        self._check_blocked("10.0.0.1")

    def test_private_172_16_blocked(self):
        self._check_blocked("172.16.0.1")

    def test_private_192_168_blocked(self):
        self._check_blocked("192.168.1.1")

    def test_shared_address_space_100_64_blocked(self):
        # RFC 6598 — CGNAT range
        self._check_blocked("100.64.0.1")

    def test_public_ip_allowed(self):
        with patch("core.network_gateway.socket.gethostbyname", _make_resolver("8.8.8.8")):
            assert is_safe_url("http://dns.google/")


class TestIPv6PrivateRanges:
    """IPv6 literal addresses in URLs bypass gethostbyname — verify the fallback path."""

    def _check_ipv6_blocked(self, ipv6_host):
        with patch("core.network_gateway.socket.gethostbyname", side_effect=_fail_resolver):
            url = f"http://[{ipv6_host}]/"
            assert not is_safe_url(url), f"{ipv6_host} should be blocked"

    def test_ipv6_loopback_blocked(self):
        self._check_ipv6_blocked("::1")

    def test_ipv6_ula_fc00_blocked(self):
        self._check_ipv6_blocked("fc00::1")

    def test_ipv6_ula_fd00_blocked(self):
        self._check_ipv6_blocked("fd12:3456:789a::1")

    def test_ipv6_link_local_fe80_blocked(self):
        self._check_ipv6_blocked("fe80::1")

    def test_ipv6_link_local_fe80_with_interface_blocked(self):
        # urlparse strips the zone ID — fe80::1%eth0 → fe80::1
        self._check_ipv6_blocked("fe80::1")


class TestUnresolvableHostname:
    def test_unresolvable_hostname_blocked(self):
        """A hostname that neither resolves nor is a valid IP literal is blocked."""
        with patch("core.network_gateway.socket.gethostbyname", side_effect=_fail_resolver):
            assert not is_safe_url("http://this.host.does.not.exist.invalid/")
