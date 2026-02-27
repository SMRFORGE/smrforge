"""
Pro licensing: JSON key validation, expiry, 7-day grace period, RSA-signed licensing.
"""

from .validator import parse_license_key, validate_license

__all__ = ["parse_license_key", "validate_license"]
