#!/usr/bin/env bash
# Run performance + memory profiling (keff and optionally mesh).
# Use when changing solver, mesh, or data handling. See docs/development/performance-and-benchmarking-assessment.md.
#
# Usage: ./scripts/run_performance_profile.sh [--mesh] [--output PATH]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

MESH=""
OUTPUT="output/profiling/report"
while [[ $# -gt 0 ]]; do
  case $1 in
    --mesh) MESH=1; shift ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT")"
echo "Performance + memory profile (keff${MESH:+, mesh}) - mode both"
echo ""

python scripts/profile_performance.py --function keff --mode both --output "$OUTPUT"
if [[ -n "$MESH" ]]; then
  python scripts/profile_performance.py --function mesh --mode both --output "${OUTPUT}_mesh"
fi

echo ""
echo "Done. Check CPU and memory reports above (or --output files)."
