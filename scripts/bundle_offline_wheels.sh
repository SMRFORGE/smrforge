#!/usr/bin/env bash
# Bundle wheels for air-gapped SMRForge Community installation.
# Run from smrforge (Community) repo root.
#
# Usage: ./scripts/bundle_offline_wheels.sh [OUTPUT_DIR]
#
# Tier: Community. For Pro air-gapped bundles, see smrforge-pro (scripts/airgap/).

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
OUTPUT_DIR="${1:-./offline-wheels}"
mkdir -p "$OUTPUT_DIR"

REQ_FILE="requirements-lock.txt"
[ -f "$REQ_FILE" ] || REQ_FILE="requirements.txt"

echo "==> Bundling SMRForge Community wheels to $OUTPUT_DIR"
echo "==> Using $REQ_FILE"
pip download -r "$REQ_FILE" -d "$OUTPUT_DIR"
pip download . -d "$OUTPUT_DIR"

# Write install instructions
cat > "$OUTPUT_DIR/INSTALL.md" << 'EOF'
# Air-Gap Installation (Community)

Transfer this directory to the air-gapped machine, then:

  pip install --no-index --find-links ./offline-wheels -r requirements-lock.txt
  pip install --no-index --find-links ./offline-wheels .

For nuclear data, also run scripts/bundle_nuclear_data.sh and transfer that archive.
See docs/guides/air-gapped-deployment.md for full guide.

Community tier includes: parametric builders, 2D Plotly flux maps, diffusion, built-in MC,
basic variance reduction (ImportanceMap, WeightWindow), OpenMC export.
Pro adds: CAD/DAGMC import, advanced variance reduction (CADIS from diffusion adjoint).
EOF

echo "==> Done. Transfer $OUTPUT_DIR to air-gapped machine, then:"
echo "    pip install --no-index --find-links $OUTPUT_DIR -r $REQ_FILE"
echo "    pip install --no-index --find-links $OUTPUT_DIR ."
