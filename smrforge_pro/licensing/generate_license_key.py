#!/usr/bin/env python3
"""
Generate RSA-signed license keys for SMRForge Pro.

Usage:
    python -m smrforge_pro.licensing.generate_license_key generate-keys
        Create key pair (license_private.pem, license_public.pem) in current dir.

    python -m smrforge_pro.licensing.generate_license_key sign \\
        --license-key "customer-id-123" \\
        --expiry-days 365 \\
        --private-key license_private.pem
        Output base64-encoded signed license JSON.
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def generate_keys(output_dir: Path) -> None:
    """Generate RSA key pair for licensing."""
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        print("ERROR: cryptography required. pip install cryptography", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    public_key = private_key.public_key()

    priv_path = output_dir / "license_private.pem"
    pub_path = output_dir / "license_public.pem"

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)

    print(f"Created {priv_path}")
    print(f"Created {pub_path}")
    print("WARNING: Keep license_private.pem secure and never commit to version control.")


def sign_license(
    license_key: str,
    expiry_days: int,
    private_key_path: Path,
) -> str:
    """Sign license payload and return JSON string."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        print("ERROR: cryptography required. pip install cryptography", file=sys.stderr)
        sys.exit(1)

    expiry = datetime.now(timezone.utc) + timedelta(days=expiry_days)
    payload = {
        "license_key": license_key,
        "expiry_iso": expiry.isoformat(),
    }

    payload_str = json.dumps(payload, sort_keys=True)
    payload_bytes = payload_str.encode("utf-8")

    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

    signature = private_key.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())
    payload["signature"] = base64.b64encode(signature).decode("ascii")

    return json.dumps(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="SMRForge Pro license key generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate-keys", help="Generate RSA key pair")
    gen_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for .pem files",
    )
    gen_parser.set_defaults(func=lambda a: generate_keys(a.output_dir))

    sign_parser = subparsers.add_parser("sign", help="Sign a license")
    sign_parser.add_argument("--license-key", required=True, help="License identifier")
    sign_parser.add_argument("--expiry-days", type=int, default=365)
    sign_parser.add_argument(
        "--private-key",
        type=Path,
        default=Path("license_private.pem"),
        help="Path to private key PEM",
    )
    sign_parser.set_defaults(
        func=lambda a: print(sign_license(a.license_key, a.expiry_days, a.private_key))
    )

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
