# Flux-Weighting Limitation in Multi-Group Collapse

**Status:** Implemented (February 2026) | **Impact:** Medium | **Regulatory:** Document for NQA-1 dedication

---

## Summary

Multi-group cross-section collapse in `smrforge/core/endf_extractors.py` uses **flux-weighted averaging** via `_collapse_to_multigroup_flux_weighted()`. When no flux spectrum is provided, uses 1/E default spectrum (typical for LWR slowing-down). Callers may pass `flux_energy` and `flux_phi` for iterative schemes.

## Location

- **Module:** `smrforge.core.endf_extractors`
- **Function:** `compute_improved_scattering_matrix()` (elastic cross-section collapse)
- **Helper:** `_collapse_to_multigroup_flux_weighted()`

## Implementation

```python
# Flux-weighted collapse: σ_g = ∫σ(E)φ(E)dE/∫φ(E)dE
elastic_mg = _collapse_to_multigroup_flux_weighted(
    energy, sigma_elastic, group_structure,
    flux_energy=flux_energy, flux_phi=flux_phi
)
```

When `flux_energy`/`flux_phi` are not provided, uses 1/E default spectrum. `compute_improved_scattering_matrix()` accepts optional `flux_energy` and `flux_phi` for iterative schemes.

## Flux-Weighting Formula

```
σ_g = ∫ σ(E) φ(E) dE / ∫ φ(E) dE   over group g
```

where φ(E) is the neutron flux spectrum. Implemented in `_collapse_to_multigroup_flux_weighted()`.

## Iterative Flux Passing (Self-Consistency)

For coupled neutronics–burnup or iterative schemes, pass flux from the previous solution:

```python
# In burnup/neutronics iteration: use flux from previous step for collapse
flux_energy = group_centers  # eV
flux_phi = phi_prev         # from solve_steady_state or transport
sigma_s = compute_improved_scattering_matrix(
    cache, nuclide, group_structure, temperature,
    flux_energy=flux_energy, flux_phi=flux_phi
)
```

## Impact Assessment

| Factor | Assessment |
|--------|------------|
| **Accuracy** | Flux-weighting reduces errors vs midpoint interpolation, especially in thermal groups (5–20% improvement). |
| **Use cases** | Most sensitive for thermal reactors, H₂O moderation, and resonance-heavy nuclides. Less critical for fast spectrum or coarse groups. |
| **Mitigation** | Use fine group structures (more groups) to reduce error. Pass flux from iteration for self-consistent collapse. |
| **Future work** | Wire flux from BurnupSolver neutronics solution into multi-group collapse when available. |

## Regulatory Traceability

For NQA-1 dedication and commercial-grade software:

1. **Model assumption:** Multi-group elastic cross-section collapse uses flux-weighting with 1/E default spectrum when flux not provided.
2. **Justification:** Improved accuracy over midpoint interpolation; callers may pass flux from previous iteration.
3. **Impact:** Typically more accurate for thermal and resonance regions.
4. **Uncertainty:** Add to validation uncertainty budget if used for safety analysis.

## References

- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
- SAFETY_CRITICAL_MODULES.md
- NRC Regulatory Guide 1.231
