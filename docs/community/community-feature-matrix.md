# Community Tier — Feature Matrix

Each feature includes: **workflow**, **required data**, and **outputs**.

> **Pro:** For Serpent/OpenMC/MCNP export, full benchmark suite, and regulatory reports, see [Community vs Pro](../../community_vs_pro.md). Community includes Serpent run+parse (round-trip with Pro export): `smrforge.io.run_serpent()`, `parse_serpent_res()`.

---

## 1. Neutronics (Multi-Group Diffusion)

| Item | Details |
|------|---------|
| **Module** | `smrforge.neutronics.solver.MultiGroupDiffusion` |
| **Required data** | Geometry (material map, mesh), cross-section data (σt, σa, σf, νσf, σs, χ, D) |
| **Optional** | ENDF files for cross-section generation; otherwise use synthetic XS |

### Workflow

1. Create or load geometry (e.g., `PrismaticCore`, custom mesh).
2. Build cross-section data: `CrossSectionData(n_groups, n_materials, sigma_t, sigma_a, ...)` or from `NuclearDataCache.get_cross_section()`.
3. Create solver: `MultiGroupDiffusion(geometry, xs_data, options)`.
4. Solve: `k_eff, flux = solver.solve_steady_state()`.
5. Power: `power = solver.compute_power_distribution(total_power_mw)`.

### Data Sources

- **Synthetic:** Use `CrossSectionData` with hand-crafted arrays (no ENDF).
- **ENDF:** `NuclearDataCache(local_endf_dir=Path(...)).get_cross_section(nuclide, reaction, T)`.

### Outputs

- `k_eff`, flux shape, power distribution.

---

## 2. Nuclear Data (ENDF Parsing & Caching)

| Item | Details |
|------|---------|
| **Module** | `smrforge.core.reactor_core.NuclearDataCache` |
| **Required data** | ENDF files (NNDC/IAEA) in a local directory |
| **Optional backends** | endf-parserpy, SANDY, built-in parser |

### Workflow

1. Download ENDF: use `data_downloader.download_endf_data()` or manual download.
2. Configure: `export SMRFORGE_ENDF_DIR=/path/to/ENDF-B-VIII.1` or pass `cache_dir` to `NuclearDataCache`.
3. Fetch: `energy, xs = cache.get_cross_section(nuclide, reaction, temperature)`.
4. Optional: resonance self-shielding via `get_cross_section_self_shielded()`.

### Required Data

- ENDF directory with evaluated files (e.g., `n-092_U_235.endf`).
- Libraries: ENDF/B-VIII.0, ENDF/B-VIII.1, JEFF-3.3, JENDL-5.0.

### Outputs

- Energy arrays, cross-section arrays (barns).

---

## 3. Geometry Creation

| Item | Details |
|------|---------|
| **Modules** | `smrforge.geometry.PrismaticCore`, `PebbleBedCore`, `smrforge.geometry.lwr_smr.LWR_SMR` |
| **Required data** | Core dimensions, material assignments, mesh parameters |

### Workflow

1. Create core: `core = PrismaticCore(name="MyCore")`.
2. Set dimensions: `core.core_height`, `core.core_diameter`.
3. Build mesh: `core.build_mesh(n_radial=..., n_axial=...)`.
4. Extract material map or pass to neutronics solver.

### Required Data

- Core height (cm), core diameter (cm).
- Optional: fuel radius, number of rings, pitch (for lattice cores).

### Outputs

- Geometry object with mesh, material map, surface/volume mesh extraction.

---

## 4. Burnup (Depletion)

| Item | Details |
|------|---------|
| **Module** | `smrforge.burnup.BurnupSolver` |
| **Required data** | Neutronics solver, time steps, power density, initial enrichment |
| **Optional** | `NuclearDataCache` for real cross-sections; otherwise uses solver XS |

### Workflow

1. Create neutronics solver (see Neutronics).
2. Define `BurnupOptions(time_steps=[0, 30, 60, ...], power_density=..., initial_enrichment=...)`.
3. Create `BurnupSolver(neutronics, options, cache=...)`.
4. Run: `inventory = burnup.solve()`.
5. Query: `inventory.get_concentration(nuclide, time_index)`, `inventory.burnup`.

### Required Data

- Time steps (days), power density (W/cm³), initial enrichment (U-235).
- Optional: decay data, fission yields from ENDF if using cache.

### Outputs

- `NuclideInventory`: concentrations vs time, burnup (MWd/kgU), decay heat.

---

## 5. Decay Heat

| Item | Details |
|------|---------|
| **Module** | `smrforge.decay_heat.DecayHeatCalculator` or `burnup.compute_decay_heat()` |
| **Required data** | Nuclide inventory (atoms) and cooling time |

### Workflow

1. From burnup: `decay_heat = burnup.compute_decay_heat()`.
2. Standalone: `calculator = DecayHeatCalculator()`; `heat = calculator.compute(inventory_dict, time_seconds)`.

### Required Data

- Dictionary of nuclide → atom counts.
- Cooling time (seconds).

### Outputs

- Decay heat (W).

---

## 6. Preset Reactor Designs

| Item | Details |
|------|---------|
| **Module** | `smrforge.create_reactor`, `smrforge.list_presets`, `smrforge.get_preset` |
| **Required data** | None (presets are built-in) |

### Workflow

1. List: `presets = smr.list_presets()`.
2. Create: `reactor = smr.create_reactor("valar-10")` or `smr.create_reactor("gt-mhr-350")`.
3. Solve: `k_eff = reactor.solve_keff()` or `results = reactor.solve()`.

### Presets

- `valar-10`, `gt-mhr-350`, `htr-pm-200`, `micro-htgr-1`, LWR SMR designs.

### Outputs

- Reactor instance with geometry, specs, solve methods.

---

## 7. Validation & Safety Margins

| Item | Details |
|------|---------|
| **Module** | `smrforge.validation.safety_report`, `smrforge.validation.constraints` |
| **Required data** | Reactor, optional analysis results, constraint set (JSON or preset) |

### Workflow

1. Create reactor and optionally run `reactor.solve()`.
2. Load or build `ConstraintSet`.
3. Run: `report = safety_margin_report(reactor, constraint_set=cs, analysis_results=...)`.
4. Inspect: `report.margins`, `report.violations`, `report.to_text()`.

### Required Data

- Reactor instance.
- Constraint set: limits for k_eff, power, temperatures, etc. (JSON or `ConstraintSet.get_regulatory_limits()`).

### Outputs

- `SafetyMarginReport`: margins, violations, pass/fail.

---

## 8. Parameter Sweep

| Item | Details |
|------|---------|
| **Module** | `smrforge.workflows.parameter_sweep.ParameterSweep` |
| **Required data** | Sweep config (parameters, bounds, reactor template) |

### Workflow

1. Define `ParameterSweepConfig(parameters={...}, reactor_template=...)`.
2. Create `ParameterSweep(config)`.
3. Run: `result = sweep.run(resume=False, show_progress=True)`.
4. Use: `result.results`, `result.summary_stats`.

### Required Data

- Parameter names and bounds (or discrete values).
- Reactor template (preset name, path to JSON, or dict).

### Outputs

- `SweepResult`: list of result dicts, failed cases, summary stats.

---

## 9. Visualization

| Item | Details |
|------|---------|
| **Modules** | `smrforge.quick_plot_core`, `quick_plot_mesh`, Plotly/PyVista exporters |
| **Required data** | Core or mesh object |

### Workflow

1. Create core or extract mesh: `mesh = quick_mesh_extraction(core, mesh_type="volume")`.
2. Plot: `quick_plot_core(core, view="xy")` or `quick_plot_mesh(mesh, color_by="material")`.

### Optional Dependencies

- `plotly`, `pyvista` for 3D (install with `pip install smrforge[viz]`).

### Outputs

- HTML/PNG plots, interactive 3D viewers.

---

## 10. Convenience API

| Item | Details |
|------|---------|
| **Module** | `smrforge` top-level |
| **Functions** | `quick_keff()`, `create_simple_core()`, `create_simple_solver()`, `get_nuclide()`, etc. |

### Workflow

- Use high-level functions for rapid prototyping; see `smr.help("convenience")`.

### Required Data

- Depends on function (e.g., `quick_keff(power_mw=10, enrichment=0.195)` needs no geometry).

### Outputs

- Varies (k_eff, core, solver, etc.).
