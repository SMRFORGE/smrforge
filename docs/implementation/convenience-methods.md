# Convenience Methods and Functions Summary

**Date:** January 1, 2026  
**Last Updated:** February 2026  
**Status:** ✅ Complete

---

## Overview

This document summarizes the convenience methods and functions added to SMRForge to simplify common operations and reduce boilerplate code.

---

## What Was Added

### 1. New Convenience Utilities Module

**File:** `smrforge/convenience_utils.py`

A comprehensive module providing helper functions for:
- Geometry creation and manipulation
- Neutronics solver setup
- Burnup calculations
- Nuclear data operations
- Material database access
- Visualization
- Complete workflow automation

### 2. Class Extension Methods

Convenience methods added to existing classes:
- `PrismaticCore.quick_setup()` - Quick geometry and mesh setup
- `MultiGroupDiffusion.quick_solve()` - Quick solve with optional power calculation

---

## Convenience Functions by Category

### Geometry Functions

#### `create_simple_core()`
Quick creation of prismatic core with sensible defaults.

```python
from smrforge import create_simple_core

core = create_simple_core(
    name="MyCore",
    n_rings=3,
    pitch=40.0,
    block_height=80.0,
    n_axial=2,
)
```

#### `quick_mesh_extraction()`
Quick extraction of 3D meshes from core geometry.

```python
from smrforge import quick_mesh_extraction

mesh = quick_mesh_extraction(core, mesh_type="volume")
```

### Neutronics Functions

#### `create_simple_solver()`
Quick creation of neutronics solver with defaults.

```python
from smrforge import create_simple_solver

solver = create_simple_solver(core=core, n_groups=2)
k_eff, flux = solver.solve_steady_state()
```

#### `create_simple_xs_data()`
Quick creation of cross-section data.

```python
from smrforge import create_simple_xs_data

xs_data = create_simple_xs_data(n_groups=2, n_materials=2)
```

#### `quick_keff_calculation()`
One-liner k-eff calculation.

```python
from smrforge import quick_keff_calculation

k_eff, flux = quick_keff_calculation()
```

### Burnup Functions

#### `create_simple_burnup_solver()`
Quick creation of burnup solver.

```python
from smrforge import create_simple_burnup_solver

burnup = create_simple_burnup_solver(
    time_steps_days=[0, 365, 730],
    power_density=1e6,
)
inventory = burnup.solve()
```

#### `quick_burnup_calculation()`
Quick burnup calculation for single time point.

```python
from smrforge import quick_burnup_calculation

inventory = quick_burnup_calculation(time_days=365.0)
```

### Nuclear Data Functions

#### `get_nuclide()`
Get Nuclide instance from name string.

```python
from smrforge import get_nuclide

u235 = get_nuclide("U235")
print(u235.zam)  # 922350
```

#### `create_nuclide_list()`
Create list of Nuclide instances.

```python
from smrforge import create_nuclide_list

nuclides = create_nuclide_list(["U235", "U238", "Pu239"])
```

### Material Functions

#### `get_material()`
Get material from database by name.

```python
from smrforge import get_material

graphite = get_material("graphite_IG-110")
k = graphite.thermal_conductivity(1200.0)
```

#### `list_materials()`
List available materials, optionally filtered by category.

```python
from smrforge import list_materials

materials = list_materials()
moderators = list_materials(category="moderator")
```

### Decay Heat Functions

#### `quick_decay_heat()`
Quick decay heat calculation.

```python
from smrforge import quick_decay_heat

heat = quick_decay_heat(
    {"U235": 1e20, "Cs137": 1e19},
    time_seconds=86400.0,
)
```

### Visualization Functions

#### `quick_plot_core()`
Quick plot of core layout.

```python
from smrforge import quick_plot_core

quick_plot_core(core, view="xy")
```

#### `quick_plot_mesh()`
Quick 3D mesh plot.

```python
from smrforge import quick_plot_mesh

quick_plot_mesh(mesh, color_by="material")
```

### Complete Workflow Functions

#### `run_complete_analysis()`
Run complete reactor analysis workflow.

```python
from smrforge import run_complete_analysis

results = run_complete_analysis(
    power_mw=10.0,
    include_burnup=False,
)
print(f"k-eff: {results['k_eff']:.6f}")
```

---

## Class Convenience Methods

### PrismaticCore.quick_setup()

Quick setup of geometry and mesh.

```python
core = PrismaticCore("MyCore")
core.quick_setup(
    n_rings=3,
    pitch=40.0,
    block_height=80.0,
    n_axial=2,
)
```

### MultiGroupDiffusion.quick_solve()

Quick solve with optional power calculation.

```python
solver = create_simple_solver()
k_eff = solver.quick_solve()

# Or get full results
results = solver.quick_solve(return_power=True)
```

---

## Usage Examples

### Example 1: Quick k-eff Calculation

```python
from smrforge import quick_keff_calculation

k_eff, flux = quick_keff_calculation()
print(f"k-eff = {k_eff:.6f}")
```

### Example 2: Complete Workflow

```python
from smrforge import run_complete_analysis

results = run_complete_analysis(
    power_mw=10.0,
    include_burnup=True,
    burnup_time_days=365.0,
)

print(f"k-eff: {results['k_eff']:.6f}")
print(f"Peak flux: {results['peak_flux']:.2e}")
print(f"Burnup inventory: {results['burnup_inventory']}")
```

### Example 3: Nuclide Operations

```python
from smrforge import get_nuclide, create_nuclide_list

# Single nuclide
u235 = get_nuclide("U235")

# Multiple nuclides
nuclides = create_nuclide_list(["U235", "U238", "Pu239", "Cs137"])
```

### Example 4: Material Access

```python
from smrforge import get_material, list_materials

# Get material
graphite = get_material("graphite_IG-110")
k = graphite.thermal_conductivity(1200.0)

# List materials
all_materials = list_materials()
moderators = list_materials(category="moderator")
```

---

## Benefits

1. **Reduced Boilerplate**: Common operations require fewer lines of code
2. **Sensible Defaults**: Functions provide reasonable defaults for common use cases
3. **Easy Learning Curve**: New users can get started quickly
4. **Flexibility**: All functions accept keyword arguments for customization
5. **Integration**: Functions work together seamlessly

---

## Files Modified

1. **`smrforge/convenience_utils.py`** - New module with all convenience functions
2. **`smrforge/__init__.py`** - Updated to export convenience functions
3. **`examples/convenience_methods_example.py`** - Example demonstrating usage

---

## Testing

Run the example to test convenience functions:

```bash
python examples/convenience_methods_example.py
```

---

## New Convenience Functions (February 2026)

### Workflow One-Liners

| Function | Description |
|----------|-------------|
| `quick_validation_run()` | Run validation suite (mirror CLI `validate run`) |
| `quick_openmc_run()` | Export reactor → run OpenMC → parse statepoint |
| `quick_preprocessed_data()` | Download preprocessed library with defaults |
| `quick_design_study()` | Design point + safety report in one call |
| `quick_atlas()` | Build design-space atlas for presets |
| `quick_doe()` | Design of Experiments (factorial, LHS, Sobol, random) |
| `quick_pareto()` | Extract Pareto front from sweep results |
| `quick_sensitivity()` | Sensitivity ranking from sweep results |

### Discovery Functions

| Function | Description |
|----------|-------------|
| `list_validation_benchmarks()` | Benchmark IDs from validation_benchmarks.json |
| `list_preset_types()` | Presets grouped by type (HTGR, LWR, MSR) |
| `list_pro_features()` | Pro-only feature names |
| `list_tier_capabilities()` / `get_tier_info()` | Community vs Pro capabilities |
| `list_workflows()` | Workflow subcommand names |
| `list_convenience_functions()` | All quick_*, list_*, get_* names |
| `list_cli_commands()` | Top-level CLI commands |
| `get_quick_start_commands()` | Suggested first commands |
| `list_functions_by_category()` | Functions grouped by topic |

### Data & Paths

| Function | Description |
|----------|-------------|
| `find_endf_directory()` | Search for ENDF data |
| `get_data_paths()` | Standard paths (endf, output, config, examples) |
| `list_available_benchmarks()` | Benchmarks with optional metadata |

### Help Functions

| Function | Description |
|----------|-------------|
| `check_setup()` | Verify ENDF, OpenMC, optional deps |
| `get_environment_summary()` | Paths, env vars, optional deps status |
| `validate_installation()` | Basic sanity checks for bug reports |
| `get_support_info()` | Version/platform/config for support |
| `get_function_signature()` | Callable signature string |
| `suggest_next_steps()` | Suggested workflows based on completed actions |
| `what_can_i_do_with()` | Suggested functions for an object |
| `get_workflow_help()` | Argparse help for workflow subcommands |
| `get_upgrade_benefits()` | Human-readable Pro benefits |
| `check_pro_feature()` | (available, message) for a Pro feature |
| `list_pro_vs_community()` | Structured tier comparison |
| `help_search()` | Search topics and functions |
| `list_help_topics()` | Alias for help_topics() |
| `get_cheat_sheet()` | Compact one-liner reference |

### Pro-Only (Stubs in Community)

When Pro is not installed, these raise a clear upgrade message:
`quick_code_verify`, `quick_regulatory_package`, `quick_benchmark_reproduce`, `quick_surrogate_fit`, `quick_nl_design`, `quick_multi_optimize`, `quick_tally_visualization`

---

## Future Enhancements

Potential additions:
- More convenience methods for thermal-hydraulics
- Convenience methods for safety analysis
- Batch processing convenience functions
- Parallel computation helpers

---

*Implementation completed January 2025; extended February 2026*

