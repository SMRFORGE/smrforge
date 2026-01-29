# Excluded Files Troubleshooting & Fix Coordination

## Overview

This document coordinates the troubleshooting and fixing of test files that were excluded from coverage analysis runs. These files need to be fixed so they can be included in future coverage runs.

**Date Created:** January 22, 2026  
**Status:** Ready for Agent 2  
**Goal:** Fix excluded test files so they can run reliably in coverage analysis

---

## Excluded Files Status

### 1. `tests/test_optimization_utils.py`
**Status:** 🔴 Excluded - Timeout Issues  
**Reason:** Tests timeout when run in full test suite (pass individually)  
**Test Count:** 52 tests  
**Last Action:** Added `cleanup_after_test` fixture with `gc.collect()` to improve isolation

**Issues:**
- Tests pass individually (~2.45 seconds for all 52 tests)
- Timeout occurs when run as part of full test suite
- Suspected resource contention or memory leaks
- Already has `gc.collect()` fixture added

**Diagnosis Needed:**
- [x] Run tests individually to confirm they pass ✅ **All 52 tests pass in 5.57 seconds**
- [ ] Run tests in isolation (separate pytest process)
- [ ] Check for resource leaks (memory, file handles, threads)
- [ ] Verify if issue is test isolation or actual timeout
- [ ] Check if tests are creating background threads/processes that aren't cleaned up

**Diagnostic Results (2026-01-22):**
- ✅ All 52 tests pass individually in 8.96 seconds (slightly slower with enhanced cleanup)
- ✅ No timeout when run alone
- ✅ Enhanced cleanup fixture added (double gc.collect() + NumPy cleanup)
- ⚠️ Issue likely occurs only in full test suite (resource contention or test isolation)
- ✅ Improvements made to reduce resource leaks

**Potential Fixes:**
1. Add more aggressive cleanup (close file handles, join threads)
2. Add pytest markers to skip in parallel runs
3. Increase timeout for these specific tests
4. Split into smaller test files
5. Add explicit resource cleanup in each test
6. Use `pytest --forked` to run in separate processes (if pytest-forked available)

**Recommended Approach:**
Since tests pass individually, the issue is likely test isolation. Consider:
- Adding `@pytest.mark.isolated` marker and running with `--forked`
- Or ensuring all tests clean up after themselves properly
- Or running these tests in a separate pytest process during coverage runs

**Files to Review:**
- `tests/test_optimization_utils.py`
- `smrforge/utils/optimization_utils.py` (source code being tested)

---

### 2. `tests/test_parallel_batch.py`
**Status:** 🔴 Excluded - Per Request  
**Reason:** Excluded from coverage runs (reason not specified)  
**Test Count:** ~20+ tests (estimated)

**Issues:**
- [ ] Determine why it was excluded
- [ ] Check if tests pass individually
- [ ] Check if tests pass in full suite
- [ ] Identify any timeout, isolation, or resource issues

**Diagnosis Needed:**
- [x] Run tests individually: `pytest tests/test_parallel_batch.py -v` ⚠️ **Command aborted/hanging**
- [ ] Run in full suite to check for isolation issues
- [ ] Check for multiprocessing/threading issues
- [ ] Verify mock usage is correct
- [ ] Check for resource leaks

**Diagnostic Results (2026-01-22):**
- ⚠️ Test run aborted/hanging when running all tests together
- ✅ Individual tests pass successfully
- ✅ Fixed in `parallel_batch.py` - should help with resource cleanup
- ⚠️ May still need test isolation improvements or fixture cleanup

**Potential Issues:**
- Multiprocessing/threading cleanup issues
- Mock patching conflicts
- Resource contention
- Test isolation problems

**Files to Review:**
- `tests/test_parallel_batch.py`
- `smrforge/utils/parallel_batch.py` (source code being tested)

---

### 3. `tests/test_parallel_batch_extended.py`
**Status:** 🔴 Excluded - Per Request  
**Reason:** Excluded from coverage runs (reason not specified)  
**Test Count:** ~30+ tests (estimated)

**Issues:**
- [ ] Determine why it was excluded
- [ ] Check if tests pass individually
- [ ] Check if tests pass in full suite
- [ ] Identify any timeout, isolation, or resource issues

**Diagnosis Needed:**
- [x] Run tests individually: `pytest tests/test_parallel_batch_extended.py -v` 🔴 **3 tests failing**
- [ ] Run in full suite to check for isolation issues
- [ ] Check for multiprocessing/threading issues
- [ ] Verify mock usage is correct
- [ ] Check for resource leaks

**Diagnostic Results (2026-01-22):**
- ✅ **ALL TESTS NOW PASSING** (Fixed!)
- ✅ Fixed 3 failing tests by updating `parallel_batch.py`:
  1. `test_batch_process_duplicate_items` - Fixed unhashable items issue
  2. `test_batch_process_non_picklable_items_threads` - Fixed unhashable items issue
  3. `test_batch_process_zero_max_workers` - Fixed max_workers validation
- ✅ 19 tests passing in 2.32s
- ✅ Root cause fixed: Code bugs in `parallel_batch.py` (lines 88-92, 115, 144)

**Potential Issues:**
- **🔴 IDENTIFIED: 3 failing tests with specific errors:**
  1. `test_batch_process_duplicate_items` - `TypeError: unhashable type: 'list'`
     - **Root Cause:** Line 144 in `parallel_batch.py`: `item_to_index = {item: i for i, item in enumerate(items)}`
     - **Issue:** Uses items as dictionary keys, but lists are unhashable
     - **Fix:** Use index-based tracking instead of item-based dictionary
  2. `test_batch_process_non_picklable_items_threads` - Same issue as #1
  3. `test_batch_process_zero_max_workers` - `ValueError: max_workers must be greater than 0`
     - **Root Cause:** Code doesn't validate `max_workers > 0` before passing to executor
     - **Fix:** Add validation: `max_workers = max(1, max_workers or cpu_count())`

**Recommended Fixes:**
1. Fix `parallel_batch.py` line 144: Use index-based tracking for unhashable items
2. Fix `parallel_batch.py` line 88-92: Validate `max_workers > 0`
3. Fix test expectations if needed

**Files to Review:**
- `tests/test_parallel_batch_extended.py`
- `smrforge/utils/parallel_batch.py` (source code being tested)

---

### 4. `tests/performance/test_performance_benchmarks.py`
**Status:** 🟡 Excluded - Performance Tests (Expected)  
**Reason:** Performance/benchmark tests - typically excluded from coverage  
**Test Count:** Unknown

**Note:** This file may be intentionally excluded as performance tests are often not included in coverage metrics. Verify if this should remain excluded or if it needs fixing.

**Action:**
- [ ] Verify if performance tests should be included in coverage
- [ ] If yes, check for any issues preventing execution
- [ ] If no, document why it's excluded

---

## Agent 2 Assignment

### Priority 1: `test_optimization_utils.py`
**Goal:** Fix timeout issues so tests can run in full suite

**Steps:**
1. **Diagnose the issue:**
   ```powershell
   # Run individually (should pass)
   pytest tests/test_optimization_utils.py -v
   
   # Run with timeout detection
   pytest tests/test_optimization_utils.py -v --timeout=60
   
   # Run in isolation
   pytest tests/test_optimization_utils.py -v --forked
   ```

2. **Check for resource leaks:**
   - Monitor memory usage during test run
   - Check for unclosed file handles
   - Verify threads/processes are cleaned up
   - Check for unclosed sockets/connections

3. **Implement fixes:**
   - Add explicit cleanup in tests
   - Add pytest fixtures for resource management
   - Split large test classes if needed
   - Add markers for test ordering if needed
   - Consider using `pytest-xdist` with `--forked` option for isolation

4. **Verify fix:**
   ```powershell
   # Run in full suite to verify no timeout
   pytest tests/ --ignore=tests/test_parallel_batch.py --ignore=tests/test_parallel_batch_extended.py -v
   ```

---

### Priority 2: `test_parallel_batch.py` and `test_parallel_batch_extended.py`
**Goal:** Diagnose and fix issues preventing inclusion in coverage runs

**Steps:**
1. **Diagnose the issues:**
   ```powershell
   # Run individually
   pytest tests/test_parallel_batch.py -v
   pytest tests/test_parallel_batch_extended.py -v
   
   # Run together
   pytest tests/test_parallel_batch.py tests/test_parallel_batch_extended.py -v
   
   # Run in full suite
   pytest tests/ -v -k "parallel_batch"
   ```

2. **Check for common issues:**
   - Multiprocessing cleanup (ProcessPoolExecutor, ThreadPoolExecutor)
   - Mock patching conflicts
   - Resource contention
   - Test isolation problems
   - Import issues with parallel execution

3. **Implement fixes for `test_parallel_batch_extended.py`:**

   **Fix 1: Handle unhashable items in `parallel_batch.py` (Line 144)**
   ```python
   # Current (broken for lists):
   item_to_index = {item: i for i, item in enumerate(items)}
   
   # Fixed (use index-based tracking):
   # Store futures with their index instead of item
   futures = {}
   for i, item in enumerate(items):
       future = executor.submit(func, item)
       futures[future] = i  # Use index instead of item
   
   # Then in result collection:
   for future in as_completed(futures):
       idx = futures[future]  # Get index directly
       results[idx] = future.result()
   ```

   **Fix 2: Validate max_workers in `parallel_batch.py` (Line 88-92)**
   ```python
   # Current:
   if max_workers is None:
       max_workers = cpu_count()
   max_workers = min(max_workers, len(items))
   
   # Fixed:
   if max_workers is None:
       max_workers = cpu_count()
   max_workers = max(1, min(max_workers, len(items)))  # Ensure >= 1
   ```

   **Fix 3: Update test expectations if needed**
   - Verify `test_batch_process_zero_max_workers` expects correct behavior
   - Fix `test_batch_process_duplicate_items` if logic changes
   - Fix `test_batch_process_non_picklable_items_threads` if logic changes

4. **Implement fixes for `test_parallel_batch.py`:**
   - Investigate hanging issue (likely executor cleanup)
   - Add timeout to tests
   - Ensure all executors are properly closed

4. **Verify fix:**
   ```powershell
   # Run in full suite
   pytest tests/ -v
   ```

---

## Testing Strategy

### Individual Test Runs
```powershell
# Test each file individually
pytest tests/test_optimization_utils.py -v
pytest tests/test_parallel_batch.py -v
pytest tests/test_parallel_batch_extended.py -v
```

### Full Suite Test (After Fixes)
```powershell
# Run full suite without exclusions
pytest tests/ --cov=smrforge --cov-report=json:coverage.json -v
```

### Coverage Verification
```powershell
# Run coverage with previously excluded files
pytest tests/ \
    --cov=smrforge \
    --cov-report=json:coverage.json \
    --cov-report=term-missing \
    -v
```

---

## Success Criteria

### For `test_optimization_utils.py`:
- [ ] All 52 tests pass individually
- [ ] All 52 tests pass when run together
- [ ] Tests complete in < 60 seconds when run together
- [ ] Tests pass when run as part of full test suite
- [ ] No resource leaks detected
- [ ] Can be included in coverage runs without timeout

### For `test_parallel_batch.py`:
- [ ] All tests pass individually
- [ ] All tests pass when run together
- [ ] Tests pass when run as part of full test suite
- [ ] No resource leaks detected
- [ ] Can be included in coverage runs

### For `test_parallel_batch_extended.py`:
- [ ] All tests pass individually
- [ ] All tests pass when run together
- [ ] Tests pass when run as part of full test suite
- [ ] No resource leaks detected
- [ ] Can be included in coverage runs

---

## Documentation Updates Needed

After fixing each file:
1. Update `COVERAGE_ANALYSIS_IMPLEMENTATION.md` to remove exclusions
2. Update `scripts/run_coverage_analysis.ps1` to remove `--ignore` flags
3. Document any special considerations (e.g., test markers, fixtures)
4. Update this document with resolution status

---

## Notes

- **Test Isolation:** Many issues may be related to test isolation. Consider using `pytest --forked` or adding proper cleanup fixtures.
- **Resource Management:** Parallel processing tests often have resource cleanup issues. Ensure all executors, threads, and processes are properly closed.
- **Mock Patching:** Verify that mock patches are properly cleaned up and don't leak between tests.
- **Coverage Impact:** These files test `utils/optimization_utils.py` and `utils/parallel_batch.py`, which currently show low coverage (17.19% and 20.83% respectively) because their tests were excluded.

---

## Status Updates

**Last Updated:** January 22, 2026  
**Agent 2 Status:** ✅ **Fixes Applied - Ready for Verification**

### Completed:
- ✅ **Fixed `test_parallel_batch_extended.py`** - All 19 tests passing
  - Fixed unhashable items issue in `parallel_batch.py` (lines 115, 144)
  - Fixed `max_workers` validation (line 88-92)
  
- ✅ **Improved `test_parallel_batch.py`** - Enhanced cleanup added
  - Added cleanup fixture with double `gc.collect()` for resource cleanup
  - Code bugs fixed in `parallel_batch.py` (same fixes as extended)
  - Individual tests pass successfully
  
### In Progress:
- ✅ **`test_parallel_batch.py`** - Enhanced cleanup added, individual tests pass
  - Added cleanup fixture with double `gc.collect()` for better resource cleanup
  - Code bugs fixed in `parallel_batch.py` (unhashable items, max_workers validation)
  - May still hang when run together - needs full suite verification
  
### Remaining:
- ✅ **`test_optimization_utils.py`** - Enhanced cleanup added, passes individually
  - Added double `gc.collect()` for better memory cleanup
  - Added NumPy error state reset
  - May still need full suite verification or additional isolation measures

**Priority:** Verify `test_parallel_batch.py` fixes, then address `test_optimization_utils.py` isolation

---

*This document should be updated as fixes are implemented.*
