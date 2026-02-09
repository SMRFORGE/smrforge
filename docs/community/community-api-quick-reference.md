# Community Tier — API Quick Reference

Key modules and functions for Community edition.

---

## Top-Level (`smrforge`)

| Function | Purpose |
|----------|---------|
| `create_reactor(name)` | Create reactor from preset |
| `list_presets()` | List preset names |
| `get_preset(name)` | Get preset spec |
| `get_design_point(reactor)` | Design point dict |
| `quick_keff(...)` | Fast k-eff |
| `quick_keff_calculation()` | k-eff + flux |
| `create_simple_core()` | Simple core |
| `create_simple_solver()` | Simple neutronics solver |
| `quick_mesh_extraction(core)` | 3D mesh |
| `quick_plot_core(core)` | 2D core plot |
| `quick_plot_mesh(mesh)` | 3D mesh plot |
| `get_nuclide(name)` | Nuclide from name |
| `help(topic)` | Interactive help |

---

## Neutronics

| Module | Class/Function |
|--------|----------------|
| `smrforge.neutronics.solver` | `MultiGroupDiffusion` |
| `smrforge.validation.models` | `CrossSectionData`, `SolverOptions` |

---

## Burnup

| Module | Class/Function |
|--------|----------------|
| `smrforge.burnup` | `BurnupSolver`, `BurnupOptions` |

---

## Geometry

| Module | Class |
|--------|-------|
| `smrforge.geometry` | `PrismaticCore`, `PebbleBedCore` |
| `smrforge.geometry.lwr_smr` | `LWR_SMR` |

---

## Nuclear Data

| Module | Class/Function |
|--------|----------------|
| `smrforge.core.reactor_core` | `NuclearDataCache`, `Nuclide`, `Library` |

---

## Validation

| Module | Function/Class |
|--------|----------------|
| `smrforge.validation.safety_report` | `safety_margin_report` |
| `smrforge.validation.constraints` | `ConstraintSet` |
| `smrforge.validation.constraint_builder` | `constraint_set_from_design_and_report` |

---

## Workflows

| Module | Class/Function |
|--------|----------------|
| `smrforge.workflows.parameter_sweep` | `ParameterSweep`, `ParameterSweepConfig` |
| `smrforge.workflows.scenario_design` | `run_scenario_design`, `scenario_comparison_report` |
| `smrforge.workflows.atlas` | `build_atlas`, `filter_atlas` |
| `smrforge.workflows.pareto_report` | `pareto_summary_report`, `pareto_knee_point` |
