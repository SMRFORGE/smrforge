## Visual analytics cookbook

This page collects **copy‑pasteable** examples for visualizing SMRForge outputs.

Most plots support two backends:
- **Plotly** (interactive; great for Dash / notebooks)
- **Matplotlib** (static; great for docs / reports)

---

### Parameter sweeps (heatmaps, tornado, Pareto)

```python
from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig
from smrforge.visualization.sweep_plots import (
    plot_sweep_heatmap,
    plot_sweep_tornado,
    plot_sweep_pareto,
    plot_sweep_correlation_matrix,
)

cfg = SweepConfig(
    parameters={"enrichment": [0.15, 0.195, 0.24], "power_mw": [8.0, 10.0, 12.0]},
    analysis_types=["keff"],
    reactor_template={"name": "sweep-demo"},  # custom base reactor (not a preset)
    parallel=False,
)
res = ParameterSweep(cfg).run()

fig = plot_sweep_heatmap(res, x_param="enrichment", y_param="power_mw", metric="k_eff", backend="plotly")
fig.show()

fig = plot_sweep_tornado(res, metric="k_eff", mode="range", backend="plotly")
fig.show()

fig = plot_sweep_correlation_matrix(res, backend="plotly")
fig.show()
```

---

### Uncertainty quantification (distributions, correlations)

```python
import numpy as np
from smrforge.uncertainty.uq import UQResults, UncertainParameter
from smrforge.uncertainty.visualization import (
    plot_uq_distribution,
    plot_uq_correlation_matrix,
)

params = [
    UncertainParameter(name="enrichment", distribution="normal", nominal=0.195, uncertainty=0.01),
    UncertainParameter(name="power_mw", distribution="uniform", nominal=10.0, uncertainty=(8.0, 12.0)),
]

n = 1000
samples = np.column_stack([p.sample(n, random_state=10 + i) for i, p in enumerate(params)])
keff = 1.0 + 0.8 * (samples[:, 0] - 0.195) - 0.002 * (samples[:, 1] - 10.0)
outputs = keff.reshape(-1, 1)

res = UQResults(
    parameter_names=[p.name for p in params],
    parameter_samples=samples,
    output_samples=outputs,
    output_names=["k_eff"],
)

plot_uq_distribution(res, backend="plotly").show()
plot_uq_correlation_matrix(res, include_outputs=True, backend="plotly").show()
```

---

### Neutronics spectra dashboards

```python
import numpy as np
from smrforge.visualization.tally_data import plot_neutronics_dashboard

ng = 26
energy_groups = np.logspace(7, -5, ng + 1)
flux = np.random.default_rng(0).random((20, 15, ng))  # [nz, nr, ng] demo shape

plot_neutronics_dashboard(flux, energy_groups, k_eff=1.0, backend="plotly").show()
```

---

### Burnup / isotopics evolution (NuclideInventory)

```python
import numpy as np
from smrforge.burnup.solver import NuclideInventory
from smrforge.core.reactor_core import Nuclide
from smrforge.visualization.material_composition import (
    plot_burnup_dashboard,
    plot_nuclide_evolution,
)

t_days = np.linspace(0.0, 365.0, 61)
t_s = t_days * 24.0 * 3600.0
burnup = 50.0 * (t_days / t_days.max())

nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238), Nuclide(Z=94, A=239)]
concentrations = np.vstack(
    [
        np.exp(-2.0 * t_days / t_days.max()),
        5.0 * np.ones_like(t_days),
        0.2 + 0.8 * (1.0 - np.exp(-3.0 * t_days / t_days.max())),
    ]
)

inv = NuclideInventory(nuclides=nuclides, concentrations=concentrations, times=t_s, burnup=burnup)
plot_burnup_dashboard(inv, backend="plotly").show()
plot_nuclide_evolution(inv, backend="plotly").show()
```

---

### Transients (with event annotations)

```python
from smrforge.convenience.transients import quick_transient
from smrforge.visualization.transients import plot_transient

res = quick_transient(
    power=1e6,
    temperature=1200.0,
    transient_type="reactivity_insertion",
    reactivity_insertion=0.001,
    duration=30.0,
    plot=False,
)

plot_transient(
    res,
    backend="plotly",
    annotate_peaks=True,
    events=[(5.0, "Example event", "info")],
).show()
```

---

### Mesh diagnostics

```python
import numpy as np
from smrforge.geometry.mesh_generation import AdvancedMeshGenerator
from smrforge.visualization.mesh_diagnostics import plot_mesh_verification_dashboard

rng = np.random.default_rng(0)
points = rng.normal(size=(200, 2))
gen = AdvancedMeshGenerator()
vertices, triangles = gen.generate_2d_unstructured_mesh(points=points)
quality = gen.evaluate_mesh_quality(vertices, triangles)

sizes = rng.lognormal(mean=0.0, sigma=0.7, size=500)
plot_mesh_verification_dashboard(quality=quality, sizes=sizes, backend="plotly").show()
```

---

### Validation plots

```python
from smrforge.validation.data_validation import ValidationLevel, ValidationResult
from smrforge.visualization.validation_plots import plot_validation_summary, plot_validation_issues

res = ValidationResult(valid=True)
res.add_issue(ValidationLevel.WARNING, "temperature", "Below expected minimum", value=250.0, expected=">= 273 K")
res.add_issue(ValidationLevel.ERROR, "pressure", "Negative pressure", value=-1.0, expected=">= 0 Pa")

plot_validation_summary(res, backend="plotly").show()
plot_validation_issues(res, backend="plotly").show()
```

---

### Economics + optimization

```python
from smrforge.economics.cost_modeling import CapitalCostEstimator, OperatingCostEstimator, LCOECalculator
from smrforge.visualization.economics_plots import plot_capex_breakdown, plot_lcoe_breakdown
from smrforge.visualization.optimization_plots import plot_optimization_trace

power_electric = 10e6 * 0.33
cap = CapitalCostEstimator(power_electric=power_electric, reactor_type="prismatic", nth_of_a_kind=1)
op = OperatingCostEstimator(power_electric=power_electric, fuel_loading=150.0, cycle_length=3650.0, target_burnup=150.0)

plot_capex_breakdown(cap.get_cost_breakdown(), backend="plotly", kind="waterfall").show()

lcoe = LCOECalculator(capital_cost=cap.estimate_overnight_cost(), power_electric=power_electric, operating_cost_estimator=op)
plot_lcoe_breakdown(lcoe.get_cost_breakdown(), backend="plotly").show()

plot_optimization_trace([1.0, 0.7, 0.55, 0.51, 0.50], backend="plotly").show()
```

