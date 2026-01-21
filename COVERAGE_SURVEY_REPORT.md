# SMRForge Project Coverage Survey Report

**Date:** January 2026  
**Coverage File Analyzed:** `coverage_final.json`

## Executive Summary

### Full Project Coverage (All Files)
- **Overall Coverage:** **62.11%**
- **Covered Lines:** 12,894 / 20,761
- **Missing Lines:** 7,867
- **Total Files:** 142

### Coverage with Standard Exclusions (per pytest.ini)
- **Overall Coverage:** **74.36%**
- **Covered Lines:** 10,216 / 13,739
- **Missing Lines:** 3,523
- **Included Files:** 100
- **Excluded Files:** 42

**Note:** The pytest.ini configuration excludes GUI, visualization, CLI, and some large parser files from coverage reporting, as these are either hard to test or tested separately.

## Gap to 80% Target

- **Full Project:** 17.89% gap (3,714 statements needed)
- **With Standard Exclusions:** 5.64% gap (775 statements needed)

## Coverage Breakdown

### Modules Below 75% Coverage (Included Files Only)

The following modules are below the 75% target threshold:

| Module | Coverage | Covered | Missing |
|--------|----------|---------|---------|
| `economics/integration.py` | 0.00% | 0/19 | 19 |
| `data_downloader.py` | 13.08% | 31/237 | 206 |
| `neutronics/hybrid_solver.py` | 15.97% | 23/144 | 121 |
| `neutronics/adaptive_sampling.py` | 16.28% | 28/172 | 144 |
| `burnup/fuel_management_integration.py` | 16.46% | 13/79 | 66 |
| `neutronics/monte_carlo_optimized.py` | 16.67% | 52/312 | 260 |
| `utils/parallel_batch.py` | 17.19% | 11/64 | 53 |
| `control/integration.py` | 18.75% | 6/32 | 26 |
| `core/decay_chain_utils.py` | 19.77% | 17/86 | 69 |
| `neutronics/implicit_mc.py` | 21.74% | 20/92 | 72 |
| `utils/optimization_utils.py` | 22.22% | 10/45 | 35 |
| `convenience.py` | 23.44% | 30/128 | 98 |
| `utils/memory_pool.py` | 27.59% | 16/58 | 42 |
| `utils/error_messages.py` | 28.07% | 16/57 | 41 |
| `geometry/validation.py` | 30.27% | 89/294 | 205 |
| `utils/memory_mapped.py` | 32.20% | 19/59 | 40 |
| `geometry/advanced_import.py` | 33.65% | 143/425 | 282 |
| `burnup/lwr_burnup.py` | 34.03% | 49/144 | 95 |
| `convenience/__init__.py` | 36.51% | 23/63 | 40 |
| `validation/regulatory_traceability.py` | 40.00% | 54/135 | 81 |
| `validation/standards_parser.py` | 43.98% | 95/216 | 121 |
| `utils/units.py` | 45.61% | 26/57 | 31 |
| `core/multigroup_advanced.py` | 50.89% | 114/224 | 110 |
| `core/self_shielding_integration.py` | 52.05% | 38/73 | 35 |
| `core/endf_setup.py` | 52.40% | 109/208 | 99 |

... and 5 more modules below 75%

## Recent Improvements

Based on recent commits, the following modules have received comprehensive test coverage:

1. **`thermal/multiphysics_coupling.py`** - 86.4% coverage (17 new tests)
2. **`fuel_cycle/advanced_optimization.py`** - 98.3% coverage (23 new tests)

These improvements may not be reflected in the current `coverage_final.json` file if it was generated before these tests were added.

## Recommendations

1. **Focus on High-Impact Modules:** Target modules with the largest number of missing statements:
   - `data_downloader.py` (206 missing)
   - `neutronics/monte_carlo_optimized.py` (260 missing)
   - `geometry/advanced_import.py` (282 missing)
   - `neutronics/adaptive_sampling.py` (144 missing)

2. **Quick Wins:** Modules with low coverage but fewer statements:
   - `economics/integration.py` (19 statements total)
   - `control/integration.py` (26 missing)
   - `utils/parallel_batch.py` (53 missing)

3. **Regenerate Coverage:** Run a fresh coverage analysis to include recent test additions:
   ```bash
   pytest tests/ --cov=smrforge --cov-report=json:coverage_final.json
   ```

## Notes

- The coverage file analyzed may be from a previous run and may not reflect the most recent test additions
- Some modules are intentionally excluded from coverage (GUI, visualization, CLI) per pytest.ini configuration
- The 79.2% figure mentioned in documentation may be from a more recent measurement or different exclusion set
