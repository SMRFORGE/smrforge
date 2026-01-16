# Manual Test Re-run Results

**Date:** January 2026  
**Environment:** Docker (smrforge-dev)  
**SMRForge Version:** 0.1.0  
**Status:** After API fixes

---

## Test Execution Summary

### ✅ Test 1: CLI Commands (`test_01_cli_commands.py`)
**Result:** **15/15 tests passed (100%)** ✅

**Status:** All tests passing - fixes verified!

---

### ✅ Test 2: Reactor Creation (`test_02_reactor_creation.py`)
**Result:** **2/5 tests passed (40%)** - Significant improvement!

**Passed:**
- ✅ Preset listing works
- ✅ Get preset works
- ✅ Create reactor from preset works (**FIXED!**)

**Failed/Issues:**
- ❌ Custom reactor creation - needs `power_mw` instead of `power`, and other parameter fixes
- ❌ Quick k-eff - `quick_keff()` expects parameters, not a reactor object

**Notes:**
- Main reactor creation from preset is now working!
- Custom reactor creation needs API parameter names updated in test

---

### ❌ Test 3: Burnup Calculations (`test_03_burnup.py`)
**Result:** **0/4 tests passed**

**Issues:**
- `BurnupOptions.__init__()` got unexpected keyword argument `time_units`
- Test script uses wrong API parameters

**Action Required:** Fix test script to match actual `BurnupOptions` API

---

### ❌ Test 4: Parameter Sweep (`test_04_parameter_sweep.py`)
**Result:** **0/5 tests passed**

**Issues:**
- `SweepConfig.__init__()` got unexpected keyword argument `values`
- Test script uses wrong API parameters

**Action Required:** Fix test script to match actual `SweepConfig` API

---

### ✅ Test 5: Templates (`test_05_templates.py`)
**Result:** **5/6 tests passed (83%)** ✅

**Passed:**
- ✅ Create template from preset (**FIXED!**)
- ✅ Load template (**FIXED!**)
- ✅ Instantiate with defaults (**FIXED!**)
- ✅ Instantiate with overrides (**FIXED!**)
- ✅ Template library operations (**FIXED!**)

**Failed:**
- ⚠️ Template validation - returns list instead of boolean (minor issue)

**Status:** Major improvements! Template API fixes working correctly.

---

### ✅ Test 6: Design Constraints (`test_06_constraints.py`)
**Result:** **5/5 tests passed (100%)** ✅

**Passed:**
- ✅ Create constraint set (**FIXED!**)
- ✅ Validate design (**FIXED!**)
- ✅ Constraint violations (**FIXED!**)
- ✅ Save constraints (**FIXED!**)
- ✅ Load constraints (**FIXED!**)

**Status:** All tests passing! All fixes working correctly.

---

### ❌ Test 7: I/O Converters (`test_07_io_converters.py`)
**Result:** **ERROR - Import failed**

**Issue:** Test script cannot import SMRForge. May be path issue.

**Action Required:** Check import path in test script.

---

### ✅ Test 8: Data Management (`test_08_data_management.py`)
**Result:** **4/4 tests passed (100%)** ✅

**Status:** All tests passing - no changes needed.

---

### ⚠️ Test 9: Validation Framework (`test_09_validation.py`)
**Result:** **2/4 tests passed (50%)**

**Passed:**
- ✅ Validation report generation
- ✅ Validation CLI commands

**Skipped (Expected):**
- ⏭️ ValidationBenchmarker initialization - in tests module (expected)
- ⏭️ k-eff benchmarking - requires benchmarker (expected)

**Status:** Working as expected. Benchmarker is intentionally in tests module.

---

### ❌ Test 10: Visualization (`test_10_visualization.py`)
**Result:** **0/4 tests passed**

**Issues:**
- Visualization functions expect core objects, not SimpleReactor
- `plot_mesh3d_plotly()` doesn't accept `output_file` parameter

**Action Required:** Fix test script to match visualization API

---

### ⚠️ Test 11: Workflows (`test_11_workflows.py`)
**Status:** Not re-run yet

---

### ✅ Test 12: Configuration (`test_12_config.py`)
**Result:** **5/5 tests passed (100%)** ✅

**Status:** All tests passing - no changes needed.

---

### ❌ Test 13: Advanced Features (`test_13_advanced.py`)
**Status:** Not re-run yet (likely similar issues to Test 2)

---

## Overall Summary

### Tests Executed: 10
### Tests Completed: 10

### Fully Passing Tests: 4 (100% pass rate)
1. ✅ **Test 1: CLI Commands** - 15/15 (100%)
2. ✅ **Test 6: Constraints** - 5/5 (100%)
3. ✅ **Test 8: Data Management** - 4/4 (100%)
4. ✅ **Test 12: Configuration** - 5/5 (100%)

### Partially Passing Tests: 3
1. ✅ **Test 2: Reactor Creation** - 2/5 (40%) - **MAJOR IMPROVEMENT!**
2. ✅ **Test 5: Templates** - 5/6 (83%) - **MAJOR IMPROVEMENT!**
3. ⚠️ **Test 9: Validation** - 2/4 (50%) - Expected behavior

### Failing Tests: 3
1. ❌ **Test 3: Burnup** - 0/4 (0%) - API parameter mismatch
2. ❌ **Test 4: Parameter Sweep** - 0/5 (0%) - API parameter mismatch
3. ❌ **Test 10: Visualization** - 0/4 (0%) - API parameter mismatch

### Import/Path Issues: 1
1. ❌ **Test 7: I/O Converters** - Import error

---

## Fixes That Worked

### ✅ Successfully Fixed:
1. **Reactor Creation from Preset** - Changed `preset=` to positional `name` parameter ✅
2. **Template API** - Changed `template_id` to `name`, `add_template()` to `save_template()` ✅
3. **ConstraintSet API** - Fixed initialization to use `add_constraint()` method ✅
4. **ConstraintSet Save/Load** - Added save/load methods ✅
5. **Import Errors** - Fixed imports in test_06_constraints.py and test_09_validation.py ✅

---

## Remaining Issues

### 🔴 High Priority:
1. **Test 3: Burnup API** - `time_units` parameter doesn't exist in `BurnupOptions`
2. **Test 4: Parameter Sweep API** - `values` parameter doesn't exist in `SweepConfig`
3. **Test 10: Visualization API** - Functions expect different parameter types

### 🟡 Medium Priority:
4. **Test 2: Custom Reactor** - Use `power_mw` instead of `power` and fix other parameters
5. **Test 7: I/O Converters** - Import path issue

### 🟢 Low Priority:
6. **Test 5: Template Validation** - Returns list instead of boolean (minor)

---

## Progress Summary

### Before Fixes:
- Test 2: 0/5 (0%)
- Test 5: 0/6 (0%)
- Test 6: ERROR
- Test 9: ERROR

### After Fixes:
- Test 2: 2/5 (40%) - **+40% improvement!**
- Test 5: 5/6 (83%) - **+83% improvement!**
- Test 6: 5/5 (100%) - **FULLY FIXED!**
- Test 9: 2/4 (50%) - **Expected behavior**

---

## Next Steps

1. **Fix Burnup API issues** in `test_03_burnup.py`
2. **Fix Parameter Sweep API issues** in `test_04_parameter_sweep.py`
3. **Fix Visualization API issues** in `test_10_visualization.py`
4. **Fix Custom Reactor API** in `test_02_reactor_creation.py`
5. **Fix I/O Converters import** in `test_07_io_converters.py`
6. **Minor fix** for template validation return type

---

*This summary reflects test results after implementing fixes for Issues 1, 2, and 3 from MANUAL_TEST_RESULTS_SUMMARY.md*
