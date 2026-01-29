# Test Suite Hang Diagnosis

**Date:** January 22, 2026  
**Issue:** Full test suite hangs when running all tests together  
**Status:** Investigating

---

## Symptoms

- Test suite hangs when running full suite (`pytest tests/`)
- Individual test files pass successfully
- Tests pass when run in small groups
- 4401 tests collected successfully
- Hanging occurs during test execution, not collection

---

## Root Cause Analysis

### Likely Causes:

1. **ThreadPoolExecutor Resource Contention**
   - Multiple tests create ThreadPoolExecutors simultaneously
   - Windows may have thread limits or resource contention
   - Executors not cleaning up fast enough when many tests run together

2. **Test Isolation Issues**
   - Tests interfering with each other's executor cleanup
   - Resource leaks accumulating across tests
   - Threads from previous tests not fully terminated

3. **Windows-Specific Issues**
   - Windows thread creation limits
   - ProcessPoolExecutor issues on Windows
   - Thread cleanup delays on Windows

---

## Fixes Applied

### 1. `smrforge/utils/parallel_batch.py`
- ✅ Reverted to context managers for automatic cleanup
- ✅ Fixed unhashable items handling (index-based tracking)
- ✅ Fixed max_workers validation
- ✅ Added optional semaphore lock for test isolation (limits concurrent executors)
- ✅ Added completion count verification
- ✅ **Windows-specific fix**: Default to ThreadPoolExecutor on Windows (avoids ProcessPoolExecutor pickling issues)
- ✅ Added timeout handling for futures

### 2. `tests/test_parallel_batch.py` & `tests/test_parallel_batch_extended.py`
- ✅ Added cleanup fixture with double `gc.collect()`
- ✅ **Windows-specific cleanup**: Longer delays (100ms) and more aggressive GC on Windows
- ✅ Reduced max_workers to 1 in all tests (was 2-4) to reduce resource contention
- ✅ Added `pytestmark = pytest.mark.parallel_batch` to mark tests for serial execution

### 3. `tests/conftest.py`
- ✅ Added session-scoped cleanup fixture
- ✅ **Enhanced cleanup**: 5 GC passes with longer delays on Windows
- ✅ Added thread monitoring to detect lingering threads
- ✅ Added `pytest_collection_modifyitems` hook to ensure parallel_batch tests run serially with pytest-xdist

### 4. `tests/parallel_executor_lock.py`
- ✅ Created global semaphore to limit concurrent executor creation
- ✅ **Windows-specific limit**: 1 concurrent executor on Windows (was 2) to avoid thread limits
- ✅ Platform-aware: 2 concurrent executors on other platforms

### 5. `pytest.ini`
- ✅ Added `parallel_batch` marker for tests that use parallel batch processing

---

## Current Status

- ✅ Individual tests pass
- ✅ Small groups of tests pass
- ⚠️ Full suite still hangs
- ⚠️ `test_parallel_batch.py` hangs when all tests run together

---

## Recommended Solutions

### Option 1: Limit Concurrent Executors (Recommended)
Add a semaphore or lock to limit concurrent ThreadPoolExecutor creation:

```python
# In conftest.py or a shared module
import threading
_executor_lock = threading.Semaphore(4)  # Max 4 concurrent executors

# In tests that use parallel_batch
with _executor_lock:
    result = batch_process(...)
```

### Option 2: Run Parallel Tests Serially
Add pytest marker and run parallel tests separately:

```python
# In test_parallel_batch.py
@pytest.mark.serial
class TestBatchProcess:
    ...
```

Then run: `pytest -m "not serial"` for most tests, `pytest -m serial` separately

### Option 3: Reduce max_workers in Tests
Limit max_workers to 1 or 2 in all tests to reduce resource contention:

```python
result = batch_process(..., max_workers=1)  # Instead of 2 or more
```

### Option 4: Use pytest-xdist with Isolation
If using pytest-xdist, ensure tests are properly isolated:

```bash
pytest -n auto --forked  # If pytest-forked available
```

### Option 5: Exclude Problematic Tests from Full Suite
Temporarily exclude `test_parallel_batch.py` from full suite runs until issue is resolved.

---

## Next Steps

1. **Try Option 3 first** (reduce max_workers in tests) - simplest fix
2. **Try Option 2** (mark tests as serial) - good for CI/CD
3. **Try Option 1** (semaphore) - most robust but requires code changes
4. **Monitor** which specific test causes the hang (if any)

---

## Test Files Using Parallel Execution

- `tests/test_parallel_batch.py` - 30+ tests using ThreadPoolExecutor
- `tests/test_parallel_batch_extended.py` - 19 tests using ThreadPoolExecutor
- `tests/test_optimization_utils.py` - May have resource issues
- Other tests may use parallel execution indirectly

---

*Last Updated: January 22, 2026*
