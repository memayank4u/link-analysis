"""Unit tests for URL validation and SSRF protection."""

import pytest
from app.utils.validators import validate_and_sanitize_url, URLValidationError, is_private_or_restricted_ip


def test_valid_public_urls():
    """Verify that standard public domains pass validation."""
    assert validate_and_sanitize_url("https://example.com") == "https://example.com"
    assert validate_and_sanitize_url("http://example.org/about") == "http://example.org/about"
    assert validate_and_sanitize_url("google.com") == "https://google.com"


def test_empty_and_malformed_urls():
    """Verify that invalid strings raise URLValidationError."""
    with pytest.raises(URLValidationError):
        validate_and_sanitize_url("")

    with pytest.raises(URLValidationError):
        validate_and_sanitize_url("   ")

    with pytest.raises(URLValidationError):
        validate_and_sanitize_url("ftp://example.com")

    with pytest.raises(URLValidationError):
        validate_and_sanitize_url("file:///etc/passwd")


def test_ssrf_localhost_blocked():
    """Verify that localhost and loopback addresses are blocked."""
    with pytest.raises(URLValidationError, match="SSRF Protection"):
        validate_and_sanitize_url("http://localhost")

    with pytest.raises(URLValidationError, match="SSRF Protection"):
        validate_and_sanitize_url("http://127.0.0.1")

    with pytest.raises(URLValidationError, match="SSRF Protection"):
        validate_and_sanitize_url("http://127.0.0.1:8000")

    with pytest.raises(URLValidationError, match="SSRF Protection"):
        validate_and_sanitize_url("http://0.0.0.0")


def test_ssrf_cloud_metadata_blocked():
    """Verify that cloud metadata IPs (e.g. AWS/GCP 169.254.169.254) are blocked."""
    with pytest.raises(URLValidationError, match="SSRF Protection"):
        validate_and_sanitize_url("http://169.254.169.254/latest/meta-data")


def test_private_ip_detection():
    """Verify private/internal IP detection utility."""
    assert is_private_or_restricted_ip("127.0.0.1") is True
    assert is_private_or_restricted_ip("10.0.0.5") is True
    assert is_private_or_restricted_ip("172.16.0.1") is True
    assert is_private_or_restricted_ip("192.168.1.1") is True
    assert is_private_or_restricted_ip("169.254.1.1") is True
    assert is_private_or_restricted_ip("8.8.8.8") is False
    assert is_private_or_restricted_ip("1.1.1.1") is False
