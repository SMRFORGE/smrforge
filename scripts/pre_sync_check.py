#!/usr/bin/env python3
"""
Pre-sync leakage check for Path C Community release.

Run before every Community sync. Fails if Pro/Enterprise code or
license logic appears in Community paths (except whitelisted delegation).

Usage:
    python scripts/pre_sync_check.py
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SMRFORGE_PKG = REPO_ROOT / "smrforge"
CONVERTERS_PY = SMRFORGE_PKG / "io" / "converters.py"

# ANSI colors (disabled when not a TTY, e.g. CI)
_tty = sys.stdout.isatty()
_GREEN = "\033[32m" if _tty else ""
_RED = "\033[31m" if _tty else ""
_YELLOW = "\033[33m" if _tty else ""
_BOLD = "\033[1m" if _tty else ""
_RESET = "\033[0m" if _tty else ""

# Whitelisted: files may contain try/except import smrforge_pro for delegation/check
WHITELIST_SMRFORGE_PRO = {
    "smrforge/convenience/__init__.py",  # pro_available() check
    "smrforge/io/converters.py",
    "smrforge/workflows/plugin_registry.py",
    "smrforge/workflows/ml_export.py",
    "smrforge/workflows/surrogate.py",
    "smrforge/workflows/surrogate_validation.py",
    "smrforge/workflows/parameter_sweep.py",
    "smrforge/ai/audit.py",
    "smrforge/cli/",
}


def run_rg(pattern: str, path: str, extra: list | None = None) -> tuple[list[str], str]:
    """Run ripgrep. Returns (list of matching files, full output). Fallback to Python grep if rg missing."""
    cmd = ["rg", pattern, path, "--type", "py", "-l", "-n"]
    if extra:
        cmd.extend(extra)
    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            lines = [ln.split(":")[0] for ln in r.stdout.strip().split("\n") if ln]
            return list(set(lines)), r.stdout.strip()
        return [], ""
    except FileNotFoundError:
        return _python_grep(pattern, path)


def _python_grep(pattern: str, path: str) -> tuple[list[str], str]:
    """Fallback: search *.py under path for pattern."""
    base = REPO_ROOT / path.rstrip("/")
    if not base.exists():
        return [], ""
    pat = re.compile(pattern)
    matches: list[str] = []
    out_lines: list[str] = []
    for f in base.rglob("*.py"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                rel = str(f.relative_to(REPO_ROOT))
                matches.append(rel)
                out_lines.append(f"{rel}:{i}:{line.strip()}")
                break
    return list(set(matches)), "\n".join(out_lines)


def _norm(f: str) -> str:
    return Path(f).as_posix()


def _is_whitelisted(path: str) -> bool:
    """Check if path is whitelisted (exact match or under a whitelisted directory)."""
    normed = _norm(path)
    for wl in WHITELIST_SMRFORGE_PRO:
        if normed == wl:
            return True
        if wl.endswith("/") and normed.startswith(wl):
            return True
    return False


def check_smrforge_pro_enterprise() -> tuple[bool, str]:
    """
    Check: No smrforge_pro or smrforge_enterprise in smrforge/ except whitelisted delegation.
    """
    # Word boundaries: match package names, not smrforge_project.json
    files, out = run_rg(r"\bsmrforge_pro\b|\bsmrforge_enterprise\b", "smrforge/")
    bad = [f for f in files if not _is_whitelisted(f)]
    if bad:
        return False, f"Pro/Enterprise references in non-whitelisted files:\n  " + "\n  ".join(bad)
    if files and CONVERTERS_PY.exists():
        # Verify converters.py only has delegation (try/except import), not Pro logic
        content = CONVERTERS_PY.read_text(encoding="utf-8")
        if "from smrforge_pro" in content and "try:" in content and "except ImportError" in content:
            pass  # OK: delegation pattern
        elif "smrforge_enterprise" in content:
            return False, "converters.py must not reference smrforge_enterprise"
    return True, ""


def check_pro_license_logic() -> tuple[bool, str]:
    """
    Check: No Pro license validation logic in smrforge/.
    """
    patterns = [
        "check_pro_license|validate_license|parse_license_key",
        "SMRFORGE_PRO_LICENSE",
        "license_key|activation_key",
    ]
    for pattern in patterns:
        files, _ = run_rg(pattern, "smrforge/")
        # SMRFORGE_PRO_LICENSE may appear in upgrade message - that's OK (user-facing)
        # But check_pro_license, validate_license, parse_license_key must NOT exist
        if pattern.startswith("check_pro") or pattern.startswith("validate_license") or pattern.startswith("parse_license"):
            if files:
                return False, f"Pro license logic found in smrforge/: {pattern}\n  Files: {files}"
    return True, ""


def check_smrforge_enterprise_anywhere() -> tuple[bool, str]:
    """Check: No smrforge_enterprise references anywhere in package."""
    files, _ = run_rg(r"\bsmrforge_enterprise\b", "smrforge/")
    if files:
        return False, f"smrforge_enterprise found in smrforge/: {files}"
    return True, ""


def main() -> int:
    print(f"{_BOLD}Pre-Sync Leakage Check{_RESET}")
    print("=" * 50)
    if not SMRFORGE_PKG.exists():
        print(f"{_YELLOW}SKIP:{_RESET} smrforge/ not found at {SMRFORGE_PKG}")
        return 0

    checks = [
        ("Pro/Enterprise in Community (whitelist: converters delegation)", check_smrforge_pro_enterprise),
        ("Pro license logic in Community", check_pro_license_logic),
        ("smrforge_enterprise in Community", check_smrforge_enterprise_anywhere),
    ]

    all_ok = True
    for desc, fn in checks:
        ok, msg = fn()
        if ok:
            print(f"{_GREEN}PASS:{_RESET} {desc}")
        else:
            print(f"{_RED}FAIL:{_RESET} {desc}")
            print(f"  {msg}")
            all_ok = False

    print("=" * 50)
    if all_ok:
        print(f"{_GREEN}{_BOLD}Pre-sync check PASSED{_RESET}")
        return 0
    print(f"{_RED}Fix above before syncing to public.{_RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
