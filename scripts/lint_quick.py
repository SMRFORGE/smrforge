#!/usr/bin/env python
"""
Quick lint check for SMRForge: run black and isort on key source dirs.

Usage:
    python scripts/lint_quick.py [--fix]
    --fix: apply fixes (black, isort -w) instead of check-only
"""

import subprocess
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIRS = ["smrforge", "tests", "examples"]


def run(cmd: List[str]) -> int:
    """Run command, return exit code."""
    r = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return r.returncode


def main() -> int:
    fix = "--fix" in sys.argv or "-w" in sys.argv

    # Pro air-gap guard: must not exist in Community repo
    code = run([sys.executable, str(PROJECT_ROOT / "scripts" / "check_no_pro_airgap.py")])
    if code != 0:
        return 1

    # black
    black_args = ["black", "--check", "smrforge", "tests", "examples"]
    if fix:
        black_args = ["black", "smrforge", "tests", "examples"]
    code = run(black_args)
    if code != 0:
        print("black failed. Run: black smrforge tests examples")
        if not fix:
            return 1

    # isort
    isort_args = [
        "isort",
        "--check-only",
        "--diff",
        "smrforge",
        "tests",
        "examples",
    ]
    if fix:
        isort_args = ["isort", "smrforge", "tests", "examples"]
    code = run(isort_args)
    if code != 0:
        print("isort failed. Run: isort smrforge tests examples")
        if not fix:
            return 1

    print("Lint OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
