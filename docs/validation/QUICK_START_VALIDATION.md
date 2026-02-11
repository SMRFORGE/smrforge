# Quick Start: Running Validation Tests with ENDF Data

**Date:** January 2026  
**Status:** Ready to Execute

---

## Overview

This guide provides quick instructions for running validation tests with your ENDF-B-VIII.1 data located at:
```
C:\Users\cmwha\Downloads\ENDF-B-VIII.1
```

---

## Method 1: Using the Validation Script (Recommended)

The easiest way to run validation tests is using the provided validation runner script:

### Windows PowerShell:
```powershell
# Run all validation tests
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"

# Run with verbose output (see detailed progress)
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --verbose

# Run with custom output file (recommended: use output/validation/ to keep reports organized)
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --output output/validation/validation_report.txt --json-output output/validation/validation_report.json

# Run specific test files only
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --tests tests/test_validation_comprehensive.py
```

### Windows Command Prompt (CMD):
```cmd
python scripts\run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"
```

---

## Method 2: Using pytest Directly

You can also run pytest directly with the ENDF directory specified:

### Windows PowerShell:
```powershell
# Set environment variable and run tests
$env:LOCAL_ENDF_DIR = "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"
pytest tests/test_validation_comprehensive.py tests/test_endf_workflows_e2e.py -v

# Or in one line
$env:LOCAL_ENDF_DIR = "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"; pytest tests/test_validation_comprehensive.py -v
```

### Windows Command Prompt (CMD):
```cmd
set LOCAL_ENDF_DIR=C:\Users\cmwha\Downloads\ENDF-B-VIII.1
pytest tests\test_validation_comprehensive.py tests\test_endf_workflows_e2e.py -v
```

---

## Method 3: Using Python Environment Variable

Set the environment variable permanently or in your current session:

### PowerShell (Current Session):
```powershell
$env:LOCAL_ENDF_DIR = "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"
pytest tests/test_validation_comprehensive.py -v
```

### Command Prompt (Current Session):
```cmd
set LOCAL_ENDF_DIR=C:\Users\cmwha\Downloads\ENDF-B-VIII.1
pytest tests\test_validation_comprehensive.py -v
```

---

## What Tests Will Run?

The validation test suite includes:

1. **TSL (Thermal Scattering Law) Validation**
   - File discovery and parsing
   - S(α,β) interpolation accuracy
   - Cross-section generation

2. **ENDF Data Parsing**
   - Neutron cross-sections
   - Decay data
   - Fission yields
   - Photon atomic data
   - Gamma production data

3. **End-to-End Workflows**
   - Complete neutronics calculations
   - Burnup calculations
   - Decay heat calculations
   - Gamma transport

4. **Performance Benchmarking**
   - Timing measurements
   - Memory usage
   - Data loading performance

---

## Expected Output

When you run the validation tests, you should see:

1. **Test Discovery**: Tests will automatically discover ENDF files in your directory
2. **Test Execution**: Each test will run and validate different aspects of the ENDF data processing
3. **Results Summary**: A summary showing passed/failed tests
4. **Report Generation**: A validation report file (if using the script method)

### Example Output:
```
============================= test session starts ==============================
tests/test_validation_comprehensive.py::TestTSLValidationComprehensive::test_tsl_file_discovery PASSED
tests/test_validation_comprehensive.py::TestTSLValidationComprehensive::test_tsl_parsing PASSED
tests/test_endf_workflows_e2e.py::TestENDFFileDiscovery::test_neutron_file_discovery PASSED
...
============================= X passed, Y failed in Z.XXs ==============================
```

---

## Troubleshooting

### Issue: "ENDF directory not found"
**Solution**: Verify the path is correct:
```powershell
Test-Path "C:\Users\cmwha\Downloads\ENDF-B-VIII.1"
```

### Issue: "No ENDF files found"
**Solution**: Check that your ENDF directory has the expected subdirectories:
- `neutrons-version.VIII.1/`
- `decay-version.VIII.1/`
- `nfy-version.VIII.1/`
- `thermal_scatt-version.VIII.1/`
- `photoat-version.VIII.1/`
- `gammas-version.VIII.1/`

### Issue: Tests are skipped
**Solution**: The tests will skip if ENDF files are not found. Make sure:
1. The path is correct
2. The ENDF directory contains the expected subdirectories
3. The environment variable is set correctly (if using Method 2 or 3)

### Issue: Import errors
**Solution**: Make sure SMRForge is installed:
```powershell
pip install -e .
```

---

## Next Steps

After running validation tests:

1. **Review Results**: Check the test output for any failures
2. **Check Reports**: If using the script method, review the generated report file
3. **Add Benchmarks**: See `docs/validation/validation-execution-guide.md` for adding benchmark values
4. **Document Results**: Use the validation results template to document your findings

---

## Related Documentation

- **Full Guide**: `docs/validation/validation-execution-guide.md` - Complete validation guide
- **Test Documentation**: `docs/validation/endf-workflow-validation.md` - Test structure details
- **Validation Summary**: `docs/validation/validation-summary.md` - Overall validation status

---

## Validation Report Output

Validation reports are generated artifacts (not tracked in git). Recommended locations:

| Location | Use case |
|----------|----------|
| `output/validation/` | Keep reports organized (create directory first: `mkdir output\validation`) |
| `output/` | General output directory |
| Project root | Simple one-off runs (e.g. `validation_report.txt`) |

**Example with organized output:**
```powershell
mkdir -Force output\validation | Out-Null
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" `
  --output output/validation/validation_report.txt `
  --json-output output/validation/validation_report.json
```

---

## Quick Command Reference

```powershell
# Most common command (recommended)
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --verbose

# Quick test (just file discovery)
pytest tests/test_endf_workflows_e2e.py::TestENDFFileDiscovery -v -k "discovery"

# Full validation suite
python scripts/run_validation.py --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --output full_validation_report.txt --verbose
```

---

*This guide provides quick start instructions. For detailed information, see the full validation execution guide.*
