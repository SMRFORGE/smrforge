# SMRForge: Nuclear Industry Analysis and AI Future-Proofing

**Document purpose:** Identify coding issues that could impact nuclear-industry customers and recommend actions to future-proof the software for AI integration. Aligned with Path C business plan and NQA-1 regulatory path.

**Confidential | Internal planning | February 2026**

---

## Executive Summary

This analysis identifies **16 coding issues** in categories: determinism/reproducibility, error handling, physics fallbacks, security, validation, and traceability. It also provides **8 recommendations** for AI future-proofing. Priority actions include replacing `eval()` usage, fixing non-deterministic optimization paths, improving physics fallbacks, and adding API extensibility for AI integration.

---

## Quick Checklist: What to Fix

| # | Item | Status | Location / Notes |
|---|------|--------|------------------|
| 1 | Replace `eval()` on user input | Done | cli.py → `_parse_heat_source_safe()` |
| 2 | Add seeds to optimization & fuel management | Done | design.py, smr_fuel_management.py |
| 3 | Replace `np.random.seed()` with `default_rng()` | Done | monte_carlo_optimized.py |
| 4 | Log physics fallbacks (elastic, TSL) | Done | endf_extractors.py |
| 5 | Document flux-weighting limitation | Done | docs/FLUX_WEIGHTING_LIMITATION.md |
| 6 | Version-lock requirements | Done | requirements-lock.txt, docs |
| 7 | Tighten exception handling (reraise system exceptions) | Done | burnup, reactor_core; utils/exception_handling.py |
| 8 | Auto-attach CalculationAuditTrail | Done | solve_steady_state(), BurnupSolver.solve() |
| 9 | Plugin/hook architecture | Done | workflows/plugin_registry.py |
| 10 | API stability document | Done | docs/API_STABILITY.md |
| 11 | Centralize NaN/Inf validation | Done | validation/numerical_validation.py |
| 12 | Audit log append failure | Done | audit_log.py: log WARNING, return bool |
| 13 | Apply `reraise_if_system` in parameter_sweep, atlas | Done | parameter_sweep.py, atlas.py |
| 14 | Wire `validate_safety_critical_outputs` at solver boundaries | Done | neutronics, burnup, thermal/lumped |
| 15 | Implement flux-weighting (or keep documented) | Done | endf_extractors: _collapse_to_multigroup_flux_weighted, 1/E default |
| 16 | Pydantic result models (KeffResult, etc.) | Done | pydantic_layer: KeffResult, BurnupResultSummary |
| 17 | AI audit: extend CalculationAuditTrail with ai_models_used | Done | regulatory_traceability.py; smrforge.ai.audit.record_ai_model |
| 18 | REST API, ML export, AI audit trail | Future | SaaS Pro / Enterprise roadmap |

---

## Part 1: Coding Issues for Nuclear Industry Customers

### 1.1 Critical: Security and Arbitrary Code Execution

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **`eval()` on user input** | `cli.py` ~5359 | Arbitrary code execution if config is from untrusted source | Config files (e.g., thermal lump `heat_source`) could be compromised; NRC 10 CFR 21 implications if malicious config is distributed. |

**Recommendation:** Replace `eval(heat_source_str)` with a safe expression parser (e.g., `ast.literal_eval` for literals, or a restricted DSL for `lambda t: ...` expressions). Never evaluate user-controlled strings as Python.

---

### 1.2 Critical: Reproducibility and Determinism

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **Global `np.random.seed()`** | `monte_carlo_optimized.py` ~464 | Breaks in parallel runs; affects other threads/processes | Monte Carlo runs may not be reproducible across workers; unacceptable for licensing and V&V. |
| **Optimization without seed** | `design.py`, `advanced_optimization.py`, `smr_fuel_management.py` | Genetic algorithm, PSO, fuel management use `np.random` without `seed` parameter | Results vary run-to-run; cannot reproduce optimization or fuel-loading studies. |
| **Fuel management random batch** | `smr_fuel_management.py` ~235 | `assembly.batch = np.random.choice([1, 2])` | Refueling logic non-deterministic; cannot audit or replicate. |

**Recommendation:**
- Use `np.random.default_rng(seed)` and pass the RNG through functions; avoid global `np.random.seed()`.
- Add `seed` parameter to all optimization classes (`DesignOptimizer`, `LoadingPatternOptimizer`, `advanced_optimization`, etc.) and pass RNG consistently.
- For fuel management, use deterministic assignment or explicit seed.

---

### 1.3 High: Silent Fallbacks and Physics Accuracy

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **Fallback to 5 barns elastic** | `endf_extractors.py` ~326–328 | On any `Exception`, elastic cross-section defaults to 5 barns with no warning | Incorrect physics for licensing; NQA-1 / dedication would require documented fallbacks and clear user notification. |
| **TSL fallback silently passed** | `endf_extractors.py` ~338 | `except Exception: pass` — thermal scattering data failure ignored | User unaware thermal scattering may be wrong; affects accuracy in thermal spectrum. |
| **TODO: flux-weighting** | `endf_extractors.py` ~321 | Multi-group collapse uses simple average instead of flux-weighting | Known accuracy gap; should be documented and flagged in regulatory traceability. |

**Recommendation:**
- On fallback: log at WARNING or ERROR, and optionally add a flag to results (e.g., `used_fallback: true`) for audit.
- Document all fallbacks in model assumptions (regulatory traceability).
- Implement proper flux-weighting or mark as known limitation with impact assessment.

---

### 1.4 High: Broad Exception Handling

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **`except Exception` without re-raise** | `reactor_core.py`, `burnup/solver.py`, `parameter_sweep.py`, `atlas.py` | Masks bugs (e.g., `KeyboardInterrupt`, `MemoryError`); can hide numerical errors | Silent failures in physics; difficult to debug and audit. |
| **Audit log append failure** | `audit_log.py` ~76 | `except Exception: logger.debug(...)` — audit trail can fail silently | Loss of run history; problem for regulatory and NQA-1 records. |

**Recommendation:**
- Catch specific exceptions where possible; avoid bare `except Exception` for core physics.
- For audit log: at minimum log at WARNING and consider raising or returning failure status so callers know the audit record was not written.

---

### 1.5 Medium: NaN/Inf Handling

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **Inconsistent NaN checks** | `solver.py`, `reactor_core.py`, `data_validation.py`, `integration.py`, `pydantic_layer.py` | Some paths check NaN/Inf, others do not | Propagation of invalid values can invalidate safety margins; BEPU workflows need consistent validation. |

**Recommendation:** Centralize NaN/Inf validation for safety-critical outputs (k_eff, power, flux). Use `validation.integration` patterns and ensure they are applied before results are written or used in margins.

**Pydantic and validation consistency:** Pydantic can strengthen validation (see `docs/development/pydantic-integration-guide.md`). Inputs (ReactorSpecification, CrossSectionData, SolverOptions) already use Pydantic with `PositiveArray` (NaN/Inf rejection). Outputs currently use tuples, dicts, or dataclasses (NuclideInventory, SweepResult, etc.) with no Pydantic validation at the boundary. The project uses multiple validation paths: DataValidator, numerical_validation, and Pydantic—only for inputs. A unified approach would introduce Pydantic result models (e.g., KeffResult, BurnupResult) for solver outputs, but that would require refactoring. For now, use `numerical_validation.validate_safety_critical_outputs()` at key boundaries; consider Pydantic result models as a phased enhancement for new APIs.

---

### 1.6 Medium: Dependency and Version Reproducibility

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **Unpinned versions** | `requirements.txt` | `numpy>=1.20.0` etc. — different environments yield different numerical results | Reproducibility demands pinned versions; NQA-1 dedication requires controlled environment. |

**Recommendation:** Produce a `requirements-lock.txt` or similar with exact versions for releases. Document in V&V plan which versions were validated.

---

### 1.7 Lower: Traceability and API Design

| Issue | Location | Risk | Nuclear Impact |
|-------|----------|------|----------------|
| **Calculation audit trail opt-in** | `regulatory_traceability.py` | `CalculationAuditTrail` exists but may not be auto-invoked everywhere | Regulatory submittals need end-to-end traceability for key calculations. |
| **API stability** | General | No formal deprecation policy in Community repo | Pro has `api.py` / `deprecated()`; Community should document stability for integration partners. |

**Recommendation:** Ensure audit trails are automatically attached to k_eff, burnup, transient, and margin calculations. Add `API_STABILITY.md` to Community repo documenting public API and deprecation policy.

---

## Part 2: Business Path Considerations

### 2.1 Alignment with Path C

- **Pro launch (M6):** Serpent/OpenMC/MCNP export, benchmarks, report generator — these are the features labs and vendors pay for. Ensuring reproducibility and safe error handling supports credibility.
- **Enterprise (M10–15):** System TH, BEPU, NQA-1 path — requires:
  - Documented fallbacks and assumptions
  - Reproducible runs (seeds, versions)
  - Robust audit logging
- **SaaS (M4–12):** Cloud runs need deterministic results; same config must yield same output across workers.

### 2.2 Competitive and Regulatory Context

- **Studsvik, ARMI:** Enterprise nuclear vendors emphasize reproducibility, V&V, and traceability.
- **NQA-1 / Regulatory Guide 1.231:** Commercial-grade software dedication requires configuration control, error handling, and documentation of limitations.
- **10 CFR Part 21:** Defects and noncompliance must be reportable; silent failures and arbitrary `eval()` increase liability.

---

## Part 3: AI Future-Proofing

### 3.1 Industry Trends (2024–2025)

- **ARTISANS, NCSU:** AI for nuclear system simulation and engineering workflows.
- **Digital twins:** AI/ML for predictive maintenance, monitoring, and near-real-time simulation (Princeton–NVIDIA, DOE fusion goals).
- **Surrogate models:** ML surrogates for expensive Monte Carlo / CFD (SMRForge already has `surrogate.py` with scikit-learn).
- **Automation:** AI-assisted design exploration, constraint handling, and report generation.

### 3.2 Recommendations for AI Readiness

| # | Recommendation | Rationale | Status |
|---|----------------|----------|--------|
| 1 | **Stable, versioned API** | AI agents and automation need a consistent interface; document public API and deprecation policy. | ✅ docs/API_STABILITY.md; smrforge.api.stable |
| 2 | **Plugin / hook architecture** | Allow AI/ML models to plug in as solvers, surrogates, or post-processors without modifying core. | ✅ plugin_registry.py; fit_surrogate uses registry |
| 3 | **REST API (SaaS Pro)** | Machine-to-machine access for AI pipelines; Path C already plans REST API in SaaS Pro. | Future |
| 4 | **Structured inputs/outputs** | JSON schemas for reactor config and results; enables LLM/AI tool use and automated workflows. | ✅ Pydantic models (model_dump); reactor.json |
| 5 | **Surrogate interface abstraction** | `surrogate.py` exists; abstract it so different backends (sklearn, custom NN, external service) can be swapped. | ✅ register_surrogate + fit_surrogate |
| 6 | **Audit trail for AI-assisted runs** | Record which models/versions and prompts (if LLM) were used; needed for regulatory and reproducibility. | ✅ CalculationAuditTrail.ai_models_used; smrforge.ai.audit.record_ai_model |
| 7 | **Deterministic mode** | Guarantee reproducibility when seed is set; required for AI training and validation. | ✅ seeds in optimization, fuel mgmt; default_rng |
| 8 | **Data export for ML** | Export design points, parameters, and results in ML-friendly formats (e.g., Parquet, HDF5 with clear schema) for training pipelines. | ✅ export_ml_dataset (workflows/ml_export.py) |

### 3.3 Suggested Architecture Additions

```
smrforge/
  workflows/
    surrogate.py        # Abstract backend; uses plugin registry
    ml_export.py        # export_ml_dataset (Parquet/HDF5)
  ai/
    __init__.py         # AI integration namespace
    audit.py            # record_ai_model() for audit trails
  api/
    stable.py           # Public API surface; versioned
```

- **Plugin registry:** Allow `register_surrogate(name, factory)` so Pro/Enterprise or third parties can add ML models without forking. ✅ *Done: fit_surrogate() checks registry first; use method="custom_name" after register_surrogate().*
- **AI audit:** Extend `CalculationAuditTrail` with `ai_models_used: List[Dict]` (model name, version, config hash). ✅ *Done: ai_models_used field; record_ai_model() in smrforge.ai.audit.*

---

## Part 4: Priority Action List

### Immediate (Pre–Pro Launch)

1. **Replace `eval()` in cli.py** — Security. ✅ *Done: `_parse_heat_source_safe()` uses `ast.literal_eval`.*
2. **Add `seed` to optimization and fuel management** — Reproducibility. ✅ *Done: `DesignOptimizer`, `LoadingPatternOptimizer`, `SMRFuelManager.refuel_smr`.*
3. **Replace `np.random.seed()` with `default_rng(seed)`** in Monte Carlo — Reproducibility. ✅ *Done: `monte_carlo_optimized` uses `self._rng`; seed set at run start for Numba.*
4. **Log fallbacks in endf_extractors** — Transparency. ✅ *Done: WARNING logs for elastic 5-barn and TSL fallbacks.*

### Short-Term (Pro Launch – M6)

5. **Document flux-weighting TODO and impact** — Regulatory traceability. ✅ *Done: docs/FLUX_WEIGHTING_LIMITATION.md; endf_extractors comment.*
6. **Produce version-locked requirements** — Reproducibility. ✅ *Done: docs/VERSION_LOCK_REQUIREMENTS.md, requirements-lock.txt.*
7. **Tighten exception handling** in burnup, reactor_core — Reduce silent failures. ✅ *Done: reraise_if_system() in utils/exception_handling.py; applied to burnup, reactor_core.*
8. **Auto-attach CalculationAuditTrail** to safety-critical workflows — Traceability. ✅ *Done: audit_trail_path param on solve_steady_state(), BurnupSolver.solve().*

### Medium-Term (Enterprise Path)

9. **Implement plugin/hook architecture** — AI extensibility. ✅ *Done: smrforge/workflows/plugin_registry.py, docs/PLUGIN_ARCHITECTURE.md.*
10. **API stability document** — Integration readiness. ✅ *Done: docs/API_STABILITY.md.*
11. **Centralize NaN/Inf validation** — BEPU readiness. ✅ *Done: smrforge/validation/numerical_validation.py (validate_k_eff, validate_flux, validate_power, validate_safety_critical_outputs).*

---

## References

- NRC Regulatory Guide 1.231 (commercial-grade computer programs)
- ASME NQA-1:2024 (process and software)
- SMRForge Path C Business Plan (SMRForge-Private)
- SAFETY_CRITICAL_MODULES.md
- ARTISANS (AI for nuclear simulation), PMDT (predictive maintenance digital twins)
- docs/development/pydantic-integration-guide.md
- docs/FLUX_WEIGHTING_LIMITATION.md
- docs/VERSION_LOCK_REQUIREMENTS.md
- docs/PLUGIN_ARCHITECTURE.md
- docs/API_STABILITY.md
