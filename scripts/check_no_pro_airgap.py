#!/usr/bin/env python3
"""
Ensure Pro air-gap files do not exist in the Community repo.
Air-gap scripts, docs, and workflow belong in smrforge-pro only.

Usage:
    python scripts/check_no_pro_airgap.py

Exits 0 if no Pro air-gap files present; 1 and lists violations otherwise.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths that must NOT exist in Community repo (relative to project root)
PRO_AIRGAP_FORBIDDEN = [
    "scripts/airgap",
    "docs/deployment/air-gapped-pro.md",
    ".github/workflows/release-airgap.yml",
]


def main() -> int:
    violations = []
    for rel in PRO_AIRGAP_FORBIDDEN:
        p = PROJECT_ROOT / rel
        if p.exists():
            violations.append(str(rel))

    if violations:
        print(
            "ERROR: Pro air-gap files must not exist in the Community repo.\n"
            "They belong in smrforge-pro: https://github.com/SMRFORGE/smrforge-pro\n"
            "Remove or use: ./scripts/setup_pro_airgap.sh /path/to/smrforge-pro\n"
            "Violations:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
