# Validation Accuracy Metrics

**Last Updated:** February 2026  
**Status:** Reference documentation for SMRForge validation benchmarks

---

## Overview

SMRForge validation benchmarks compare calculated results against reference values from international standards and evaluated nuclear data. This document describes the benchmark categories, expected tolerances, and how to interpret accuracy metrics.

---

## Benchmark Categories

### 1. Cross-Section Spot Checks

| Category | Energy | Source | Typical Tolerance |
|----------|--------|--------|-------------------|
| **Thermal (0.0253 eV)** | 2200 m/s | IAEA Neutron Data Standards, ENDF | 2–5% |
| **Fast/High energy** | 10 keV – 30 MeV | ENDF parser regression | 10–20% |

**Thermal reference values (IAEA 2017 / ENDF-B-VIII.1):**

| Nuclide | Reaction | Value [barns] | Uncertainty |
|---------|----------|---------------|-------------|
| U-235 | (n,f) | 587.29 | ±1.3 |
| U-235 | (n,γ) | ~99 | ~2% |
| U-238 | (n,γ) | ~2.68 | ~4% |

**Interpretation:**

- `within_tolerance: true` — calculated value agrees with reference within the specified relative tolerance
- `relative_error_percent` — percentage difference; aim for &lt;5% for thermal XS when ENDF is available

### 2. Burnup / k-eff

| Benchmark | Type | Tolerance |
|-----------|------|-----------|
| **simple_neutronics_2g** | SMRForge regression | 1% (stability check) |
| **IAEA-style burnup** | External benchmark | 0.5–1% (when available) |

**Interpretation:**

- Regression benchmarks ensure code stability; k_eff should match the stored baseline
- IAEA benchmarks (when populated) compare against published criticality/burnup results

### 3. Decay Heat (ANSI/ANS-5.1)

| Time after shutdown | Typical fraction of initial power |
|---------------------|-----------------------------------|
| 1 hour | ~7% |
| 1 day | ~4–5% |
| 1 week | ~2–3% |
| 30 days | ~1–2% |

**Interpretation:**

- Decay heat should decrease monotonically (after short initial peak)
- Values are compared against ANSI/ANS-5.1 when benchmark DB includes reference values

### 4. TSL Interpolation, Fission Yields, Gamma Transport

- **TSL:** Interpolation accuracy for thermal scattering law data
- **Fission yields:** Parser correctness vs ENDF MF8
- **Gamma transport:** Structure validation; comparison to MCNP when benchmarks exist

---

## Running Validation

```bash
# With ENDF data and default benchmarks
smrforge validate run --endf-dir $SMRFORGE_ENDF_DIR --output report.txt

# With custom benchmark file
smrforge validate run --endf-dir $SMRFORGE_ENDF_DIR --benchmarks my_benchmarks.json --output report.txt
```

---

## Accuracy Summary Table (Example)

| Test | Reference | Expected | Typical Result |
|------|-----------|----------|----------------|
| U-235(n,f) @ 0.0253 eV | 587.29 b | Within 2% | Pending ENDF run |
| U-238(n,γ) @ 0.0253 eV | 2.68 b | Within 5% | Pending ENDF run |
| simple_neutronics_2g k_eff | 1.328 | Within 1% | Regression pass |
| Decay heat @ 1 h | ANSI/ANS-5.1 | Structure check | Pass |

*Populate this table by running `smrforge validate run` and inspecting the JSON/ report output.*

---

## Benchmark Database Structure

See `benchmarks/validation_benchmarks.json` and `docs/validation/adding-benchmark-values.md` for:

- `cross_section_benchmarks` — nuclide, reaction, energy_ev, expected_value, tolerance
- `decay_heat_benchmarks` — nuclides, time_points, benchmark_values
- `burnup_benchmarks` — time_steps, benchmark_k_eff

---

## Related Documentation

- [Adding Benchmark Values](adding-benchmark-values.md)
- [Validation Execution Guide](validation-execution-guide.md)
- [Standards Data Availability](standards-data-availability.md)
