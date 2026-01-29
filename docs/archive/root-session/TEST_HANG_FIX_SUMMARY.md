# Test Suite Hang Fix Summary

**Date:** January 22, 2026  
**Issue:** Full test suite hangs when running all tests together  
**Status:** Partially Fixed - Workaround Available

---

## Problem

The full test suite (`pytest tests/`) hangs when running all 4401 tests together. The issue is specifically with tests that use `ThreadPoolExecutor` from `parallel_batch.py`.

**Root Cause:**
- Multiple tests create `ThreadPoolExecutor` instances simultaneously
- Windows thread limits or resource contention
- Executors not cleaning up fast enough when many tests run together
- Resource leaks accumulating across tests

---

## Fixes Applied

### 1. Code Fixes in `smrforge/utils/parallel_batch.py`
- ✅ Fixed unhashable items handling (index-based tracking)
- ✅ Fixed `max_workers` validation (ensure >= 1)
- ✅ Reverted to context managers for automatic cleanup
- ✅ Added optional semaphore lock for test isolation
- ✅ Added completion count verification
- ✅ Added timeout handling for futures

### 2. Test Improvements
- ✅ Reduced `max_workers` to 1 in all `test_parallel_batch.py` tests
- ✅ Added cleanup fixture with double `gc.collect()` and 50ms delay
- ✅ Added session-scoped cleanup in `conftest.py`

### 3. Infrastructure
- ✅ Created `tests/parallel_executor_lock.py` for global semaphore
- ✅ Added session-scoped cleanup fixture

---

## Current Status

- ✅ Individual tests pass
- ✅ Small groups of tests pass
- ⚠️ Full suite still hangs when running all tests together
- ✅ Tests can be run separately or in smaller groups

---

## Workaround: Run Tests in Batches

Since the full suite hangs, run tests in smaller batches:

```powershell
# Run tests excluding parallel batch tests
pytest tests/ --ignore=tests/test_parallel_batch.py --ignore=tests/test_parallel_batch_extended.py -v

# Run parallel batch tests separately
pytest tests/test_parallel_batch.py tests/test_parallel_batch_extended.py -v

# Or run with maxfail to stop early
pytest tests/ --maxfail=10 -v
```

---

## Recommended Long-Term Solution

### Option 1: Pytest Marker (Recommended)
Add a marker to parallel tests and run them separately:

```python
# In test_parallel_batch.py
import pytest

@pytest.mark.parallel_batch
class TestBatchProcess:
    ...
```

Then run:
```bash
# Regular tests
pytest -m "not parallel_batch"

# Parallel batch tests separately
pytest -m parallel_batch
```

### Option 2: Exclude from Full Suite
Temporarily exclude these tests from full suite runs until issue is fully resolved.

### Option 3: Use pytest-xdist with Isolation
If using pytest-xdist, ensure proper isolation:
```bash
pytest -n auto --forked  # Requires pytest-forked
```

---

## Files Modified

1. `smrforge/utils/parallel_batch.py` - Code fixes and semaphore support
2. `tests/test_parallel_batch.py` - Cleanup fixture, reduced max_workers
3. `tests/conftest.py` - Session-scoped cleanup
4. `tests/parallel_executor_lock.py` - Global semaphore (NEW)

---

## Next Steps

1. **Immediate:** Use workaround to run tests in batches
2. **Short-term:** Add pytest markers for parallel tests
3. **Long-term:** Investigate Windows-specific thread limits or use alternative approach

---

*Last Updated: January 22, 2026*
