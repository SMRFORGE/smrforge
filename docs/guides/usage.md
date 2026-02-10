# SMRForge Usage Guide

**Last Updated:** February 10, 2026

This guide shows how to use SMRForge with simple one-liners and easy-to-use APIs.

> **Pro:** For Serpent/MCNP export and tally visualization, see [Community vs Pro](../community_vs_pro.md). Community: OpenMC full export/import; Serpent run+parse (round-trip with Pro export). See `examples/openmc_export_example.py`.

## Quick Reference

### One-Liners

```python
import smrforge as smr

# Get k-eff (simplest!)
k = smr.quick_keff()

# Analyze preset design
results = smr.analyze_preset("valar-10")

# Create and solve custom reactor
reactor = smr.create_reactor(power_mw=10, enrichment=0.195)
results = reactor.solve()
```

### Available Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `quick_keff(...)` | Quick k-eff calculation | `float` |
| `create_reactor(name)` | Create reactor from preset | `SimpleReactor` |
| `create_reactor(**kwargs)` | Create custom reactor | `SimpleReactor` |
| `analyze_preset(name)` | Full analysis of preset | `Dict` |
| `list_presets()` | List available presets | `List[str]` |
| `compare_designs(names)` | Compare multiple designs | `Dict[str, Dict]` |

### SimpleReactor Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `solve_keff()` | Get k-eff only | `float` |
| `solve()` | Full analysis | `Dict` |
| `save(filepath)` | Save to JSON | None |
| `load(filepath)` | Load from JSON | `SimpleReactor` |

### Preset Designs

- `"valar-10"` - Valar Atomics 10 MWth micro-reactor
- `"gt-mhr-350"` - GT-MHR 350 MWth
- `"htr-pm-200"` - HTR-PM 200 MWth
- `"micro-htgr-1"` - Micro HTGR 1 MWth

---

## Beginner Workflow (Start Here)

This is the simplest end-to-end workflow using **preset data**.

### Option 1: Python-only workflow (recommended for “all features”)

1) **Create a reactor from a preset**:

```python
import smrforge as smr

reactor = smr.create_reactor("valar-10")
print(reactor.spec)
```

2) **Run neutronics**:

```python
results = reactor.solve()
print("k_eff:", results["k_eff"])
```

3) **Save the reactor to a reusable input file**:

```python
reactor.save("reactor.json")
```

### Option 2: CLI workflow (best for quick runs)

1) **Create an input file** from a preset:

```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

2) **Analyze** and write a results file:

```bash
smrforge reactor analyze --reactor reactor.json --neutronics --output results.json
```

3) **Visualize geometry**:

```bash
smrforge visualize geometry --reactor reactor.json --output geometry.png --format png
```

Notes:
- In the current CLI, burnup and flux plotting are primarily done via the Python API (the CLI commands print guidance).

---

## Examples

### 1. Quick k-eff Calculation

```python
import smrforge as smr

# Simplest possible usage
k = smr.quick_keff(
    power_mw=10,
    enrichment=0.195
)
print(f"k-eff = {k:.6f}")
```

### 2. Analyze Preset Design

```python
import smrforge as smr

# List available presets
print("Available designs:", smr.list_presets())

# Analyze a preset
results = smr.analyze_preset("valar-10")
print(f"\nValar-10 Analysis:")
print(f"  k-eff: {results['k_eff']:.6f}")
print(f"  Power: {results['power_thermal_mw']:.1f} MWth")
print(f"  Flux shape: {results['flux'].shape}")
```

### 3. Create Custom Reactor

```python
import smrforge as smr

# Create custom reactor
reactor = smr.create_reactor(
    power_mw=10,
    core_height=200,
    core_diameter=100,
    enrichment=0.195,
    name="My-Custom-Reactor"
)

# Solve for k-eff only
k = reactor.solve_keff()
print(f"k-eff = {k:.6f}")

# Or run full analysis
results = reactor.solve()
print(f"\nFull Results:")
print(f"  k-eff: {results['k_eff']:.6f}")
print(f"  Flux max: {results['flux'].max():.3e}")
print(f"  Power: {results['power_thermal_mw']:.1f} MWth")
```

### 4. Compare Multiple Designs

```python
import smrforge as smr

# Compare multiple designs
results = smr.compare_designs(["valar-10", "htr-pm-200", "micro-htgr-1"])

for name, data in results.items():
    if 'k_eff' in data:
        print(f"{name}: k-eff = {data['k_eff']:.6f}")
    else:
        print(f"{name}: Error - {data.get('error', 'Unknown')}")
```

### 5. Save and Load Reactors

```python
import smrforge as smr

# Create and save
reactor = smr.create_reactor("valar-10")
reactor.save("my_reactor.json")

# Load later
reactor2 = smr.SimpleReactor.load("my_reactor.json")
k = reactor2.solve_keff()
print(f"k-eff from saved reactor: {k:.6f}")
```

### 6. Design Study (Enrichment Sweep)

```python
import smrforge as smr
import numpy as np
import matplotlib.pyplot as plt

# Study effect of enrichment on k-eff
enrichments = np.linspace(0.15, 0.25, 11)
keffs = []

for enr in enrichments:
    k = smr.quick_keff(enrichment=enr)
    keffs.append(k)
    print(f"Enrichment {enr:.3f}: k-eff = {k:.6f}")

# Plot results
plt.plot(enrichments, keffs, 'o-')
plt.xlabel('Enrichment')
plt.ylabel('k-eff')
plt.grid(True)
plt.show()
```

### 7. Access Detailed Results

```python
import smrforge as smr
import numpy as np

# Get full analysis results
reactor = smr.create_reactor("valar-10")
results = reactor.solve()

# Access flux distribution
flux = results['flux']
print(f"Flux shape: {flux.shape}")
print(f"Flux range: [{flux.min():.3e}, {flux.max():.3e}]")

# Access power distribution if available
if 'power_distribution' in results:
    power = results['power_distribution']
    print(f"Power shape: {power.shape}")
    print(f"Max power density: {power.max():.3e} W/cm³")
```

---

## Comparison: Before vs After

### Before (Many Steps - Complex)

```python
# Old way - too many steps!
from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions
import numpy as np

# Step 1: Create geometry
core = PrismaticCore(name="test")
core.build_hexagonal_lattice(n_rings=3, pitch=40.0, block_height=50.0, 
                             n_axial=4, flat_to_flat=36.0)
core.generate_mesh(n_radial=15, n_axial=20)

# Step 2: Create cross sections (lots of arrays!)
xs_data = CrossSectionData(
    n_groups=2, n_materials=2,
    sigma_t=np.array([[0.30, 0.90], [0.28, 0.75]]),
    sigma_a=np.array([[0.008, 0.12], [0.002, 0.025]]),
    # ... many more arrays
)

# Step 3: Create solver options
options = SolverOptions(max_iterations=1000, tolerance=1e-6)

# Step 4: Create solver
solver = MultiGroupDiffusion(core, xs_data, options)

# Step 5: Solve
k_eff, flux = solver.solve_steady_state()
```

### After (One-Liner - Easy!)

```python
# New way - one-liner!
import smrforge as smr

k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)
print(f"k-eff = {k_eff:.6f}")
```

**That's it!** From ~40 lines to 3 lines, and much more readable!

---

## Advanced Usage

The convenience API is great for common tasks, but the full API is still available for advanced use cases:

```python
from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions

# Full control when needed
core = PrismaticCore(name="advanced")
# ... configure geometry ...

xs_data = CrossSectionData(...)
options = SolverOptions(...)
solver = MultiGroupDiffusion(core, xs_data, options)
k_eff, flux = solver.solve_steady_state()
```

See the `examples/` directory for more complete examples:
- `examples/basic_neutronics.py` - Basic neutronics calculations
- `examples/preset_designs.py` - Working with preset designs
- `examples/custom_reactor.py` - Custom reactor specifications
- `examples/visualization_examples.py` - Geometry visualization (2D plots, flux/power/temperature)
- `examples/control_rods_example.py` - Control rod geometry and management
- `examples/assembly_refueling_example.py` - Assembly management and refueling
- `examples/geometry_import_example.py` - Geometry import/export (JSON)
- `examples/complete_integration_example.py` - Complete workflow

### Visualization screenshots

For a quick visual overview, see the [Visualization gallery](visualization-gallery.md).

For copy-paste plotting recipes across sweeps/UQ/burnup/transients/validation/economics, see the [Visual analytics cookbook](visual-analytics.md).

---

## Tips

1. **Start with presets**: Use `smr.list_presets()` to see available designs
2. **Use defaults**: Most functions have sensible defaults
3. **One-liners for exploration**: Use `quick_keff()` for quick studies
4. **Full analysis when needed**: Use `analyze_preset()` or `reactor.solve()` for complete results
5. **Save your designs**: Use `reactor.save()` to save custom reactors

---

*For more information, see the [API Reference](docs/api_reference.rst) and [Examples](examples/).*

