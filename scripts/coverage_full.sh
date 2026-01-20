#!/bin/bash
# Full coverage report with detailed missing lines
# Usage: ./scripts/coverage_full.sh [test_path]

set -e

# Default to all tests if no path provided
TEST_PATH="${1:-tests}"

echo "Running full coverage report on: $TEST_PATH"
echo "This may take longer but provides detailed missing line information..."

# Run tests with parallel execution and detailed coverage reporting
pytest "$TEST_PATH" \
    -n auto \
    --cov=smrforge \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=json:coverage.json \
    --tb=short

echo ""
echo "Full coverage report complete!"
echo "HTML report available at: htmlcov/index.html"
