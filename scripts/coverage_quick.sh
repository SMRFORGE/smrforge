#!/bin/bash
# Quick coverage check script - faster than full coverage report
# Usage: ./scripts/coverage_quick.sh [test_path]

set -e

# Default to all tests if no path provided
TEST_PATH="${1:-tests}"

echo "Running quick coverage check on: $TEST_PATH"
echo "Using parallel execution for speed..."

# Run tests with parallel execution and minimal coverage reporting
pytest "$TEST_PATH" \
    -n auto \
    --cov=smrforge \
    --cov-report=term \
    --cov-report=json:coverage_quick.json \
    -q \
    --tb=short

echo ""
echo "Quick coverage check complete!"
echo "For detailed missing lines, run: pytest --cov=smrforge --cov-report=term-missing"
