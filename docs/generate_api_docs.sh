#!/bin/bash
# Generate Sphinx API documentation
# Run this from the repository root

cd docs

# Generate API documentation
echo "Generating API documentation..."
sphinx-apidoc -o api ../smrforge --separate --module-first

# Build HTML documentation
echo "Building HTML documentation..."
sphinx-build -b html . _build/html

echo "Documentation generated in docs/_build/html/"
echo "Open docs/_build/html/index.html in your browser"

