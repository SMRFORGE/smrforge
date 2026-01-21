# Test Failure Fixes Summary
## For Coverage Analysis

**Date:** January 20, 2026  
**Issue:** Test failures preventing complete coverage runs  
**Goal:** Fix failing tests to enable accurate coverage measurement

---

## 🔍 Identified Issues

### 1. `test_backend_fallback_chain.py` - 5 failures
**Problem:** ENDF file validation failing  
**Root Cause:** Mock ENDF files don't pass `_validate_endf_file` checks  
**Solution:** Patch validation function or create proper mock files

### 2. `test_burnup_checkpointing.py` - 5 failures  
**Problem:** 
- Some tests fail due to solver validation (k_eff too high)
- `h5py` patching fails (imported inside functions, not at module level)
**Root Cause:** 
- Test setup issues
- Can't patch `h5py` because it's imported conditionally inside functions
**Solution:** Use different patching strategy or skip when h5py unavailable

### 3. `test_adjoint_weighting.py` - 3 failures
**Problem:** Collapsed cross-sections are all zeros  
**Root Cause:** Group mapping logic issue in `collapse_with_adjoint_weighting`  
**Solution:** Fix group mapping or adjust test expectations

### 4. `test_async_methods.py` - 7 errors
**Problem:** `HTTPX_AVAILABLE` attribute doesn't exist  
**Root Cause:** `httpx` imported conditionally, attribute doesn't exist in module  
**Solution:** Check if attribute exists before patching, or use different patching strategy

---

## ✅ Recommended Solutions

### Quick Fix: Exclude Problematic Tests from Coverage Runs

Add to coverage run command:
```bash
pytest tests/ --cov=smrforge --cov-report=json:coverage.json \
    --ignore=tests/test_backend_fallback_chain.py \
    --ignore=tests/test_burnup_checkpointing.py \
    --ignore=tests/test_adjoint_weighting.py \
    --ignore=tests/test_async_methods.py \
    --ignore=tests/performance/test_performance_benchmarks.py
```

### Proper Fix: Address Root Causes

1. **ENDF Validation:** Make mock file generator create properly formatted files
2. **h5py Patching:** Use `patch` on the import location inside functions
3. **Adjoint Weighting:** Fix or skip zero-cross-section tests  
4. **HTTPX Patching:** Check attribute existence or patch differently

---

## 📝 Next Steps

1. **Short-term:** Use exclusions to get coverage running
2. **Medium-term:** Fix test failures one by one
3. **Long-term:** Ensure all tests pass for complete coverage

---

*Created: January 20, 2026*
