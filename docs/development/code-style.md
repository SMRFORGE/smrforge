# Code Style Guide - SMRForge

**Last Updated:** January 1, 2026

## Formatting

We use **Black** for code formatting with default settings (88 character line length).

### Setup

```bash
# Install black
pip install black

# Or with dev dependencies
pip install -e ".[dev]"
```

### Usage

```bash
# Format all Python files
black smrforge/ tests/

# Check formatting without making changes
black --check smrforge/ tests/

# Format specific file
black smrforge/neutronics/solver.py
```

### Configuration

Black is configured in `pyproject.toml`:
- Line length: 88 characters
- Target Python versions: 3.8, 3.9, 3.10, 3.11
- Excludes: backup directories, build artifacts, etc.

---

## Type Hints

We use Python type hints for better code documentation and static analysis.

### Requirements

- Add type hints to all function signatures
- Use `typing` module for complex types
- Use `Optional[Type]` for nullable values
- Use `Union[Type1, Type2]` for multiple types

### Examples

```python
from typing import Tuple, Optional, Dict, List
import numpy as np

def solve_steady_state(self) -> Tuple[float, np.ndarray]:
    """Solve for k-eff and flux."""
    ...

def compute_power(
    total_power: float,
    flux: Optional[np.ndarray] = None
) -> np.ndarray:
    """Compute power distribution."""
    ...
```

### Tools

```bash
# Type checking with mypy
mypy smrforge/

# Note: Some third-party libraries may not have type stubs
# These are ignored in pyproject.toml configuration
```

---

## Import Style

We use **isort** for import organization (compatible with Black).

```bash
# Sort imports
isort smrforge/ tests/

# Check import order
isort --check-only smrforge/ tests/
```

Import order:
1. Standard library
2. Third-party packages
3. Local application imports

---

## Pre-commit Hooks (Recommended)

Set up pre-commit hooks to automatically format code:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see below)
# Install hooks
pre-commit install
```

---

## Naming Conventions

- **Classes**: `PascalCase` (e.g., `MultiGroupDiffusion`)
- **Functions/Methods**: `snake_case` (e.g., `solve_steady_state`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`)
- **Private methods**: `_leading_underscore` (e.g., `_update_xs_maps`)
- **Type variables**: `T`, `K`, `V` for generic types

---

## Documentation

- Use docstrings for all public classes and functions
- Follow Google or NumPy docstring style
- Include type information in docstrings if not in type hints

---

## Code Quality Tools

We use several tools for code quality:

```bash
# Format code
black smrforge/ tests/

# Sort imports
isort smrforge/ tests/

# Type checking
mypy smrforge/

# Linting
flake8 smrforge/ tests/

# All at once (if configured)
pre-commit run --all-files
```

---

*Last Updated: 2025*

