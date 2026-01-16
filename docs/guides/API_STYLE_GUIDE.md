# SMRForge API Style Guide

**Date:** January 2026  
**Purpose:** Guidelines for consistent API design across SMRForge

---

## Overview

This guide documents the API patterns and conventions used throughout SMRForge. Follow these guidelines when adding new features or modifying existing APIs.

---

## 1. Function Naming Conventions

### Creation Functions
- **`create_*`** - Factory functions that create new instances
  - Example: `create_reactor()`, `create_plot()`, `create_simple_solver()`
  - Should return new instances, not retrieve existing ones

### Access Functions
- **`get_*`** - Retrieve existing resources or data
  - Example: `get_preset()`, `get_design()`, `get_cross_section_table()`
  - Should not create new instances unless explicitly needed

### List Functions
- **`list_*`** - Enumerate available options
  - Example: `list_presets()`, `list_designs()`
  - Should return lists of strings or identifiers

### Build Functions
- **`build_*`** - Construct or assemble complex objects
  - Example: `build_mesh()`, `build_hexagonal_lattice()`
  - Used for geometry construction and assembly operations

---

## 2. Unit Conventions

### Power Units
- **Public API**: Use `power_mw` (megawatts) for user-facing functions
  - `create_reactor(power_mw=10.0)` ✅
  - `quick_keff(power_mw=10.0)` ✅
- **Internal Models**: Use `power_thermal` (watts) for precision
  - `ReactorSpecification.power_thermal` (watts) ✅
- **Conversion**: Document when conversions happen
  - `power_mw * 1e6 -> power_thermal` (converted internally)

### Time Units
- **Burnup**: Always use **days** for time steps
  - `BurnupOptions.time_steps` - **Must be in days** ✅
  - Document clearly: `time_steps: List[float]  # days`
  - For explicit naming: `time_steps_days` is acceptable in convenience functions

### Length Units
- **Core dimensions**: Always use **cm** (centimeters)
  - `core_height`, `core_diameter` - units in cm ✅
- **Power density**: Always use **W/cm³**
  - `power_density: float = 1e6  # W/cm³` ✅

---

## 3. Parameter Ordering

### Solver Initialization
All solvers follow this pattern:
```python
SolverClass(
    required_param1,      # Required: Core dependency
    required_param2,      # Required: Data/configuration
    options=options_obj,  # Required: Options object
    optional_dep=None     # Optional: Dependencies
)
```

Examples:
- `MultiGroupDiffusion(geometry, xs_data, options)`
- `BurnupSolver(neutronics_solver, options, cache=None)`

### Factory Functions
Convenience functions should provide sensible defaults:
```python
def create_simple_solver(
    core: Optional[PrismaticCore] = None,  # Optional: creates if None
    xs_data: Optional[CrossSectionData] = None,  # Optional: creates if None
    n_groups: int = 2,  # Default parameter
    max_iterations: int = 1000,  # Default parameter
    ...
) -> MultiGroupDiffusion:
```

---

## 4. Dual API Patterns

### Visualization API

SMRForge provides two visualization APIs for flexibility:

**1. Class-based API (Recommended for reusable plots):**
```python
from smrforge.visualization.plot_api import Plot, create_plot

# Create reusable plot configuration
plot = Plot(
    plot_type='slice',
    origin=(0, 0, 200),
    width=(300, 300, 400),
    color_by='material',
    backend='plotly'
)
fig = plot.plot(geometry)
```

**When to use:**
- Creating multiple plots with similar configuration
- Saving/loading plot configurations
- Programmatic plot generation
- Reusable plot setups

**2. Standalone Function API (Recommended for quick plots):**
```python
from smrforge.visualization.voxel_plots import plot_voxel

# Quick one-off plot
fig = plot_voxel(
    geometry,
    origin=(0, 0, 0),
    width=(300, 300, 400),
    color_by='material',
    backend='plotly'
)
```

**When to use:**
- One-off plots
- Quick visualization
- Simple use cases
- Interactive exploration

Both APIs support the same parameters and backends. Choose based on your use case.

### Nuclear Data Access API

**1. Cache Methods (Preferred for multiple operations):**
```python
from smrforge.core.reactor_core import NuclearDataCache

cache = NuclearDataCache(local_endf_dir=Path('/path/to/ENDF'))
xs_table = cache.get_cross_section_table(nuclide, library='endfb8.1')
```

**When to use:**
- Accessing multiple nuclides
- Repeated data access
- When you already have a cache instance
- Performance-critical code

**2. Standalone Functions (Convenient for single operations):**
```python
from smrforge.core.reactor_core import get_fission_yield_data, Nuclide

u235 = Nuclide(Z=92, A=235)
yield_data = get_fission_yield_data(u235)
```

**When to use:**
- One-off data access
- Quick calculations
- When you don't have a cache instance
- Simple use cases

Both patterns are valid. Prefer cache methods when working with multiple nuclides.

---

## 5. Error Handling

### Exception Types

Use appropriate exception types:

- **`ValueError`** - Invalid parameter values
  ```python
  if name not in presets:
      raise ValueError(f"Unknown preset '{name}'. Available: {list_presets()}")
  ```

- **`ValidationError`** (Pydantic) - Data validation failures
  ```python
  try:
      spec = ReactorSpecification(**data)
  except ValidationError as e:
      # Handle validation error
  ```

- **`ImportError`** - Missing optional dependencies
  ```python
  try:
      import plotly
      _PLOTLY_AVAILABLE = True
  except ImportError:
      _PLOTLY_AVAILABLE = False
      plotly = None
  ```

- **`RuntimeError`** - Solver/convergence failures
  ```python
  if not converged:
      raise RuntimeError(f"Solver failed to converge after {iterations} iterations")
  ```

### Error Messages

Always provide helpful error messages:
- Include available options when relevant
- Suggest fixes when possible
- Include context (parameter names, expected values)

---

## 6. Documentation Standards

### Docstring Format

Use Google-style docstrings with clear sections:

```python
def create_reactor(
    power_mw: Optional[float] = None,
    ...
) -> "SimpleReactor":
    """
    Brief one-line description.

    Longer description explaining purpose, behavior, and important details.
    
    **Unit Notes:**
    - power_mw: Thermal power in MW (converted to watts internally)
    - All dimensions in cm
    
    Args:
        power_mw: Thermal power in MW (for custom designs only).
                  **Note:** Converted internally to watts (power_thermal = power_mw * 1e6).
        ...
    
    Returns:
        SimpleReactor object with easy-to-use methods for analysis.
    
    Raises:
        ValueError: If preset name is not found or parameters are invalid.
        ImportError: If preset designs module is not available.
    
    Examples:
        >>> reactor = smr.create_reactor("valar-10")
        >>> k_eff = reactor.solve_keff()
    """
```

### Required Documentation

For all public functions, document:
- **Parameters**: Type, units, purpose, defaults
- **Returns**: Type and description
- **Raises**: Exception types and conditions
- **Examples**: At least one usage example
- **Unit Notes**: Clear indication of units for all parameters

---

## 7. Return Type Patterns

### Object Returns
Factory functions return objects:
- `create_reactor()` -> `SimpleReactor`
- `create_plot()` -> `Plot`
- `create_simple_solver()` -> `MultiGroupDiffusion`

### Dictionary Returns
Analysis functions return dictionaries:
- `analyze_preset(design_name)` -> `Dict`
- `compare_designs(design_names)` -> `Dict[str, Dict]`

### Value Returns
Computation functions return values:
- `quick_keff(...)` -> `float`
- `list_presets()` -> `List[str]`

### Dataclass Returns
Complex results use dataclasses:
- `sweep.run()` -> `SweepResult` (dataclass)
- `burnup.solve()` -> `NuclideInventory` (dataclass)

---

## 8. Configuration Objects

For complex operations, use dataclass configuration objects:

```python
@dataclass
class SolverOptions:
    max_iterations: int = 1000
    tolerance: float = 1e-6
    eigen_method: str = "power"
    verbose: bool = False

# Usage
options = SolverOptions(max_iterations=2000, tolerance=1e-8)
solver = MultiGroupDiffusion(geometry, xs_data, options)
```

Benefits:
- Type safety via dataclasses
- Validation via Pydantic (where applicable)
- Clear parameter organization
- Easy to extend

---

## 9. Optional Dependencies

Handle optional dependencies gracefully:

```python
try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

def plot_something(backend='plotly'):
    if backend == 'plotly' and not _PLOTLY_AVAILABLE:
        raise ImportError(
            "Plotly not available. Install with: pip install plotly"
        )
```

- Always check availability before use
- Provide clear error messages
- List installation instructions

---

## 10. Breaking Changes

### When to Make Breaking Changes

- Only for critical bugs or major API improvements
- Document in CHANGELOG.md
- Provide migration guide if significant
- Consider deprecation warnings first

### Deprecation Process

1. Mark old function with `@deprecated` decorator
2. Add warning message with alternative
3. Keep old function for 1-2 versions
4. Remove in next major version

---

## 11. Testing Requirements

All public APIs should have:
- Unit tests for core functionality
- Edge case tests (None, empty, invalid inputs)
- Integration tests for workflows
- Documentation examples should be testable

---

## Summary

**Key Principles:**
1. ✅ Use consistent naming (`create_*`, `get_*`, `list_*`, `build_*`)
2. ✅ Document units clearly (power_mw → watts, time_steps → days)
3. ✅ Follow parameter ordering conventions
4. ✅ Support dual APIs where appropriate (document when to use which)
5. ✅ Use appropriate exception types with helpful messages
6. ✅ Provide complete docstrings with examples
7. ✅ Use dataclasses for complex configurations
8. ✅ Handle optional dependencies gracefully

**Questions?** See `docs/status/API_CONSISTENCY_REPORT.md` for detailed analysis of current patterns.

---

**Last Updated:** January 2026  
**Next Review:** After major API changes
