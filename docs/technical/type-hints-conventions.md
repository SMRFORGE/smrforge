# Type Hints Conventions for SMRForge

**Date:** January 2026  
**Status:** Guidelines Document  
**Reference:** [OpenMC Improvements](OPENMC-IMPROVEMENTS-COMPLETE.md)

---

## Executive Summary

This document outlines type hint conventions for SMRForge to improve code readability, maintainability, and developer experience. Type hints help catch errors early, provide better IDE autocomplete, and serve as inline documentation.

---

## Type Hints Status

### ✅ Files with Complete Type Hints

- `smrforge/utils/parallel_batch.py` - Complete with Protocol
- `smrforge/utils/error_messages.py` - Complete
- `smrforge/utils/optimization_utils.py` - Complete
- `smrforge/validation/pydantic_layer.py` - Complete (Pydantic models)

### 📋 Files Needing Enhanced Type Hints

- Some older utility files
- Geometry modules (partial coverage)
- Neutronics modules (partial coverage)

---

## Type Hint Conventions

### 1. Basic Type Hints

**Always specify return types:**
```python
def solve_keff(reactor: Reactor) -> float:
    """Solve for k-effective."""
    return 1.0
```

**Always specify parameter types:**
```python
def create_reactor(
    power_mw: float,
    enrichment: float = 0.195,
    name: Optional[str] = None
) -> Reactor:
    """Create a reactor."""
    pass
```

---

### 2. Collection Types

**Use typing.List, typing.Dict, etc. (not built-in list, dict):**
```python
from typing import List, Dict, Tuple

def process_items(items: List[int]) -> List[str]:
    """Process items."""
    pass

def get_cross_sections() -> Dict[str, float]:
    """Get cross sections."""
    pass
```

**For Python 3.9+, can use built-in types:**
```python
# Python 3.9+
def process_items(items: list[int]) -> list[str]:
    """Process items."""
    pass
```

**Note:** SMRForge supports Python 3.8+, so use `typing.List` for compatibility.

---

### 3. Optional Types

**Use Optional for nullable values:**
```python
from typing import Optional

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get configuration value."""
    return default
```

**For non-optional values, don't use Optional:**
```python
def solve_keff(reactor: Reactor) -> float:  # Never None
    """Solve for k-effective."""
    return 1.0
```

---

### 4. Protocol for Duck Typing

**Use Protocol for structural typing:**
```python
from typing import Protocol

class ReactorLike(Protocol):
    """Protocol for reactor-like objects."""
    
    def solve_keff(self) -> float:
        """Solve for k-effective."""
        ...
    
    def get_power(self) -> float:
        """Get thermal power."""
        ...

def batch_solve_keff(reactors: List[ReactorLike]) -> List[float]:
    """Solve k-eff for multiple reactors."""
    return [r.solve_keff() for r in reactors]
```

**Benefits:**
- Works with any object that implements the protocol
- No inheritance required
- Better type checking

---

### 5. TypeVar for Generic Functions

**Use TypeVar for generic functions:**
```python
from typing import TypeVar, Callable, List

T = TypeVar("T")
R = TypeVar("R")

def batch_process(
    items: List[T],
    func: Callable[[T], R]
) -> List[R]:
    """Process items with function."""
    return [func(item) for item in items]
```

---

### 6. Literal Types

**Use Literal for specific values:**
```python
from typing import Literal

def solve(
    method: Literal["power", "arnoldi", "monte_carlo"] = "power"
) -> float:
    """Solve with specified method."""
    pass
```

---

### 7. NumPy Array Types

**Use numpy.ndarray for NumPy arrays:**
```python
import numpy as np
from typing import Tuple

def compute_flux(reactor: Reactor) -> np.ndarray:
    """Compute neutron flux."""
    return np.zeros((10, 10))

def solve_multigroup(
    xs_data: np.ndarray,
    geometry: np.ndarray
) -> Tuple[float, np.ndarray]:
    """Solve multi-group diffusion."""
    return 1.0, np.zeros((10, 10))
```

**For specific shapes, use comments or asserts:**
```python
def solve_multigroup(
    xs_data: np.ndarray,  # Shape: (n_materials, n_groups)
    geometry: np.ndarray   # Shape: (nz, nr)
) -> Tuple[float, np.ndarray]:
    """Solve multi-group diffusion."""
    assert xs_data.ndim == 2, "xs_data must be 2D"
    assert geometry.ndim == 2, "geometry must be 2D"
    return 1.0, np.zeros((10, 10))
```

---

### 8. Any Type

**Avoid Any when possible, but use when necessary:**
```python
from typing import Any

# Prefer specific types
def process(value: str) -> int:
    """Process string value."""
    return int(value)

# Use Any only when necessary (e.g., for compatibility)
def validate(value: Any) -> bool:
    """Validate any type of value."""
    return isinstance(value, (str, int, float))
```

---

### 9. Union Types

**Use Union for multiple types:**
```python
from typing import Union

def convert(value: Union[str, int, float]) -> float:
    """Convert to float."""
    return float(value)
```

**Prefer Optional over Union[..., None]:**
```python
# Good
def get_config(key: str) -> Optional[str]:
    """Get configuration."""
    pass

# Avoid
def get_config(key: str) -> Union[str, None]:
    """Get configuration."""
    pass
```

---

## Best Practices

### ✅ Do

- **Always specify return types** - Helps catch errors and provides documentation
- **Use Protocol for duck typing** - More flexible than inheritance
- **Use TypeVar for generic functions** - Type-safe generic programming
- **Use Literal for specific values** - Better type checking for enums
- **Document array shapes in comments** - NumPy doesn't support shape annotations

### ❌ Don't

- **Don't use Any unnecessarily** - Reduces type safety
- **Don't omit return types** - Makes code harder to understand
- **Don't use built-in list/dict** (Python < 3.9) - Use typing.List/Dict
- **Don't use Union[..., None]** - Use Optional instead

---

## Type Checking with mypy

**Run mypy to check type hints:**
```bash
mypy smrforge/
```

**Configuration in pyproject.toml:**
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Allow gradual adoption
```

---

## Migration Strategy

### Phase 1: New Code
- All new code must have complete type hints
- Use Protocol for interfaces
- Use TypeVar for generics

### Phase 2: Critical Paths
- Add type hints to frequently-used functions
- Focus on public APIs first
- Add Protocol definitions for common interfaces

### Phase 3: Complete Coverage
- Gradually add type hints to all code
- Update older code when modifying
- Run mypy regularly to catch issues

---

## Examples

### Complete Type Hints Example

```python
from typing import List, Optional, Protocol, TypeVar
import numpy as np

# Protocol for duck typing
class ReactorLike(Protocol):
    """Protocol for reactor-like objects."""
    
    def solve_keff(self) -> float:
        """Solve for k-effective."""
        ...
    
    def get_power(self) -> float:
        """Get thermal power."""
        ...

# TypeVar for generics
T = TypeVar("T")
R = TypeVar("R")

def batch_process(
    items: List[T],
    func: Callable[[T], R],
    parallel: bool = True,
    max_workers: Optional[int] = None
) -> List[R]:
    """Process items in parallel."""
    if parallel:
        # Parallel processing
        pass
    else:
        return [func(item) for item in items]

# Usage
def batch_solve_keff(
    reactors: List[ReactorLike],
    parallel: bool = True
) -> List[float]:
    """Batch solve k-eff for multiple reactors."""
    return batch_process(
        items=reactors,
        func=lambda r: r.solve_keff(),
        parallel=parallel
    )
```

---

## Conclusion

Type hints significantly improve code quality and developer experience. Following these conventions ensures:

✅ **Better IDE Support** - Autocomplete and error detection  
✅ **Early Error Detection** - Catch type errors before runtime  
✅ **Self-Documenting Code** - Types serve as documentation  
✅ **Easier Refactoring** - Type checker catches breaking changes

---

**Last Updated:** January 2026
