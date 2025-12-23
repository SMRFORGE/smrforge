# Code Formatting Instructions

This document provides instructions for running code formatters on SMRForge.

## Black Code Formatter

### Installation

If not already installed:

```bash
pip install black
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

### Format Code

Format all Python files:

```bash
black smrforge/ tests/
```

Format specific directories:

```bash
black smrforge/neutronics/
black tests/
```

### Check Formatting

Check without making changes:

```bash
black --check smrforge/ tests/
```

### Configuration

Black is configured in `pyproject.toml`:
- Line length: 88 characters
- Target Python versions: 3.8, 3.9, 3.10, 3.11

## isort (Import Sorting)

### Installation

```bash
pip install isort
```

### Sort Imports

```bash
isort smrforge/ tests/
```

### Check Import Order

```bash
isort --check-only smrforge/ tests/
```

## Pre-commit Hooks

To automatically format code before commits:

```bash
pip install pre-commit
pre-commit install
```

This will run Black and isort automatically on commit.

## CI/CD

The GitHub Actions CI pipeline checks code formatting automatically. PRs will fail if code is not formatted correctly.

## Notes

- **Before committing**: Run `black` and `isort` to ensure code passes CI checks
- **IDE integration**: Many IDEs (VS Code, PyCharm) support Black formatting on save
- **Pre-commit hooks**: Recommended for automatic formatting

