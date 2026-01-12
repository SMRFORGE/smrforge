# Test Coverage Completion Plan

**Date:** January 2026  
**Current Coverage:** 79.2%  
**Target Coverage:** 80%  
**Gap:** ~83 statements (0.8% increase needed)

---

## Executive Summary

SMRForge has achieved **excellent test coverage** with 79.2% overall coverage. All critical and priority modules exceed the 75-80% target. The remaining gap to 80% is primarily in low-priority areas (package initialization files, CLI tools).

**Status:** ✅ **Ready for production** - Remaining gaps are incremental improvements.

---

## Current Status

### Overall Coverage Metrics

- **Current:** 79.2% (10,340 statements, 2,147 missing)
- **Target:** 80%
- **Gap:** ~83 statements (0.8% increase)
- **Critical Modules:** ✅ All exceed 75-80% target
- **Priority Modules:** ✅ All complete

### Coverage Distribution

| Coverage Level | Module Count | Status |
|----------------|--------------|--------|
| 100% | 17 modules | ✅ Perfect |
| 90-99% | 20 modules | ✅ Excellent |
| 80-89% | 11 modules | ✅ Good |
| 70-79% | 12 modules | ⚠️ Acceptable |
| <70% | 29 modules | ⚠️ Needs Work |

**Note:** Many <70% modules are `__init__.py` files or stub modules.

---

## Completion Strategy

### Phase 1: Quick Wins (0.5-1.0% gain) 🟢 **LOW EFFORT**

**Target:** Package initialization files (`__init__.py`)

#### 1.1 Root Package `__init__.py` (64.9% → 75%)

**Current:** 64.9%  
**Target:** 75%  
**Gap:** 10.1%  
**Estimated Effort:** 2-3 hours

**Actions:**
- Add tests for import error handling
- Test conditional imports (try/except blocks)
- Test `__all__` exports
- Test version info access

**Test File:** `tests/test_init_root.py`

**Expected Coverage Gain:** +0.1-0.2%

---

#### 1.2 Core Package `__init__.py` (73.3% → 80%)

**Current:** 73.3%  
**Target:** 80%  
**Gap:** 6.7%  
**Estimated Effort:** 2-3 hours

**Actions:**
- Test all conditional import paths
- Test `_ENDF_EXTRACTORS_AVAILABLE` flag
- Test `_DECAY_CHAIN_UTILS_AVAILABLE` flag
- Test `_MULTIGROUP_ADVANCED_AVAILABLE` flag
- Test all `__all__` extensions

**Test File:** `tests/test_core_init.py`

**Expected Coverage Gain:** +0.1-0.2%

---

#### 1.3 Geometry Package `__init__.py` (69.6% → 75%)

**Current:** 69.6%  
**Target:** 75%  
**Gap:** 5.4%  
**Estimated Effort:** 1-2 hours

**Actions:**
- Test conditional imports
- Test import error paths
- Test `__all__` exports

**Test File:** `tests/test_geometry_init.py`

**Expected Coverage Gain:** +0.1%

---

#### 1.4 Visualization Package `__init__.py` (64.7% → 75%)

**Current:** 64.7%  
**Target:** 75%  
**Gap:** 10.3%  
**Estimated Effort:** 2-3 hours

**Actions:**
- Test new visualization module imports
- Test conditional availability flags
- Test `__all__` exports for new modules

**Test File:** `tests/test_visualization_init.py`

**Expected Coverage Gain:** +0.1-0.2%

---

#### 1.5 Other Package `__init__.py` Files

**Modules:**
- `neutronics/__init__.py` (60.0%)
- `thermal/__init__.py` (63.6%)
- `safety/__init__.py` (60.0%)
- `uncertainty/__init__.py` (60.0%)
- `presets/__init__.py` (60.0%)

**Estimated Effort:** 3-4 hours total  
**Expected Coverage Gain:** +0.1-0.2%

---

**Phase 1 Total Expected Gain:** +0.5-1.0%  
**Phase 1 Total Effort:** 10-15 hours

---

### Phase 2: Incremental Improvements (0.2-0.3% gain) 🟡 **MEDIUM EFFORT**

#### 2.1 Core Decay Parser (76.2% → 80%)

**Current:** 76.2%  
**Target:** 80%  
**Gap:** 3.8%  
**Estimated Effort:** 4-6 hours

**Actions:**
- Add edge case tests for decay data parsing
- Test error handling paths
- Test boundary conditions
- Test invalid input handling

**Test File:** `tests/test_decay_parser_complete.py`

**Expected Coverage Gain:** +0.1-0.2%

---

#### 2.2 Core ENDF Setup (6.2% → 50%)

**Current:** 6.2%  
**Target:** 50% (CLI tool - lower priority)  
**Gap:** 43.8%  
**Estimated Effort:** 6-8 hours

**Actions:**
- Add CLI tests using `pytest-click` or similar
- Test interactive prompts (mocked)
- Test validation functions
- Test file system operations

**Test File:** `tests/test_endf_setup.py`

**Expected Coverage Gain:** +0.1% (low impact due to small module size)

**Note:** This is a CLI tool - lower priority for unit testing.

---

**Phase 2 Total Expected Gain:** +0.2-0.3%  
**Phase 2 Total Effort:** 10-14 hours

---

### Phase 3: Advanced Coverage (0.1-0.2% gain) 🔵 **OPTIONAL**

#### 3.1 Edge Cases in Well-Covered Modules

**Target Modules:**
- `core/reactor_core.py` (86.5% → 90%)
- `core/endf_parser.py` (97.3% → 98%)
- `neutronics/solver.py` (85.5% → 90%)

**Estimated Effort:** 15-20 hours  
**Expected Coverage Gain:** +0.1-0.2%

**Note:** Diminishing returns - these modules already exceed target.

---

## Implementation Timeline

### Week 1: Phase 1 (Quick Wins)

**Days 1-2:** Root and Core `__init__.py` files
- ✅ Complete root package `__init__.py` tests
- ✅ Complete core package `__init__.py` tests
- **Expected gain:** +0.2-0.4%

**Days 3-4:** Geometry and Visualization `__init__.py` files
- ✅ Complete geometry package `__init__.py` tests
- ✅ Complete visualization package `__init__.py` tests
- **Expected gain:** +0.2-0.3%

**Day 5:** Other package `__init__.py` files
- ✅ Complete remaining package `__init__.py` tests
- **Expected gain:** +0.1-0.2%

**Week 1 Total Expected Gain:** +0.5-0.9%  
**Week 1 Target:** 79.7-80.1% ✅ **Would reach 80% target!**

---

### Week 2: Phase 2 (Incremental)

**Days 1-2:** Decay parser improvements
- ✅ Add edge case tests
- **Expected gain:** +0.1-0.2%

**Days 3-5:** ENDF setup CLI tests (optional)
- ✅ Add CLI tests if desired
- **Expected gain:** +0.1%

**Week 2 Total Expected Gain:** +0.2-0.3%  
**Week 2 Target:** 80.0-80.4% ✅ **Would exceed 80% target!**

---

## Priority Matrix

### 🔴 High Priority (Blocks 80% target)

**None** - All critical modules complete!

### 🟡 Medium Priority (Incremental improvements)

1. **Package `__init__.py` files** - Quick wins, low effort
2. **Decay parser edge cases** - Incremental improvement

### 🟢 Low Priority (Optional)

1. **ENDF setup CLI tests** - CLI tool, lower priority
2. **Edge cases in well-covered modules** - Diminishing returns

---

## Success Criteria

### Minimum Success (80% overall)

- ✅ Complete Phase 1 (Quick Wins)
- **Result:** 79.7-80.1% coverage
- **Status:** ✅ Target achieved!

### Optimal Success (80.5% overall)

- ✅ Complete Phase 1 (Quick Wins)
- ✅ Complete Phase 2 (Incremental)
- **Result:** 80.0-80.4% coverage
- **Status:** ✅ Target exceeded!

### Stretch Goal (81% overall)

- ✅ Complete Phase 1 (Quick Wins)
- ✅ Complete Phase 2 (Incremental)
- ✅ Complete Phase 3 (Advanced)
- **Result:** 80.5-81.0% coverage
- **Status:** ✅ Excellent coverage!

---

## Risk Assessment

### Low Risk Items ✅

- **Package `__init__.py` files** - Low complexity, well-defined scope
- **Decay parser** - Existing test infrastructure, clear gaps

### Medium Risk Items ⚠️

- **ENDF setup CLI** - Requires CLI testing framework, interactive prompts
- **Edge cases in well-covered modules** - Diminishing returns, harder to find gaps

---

## Resource Requirements

### Developer Time

- **Phase 1:** 10-15 hours (1-2 weeks part-time)
- **Phase 2:** 10-14 hours (1-2 weeks part-time)
- **Phase 3:** 15-20 hours (2-3 weeks part-time)

**Total:** 35-49 hours (4-7 weeks part-time)

### Testing Infrastructure

- ✅ Existing test framework (pytest)
- ✅ Coverage tools (pytest-cov)
- ✅ Mock fixtures available
- ⚠️ May need CLI testing framework for ENDF setup

---

## Monitoring and Tracking

### Coverage Metrics to Track

1. **Overall coverage percentage**
2. **Coverage by package**
3. **Coverage by module**
4. **Number of uncovered statements**
5. **Coverage trends over time**

### Reporting

- **Weekly coverage reports** during implementation
- **Coverage dashboard** (if available)
- **Coverage badges** in README

---

## Recommendations

### Immediate Actions (This Week)

1. ✅ **Start Phase 1** - Package `__init__.py` files
2. ✅ **Set up coverage tracking** - Ensure coverage reports are generated
3. ✅ **Review gaps** - Identify specific uncovered lines

### Short-Term (This Month)

1. ✅ **Complete Phase 1** - Reach 80% target
2. ✅ **Document improvements** - Update coverage documentation
3. ✅ **Celebrate success!** 🎉

### Long-Term (Ongoing)

1. ✅ **Maintain coverage** - Prevent regression
2. ✅ **Incremental improvements** - Address gaps as they arise
3. ✅ **Coverage in CI/CD** - Enforce minimum coverage thresholds

---

## Conclusion

SMRForge has achieved **excellent test coverage** with 79.2% overall coverage. All critical and priority modules exceed the 75-80% target. The remaining gap to 80% is small (~0.8%) and primarily in low-priority areas.

**Recommendation:** 
- ✅ **Proceed with Phase 1** (Quick Wins) to reach 80% target
- ✅ **Optional:** Continue with Phase 2 for incremental improvements
- ✅ **Project is ready for production** - Current coverage is excellent

**Expected Outcome:** 
- **Week 1:** Reach 80% target ✅
- **Week 2:** Exceed 80% target ✅
- **Status:** ✅ **Success!**

---

**See Also:**
- [Comprehensive Coverage Inventory](comprehensive-coverage-inventory.md) - Full module breakdown
- [Test Coverage Summary](test-coverage-summary.md) - Detailed coverage metrics
- [Testing and Coverage Guide](../development/testing-and-coverage.md) - Testing strategies
