#!/usr/bin/env python3
"""
Check API stability for smrforge_pro. Run in CI to enforce deprecation policy.

Usage:
    python scripts/check_api_stability.py
    python scripts/check_api_stability.py --module smrforge_pro.workflows
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SMRForge Pro API stability")
    parser.add_argument(
        "--module",
        default="smrforge_pro.api",
        help="Module to check (default: smrforge_pro.api)",
    )
    args = parser.parse_args()

    try:
        from smrforge_pro.api import check_api_stability
    except ImportError:
        # Community repo: smrforge_pro lives in smrforge-pro; skip gracefully
        print("OK: smrforge_pro not in repo (Community-only); API stability check skipped")
        return 0

    code, issues = check_api_stability(args.module)
    if issues:
        for msg in issues:
            print(f"API stability: {msg}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
