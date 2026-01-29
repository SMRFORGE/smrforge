#!/usr/bin/env bash
# One-time Git setup to reduce "Permission denied" / index.lock issues
# when the repo lives in a OneDrive-synced folder (e.g. on Windows or macOS).
#
# Run from repo root: ./scripts/setup_git_onedrive.sh
# See: docs/development/git-onedrive.md

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -d .git ]]; then
  echo "Not a git repository (expected .git in: $REPO_ROOT)" >&2
  exit 1
fi

echo "Git + OneDrive setup (repo: $REPO_ROOT)"
echo ""

echo "1. Removing stale .git/index.lock and .git/config.lock (if present)..."
removed=
[[ -f .git/index.lock ]]  && { rm -f .git/index.lock;  removed=1; }
[[ -f .git/config.lock ]] && { rm -f .git/config.lock; removed=1; }
if [[ -n "$removed" ]]; then
  echo "   Done."
else
  echo "   No stale locks found."
fi

echo "2. Setting local git config..."
git config core.fscache false 2>/dev/null || true
git config core.longpaths true 2>/dev/null || true
echo "   core.fscache = false, core.longpaths = true"

echo ""
echo "Setup complete."
echo ""
echo "If you still see 'Permission denied' when creating index.lock:"
echo "  - Use scripts/git_safe.ps1 (Windows) for add/commit/push."
echo "  - Prefer 'Always keep on this device' for this folder in OneDrive."
echo "  - Or move the repo outside OneDrive."
echo "  - See docs/development/git-onedrive.md for more."
echo ""
