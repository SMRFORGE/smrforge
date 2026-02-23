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

## Stable Public API

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

### Workflows

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge.workflows.parameter_sweep.ParameterSweep` | Parameter sweep |
| `smrforge.workflows.fit_surrogate()` | Fit surrogate model (Pro: full; Community: stub) |
| `smrforge.workflows.register_surrogate()` | Register custom surrogate (Pro: full; Community: stub) |
| `smrforge.workflows.register_hook()` | Register event hooks |
| `smrforge.workflows.run_hooks()` | Run registered hooks |
| `smrforge.workflows.export_ml_dataset()` | Export design points to Parquet/HDF5 for ML (Pro: full; Community: stub) |

### Stable API Facade

| Import | Purpose |
|--------|---------|
| `from smrforge.api import fit_surrogate, register_surrogate, ...` | Single import for stable symbols |

### Plugin Registry

| Symbol | Purpose |
|--------|---------|
| `register_surrogate(name, factory)` | Register surrogate factory |
| `get_surrogate(name)` | Get surrogate factory |
| `list_surrogates()` | List registered surrogates |
| `register_hook(name, callback)` | Register hook callback |
| `run_hooks(name, context, **kwargs)` | Run hooks |

## Deprecation Policy

1. **Deprecation notice:** Deprecated symbols will log a `DeprecationWarning` when used, and will be documented in release notes.
2. **Deprecation period:** At least one minor version (e.g., 0.6 → 0.7) before removal.
3. **Replacement:** When deprecating, a replacement API will be provided and documented.
4. **Breaking changes:** Reserved for major version bumps (e.g., 1.0 → 2.0).

## Internal / Unstable

- `smrforge.cli` — CLI entry points; schema may change with CLI evolution.
- `smrforge.gui` — Web app; internal structure may change.
- Private attributes (leading underscore) and modules not listed above — no stability guarantee.
- Pydantic model internals — `model_dump()`, `model_validate()` are stable; internal fields may evolve.

## Versioning

- **Semantic versioning:** MAJOR.MINOR.PATCH
- **MAJOR:** Breaking changes to stable API
- **MINOR:** New features, backward-compatible
- **PATCH:** Bug fixes, no API changes

## References

- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
- docs/PLUGIN_ARCHITECTURE.md
