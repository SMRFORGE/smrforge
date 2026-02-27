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
        print("ERROR: smrforge_pro not installed", file=sys.stderr)
        return 1

    code, issues = check_api_stability(args.module)
    if issues:
        for msg in issues:
            print(f"API stability: {msg}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
