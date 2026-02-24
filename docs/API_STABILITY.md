# SMRForge API Stability Policy

**Last Updated:** February 2026  
**Purpose:** Document public API surface and deprecation policy for integration partners and AI/automation.  
**Reference:** NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 1.7

---

## Scope

This document describes which parts of SMRForge are considered **stable** for external use and how we handle deprecations and breaking changes.

## Stability Levels

| Level | Description | Commitment |
|-------|-------------|------------|
| **Stable** | Public API; backward-compatible within major version | Deprecation period before removal |
| **Provisional** | May change based on feedback; not yet frozen | Best-effort compatibility |
| **Internal** | Not part of public API; may change without notice | No commitment |

---

## Tier 1: Stable Public API

### Core Entry Points

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge.convenience.create_reactor()` | Create reactor from preset or kwargs |
| `smrforge.convenience.quick_keff()` | One-liner k-eff analysis |
| `smrforge.neutronics.solver.MultiGroupDiffusion` | Multi-group diffusion solver |
| `MultiGroupDiffusion.solve_steady_state(audit_trail_path=...)` | k-eff and flux |
| `smrforge.burnup.solver.BurnupSolver` | Coupled neutronics-burnup |
| `BurnupSolver.solve(audit_trail_path=...)` | Burnup solution |
| `smrforge.validation.models.ReactorSpecification` | Reactor input model |
| `smrforge.validation.models.CrossSectionData` | Cross-section input model |
| `smrforge.validation.models.SolverOptions` | Solver options model |

### Validation and Traceability

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge.validation.regulatory_traceability.CalculationAuditTrail` | Audit trail dataclass |
| `smrforge.validation.regulatory_traceability.create_audit_trail()` | Create audit trail |
| `smrforge.validation.regulatory_traceability.SafetyMarginReport` | Safety margin report |
| `CalculationAuditTrail.save(path)` | Save to JSON |
| `CalculationAuditTrail.load(path)` | Load from JSON |

### Workflows (Stable)

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge.workflows.parameter_sweep.ParameterSweep` | Parameter sweep |
| `smrforge.workflows.register_hook()` | Register event hooks |
| `smrforge.workflows.run_hooks()` | Run registered hooks |

### Stable API Facade

| Import | Purpose |
|--------|---------|
| `from smrforge.api import ...` | Single import for stable symbols |

### Plugin Registry (Stable)

| Symbol | Purpose |
|--------|---------|
| `register_hook(name, callback)` | Register hook callback |
| `run_hooks(name, context, **kwargs)` | Run hooks |

### Dependencies (Stable)

| Package | Role | Commitment |
|---------|------|------------|
| numpy, scipy | Numerical core | Pinned in requirements-lock.txt for releases |
| pydantic, pydantic-settings | Validation, schemas | Version-locked for reproducibility |
| h5py, zarr | Data I/O | Stable within major version |
| pandas, polars | Data processing | Best-effort compatibility |

---

## Tier 2: Provisional (Best-Effort)

Symbols in this tier are part of the public surface but may evolve based on feedback. Use with awareness that signatures or behavior may change.

### Workflows (Provisional)

| Module / Symbol | Purpose | Note |
|-----------------|---------|------|
| `smrforge.workflows.fit_surrogate()` | Fit surrogate model | Pro: full; Community: stub |
| `smrforge.workflows.register_surrogate()` | Register custom surrogate | Pro: full; Community: stub |
| `smrforge.workflows.export_ml_dataset()` | Export design points to Parquet/HDF5 | Pro: full; Community: stub |

### Plugin Registry (Provisional)

| Symbol | Purpose |
|--------|---------|
| `register_surrogate(name, factory)` | Register surrogate factory |
| `get_surrogate(name)` | Get surrogate factory |
| `list_surrogates()` | List registered surrogates |

### Dependencies (Provisional)

| Package | Role | Note |
|---------|------|------|
| plotly, pyvista, dash | Visualization, dashboard | May add/remove optional backends |
| scikit-learn, SALib, seaborn | ML, UQ, sensitivity | Optional extras; API may evolve |
| requests, httpx, tqdm, pyyaml | Data download, config | Fallback paths when unavailable |

---

## Tier 3: Internal / Unstable

- `smrforge.cli` — CLI entry points; schema may change with CLI evolution.
- `smrforge.gui` — Web app; internal structure may change.
- Private attributes (leading underscore) and modules not listed above — no stability guarantee.
- Pydantic model internals — `model_dump()`, `model_validate()` are stable; internal fields may evolve.

### Dependencies (Internal)

| Package | Role | Note |
|---------|------|------|
| pytest, black, isort, mypy, flake8 | Development, testing, linting | requirements-dev.txt only |
| numba | JIT optimization | Internal; version affects performance |

---

## Deprecation Policy

1. **Deprecation notice:** Deprecated symbols will log a `DeprecationWarning` when used, and will be documented in release notes.
2. **Deprecation period:** At least one minor version (e.g., 0.6 → 0.7) before removal.
3. **Replacement:** When deprecating, a replacement API will be provided and documented.
4. **Breaking changes:** Reserved for major version bumps (e.g., 1.0 → 2.0).

## Versioning

- **Semantic versioning:** MAJOR.MINOR.PATCH
- **MAJOR:** Breaking changes to stable API
- **MINOR:** New features, backward-compatible
- **PATCH:** Bug fixes, no API changes

## SMRForge Pro (Licensed Tier)

Pro extends Community with additional symbols and optional extras. Same stability levels apply; Pro-specific APIs follow the deprecation policy above.

### Pro Stable Symbols

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge_pro.converters.OpenMCConverter` | OpenMC export/import (delegates to Community; Pro adds tally viz docs) |
| `smrforge_pro.converters.SerpentConverter` | Serpent export/import (export full; import basic) |
| `smrforge_pro.converters.MCNPConverter` | MCNP export (full) |
| `smrforge_pro.visualization.visualize_openmc_tallies` | OpenMC mesh tally visualization |
| `smrforge_pro.workflows.fit_surrogate` | Fit RBF/linear surrogate |
| `smrforge_pro.workflows.surrogate_from_sweep_results` | Fit surrogate from sweep JSON |
| `smrforge_pro.workflows.export_ml_dataset` | Export to Parquet/HDF5 |
| `smrforge_pro.ai.validation_report.SurrogateValidationReport` | Surrogate validation report |
| `smrforge_pro.ai.validation_report.generate_validation_report` | Compare pred vs reference |
| `smrforge_pro.ai.audit.record_ai_model` | Record AI model in audit trail |

### Pro Optional Extras

| Extra | Packages | Purpose |
|-------|----------|---------|
| `[ai]` | onnxruntime, torch | ONNX/TorchScript surrogate loading |
| `[reporting]` | reportlab | PDF export for validation reports |
| `[ml]` | pyarrow, tables | Parquet, HDF5 for ML export |
| `[all]` | All above | Full Pro feature set |

### Pro–Community Compatibility

- **Version pinning:** Pro version X.Y is tested with Community version ≥ X.Y (same major). Document validated combinations in release notes.
- **Import path:** Pro features are reached via `smrforge.api` when Pro is installed; `smrforge_pro` is a direct import for Pro-only code.

## Air-Gapped Deployment

For environments without internet access, use the strategy in **[Air-Gapped Deployment Guide](guides/air-gapped-deployment.md)**. Summary:

- **Python packages:** Use `requirements-lock.txt` with `pip download` + `pip install --no-index`.
- **Nuclear data (ENDF):** Pre-stage to local directory; SMRForge uses built-in parser (no network).
- **Reproducibility:** Pin versions; document validated environment in V&V plan.
- **Pro:** See `docs/guides/air-gapped-deployment.md` for Pro pip download and install.

## References

- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
- docs/PLUGIN_ARCHITECTURE.md
- docs/guides/air-gapped-deployment.md
- docs/community_vs_pro.md
