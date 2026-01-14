# Validation Results Report

**Date:** [Date]  
**SMRForge Version:** [Version]  
**ENDF Library:** ENDF-B-VIII.1  
**Validation Test Suite:** Comprehensive Validation Framework

---

## Executive Summary

**Overall Status:** [PASS/FAIL/PARTIAL]

- **Total Tests Run:** [Number]
- **Tests Passed:** [Number]
- **Tests Failed:** [Number]
- **Tests Skipped:** [Number]

**Key Findings:**
- [Summary of key validation results]
- [Any issues or discrepancies found]
- [Overall assessment of calculation accuracy]

---

## Test Results

### 1. File Discovery Tests

**Status:** [PASS/FAIL/SKIP]

| Test | Status | Notes |
|------|--------|-------|
| Neutron file discovery | [PASS/FAIL/SKIP] | [Notes] |
| Decay file discovery | [PASS/FAIL/SKIP] | [Notes] |
| Fission yield file discovery | [PASS/FAIL/SKIP] | [Notes] |
| TSL file discovery | [PASS/FAIL/SKIP] | [Notes] |
| Photon file discovery | [PASS/FAIL/SKIP] | [Notes] |
| Gamma production file discovery | [PASS/FAIL/SKIP] | [Notes] |

---

### 2. Data Parsing Tests

**Status:** [PASS/FAIL/SKIP]

| Test | Status | Data Points | Notes |
|------|--------|-------------|-------|
| Neutron cross-section parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |
| Decay data parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |
| Fission yield parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |
| TSL parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |
| Photon cross-section parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |
| Gamma production parsing | [PASS/FAIL/SKIP] | [Number] | [Notes] |

---

### 3. TSL Validation with Interpolation Accuracy

**Status:** [PASS/FAIL/SKIP]

**Test Materials:**
- [Material 1]: [Status] - [Notes]
- [Material 2]: [Status] - [Notes]

**Interpolation Accuracy:**
- Temperature points tested: [Number]
- Average interpolation error: [Value]%
- Maximum interpolation error: [Value]%

**Notes:**
[Any issues or observations]

---

### 4. Fission Yield Validation

**Status:** [PASS/FAIL/SKIP]

**Test Nuclides:**
- U-235: [Status] - [Notes]
- U-238: [Status] - [Notes]
- Pu-239: [Status] - [Notes]

**Validation Metrics:**
- Total yield sum: [Value] (expected: ~2.0)
- Independent yields: [Number]
- Cumulative yields: [Number]

---

### 5. Decay Heat Validation (ANSI/ANS Standard)

**Status:** [PASS/FAIL/SKIP]

**Test Cases:**

#### Test Case 1: [Description]
- Nuclides: [List]
- Time points: [List]
- Status: [PASS/FAIL/SKIP]

**Comparison with ANSI/ANS-5.1:**

| Time (s) | Calculated (W) | Benchmark (W) | Relative Error (%) | Status |
|----------|----------------|---------------|-------------------|--------|
| [Time] | [Value] | [Value] | [%] | [PASS/FAIL] |
| [Time] | [Value] | [Value] | [%] | [PASS/FAIL] |

**Accuracy Assessment:**
- Average relative error: [Value]%
- Maximum relative error: [Value]%
- All values within tolerance: [Yes/No]

---

### 6. Gamma Transport Benchmarking (MCNP Comparison)

**Status:** [PASS/FAIL/SKIP]

**Test Case:** [Description]
- Geometry: [Description]
- Source: [Description]
- Energy groups: [Number]

**Comparison with MCNP:**

| Metric | Calculated | MCNP | Relative Error (%) | Status |
|--------|------------|------|-------------------|--------|
| Max flux (photons/cm²/s) | [Value] | [Value] | [%] | [PASS/FAIL] |
| Dose rate (Sv/h) | [Value] | [Value] | [%] | [PASS/FAIL] |

**Accuracy Assessment:**
- [Assessment of agreement with MCNP]

---

### 7. Burnup Solver Reference Validation

**Status:** [PASS/FAIL/SKIP]

**Test Cases:**

#### Test Case 1: [Description]
- Problem: [Description]
- Time steps: [List]
- Status: [PASS/FAIL/SKIP]

**Comparison with Reference:**

| Time (days) | k-eff (calculated) | k-eff (reference) | Relative Error (%) | Status |
|-------------|-------------------|-------------------|-------------------|--------|
| [Time] | [Value] | [Value] | [%] | [PASS/FAIL] |
| [Time] | [Value] | [Value] | [%] | [PASS/FAIL] |

---

## Performance Benchmarking

### Timing Summary

| Test | Average Time (s) | Iterations |
|------|------------------|------------|
| TSL validation | [Value] | [Number] |
| Fission yield validation | [Value] | [Number] |
| Decay heat calculation | [Value] | [Number] |
| Gamma transport | [Value] | [Number] |
| Burnup solver | [Value] | [Number] |

**Total Validation Time:** [Value] seconds

---

## Accuracy Metrics Summary

### Decay Heat
- Average relative error: [Value]%
- Maximum relative error: [Value]%
- Tests within tolerance: [Number]/[Total]

### Gamma Transport
- Average relative error: [Value]%
- Maximum relative error: [Value]%
- Tests within tolerance: [Number]/[Total]

### Burnup
- Average relative error: [Value]%
- Maximum relative error: [Value]%
- Tests within tolerance: [Number]/[Total]

---

## Issues and Limitations

### Known Issues
- [List any known issues or limitations]

### Limitations
- [List any limitations in validation scope]

---

## Conclusions

[Summary of validation results and conclusions]

### Overall Assessment
[Overall assessment of calculation accuracy and reliability]

### Recommendations
- [Recommendations for improvements]
- [Recommendations for additional validation]

---

## Appendix

### Test Environment
- Python version: [Version]
- SMRForge version: [Version]
- ENDF library: ENDF-B-VIII.1
- Test date: [Date]

### Benchmark Data Sources
- Decay heat: ANSI/ANS-5.1 standard
- Gamma transport: MCNP [Version]
- Burnup: IAEA benchmarks / [Other sources]

### References
- [List references to standards and benchmarks used]

---

*This report was generated by the SMRForge validation framework.*
