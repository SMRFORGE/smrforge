#!/usr/bin/env bash
# Copy air-gap scripts, docs, and workflow from Community repo to smrforge-pro.
# Run from smrforge (Community) repo root.
#
# Usage:
#   ./scripts/airgap/copy_to_pro.sh /path/to/smrforge-pro

set -e
COMMUNITY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRO_ROOT="${1:?Usage: $0 /path/to/smrforge-pro}"

if [ ! -d "$PRO_ROOT" ]; then
  echo "Error: Pro repo path does not exist: $PRO_ROOT"
  exit 1
fi

echo "==> Copying air-gap content from $COMMUNITY_ROOT to $PRO_ROOT"

# Scripts
mkdir -p "$PRO_ROOT/scripts/airgap"
cp "$COMMUNITY_ROOT/scripts/airgap/bundle_wheels.sh"   "$PRO_ROOT/scripts/airgap/"
cp "$COMMUNITY_ROOT/scripts/airgap/bundle_wheels.ps1" "$PRO_ROOT/scripts/airgap/"
cp "$COMMUNITY_ROOT/scripts/airgap/bundle_docker.sh"  "$PRO_ROOT/scripts/airgap/"
cp "$COMMUNITY_ROOT/scripts/airgap/README.md"         "$PRO_ROOT/scripts/airgap/"

# Docs
mkdir -p "$PRO_ROOT/docs/deployment"
cp "$COMMUNITY_ROOT/docs/deployment/air-gapped-pro.md" "$PRO_ROOT/docs/deployment/"

# Workflow
mkdir -p "$PRO_ROOT/.github/workflows"
cp "$COMMUNITY_ROOT/.github/workflows/release-airgap.yml" "$PRO_ROOT/.github/workflows/"

echo "==> Done. Pro repo has air-gap scripts, docs, and release workflow."
