"""URL validation and SSRF (Server-Side Request Forgery) protection utilities."""

import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
}


class URLValidationError(ValueError):
    """Raised when URL validation fails or SSRF attempt is detected."""
    pass


def is_private_or_restricted_ip(ip_str: str) -> bool:
    """Check if an IP string belongs to private, loopback, link-local, or reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_and_sanitize_url(url: str) -> str:
    """
    Validate a website URL for correctness and SSRF safety.
    
    Checks:
    1. Valid non-empty string.
    2. Scheme must be http or https.
    3. Hostname must be present and valid.
    4. Hostname must not resolve to loopback, private, or internal network IPs (SSRF).
    
    Returns:
        Sanitized URL string.
        
    Raises:
        URLValidationError: When validation fails.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL cannot be empty.")

    cleaned_url = url.strip()

    # Prepend https:// if no scheme provided
    if not cleaned_url.startswith(("http://", "https://")):
        cleaned_url = "https://" + cleaned_url

    try:
        parsed = urlparse(cleaned_url)
    except Exception as exc:
        raise URLValidationError(f"Invalid URL structure: {str(exc)}")

    if parsed.scheme.lower() not in ("http", "https"):
        raise URLValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must include a valid domain or host name.")

    # Lowercase hostname
    hostname_lower = hostname.lower().strip()

    # Disallow known localhost/internal keywords
    if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        raise URLValidationError(f"Access to private/internal host '{hostname}' is forbidden (SSRF Protection).")

    # Basic hostname syntax check (RFC 1123)
    if not re.match(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$", hostname_lower):
        # Check if it's an IP address directly
        try:
            ip = ipaddress.ip_address(hostname_lower)
            if is_private_or_restricted_ip(str(ip)):
                raise URLValidationError(f"Access to IP '{hostname}' is forbidden (SSRF Protection).")
        except ValueError:
            raise URLValidationError(f"Invalid domain format '{hostname}'. Please provide a valid public domain.")

    # Resolve domain to IP addresses to prevent SSRF via DNS rebinding / private DNS
    try:
        addr_info = socket.getaddrinfo(hostname_lower, None)
        resolved_ips = set()
        for item in addr_info:
            ip_str = item[4][0]
            resolved_ips.add(ip_str)

        for ip_str in resolved_ips:
            if is_private_or_restricted_ip(ip_str):
                raise URLValidationError(
                    f"Host '{hostname}' resolves to private/internal IP {ip_str} (SSRF Protection)."
                )
    except socket.gaierror:
        raise URLValidationError(f"Could not resolve domain '{hostname}'. Please check if the website exists.")
    except URLValidationError:
        raise
    except Exception as exc:
        raise URLValidationError(f"Failed to verify domain safety: {str(exc)}")

    return cleaned_url
