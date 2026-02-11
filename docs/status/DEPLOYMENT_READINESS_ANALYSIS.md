# SMRForge Deployment Readiness Analysis

**Purpose:** Identify software issues that would prevent reliable deployment of Community Tier and SMRForge-Pro tier, with emphasis on reliability and accuracy.

**Assessment Date:** February 2026

---

## Executive Summary

The codebase has addressed most critical items from the Nuclear Industry Analysis. **Community Tier** is largely ready for Beta release, with a few blocking metadata/config issues and one remaining physics fallback that should log. **SMRForge-Pro** depends on Community and requires RSA licensing, Pro docs, and pre-sync validation before deployment. Key findings:

- **Tests:** Core solver, validation, burnup, and assembly tests pass.
- **Pre-sync check:** PASSES (no Pro leakage in Community).
- **Security:** `eval()` replaced with `ast.literal_eval` in heat-source parsing.
- **Validation:** `validate_safety_critical_outputs` wired at neutronics, burnup, and thermal solver boundaries.
- **Physics:** Flux-weighting implemented; one elastic fallback path still lacks logging.

---

## 1. Community Tier Deployment Blockers

### 1.1 PyPI Metadata (BLOCKER)

| Issue | Location | Action |
|-------|----------|--------|
| `author_email="your.email@example.com"` | `setup.py` line 26 | Replace with real contact email. Required for PyPI. |
| Contact/citation section in README | `README.md` | Ensure accurate contact info per checklist 1.2. |

**Impact:** PyPI will accept the package, but the placeholder email is unprofessional and may trigger moderation.

---

### 1.2 Pre-Deploy Verification (RECOMMENDED)

| Task | Status | Notes |
|------|--------|-------|
| Run `pre_sync_check.py` before every Community sync | ✅ Script exists | Run: `python scripts/pre_sync_check.py` |
| Test build: `python -m build` | ⬜ | Verify before PyPI upload |
| TestPyPI upload before main PyPI | ⬜ | Catch metadata/install issues |
| Manual smoke test (CLI, dashboard, example) | ⬜ | Per checklist 5.4 |

---

## 2. Pro Tier Deployment Blockers

### 2.1 Prerequisites

- **Community checklist must be complete first.** Pro extends Community.
- **Package separation:** `pre_sync_check.py` validates; currently PASSES.

### 2.2 Pro-Specific Gaps

| Gap | Status | Notes |
|-----|--------|-------|
| RSA license validation | ⬜ | Required for Pro distribution |
| Pro docs hosted | ⬜ | Private or restricted |
| API stability policy for Pro | ⬜ | Semver, deprecation |
| Support/contact process for Pro users | ⬜ | Per checklist 4.3 |

### 2.3 Pro/Community Separation

- `converters.py` uses try/except for `smrforge_pro` delegation — correct pattern.
- Whitelist in `pre_sync_check.py`: `smrforge/io/converters.py` — validated.

---

## 3. Reliability Issues

### 3.1 Physics Fallbacks Without Logging (MEDIUM)

| Location | Issue | Risk |
|----------|-------|------|
| `endf_extractors.py` ~623–632 | In `compute_anisotropic_scattering_matrix`, when `elastic_mg` is recomputed for P1 moment and `cache.get_cross_section` or `_collapse_to_multigroup_flux_weighted` fails, falls back to 5 barns **with no logger.warning** | User unaware of incorrect physics; regulatory traceability gap |

**Note:** The main path in `compute_improved_scattering_matrix` (lines 400–410) **does** log the elastic fallback. This is a second code path in the anisotropic scattering function that bypasses `compute_improved_scattering_matrix` for the P1 computation and lacks logging.

**Recommendation:** Add `logger.warning(...)` before `elastic_mg = np.ones(n_groups) * 5.0` in the anisotropic scattering block, matching the pattern in `compute_improved_scattering_matrix`.

---

### 3.2 Silent Fallbacks (LOW)

| Location | Issue |
|----------|-------|
| `endf_extractors.py` ~619 | `except Exception: pass` for MF6 energy-angle parser — fallback to simplified models; acceptable but could add debug log |
| `endf_extractors.py` ~323 | Watt spectrum fallback — no log; hardcoded chi fallback |
| `reactor_core.py` ~4424 | `except Exception: pass` in nuclide parsing — best-effort; could mask malformed input |

---

### 3.3 Broad Exception Handling (REVIEWED)

- **Burnup, reactor_core, parameter_sweep, atlas, audit_log:** Use `reraise_if_system(e)` before fallbacks — **good**.
- **neutronics/solver.py ~91:** `except Exception: return False` for Unicode console check — acceptable for that narrow use.
- **plugin_registry.py ~98:** `except Exception` for hook callbacks — intentional; hooks must not break core flow.
- **CLI:** Broad `except Exception` used for user-facing error handling; logs and exits cleanly — acceptable.

---

## 4. Accuracy Considerations

### 4.1 Flux-Weighting (ADDRESSED)

- **Implementation:** `_collapse_to_multigroup_flux_weighted()` in `endf_extractors.py`.
- **Default spectrum:** 1/E when flux not provided.
- **Documentation:** `docs/FLUX_WEIGHTING_LIMITATION.md`.
- **Regulatory:** Documented for NQA-1 dedication.

### 4.2 Validation at Solver Boundaries (ADDRESSED)

- **Neutronics:** `validate_safety_critical_outputs(k_eff, flux)` in `_validate_solution()`; raises `ValueError` on NaN/Inf.
- **Burnup:** Same validation after each step.
- **Thermal lumped:** Same for transient outputs.

### 4.3 Determinism (ADDRESSED)

- Seeds in optimization and fuel management.
- `default_rng(seed)` in Monte Carlo (no global `np.random.seed`).

---

## 5. Version and Dependency Consistency

| Item | Status |
|------|--------|
| `__version__.py` vs `setup.py` | Both 0.1.0 — synced |
| `requirements-lock.txt` | Exists per VERSION_LOCK_REQUIREMENTS.md |
| `httpx` in requirements.txt | Present; used by data_downloader |

---

## 6. Test and CI Status

- **Core tests:** Neutronics, burnup, validation, assembly tests pass.
- **Pre-sync:** Passes.
- **One skip:** `test_validation_comprehensive.py` H2O TSL material not found — expected when TSL data not installed.

---

## 7. Recommended Action Summary

### Before Community Beta (v0.2.0)

1. **Update `author_email`** in `setup.py` (and README contact).
2. **Add logging** to the elastic 5-barn fallback in `compute_anisotropic_scattering_matrix` (endf_extractors.py ~631).
3. Run `python -m build` and TestPyPI upload.
4. Manual smoke test: CLI create/analyze, dashboard, at least one example.

### Before Pro Release

1. Complete Community checklist.
2. Implement RSA licensing and test.
3. Host Pro docs and define support process.
4. Run `pre_sync_check.py` before every sync.

### Optional (Medium-Term) — Implemented

- Add `logger.warning` for Watt spectrum fallback — Done (`endf_extractors.py`).
- Add `logger.warning` for MF6 parser fallback — Done (`endf_extractors.py`).
- Add `logger.debug` for nuclide parsing failures in reactor_core — Done (`reactor_core.py`).

---

## References

- `docs/status/PRODUCTION_READINESS_CHECKLIST.md`
- `docs/status/NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md`
- `docs/FLUX_WEIGHTING_LIMITATION.md`
- `docs/development/PYPI_READINESS_CHECKLIST.md`
- `scripts/pre_sync_check.py`
