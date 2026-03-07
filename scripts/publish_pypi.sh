#!/usr/bin/env bash
# Publish SMRForge Community tier to PyPI.
# Prerequisites: pip install build twine
# PyPI token: set TWINE_PASSWORD or use --password; TWINE_USERNAME=__token__
#
# Usage:
#   ./scripts/publish_pypi.sh           # Upload to PyPI
#   ./scripts/publish_pypi.sh --test    # Upload to TestPyPI first

set -e
cd "$(dirname "$0")/.."

# Check version sync
VERSION=$(python -c "from smrforge import __version__; print(__version__)")
echo "Building smrforge v${VERSION}"

# Clean previous builds
rm -rf dist/
rm -rf build/
rm -rf smrforge.egg-info/

# Build
pip install -q build
python -m build

# Check
python -m twine check dist/*

# Upload
if [[ "$1" == "--test" ]]; then
    echo "Uploading to TestPyPI..."
    python -m twine upload --repository testpypi dist/*
    echo "Test install: pip install -i https://test.pypi.org/simple/ smrforge"
else
    echo "Uploading to PyPI..."
    python -m twine upload dist/*
    echo "Verify: pip install smrforge && python -c 'import smrforge; print(smrforge.__version__)'"
fi
