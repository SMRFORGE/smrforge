#!/bin/bash
# Full coverage report with detailed missing lines
# Usage: ./scripts/coverage_full.sh [test_path]

set -e

# Default to all tests if no path provided
TEST_PATH="${1:-tests}"

echo "Running full coverage report on: $TEST_PATH"
echo "This may take longer but provides detailed missing line information..."

# Keep generated artifacts out of repo root
COVERAGE_OUT_DIR="coverage/generated"
mkdir -p "$COVERAGE_OUT_DIR"

# Run tests with parallel execution and detailed coverage reporting
pytest "$TEST_PATH" \
    -n auto \
    --cov=smrforge \
    --cov-report=term-missing \
    --cov-report=html:"$COVERAGE_OUT_DIR/htmlcov" \
    --cov-report=json:"$COVERAGE_OUT_DIR/coverage.json" \
    --tb=short

echo ""
echo "Full coverage report complete!"
echo "HTML report available at: $COVERAGE_OUT_DIR/htmlcov/index.html"
