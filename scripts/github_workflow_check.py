#!/usr/bin/env python3
"""
Check whether a GitHub Actions workflow feature is enabled.

Reads .github/workflows-enabled (global) and .github/workflows-config.json
(per-feature). Outputs run_workflow=true|false to GITHUB_OUTPUT for use in
workflow if: conditions.

Usage (from repo root):
  python scripts/github_workflow_check.py <feature_id>

Feature IDs: ci, ci-quick, docs, performance, security, release, nightly, docker, dependabot, stale
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def repo_root() -> Path:
    """Repo root: prefer GITHUB_WORKSPACE, else cwd."""
    root = os.environ.get("GITHUB_WORKSPACE")
    if root:
        return Path(root)
    return Path.cwd()


def global_enabled(root: Path) -> bool:
    """True if .github/workflows-enabled exists and contains 'true'."""
    p = root / ".github" / "workflows-enabled"
    if not p.exists():
        return False
    return p.read_text().strip().lower() == "true"


def feature_enabled_from_config(root: Path, feature_id: str) -> bool | None:
    """
    True if feature is on, False if off, None if config missing or key missing.
    """
    p = root / ".github" / "workflows-config.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    if feature_id not in data:
        return None
    return bool(data[feature_id])


def run_workflow_enabled(feature_id: str) -> bool:
    """
    True if this workflow should run: global on AND (no config or config[feature] on).
    """
    root = repo_root()
    if not global_enabled(root):
        return False
    cfg = feature_enabled_from_config(root, feature_id)
    if cfg is None:
        return True  # no config or key missing -> use global only
    return cfg


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: github_workflow_check.py <feature_id>", file=sys.stderr)
        return 2
    feature_id = sys.argv[1].strip().lower()
    allowed = {
        "ci", "ci-quick", "docs", "performance", "security",
        "release", "nightly", "docker", "dependabot", "stale",
    }
    if feature_id not in allowed:
        print(f"Unknown feature_id: {feature_id}. Allowed: {allowed}", file=sys.stderr)
        return 2
    enabled = run_workflow_enabled(feature_id)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            # Use "enabled" so workflow if: needs.check-enabled.outputs.enabled works
            f.write("enabled=true\n" if enabled else "enabled=false\n")
    else:
        print("enabled=true" if enabled else "enabled=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
