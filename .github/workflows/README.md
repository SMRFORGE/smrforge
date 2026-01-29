# GitHub Actions Workflows

This directory contains CI/CD workflows for SMRForge.

## Workflows

### `performance.yml` - Performance benchmarks

Runs performance (time + memory) regression tests on a **weekly schedule** and via **workflow_dispatch**. Uses `--run-performance` and `--override-ini`; excluded from default pytest. See [performance-and-benchmarking-assessment](development/performance-and-benchmarking-assessment.md).

### `ci.yml` - Continuous Integration

This workflow runs on every push and pull request to `main` and `develop` branches.

**Jobs:**

1. **Test** - Runs test suite on multiple Python versions (3.8, 3.9, 3.10, 3.11)
   - Installs system dependencies
   - Installs core dependencies (without OpenMC for faster builds)
   - Optionally installs OpenMC (continues if it fails)
   - Runs pytest with coverage
   - Uploads coverage to Codecov

2. **Lint** - Checks code quality
   - Black (code formatting)
   - isort (import sorting)
   - flake8 (style checking)
   - mypy (type checking)

3. **Build** - Validates package builds correctly
   - Builds source and wheel distributions
   - Validates package with twine

## Usage

Workflows run automatically on push/PR. You can also trigger them manually from the GitHub Actions tab.

## Dependencies

The CI workflow requires:
- System packages: build-essential, gfortran, cmake, pkg-config, libhdf5-dev, libblas-dev, liblapack-dev, libxml2-dev, libpng-dev
- Python packages: Listed in `requirements.txt`

## Notes

- OpenMC installation is optional - the build continues even if OpenMC fails to install
- Coverage is uploaded to Codecov (requires Codecov token in repository settings)
- Linting checks are set to `continue-on-error: true` to avoid blocking merges while code is being improved

