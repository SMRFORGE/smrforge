#!/usr/bin/env bash
# Bundle nuclear data (ENDF) for air-gapped transfer.
# Run from smrforge repo root or with ENDF_DIR pointing to ENDF-B-VIII.1.
#
# Usage: ./scripts/bundle_nuclear_data.sh [ENDF_DIR] [OUTPUT_ARCHIVE]
#   ENDF_DIR: Path to ENDF-B-VIII.1 (default: $SMRFORGE_ENDF_DIR or ./ENDF-B-VIII.1)
#   OUTPUT_ARCHIVE: Output .tar.gz path (default: ./nuclear-data-bundle.tar.gz)
#
# Tier: Community. Use on connected machine; transfer archive to air-gapped system.
# On air-gapped: tar -xzf nuclear-data-bundle.tar.gz && export SMRFORGE_ENDF_DIR=/path/to/ENDF-B-VIII.1

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENDF_DIR="${1:-${SMRFORGE_ENDF_DIR:-./ENDF-B-VIII.1}}"
OUTPUT="${2:-./nuclear-data-bundle.tar.gz}"

if [ ! -d "$ENDF_DIR" ]; then
  echo "Error: ENDF directory not found: $ENDF_DIR"
  echo "Download ENDF first: python -m smrforge.core.endf_setup or smrforge data download"
  exit 1
fi

echo "==> Bundling nuclear data from $ENDF_DIR"
tar -czf "$OUTPUT" -C "$(dirname "$ENDF_DIR")" "$(basename "$ENDF_DIR")"
echo "==> Created $OUTPUT"
echo "==> Transfer to air-gapped; then:"
echo "    tar -xzf nuclear-data-bundle.tar.gz -C /install/path"
echo "    export SMRFORGE_ENDF_DIR=/install/path/ENDF-B-VIII.1"
