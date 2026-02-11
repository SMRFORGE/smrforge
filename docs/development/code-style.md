# Code Style Guide - SMRForge

**Last Updated:** February 2026

This guide covers formatting, **type hints**, import style, and code quality tools. Type hints are required for all new and modified code.

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

We use Python type hints for better code documentation, static analysis, and IDE support. Type hints are required for all new and modified code.

### Requirements

- **All function signatures** must have parameter types and return types
- **Class methods** must have typed parameters and return types (use `-> None` for void methods)
- Use `typing` module: `List`, `Dict`, `Tuple`, `Optional`, `Union`, `Any`
- Use `Optional[Type]` for nullable values (not `Union[Type, None]`)
- Use `Protocol` for duck typing; `TypeVar` for generics
- Use `numpy.ndarray` for NumPy arrays; document shapes in comments when important
- Avoid `Any` when a more specific type is possible

### Examples

```python
from typing import List, Optional, Tuple
import numpy as np

def solve_steady_state(self) -> Tuple[float, np.ndarray]:
    """Solve for k-eff and flux."""
    ...

def compute_power(
    total_power: float,
    flux: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Compute power distribution."""
    ...

def add_constraint(
    self,
    name: str,
    limit: float,
    constraint_type: str = "max",
) -> None:
    """Add a constraint (void method)."""
    ...
```

### Conventions

- **Python 3.8+**: Use `typing.List`, `typing.Dict` (not built-in `list`, `dict`) for compatibility
- **Optional parameters**: `param: Optional[str] = None`
- **Multiple types**: `Union[str, int]` or `str | int` (Python 3.10+)
- **Literals**: `Literal["power", "arnoldi"]` for fixed string/value sets
- **Protocols**: For structural typing without inheritance

See **[Type Hints Conventions](../technical/type-hints-conventions.md)** for full guidelines, including Protocol, TypeVar, NumPy arrays, and migration strategy.

### Tools

```bash
# Type checking with mypy
mypy smrforge/

# Note: Some third-party libraries may not have type stubs
# These are ignored in pyproject.toml configuration
```

### Migration

- New code: type hints required
- Modified code: add type hints when touching a function
- Existing code: add hints incrementally; run `mypy smrforge/` to find gaps

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

# Type checking (see type hints section)
mypy smrforge/

# Linting (matches CI: line-length=88, ignore E203/W503 for Black compatibility)
flake8 smrforge/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# All at once (if configured)
pre-commit run --all-files
```

**Type hints** are enforced as part of code quality. See the [Type Hints](#type-hints) section and [Type Hints Conventions](../technical/type-hints-conventions.md) for full guidelines.

---

*Last Updated: February 2026*

