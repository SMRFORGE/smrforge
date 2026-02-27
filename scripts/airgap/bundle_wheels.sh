#!/usr/bin/env bash
# Bundle all wheels for air-gapped installation.
# Run from repo root (smrforge or smrforge-pro).
#
# Usage:
#   ./scripts/airgap/bundle_wheels.sh [OUTPUT_DIR]
#
# Output: wheels in OUTPUT_DIR (default: ./offline-wheels)
# Creates offline-wheels/ with all deps + this package for pip install --no-index.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
OUTPUT_DIR="${1:-./offline-wheels}"
mkdir -p "$OUTPUT_DIR"

REQ_FILE="requirements-lock.txt"
[ -f "$REQ_FILE" ] || REQ_FILE="requirements.txt"

echo "==> Bundling wheels to $OUTPUT_DIR"
echo "==> Using $REQ_FILE"

# Download all dependencies
pip download -r "$REQ_FILE" -d "$OUTPUT_DIR" --no-deps 2>/dev/null || true
pip download -r "$REQ_FILE" -d "$OUTPUT_DIR"

# Download this package (Community or Pro from local source)
pip download . -d "$OUTPUT_DIR"

# Pro: also fetch Community from PyPI (Pro depends on it)
if [ -d "smrforge_pro" ]; then
  echo "==> Pro repo: including smrforge (Community) from PyPI"
  pip download smrforge -d "$OUTPUT_DIR" || true
fi

echo "==> Done. Transfer $OUTPUT_DIR to air-gapped machine, then:"
echo "    pip install --no-index --find-links $OUTPUT_DIR -r $REQ_FILE"
echo "    pip install --no-index --find-links $OUTPUT_DIR ."
