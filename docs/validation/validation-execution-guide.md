# Validation Execution Guide

**Date:** January 2026  
**Status:** Framework Complete - Ready for Execution

---

## Overview

This guide describes how to execute validation tests with real ENDF files, add benchmark values, compare results, and document validation results.

---

## Prerequisites

### Required Software
- Python 3.8+
- SMRForge installed (`pip install -e .`)
- ENDF-B-VIII.1 library files
- pytest for running tests

### Required Data
- ENDF-B-VIII.1 directory with subdirectories:
  - `neutrons-version.VIII.1/`
  - `decay-version.VIII.1/`
  - `nfy-version.VIII.1/`
  - `thermal_scatt-version.VIII.1/`
  - `photoat-version.VIII.1/`
  - `gammas-version.VIII.1/`

### Optional (for Benchmarking)
- Reference benchmark values (ANSI/ANS standards, MCNP results, IAEA benchmarks)
- Comparison data from other codes

---

## Running Validation Tests

### Method 1: Using the Validation Runner Script

```bash
# Run all validation tests
python scripts/run_validation.py --endf-dir /path/to/ENDF-B-VIII.1

# Run with custom output file
python scripts/run_validation.py --endf-dir /path/to/ENDF-B-VIII.1 --output my_report.txt

# Run specific test files
python scripts/run_validation.py --endf-dir /path/to/ENDF-B-VIII.1 --tests tests/test_validation_comprehensive.py

# Verbose output
python scripts/run_validation.py --endf-dir /path/to/ENDF-B-VIII.1 --verbose
```

### Method 2: Using pytest Directly

```bash
# Run all validation tests
pytest tests/test_validation_comprehensive.py tests/test_endf_workflows_e2e.py -v

# Run specific test class
pytest tests/test_validation_comprehensive.py::TestTSLValidationComprehensive -v

# Run with ENDF directory environment variable
export LOCAL_ENDF_DIR=/path/to/ENDF-B-VIII.1
pytest tests/test_validation_comprehensive.py -v
```

### Method 3: Using ValidationBenchmarker in Python

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache
from tests.validation_benchmarks import ValidationBenchmarker

# Create cache with ENDF directory
cache = NuclearDataCache(local_endf_dir=Path("/path/to/ENDF-B-VIII.1"))

# Create benchmarker
benchmarker = ValidationBenchmarker(cache)

# Run validations
# (See test_validation_comprehensive.py for examples)

# Generate report
report = benchmarker.generate_report(output_file=Path("validation_report.txt"))
print(report)
```

---

## Adding Benchmark Values

### Step 1: Create Benchmark Data File

Create a JSON file with benchmark values (or use the provided structure):

```python
from tests.validation_benchmark_data import (
    BenchmarkDatabase,
    DecayHeatBenchmark,
    GammaTransportBenchmark,
    BurnupBenchmark,
    BenchmarkValue,
)

# Create database
db = BenchmarkDatabase()

# Add decay heat benchmark (ANSI/ANS-5.1)
decay_heat_bm = DecayHeatBenchmark(
    test_case="U235_shutdown_1day",
    nuclides={"U235": 1e20},
    initial_power=100.0,  # MW
    shutdown_time=0.0,  # seconds
    time_points=[3600, 86400, 604800],  # seconds
    benchmark_values=[
        BenchmarkValue(value=1.234, uncertainty=0.01, unit="MW", source="ANSI/ANS-5.1"),
        BenchmarkValue(value=0.567, uncertainty=0.005, unit="MW", source="ANSI/ANS-5.1"),
        BenchmarkValue(value=0.234, uncertainty=0.002, unit="MW", source="ANSI/ANS-5.1"),
    ],
)
db.add_decay_heat_benchmark(decay_heat_bm)

# Add gamma transport benchmark (MCNP)
gamma_bm = GammaTransportBenchmark(
    test_case="simple_shielding",
    geometry_description="Cylindrical geometry, 10 cm radius",
    source_description="Point source at center, 1 MeV gamma",
    energy_groups=[0.1, 1.0, 10.0],
    benchmark_flux=[
        BenchmarkValue(value=1e10, uncertainty=1e8, unit="photons/cm²/s", source="MCNP 6.2"),
    ],
    benchmark_dose_rate=BenchmarkValue(
        value=1.23, uncertainty=0.01, unit="Sv/h", source="MCNP 6.2"
    ),
    reference_code="MCNP",
    reference_version="6.2",
)
db.add_gamma_transport_benchmark(gamma_bm)

# Save database
db.save(Path("validation_benchmarks.json"))
```

### Step 2: Load and Use Benchmark Values

```python
from tests.validation_benchmark_data import BenchmarkDatabase, compare_with_benchmark

# Load database
db = BenchmarkDatabase(Path("validation_benchmarks.json"))

# Get benchmark
benchmark = db.decay_heat_benchmarks["U235_shutdown_1day"]

# Compare calculated value with benchmark
calculated_value = 1.245  # From your calculation
comparison = compare_with_benchmark(
    calculated_value,
    benchmark.benchmark_values[0],
    tolerance=0.05,  # 5% tolerance
)

print(f"Relative error: {comparison['relative_error_percent']:.2f}%")
print(f"Within tolerance: {comparison['within_tolerance']}")
```

---

## Comparing Results with Benchmarks

### Using Comparison Utilities

```python
from tests.validation_benchmark_data import compare_with_benchmark, BenchmarkValue

# Compare single value
calculated = 1.234
benchmark = BenchmarkValue(value=1.200, uncertainty=0.01, unit="MW")
comparison = compare_with_benchmark(calculated, benchmark, tolerance=0.05)

print(f"Calculated: {comparison['calculated']}")
print(f"Benchmark: {comparison['benchmark']}")
print(f"Relative error: {comparison['relative_error_percent']:.2f}%")
print(f"Within tolerance: {comparison['within_tolerance']}")
```

### Comparing Time Series

```python
import numpy as np
from tests.validation_benchmark_data import BenchmarkDatabase

db = BenchmarkDatabase(Path("validation_benchmarks.json"))
benchmark = db.decay_heat_benchmarks["U235_shutdown_1day"]

# Your calculated values
calculated_values = np.array([1.245, 0.570, 0.238])

# Compare at each time point
for i, (calc_val, bench_val) in enumerate(zip(calculated_values, benchmark.benchmark_values)):
    comparison = compare_with_benchmark(calc_val, bench_val)
    print(f"Time {benchmark.time_points[i]}s: Error = {comparison['relative_error_percent']:.2f}%")
```

---

## Documenting Validation Results

### Step 1: Use the Validation Results Template

Copy the template:
```bash
cp docs/validation/validation-results-template.md docs/validation/validation-results-YYYYMMDD.md
```

### Step 2: Fill in Results

1. Update executive summary with overall status
2. Fill in test results tables
3. Add comparison data with benchmarks
4. Document performance metrics
5. Add accuracy metrics summary
6. Document any issues or limitations
7. Add conclusions and recommendations

### Step 3: Generate Reports Programmatically

```python
from tests.validation_benchmarks import ValidationBenchmarker
from pathlib import Path

# Run validations and generate report
benchmarker = ValidationBenchmarker(cache)
# ... run validations ...

# Generate text report
report_text = benchmarker.generate_report(output_file=Path("validation_report.txt"))

# Generate JSON for further processing
import json
results_json = {
    "results": [
        {
            "test_name": r.test_name,
            "passed": r.passed,
            "message": r.message,
            "metrics": r.metrics,
            "timing": {
                "elapsed_time": r.timing.elapsed_time if r.timing else None,
                "average_time": r.timing.average_time if r.timing else None,
            } if r.timing else None,
        }
        for r in benchmarker.results
    ]
}
Path("validation_results.json").write_text(json.dumps(results_json, indent=2))
```

---

## Workflow Summary

1. **Prepare ENDF Files**
   - Download ENDF-B-VIII.1 if not available
   - Organize files in required directory structure

2. **Run Validation Tests**
   - Use validation runner script or pytest directly
   - Tests will skip gracefully if ENDF files not found

3. **Collect Benchmark Values** (if available)
   - Gather reference values from standards/benchmarks
   - Create benchmark database using provided structures
   - Save to JSON file for reuse

4. **Compare Results**
   - Use comparison utilities to compare calculated vs. benchmark values
   - Calculate relative errors and check tolerances
   - Generate comparison reports

5. **Document Results**
   - Fill in validation results template
   - Generate reports (text, JSON, markdown)
   - Document accuracy metrics and conclusions

---

## Next Steps

1. **Execute validation tests** when ENDF files are available
2. **Add benchmark values** as they become available from:
   - ANSI/ANS-5.1 standard (decay heat)
   - MCNP calculations (gamma transport)
   - IAEA benchmark problems (burnup)
3. **Compare results** and document accuracy
4. **Iterate** to improve accuracy if needed

---

## Related Documentation

- `docs/validation/validation-implementation-summary.md` - Framework implementation details
- `docs/validation/validation-summary.md` - Original validation summary
- `docs/validation/endf-workflow-validation.md` - Validation test documentation
- `tests/validation_benchmarks.py` - Validation utilities
- `tests/validation_benchmark_data.py` - Benchmark data structures
- `scripts/run_validation.py` - Validation runner script

---

*This guide provides the framework for validation execution. Actual execution requires ENDF files and benchmark data to be available.*
