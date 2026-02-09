# Community Tier — Tutorial

Step-by-step introduction to SMRForge Community edition.

---

## Prerequisites

- Python 3.9+
- `pip install smrforge`

---

## Step 1: Quick k-eff (30 seconds)

No data required.

```python
import smrforge as smr

k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)
print(f"k_eff: {k_eff:.6f}")
```

---

## Step 2: Preset Reactor (1 minute)

```python
import smrforge as smr

reactor = smr.create_reactor("valar-10")
results = reactor.solve()
print(f"k_eff: {results['k_eff']:.6f}")
```

---

## Step 3: Design Point & Safety Margins

```python
import smrforge as smr

reactor = smr.create_reactor("valar-10")
point = smr.get_design_point(reactor)
print(point)

from smrforge.validation.safety_report import safety_margin_report
report = safety_margin_report(reactor)
print(report.to_text())
```

---

## Step 4: Burnup (requires a few minutes)

```python
from smrforge.burnup import BurnupSolver, BurnupOptions
from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions
import numpy as np

# Geometry
geometry = PrismaticCore(name="TutorialCore")
geometry.core_height = 200.0
geometry.core_diameter = 100.0
geometry.build_mesh(n_radial=10, n_axial=5)

# Synthetic XS
xs_data = CrossSectionData(
    n_groups=2, n_materials=1,
    sigma_t=np.array([[0.5, 0.8]]),
    sigma_a=np.array([[0.1, 0.2]]),
    sigma_f=np.array([[0.05, 0.15]]),
    nu_sigma_f=np.array([[0.125, 0.375]]),
    sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
    chi=np.array([[1.0, 0.0]]),
    D=np.array([[1.5, 0.4]]),
)

# Solver
neutronics = MultiGroupDiffusion(
    geometry, xs_data,
    SolverOptions(max_iterations=100, tolerance=1e-6, eigen_method="power", verbose=False),
)
k_eff, _ = neutronics.solve_steady_state()

# Burnup
options = BurnupOptions(
    time_steps=[0, 30, 60, 90],
    power_density=1e6,
    initial_enrichment=0.195,
)
burnup = BurnupSolver(neutronics, options)
inventory = burnup.solve()

print(f"Final burnup: {inventory.burnup[-1]:.2f} MWd/kgU")
```

---

## Step 5: 3D Visualization (optional: pip install smrforge[viz])

```python
import smrforge as smr

core = smr.create_simple_core()
mesh = smr.quick_mesh_extraction(core, mesh_type="volume")
smr.quick_plot_mesh(mesh, color_by="material")
```

---

## Next Steps

- [Community Workflows](../community/community-workflows.md)
- [Feature Matrix](../community/community-feature-matrix.md)
- [Examples](../../examples/community/)
