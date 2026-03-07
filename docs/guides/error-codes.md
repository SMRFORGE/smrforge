# SMRForge Error Codes

**Last Updated:** March 2026

Each SMRForge error includes a code (e.g., `SMR-E001`) for easy lookup and documentation.

---

## Error Code Reference

### SMR-E001 — Solver failed to converge

**Message:** Solver failed to converge within max_iterations.

**Recovery suggestions:**
- Increase `max_iterations` (e.g., 2000 instead of 1000)
- Relax `tolerance` (e.g., 1e-5 instead of 1e-6)
- Check cross-section data validity
- Verify geometry is physical (non-zero dimensions)

**See also:** [Neutronics Solver](neutronics-solver.md), [Cross-Section Data](endf-documentation.md)

---

### SMR-E002 — k_eff or flux became invalid (NaN/Inf)

**Message:** Numerical instability produced NaN or Inf in k_eff or flux.

**Recovery suggestions:**
- Check for negative cross sections in your data
- Verify all input values are finite
- Check geometry mesh is valid
- Ensure power density is positive

**See also:** [Numerical Validation](validation/numerical_validation.py), [Solver Options](validation-models.md)

---

### SMR-E003 — ENDF or nuclear data not found

**Message:** Required ENDF files or nuclear data could not be loaded.

**Recovery suggestions:**
- Run: `smrforge data setup`
- Set `SMRFORGE_ENDF_DIR` to your ENDF data directory
- Use: `python -m smrforge.core.endf_setup`
- See: [ENDF Documentation](technical/endf-documentation.md)

---

### SMR-E004 — Solution validation failed

**Message:** Solver produced a non-physical result (e.g., negative flux, k_eff out of range).

**Recovery suggestions:**
- Review enrichment (use fraction 0.195, not 19.5)
- Check geometry dimensions (core_height, core_diameter)
- Verify cross-section data matches material IDs

---

### SMR-E005 — Invalid input parameter

**Message:** An input parameter is out of range or invalid.

**Recovery suggestions:**
- Check enrichment is 0-1 (fraction, not percent)
- Ensure power_mw > 0
- Verify temperatures are in Kelvin

---

### SMR-E006 — Burnup solver failed

**Message:** Burnup depletion calculation failed.

**Recovery suggestions:**
- Check time_steps are in days
- Verify power_density is positive
- Ensure initial_enrichment is in valid range

---

### SMR-E007 — Pro feature requires SMRForge Pro

**Message:** This feature requires a SMRForge Pro license.

**Recovery suggestions:**
- Install: `pip install smrforge-pro`
- See: [Community vs Pro](community_vs_pro.md)

---

### SMR-E008 — Geometry or mesh error

**Message:** Geometry construction or mesh generation failed.

**Recovery suggestions:**
- Call `geometry.build_mesh()` before solving
- Check mesh dimensions (n_radial, n_axial) are positive
- Verify core_height and core_diameter are valid

---

## Reporting Errors

When reporting an error, include:
- The full error message including `SMR-Exxx` code
- Steps to reproduce
- SMRForge version: `smrforge --version`
- Python version and environment

**GitHub Issues:** [SMRFORGE/smrforge/issues](https://github.com/SMRFORGE/smrforge/issues)
