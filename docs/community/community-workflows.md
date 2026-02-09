# Community Tier — Workflow Guide

Step-by-step workflows with required inputs and outputs.

---

## Workflow 1: Quick k-eff (No ENDF)

**Goal:** Compute k-effective in seconds using built-in synthetic cross-sections.

**Required data:** None.

**Steps:**

```python
import smrforge as smr

k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)
print(f"k_eff: {k_eff:.6f}")
```

**Output:** Scalar k_eff.

---

## Workflow 2: Preset Reactor Analysis

**Goal:** Analyze a preset design (e.g., Valar-10) with full solve.

**Required data:** None.

**Steps:**

```python
import smrforge as smr

reactor = smr.create_reactor("valar-10")
results = reactor.solve()
print(f"k_eff: {results['k_eff']:.6f}")
print(f"Peak flux: {results.get('peak_flux', 'N/A')}")
```

**Output:** Dict with k_eff, peak_flux, power, etc.

---

## Workflow 3: Custom Neutronics with Synthetic XS

**Goal:** Run multi-group diffusion on custom geometry with hand-crafted cross-sections.

**Required data:** Geometry dimensions, mesh counts, 2-group (or N-group) XS arrays.

**Steps:**

1. Define geometry (e.g., cylindrical with fuel/reflector).
2. Build `CrossSectionData` with sigma_t, sigma_a, sigma_f, nu_sigma_f, sigma_s, chi, D.
3. Create `MultiGroupDiffusion(geometry, xs_data, options)`.
4. Solve: `k_eff, flux = solver.solve_steady_state()`.

**Output:** k_eff, flux array, optional power distribution.

---

## Workflow 4: ENDF-Based Cross-Sections

**Goal:** Fetch real cross-sections from ENDF files.

**Required data:**
- ENDF directory (e.g., from `data_downloader.download_endf_data()` or manual).
- Nuclide (e.g., U235), reaction (e.g., "fission", "capture"), temperature (K).

**Steps:**

1. Set `SMRFORGE_ENDF_DIR` or create `NuclearDataCache(local_endf_dir=Path(...))`.
2. Create `Nuclide(Z=92, A=235)` or use `get_nuclide("U235")`.
3. Call `cache.get_cross_section(nuclide, "fission", temperature=293.6)`.
4. Use returned (energy, xs) in multi-group generation or solver.

**Output:** Energy array (eV), cross-section array (b).

---

## Workflow 5: Burnup Calculation

**Goal:** Track nuclide inventory over irradiation time.

**Required data:**
- Neutronics solver (from Workflow 2 or 3).
- Time steps (days), power density (W/cm³), initial enrichment.

**Steps:**

1. Create neutronics solver and solve initial k_eff.
2. Create `BurnupOptions(time_steps=[0, 30, 60, 90, 365], power_density=1e6, initial_enrichment=0.195)`.
3. Create `BurnupSolver(neutronics, options)`.
4. Run `inventory = burnup.solve()`.
5. Query concentrations, burnup, decay heat.

**Output:** `NuclideInventory` with concentrations vs time, burnup (MWd/kgU).

---

## Workflow 6: Design Point & Safety Margins

**Goal:** Get design point and safety margin report for a reactor.

**Required data:** Reactor instance, optional constraint set (JSON or preset).

**Steps:**

1. Create reactor: `reactor = smr.create_reactor("valar-10")`.
2. Get design point: `point = smr.get_design_point(reactor)`.
3. Run safety report: `report = safety_margin_report(reactor, constraint_set=...)`.
4. Inspect margins and violations.

**Output:** Design point dict, `SafetyMarginReport`.

---

## Workflow 7: Parameter Sweep

**Goal:** Run many design points over parameter space.

**Required data:** Parameter names, bounds or values, reactor template.

**Steps:**

1. Define `ParameterSweepConfig(parameters={"enrichment": [0.17, 0.19, 0.21], "power_mw": [5, 10, 15]}, reactor_template="valar-10")`.
2. Create `ParameterSweep(config)`.
3. Run `result = sweep.run(show_progress=True)`.
4. Post-process `result.results` for Pareto, sensitivity, etc.

**Output:** `SweepResult` with results list and summary stats.

---

## Workflow 8: Decay Heat

**Goal:** Compute decay heat from a nuclide inventory.

**Required data:** Nuclide concentrations (atoms) and cooling time (s).

**Steps:**

1. From burnup: `heat = burnup.compute_decay_heat()`.
2. Standalone: `DecayHeatCalculator().compute({"U235": 1e20, "Cs137": 1e19}, time_seconds=86400)`.

**Output:** Decay heat (W).

---

## Workflow 9: 3D Mesh & Visualization

**Goal:** Extract 3D mesh and visualize core.

**Required data:** Core geometry.

**Steps:**

1. Create core: `core = smr.create_simple_core()` or preset reactor core.
2. Extract mesh: `mesh = smr.quick_mesh_extraction(core, mesh_type="volume")`.
3. Plot: `smr.quick_plot_mesh(mesh, color_by="material")` or `quick_plot_core(core)`.

**Optional:** `pip install smrforge[viz]` for Plotly/PyVista.

**Output:** Mesh object, HTML/PNG plot.

---

## Data Requirements Summary

| Workflow | ENDF | Geometry | Other |
|----------|------|----------|-------|
| Quick k-eff | No | No | — |
| Preset analysis | No | Built-in | — |
| Custom neutronics (synthetic) | No | Yes | XS arrays |
| ENDF XS | Yes | Optional | Nuclide, reaction |
| Burnup | Optional | Yes | Time steps, power |
| Design point | No | Yes | Reactor |
| Parameter sweep | No | Template | Parameter bounds |
| Decay heat | No | No | Inventory |
| 3D mesh | No | Yes | Core |
