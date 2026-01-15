# Adding Benchmark Values to Validation Database

**Last Updated:** January 2026  
**Status:** ✅ Complete - All utilities available

---

## Overview

The SMRForge validation framework supports comprehensive benchmarking against reference values from:
- **ANSI/ANS-5.1** standards (decay heat)
- **MCNP** comparisons (gamma transport)
- **IAEA benchmarks** (burnup and k-eff)

This guide explains how to add benchmark values to the validation database.

---

## Quick Start

### 1. Create a Template

Create a template benchmark file:

```bash
python scripts/add_benchmark_values.py create-template --output benchmarks_template.json
```

### 2. Add Benchmark Values

#### Interactive Addition (Decay Heat)

```bash
python scripts/add_benchmark_values.py add-decay-heat --file validation_benchmarks.json
```

Follow the interactive prompts to add decay heat benchmark values.

#### From JSON Files

```bash
# Add from ANSI/ANS-5.1 format
python scripts/add_benchmark_from_sources.py --ansi-ans input.json --output benchmarks.json

# Add from MCNP format
python scripts/add_benchmark_from_sources.py --mcnp input.json --output benchmarks.json

# Add from IAEA format
python scripts/add_benchmark_from_sources.py --iaea input.json --output benchmarks.json
```

### 3. Load Multiple Files

Load benchmark files from a directory:

```bash
python scripts/load_benchmark_references.py --dir benchmarks/ --output validation_benchmarks.json
```

---

## Detailed Instructions

### Decay Heat Benchmarks (ANSI/ANS-5.1)

Decay heat benchmarks follow the ANSI/ANS-5.1 standard format.

**Template Structure:**

```json
{
  "decay_heat_benchmarks": {
    "example_u235_shutdown": {
      "test_case": "example_u235_shutdown",
      "nuclides": {"U235": 1e20},
      "initial_power": 100.0,
      "shutdown_time": 0.0,
      "time_points": [3600, 86400, 604800],
      "benchmark_values": [
        {
          "value": 1.23,
          "uncertainty": 0.01,
          "unit": "MW",
          "source": "ANSI/ANS-5.1",
          "notes": "Reference value from ANSI/ANS-5.1 standard"
        }
      ],
      "standard": "ANSI/ANS-5.1"
    }
  }
}
```

**Adding Values:**

1. Use the interactive tool:
   ```bash
   python scripts/add_benchmark_values.py add-decay-heat --file benchmarks.json
   ```

2. Or edit JSON directly and load:
   ```bash
   python scripts/load_benchmark_references.py --file my_benchmarks.json --output benchmarks.json --append
   ```

### Gamma Transport Benchmarks (MCNP)

Gamma transport benchmarks compare against MCNP Monte Carlo results.

**Template Structure:**

```json
{
  "gamma_transport_benchmarks": {
    "example_simple_shielding": {
      "test_case": "example_simple_shielding",
      "geometry_description": "1m x 1m x 1m lead shield",
      "source_description": "Point source, 1 MeV gamma",
      "energy_groups": [0.1, 1.0, 10.0],
      "benchmark_flux": [
        {
          "value": 1e12,
          "uncertainty": 0.05,
          "unit": "photons/cm²/s",
          "source": "MCNP 6.2"
        }
      ],
      "benchmark_dose_rate": {
        "value": 1e-6,
        "uncertainty": 0.02,
        "unit": "Sv/h",
        "source": "MCNP 6.2"
      },
      "reference_code": "MCNP",
      "reference_version": "6.2"
    }
  }
}
```

**Adding Values:**

```bash
python scripts/add_benchmark_from_sources.py --mcnp mcnp_results.json --output benchmarks.json
```

### Burnup Benchmarks (IAEA)

Burnup benchmarks compare against IAEA benchmark problems.

**Template Structure:**

```json
{
  "burnup_benchmarks": {
    "example_simple_burnup": {
      "test_case": "example_simple_burnup",
      "problem_description": "Simple PWR pin cell",
      "initial_composition": {"U235": 0.02, "U238": 0.98},
      "time_steps": [0, 30, 60, 90],
      "benchmark_compositions": [
        {"U235": 0.0195, "U238": 0.9805}
      ],
      "benchmark_k_eff": [
        {
          "value": 1.00123,
          "uncertainty": 0.0001,
          "unit": "",
          "source": "IAEA Benchmark"
        }
      ],
      "reference_source": "IAEA"
    }
  }
}
```

**Adding Values:**

```bash
python scripts/add_benchmark_from_sources.py --iaea iaea_benchmark.json --output benchmarks.json
```

---

## Validation

Validate benchmark files before use:

```bash
python scripts/add_benchmark_values.py validate benchmarks.json
```

This checks:
- File structure is correct
- Required fields are present
- Data can be loaded into `BenchmarkDatabase`

---

## Integration with Validation Tests

Once benchmark values are added, use them in validation tests:

```python
from tests.validation_benchmark_data import BenchmarkDatabase
from smrforge.validation.validation_benchmarks import ValidationBenchmarker

# Load benchmark database
benchmark_db = BenchmarkDatabase("validation_benchmarks.json")

# Create benchmarker
benchmarker = ValidationBenchmarker(
    endf_dir=Path("~/ENDF-B-VIII.1"),
    benchmark_database=benchmark_db
)

# Run validation with benchmark comparison
results = benchmarker.run_all_tests()

# Compare with benchmarks
comparison = benchmarker.compare_with_benchmarks(results)
```

Or via CLI:

```bash
smrforge validate run \
    --endf-dir ~/ENDF-B-VIII.1 \
    --benchmarks validation_benchmarks.json \
    --output validation_report.txt
```

---

## Generating Reports

Generate validation reports with benchmark comparisons:

```bash
python scripts/generate_validation_report.py \
    --results validation_results.json \
    --benchmarks validation_benchmarks.json \
    --output validation_report.md
```

---

## Best Practices

1. **Use Templates**: Start with template files to ensure correct structure
2. **Validate Early**: Validate benchmark files before adding many values
3. **Document Sources**: Always include source information in benchmark values
4. **Include Uncertainties**: Provide uncertainty values when available
5. **Version Control**: Keep benchmark databases in version control
6. **Append Mode**: Use `--append` flag when adding to existing databases

---

## Example Workflow

```bash
# 1. Create template
python scripts/add_benchmark_values.py create-template --output my_benchmarks.json

# 2. Edit template with your benchmark values
# (Edit my_benchmarks.json manually)

# 3. Validate the file
python scripts/add_benchmark_values.py validate my_benchmarks.json

# 4. Load into main database
python scripts/load_benchmark_references.py \
    --file my_benchmarks.json \
    --output validation_benchmarks.json \
    --append

# 5. Run validation with benchmarks
smrforge validate run \
    --endf-dir ~/ENDF-B-VIII.1 \
    --benchmarks validation_benchmarks.json \
    --output report.txt

# 6. Generate detailed report
python scripts/generate_validation_report.py \
    --results report.txt \
    --benchmarks validation_benchmarks.json \
    --output validation_report.md
```

---

## Related Documentation

- **Validation Framework**: `docs/validation/validation-execution-guide.md`
- **Validation Implementation**: `docs/validation/validation-implementation-summary.md`
- **Benchmark Data Structures**: `tests/validation_benchmark_data.py`
- **Validation Scripts**: `scripts/run_validation.py`, `scripts/add_benchmark_values.py`

---

## Troubleshooting

### "File structure is invalid"

- Check that all required sections are present (`decay_heat_benchmarks`, `gamma_transport_benchmarks`, `burnup_benchmarks`)
- Verify JSON syntax is correct
- Use the template as a starting point

### "Benchmark not found in database"

- Ensure the benchmark database file is loaded correctly
- Check that test case names match exactly
- Use `BenchmarkDatabase` methods to inspect loaded benchmarks

### "Cannot load benchmark file"

- Verify file path is correct
- Check file permissions
- Ensure JSON is valid (use a JSON validator)

---

*For questions or issues, see the main validation documentation or create an issue on GitHub.*
