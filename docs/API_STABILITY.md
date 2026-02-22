# SMRForge API Stability Policy

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
| `smrforge.convenience.run_reactor()` | High-level reactor run |
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
| `smrforge.workflows.parameter_sweep.SweepConfig` | Sweep config (surrogate_path, seed, etc.) |
| `smrforge.workflows.fit_surrogate()` | Fit surrogate model (supports audit_trail) |
| `smrforge.workflows.surrogate_from_sweep_results()` | Build surrogate from sweep results |
| `smrforge.workflows.register_surrogate()` | Register custom surrogate (factory or path) |
| `smrforge.workflows.register_hook()` | Register event hooks |
| `smrforge.workflows.run_hooks()` | Run registered hooks |
| `smrforge.workflows.export_ml_dataset()` | Export design points to Parquet/HDF5 for ML |

### AI and Surrogates

| Module / Symbol | Purpose |
|-----------------|---------|
| `smrforge.ai.audit.record_ai_model()` | Append AI model to audit trail |
| `smrforge.ai.surrogate.load_surrogate_from_path()` | Load ONNX/TorchScript/pickle surrogate |
| `smrforge.ai.surrogate.register_surrogate_from_path()` | Register surrogate from file path |
| `smrforge.ai.surrogate.model_hash()` | SHA-256 hash for model audit |
| `smrforge.ai.validation.generate_validation_report()` | Compare surrogate vs reference |
| `smrforge.ai.validation.SurrogateValidationReport` | Validation report dataclass |

### Stable API Facade

| Import | Purpose |
|--------|---------|
| `from smrforge.api import fit_surrogate, register_surrogate, load_surrogate_from_path, ...` | Single import for stable symbols |

### Plugin Registry

| Symbol | Purpose |
|--------|---------|
| `register_surrogate(name, factory)` | Register surrogate factory or path |
| `register_surrogate(name, path, metadata)` | Register BYOS from file path |
| `get_surrogate(name)` | Get surrogate factory |
| `get_surrogate_metadata(name)` | Get metadata for registered surrogate |
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

- AI_FEATURES.md
- PLUGIN_ARCHITECTURE.md
- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md (SMRForge-Private)
