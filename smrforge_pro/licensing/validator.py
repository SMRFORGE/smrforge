"""
License validation: JSON key, expiry, 7-day grace period, optional RSA signature verification.
"""

import base64
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.licensing.validator")

GRACE_DAYS = 7


def parse_license_key(license_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse license key from JSON string.

    Args:
        license_str: JSON string with license_key, expiry_iso, optional signature.

    Returns:
        Dict or None if invalid JSON.
    """
    if not license_str or not isinstance(license_str, str):
        return None
    try:
        data = json.loads(license_str.strip())
        if not isinstance(data, dict):
            return None
        return data
    except json.JSONDecodeError:
        return None


def validate_license(
    key_data: Any,
    public_key_path: Optional[Path] = None,
    grace_days: int = GRACE_DAYS,
) -> Tuple[bool, str]:
    """
    Validate license: required fields, expiry, 7-day grace period, optional RSA signature.

    Args:
        key_data: Dict from parse_license_key, or raw dict
        public_key_path: Optional path to RSA public key for signature verification
        grace_days: Days of grace after expiry (default 7)

    Returns:
        (valid: bool, message: str)
    """
    if not isinstance(key_data, dict):
        return False, "License must be a dict"

    license_key = key_data.get("license_key")
    if not license_key:
        return False, "Missing license_key"

    expiry_iso = key_data.get("expiry_iso")
    if not expiry_iso:
        return False, "Missing expiry_iso"

    try:
        if expiry_iso.endswith("Z"):
            expiry = datetime.fromisoformat(expiry_iso.replace("Z", "+00:00"))
        else:
            expiry = datetime.fromisoformat(expiry_iso)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False, "Invalid expiry_iso format"

    now = datetime.now(timezone.utc)

    if public_key_path and Path(public_key_path).exists():
        sig = key_data.get("signature")
        if sig and not _verify_rsa_signature(key_data, sig, public_key_path):
            return False, "Invalid RSA signature"

    if expiry >= now:
        return True, "Valid"

    if expiry + timedelta(days=grace_days) >= now:
        return True, f"Valid (within {grace_days}-day grace period after expiry)"

    return False, "License expired"


def _verify_rsa_signature(key_data: Dict[str, Any], signature_b64: str, public_key_path: Path) -> bool:
    """Verify RSA signature over license payload (excluding signature field)."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        logger.warning("cryptography not installed; skipping RSA verification")
        return True

    payload = {k: v for k, v in key_data.items() if k != "signature"}
    payload_str = json.dumps(payload, sort_keys=True)
    payload_bytes = payload_str.encode("utf-8")
    sig_bytes = base64.b64decode(signature_b64)

    try:
        with open(public_key_path, "rb") as f:
            pub_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        pub_key.verify(
            sig_bytes,
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
