#!/bin/bash
# Coverage tracker wrapper script
# Convenient wrapper for track_coverage.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Default action is to generate and show summary
ACTION="${1:---generate}"

python "$SCRIPT_DIR/track_coverage.py" "$ACTION" "${@:2}"
