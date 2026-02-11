# Independent Third-Party Verification (SC-3)

## Scope Template

This document outlines the scope for independent third-party verification of SMRForge for safety-critical applications.

### 1. Verification Objectives

- [ ] Verify correctness of neutronics calculations (k-eff, flux, power)
- [ ] Verify burnup/depletion accuracy against benchmarks
- [ ] Verify safety transient simulations
- [ ] Review software quality (testing, documentation, traceability)
- [ ] Assess compliance with applicable standards (NQA-1, IEC 60880)

### 2. Scope of Verification

**In-scope modules:**
- `smrforge.neutronics.solver` - Multi-group diffusion
- `smrforge.burnup.solver` - Depletion/decay
- `smrforge.validation` - Input validation, constraints, regulatory traceability
- `smrforge.core.reactor_core` - Nuclear data handling (critical path)
- `smrforge.core.endf_parser` - ENDF parsing

**Out-of-scope (for initial verification):**
- Visualization, GUI
- Optional/external backends (SANDY, OpenMC, Serpent interfaces)

### 3. Deliverables

- [ ] Verification report
- [ ] Benchmark comparison results
- [ ] Code review findings
- [ ] Recommendations for safety use

### 4. Reference Documents

- `docs/safety-critical/V&V_EXPERIMENTAL_BENCHMARKS.md`
- `docs/safety-critical/SAFETY_CRITICAL_MODULES.md`
- `docs/validation/validation-execution-guide.md`
- `COVERAGE_TRACKING.md`

### 5. Contact

For third-party verification inquiries, contact the project maintainers.
