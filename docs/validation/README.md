# Validation Documentation

This directory contains documentation and utilities for validation and benchmarking of SMRForge calculations.

---

## Quick Start

1. **Run Validation Tests:**
   ```bash
   python scripts/run_validation.py --endf-dir /path/to/ENDF-B-VIII.1
   ```

2. **Add Benchmark Values:**
   ```bash
   # Create templates for different benchmark sources
   python scripts/add_benchmark_from_sources.py --create-templates templates/
   
   # Add benchmarks from ANSI/ANS-5.1, MCNP, or IAEA formats
   python scripts/add_benchmark_from_sources.py --ansi-ans --file ansi_data.json --output benchmarks.json
   python scripts/add_benchmark_from_sources.py --mcnp --file mcnp_data.json --output benchmarks.json --append
   python scripts/add_benchmark_from_sources.py --iaea --file iaea_data.json --output benchmarks.json --append
   
   # Validate benchmark database
   python scripts/add_benchmark_values.py validate benchmarks.json
   ```
   See `adding-benchmark-values.md` for detailed instructions.

3. **Generate Validation Report:**
   ```bash
   python scripts/generate_validation_report.py --results results.json --benchmarks benchmarks.json --output report.md
   ```

---

## Documentation Files

### Framework Documentation
- **`validation-summary.md`** - Original validation summary
- **`endf-workflow-validation.md`** - Validation test documentation
- **`validation-implementation-summary.md`** - Comprehensive framework implementation
- **`validation-execution-implementation.md`** - Execution framework implementation

### Execution Guides
- **`validation-execution-guide.md`** - Complete guide for running validation, adding benchmarks, comparing results, and documenting

### Templates
- **`validation-results-template.md`** - Template for validation results reports
- **`benchmark_data_examples.json`** - Example benchmark data structures

---

## Key Utilities

### Validation Runner
- **Script:** `scripts/run_validation.py`
- **Purpose:** Run validation tests with ENDF files
- **Usage:** See `validation-execution-guide.md`

### Benchmark Management
- **Script:** `scripts/add_benchmark_values.py`
- **Purpose:** Add and manage benchmark values
- **Features:**
  - Create template benchmark files
  - Interactively add benchmarks
  - Validate benchmark data files

### Report Generation
- **Script:** `scripts/generate_validation_report.py`
- **Purpose:** Generate validation results reports
- **Features:**
  - Generate markdown reports
  - Compare with benchmarks
  - Document accuracy metrics

### Benchmark Data Structures
- **Module:** `tests/validation_benchmark_data.py`
- **Purpose:** Data structures and utilities for benchmark values
- **Features:**
  - Benchmark database
  - Comparison utilities
  - JSON serialization

---

## Workflow

1. **Run Validation Tests**
   - Use `scripts/run_validation.py` to execute tests
   - Tests will skip gracefully if ENDF files not available

2. **Add Benchmark Values**
   - Create template: `python scripts/add_benchmark_values.py create-template`
   - Add values from ANSI/ANS-5.1, MCNP, IAEA benchmarks
   - Validate: `python scripts/add_benchmark_values.py validate benchmarks.json`

3. **Compare Results**
   - Use comparison utilities from `validation_benchmark_data.py`
   - Compare calculated values with benchmarks
   - Calculate relative errors and accuracy metrics

4. **Document Results**
   - Use `validation-results-template.md` as a template
   - Generate reports with `scripts/generate_validation_report.py`
   - Document accuracy metrics and conclusions

---

## Benchmark Data Sources

### Decay Heat
- **Standard:** ANSI/ANS-5.1
- **Source:** American Nuclear Society standard for decay heat
- **Usage:** Compare decay heat calculations at various time points

### Gamma Transport
- **Reference Code:** MCNP
- **Source:** MCNP Monte Carlo calculations
- **Usage:** Compare gamma flux and dose rate calculations

### Burnup
- **Reference:** IAEA Benchmark Problems
- **Source:** International Atomic Energy Agency benchmark problems
- **Usage:** Compare burnup calculations and k-effective evolution

---

## Example Files

- **`benchmark_data_examples.json`** - Example structures for benchmark data
- See `validation-execution-guide.md` for usage examples

---

## Related Documentation

- Development Roadmap: SMRForge-Private/roadmaps/development-roadmap.md (local)
- Validation Implementation: `docs/validation/validation-implementation-summary.md`
- Execution Guide: `docs/validation/validation-execution-guide.md`

---

*For detailed instructions, see `validation-execution-guide.md`*
