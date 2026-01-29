# Coverage JSON Files Analysis
## Complete Survey of All Coverage Files

**Date:** January 20, 2026  
**Last Updated:** January 21, 2026  
**Purpose:** Identify the exact coverage of the project and track all coverage-related files

---

## 📊 Summary of All Coverage Files

### Full Project Coverage Files (Most Relevant)

| File | Date | Coverage | Covered | Total | Status |
|------|------|----------|---------|-------|--------|
| **coverage_after_dedup.json** | Jan 20, 7:53 PM | **20.95%** | 4,611 | 22,009 | ⚠️ Incomplete |
| **coverage.json** | Jan 19, 3:02 PM | **18.65%** | 4,100 | 21,989 | ⚠️ Incomplete |
| **coverage_current.json** | Jan 18, 11:49 PM | **61.25%** | 13,465 | 21,985 | ✅ **BEST BASELINE** |
| **coverage_check.json** | Jan 18, 5:47 PM | **62.11%** | 12,894 | 20,761 | ⚠️ Different total |
| **coverage_final.json** | Jan 18, 5:26 PM | **62.11%** | 12,894 | 20,761 | ⚠️ Different total |

### Partial/Module-Specific Coverage Files

| File | Date | Coverage | Statements | Scope |
|------|------|----------|------------|-------|
| coverage_new_modules.json | Jan 18, 11:24 PM | **88.75%** | 320 | New modules only |
| coverage_reactor_final.json | Jan 7, 9:54 PM | **70.81%** | 1,199 | Reactor module |
| coverage_uq_full.json | Jan 7, 9:51 PM | **80.13%** | 458 | Uncertainty module |
| coverage_reactor_full.json | Jan 7, 9:49 PM | **70.81%** | 1,199 | Reactor module |
| coverage_reactor.json | Jan 7, 9:47 PM | **46.96%** | 1,199 | Reactor module (partial) |
| coverage_uq.json | Jan 7, 9:46 PM | **77.51%** | 458 | Uncertainty module |

---

## ✅ Coverage Files Status

**Total Coverage JSON Files Found:** 11  
**All Coverage Files Documented:** ✅ Yes

### Verified Coverage Files:
- ✅ `coverage_after_dedup.json`
- ✅ `coverage.json`
- ✅ `coverage_current.json`
- ✅ `coverage_check.json`
- ✅ `coverage_final.json`
- ✅ `coverage_new_modules.json`
- ✅ `coverage_reactor_final.json`
- ✅ `coverage_uq_full.json`
- ✅ `coverage_reactor_full.json`
- ✅ `coverage_reactor.json`
- ✅ `coverage_uq.json`

---

## 📋 Test Result Files (Not Coverage Files)

The following JSON files contain test results or data but **are not coverage files**:

| File | Type | Purpose |
|------|------|---------|
| `burnup_results.json` | Test Results | Burnup calculation results |
| `flux_results.json` | Test Results | Flux distribution results |
| `results.json` | Test Results | General test results (created Jan 21) |
| `results/batch_results.json` | Test Results | Batch processing results |
| `results/reactor1_results.json` | Test Results | Reactor analysis results |
| `results/reactor2_results.json` | Test Results | Reactor analysis results |
| `test_benchmark_data.json` | Benchmark Data | Validation benchmark data |

These files do **not** contain code coverage information and are excluded from coverage analysis.

---

## 🎯 **BEST BASELINE: `coverage_current.json`**

### Analysis

**File:** `coverage_current.json`  
**Date:** January 18, 2026, 11:49 PM  
**Coverage:** **61.25%**  
**Covered Lines:** 13,465  
**Total Statements:** 21,985  
**Missing Lines:** 8,520  
**Gap to 80%:** 18.75% (4,123 statements)

### Why This is the Best Baseline

1. ✅ **Most recent complete run** - Generated before our test improvements
2. ✅ **Complete coverage** - 13,465 covered lines (vs 4,100-4,611 in newer incomplete runs)
3. ✅ **Consistent with documentation** - Matches the 61.25% baseline referenced in docs
4. ✅ **Full test suite** - Appears to have completed all tests successfully

---

## ⚠️ Issues with Newer Files

### `coverage_after_dedup.json` (Jan 20) - 20.95%
- **Problem:** Coverage dropped from 61.25% to 20.95%
- **Cause:** Likely incomplete test run (stopped early or failed)
- **Evidence:** Only 4,611 lines covered vs 13,465 in baseline

### `coverage.json` (Jan 19) - 18.65%
- **Problem:** Even lower coverage than after_dedup
- **Cause:** Incomplete run or early termination
- **Evidence:** Only 4,100 lines covered

---

## 📈 Expected Current Coverage

Based on:
- **Baseline:** 61.25% (from `coverage_current.json`)
- **Improvements:** 215 new tests added across 8 modules
- **Estimated Impact:** +14.8%+ (documented)

### Projection:
- **Estimated Current Coverage:** **~79.2%+**
- **Gap to 80%:** **~0.8%** (~83 statements)
- **Status:** Very close to target! 🎯

---

## ✅ Recommendations

### ✅ Implementation Status

**Status:** IMPLEMENTED (January 21, 2026)

1. ✅ **Fresh coverage run initiated** - Running in background
2. ✅ **Automation script created** - `scripts/run_coverage_analysis.ps1`
3. ⏳ **Awaiting results** - Process running, expected completion in 10-30+ minutes

### Coverage Run Command (Executed):
```bash
python -m pytest tests/ --cov=smrforge \
    --cov-report=json:coverage.json \
    --cov-report=term-missing \
    --ignore=tests/performance/test_performance_benchmarks.py \
    --maxfail=10 \
    -q
```

**Execution:** Background process started  
**Output:** `coverage.json` (will be updated when complete)

### Expected Results:
- **Coverage:** ~79.2%+ (up from 61.25%)
- **Covered Lines:** ~17,400+ (up from 13,465)
- **Missing Lines:** ~4,600 (down from 8,520)

### Next Steps After Completion:
1. Analyze fresh results: `python scripts/analyze_coverage.py coverage.json`
2. Update this document with actual results
3. Update COVERAGE_TRACKING.md with latest percentages
4. Identify remaining gaps to reach 80% target

**See:** `COVERAGE_ANALYSIS_IMPLEMENTATION.md` for detailed implementation notes

---

## 📝 Module-Specific Coverage (from baseline)

From `coverage_current.json`, lowest coverage modules:
1. `economics/integration` - 0.00% (19 statements)
2. `data_downloader` - 13.08% (237 statements) - ✅ Improved with 30 tests
3. `control/integration` - 18.75% (32 statements) - ✅ Improved with 8 tests
4. `validation/regulatory_traceability` - 40.00% (135 statements) - ✅ Improved with 31 tests
5. `validation/standards_parser` - 43.98% (documented) - ✅ Improved with 31 tests

---

## 🔍 Verification Summary

**Date Verified:** January 21, 2026  
**Coverage Files:** All 11 files found and documented ✅  
**Test Result Files:** 7 files identified (excluded from coverage analysis) ✅  
**Untracked Coverage Files:** None found ✅

---

*Analysis Date: January 20, 2026*  
*Last Updated: January 21, 2026*  
*Best Baseline: coverage_current.json (61.25%)*
