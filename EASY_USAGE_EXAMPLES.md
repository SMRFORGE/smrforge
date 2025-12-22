# Easy Usage Examples - SMRForge One-Liners

This document shows how to use SMRForge with simple one-liners and easy-to-use APIs.

---

## Quick Start - One-Liners

### 1. Get k-eff for a Preset Design (1 line!)

```python
import smrforge as smr

# One-liner: Get k-eff for Valar-10 reactor
k = smr.quick_keff()  # Uses sensible defaults
print(f"k-eff = {k:.6f}")

# Or specify a preset
k = smr.create_reactor("valar-10").solve_keff()
print(f"k-eff = {k:.6f}")
```

### 2. Analyze a Preset Design (1 line!)

```python
import smrforge as smr

# One-liner: Full analysis of preset design
results = smr.analyze_preset("valar-10")
print(f"k-eff: {results['k_eff']:.6f}")
print(f"Power: {results['power_thermal_mw']:.1f} MWth")
```

### 3. Create Custom Reactor (3 lines)

```python
import smrforge as smr

# Create custom reactor with simple parameters
reactor = smr.create_reactor(
    power_mw=10,
    core_height=200,
    core_diameter=100,
    enrichment=0.195
)

# Solve (one-liner)
results = reactor.solve()
print(f"k-eff: {results['k_eff']:.6f}")
```

---

## Complete Examples

### Example 1: Quick k-eff Calculation

```python
import smrforge as smr

# Simplest possible usage
k = smr.quick_keff(
    power_mw=10,
    enrichment=0.195
)
print(f"k-eff = {k:.6f}")
```

### Example 2: Analyze Preset Design

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

### Example 3: Compare Multiple Designs

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

### Example 4: Custom Reactor with Full Control

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

### Example 5: Save and Load Reactors

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

### Example 6: Iterative Design Study

```python
import smrforge as smr
import numpy as np

# Study effect of enrichment on k-eff
enrichments = np.linspace(0.15, 0.25, 11)
keffs = []

for enr in enrichments:
    k = smr.quick_keff(enrichment=enr)
    keffs.append(k)
    print(f"Enrichment {enr:.3f}: k-eff = {k:.6f}")

# Plot results
import matplotlib.pyplot as plt
plt.plot(enrichments, keffs, 'o-')
plt.xlabel('Enrichment')
plt.ylabel('k-eff')
plt.grid(True)
plt.show()
```

### Example 7: Power Sweep Study

```python
import smrforge as smr
import numpy as np

# Study different power levels
powers = [5, 10, 20, 50]  # MW
keffs = []

for power in powers:
    k = smr.quick_keff(power_mw=power)
    keffs.append(k)
    print(f"{power:2d} MW: k-eff = {k:.6f}")
```

### Example 8: Access Detailed Results

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
    sigma_f=np.array([[0.006, 0.10], [0.0, 0.0]]),
    nu_sigma_f=np.array([[0.015, 0.25], [0.0, 0.0]]),
    sigma_s=np.array([[[0.29, 0.01], [0.0, 0.78]], 
                      [[0.28, 0.0], [0.0, 0.73]]]),
    chi=np.array([[1.0, 0.0], [1.0, 0.0]]),
    D=np.array([[1.0, 0.4], [1.2, 0.5]]),
)

# Step 3: Create solver options
options = SolverOptions(max_iterations=1000, tolerance=1e-6)

# Step 4: Create solver
solver = MultiGroupDiffusion(core, xs_data, options)

# Step 5: Solve
k_eff, flux = solver.solve_steady_state()
print(f"k-eff = {k_eff:.6f}")
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

## Advanced Usage (Still Easy!)

### Using SimpleReactor Class Directly

```python
import smrforge as smr

# Create reactor
reactor = smr.SimpleReactor(
    power_mw=10,
    core_height=200,
    core_diameter=100,
    enrichment=0.195
)

# Solve
results = reactor.solve()

# Access reactor specification
print(f"Reactor: {reactor.spec.name}")
print(f"Power: {reactor.spec.power_thermal/1e6:.1f} MWth")
print(f"Enrichment: {reactor.spec.enrichment:.1%}")

# Access underlying objects if needed
solver = reactor._get_solver()
core = reactor._get_core()
xs = reactor._get_xs_data()
```

### Custom Cross Sections (Still Simple)

For advanced users who want to customize cross sections but still use the easy API:

```python
import smrforge as smr
from smrforge.validation.models import CrossSectionData
import numpy as np

# Create reactor
reactor = smr.create_reactor("valar-10")

# Replace cross sections with custom ones
reactor._xs_data = your_custom_xs_data  # Your CrossSectionData object

# Solve with custom XS
results = reactor.solve()
```

---

## Tips for Easy Usage

1. **Start with presets**: Use `smr.list_presets()` to see available designs
2. **Use defaults**: Most functions have sensible defaults
3. **One-liners for exploration**: Use `quick_keff()` for quick studies
4. **Full analysis when needed**: Use `analyze_preset()` or `reactor.solve()` for complete results
5. **Save your designs**: Use `reactor.save()` to save custom reactors

---

## Migration Guide

If you have existing code using the old API:

1. Replace geometry + XS creation with `smr.create_reactor()`
2. Replace solver setup with `reactor.solve()` or `reactor.solve_keff()`
3. Access results from the returned dictionary instead of solver attributes

Old code still works, but the new API is much simpler for common tasks!

