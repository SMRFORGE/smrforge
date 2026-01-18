# OpenMC Benchmarking and Validation Integration Plan

**Date:** January 2026  
**Status:** Analysis and Integration Plan  
**Reference:** [OpenMC GitHub Repository](https://github.com/openmc-dev/openmc)

---

## Executive Summary

This document examines how OpenMC ([GitHub](https://github.com/openmc-dev/openmc)) implements benchmarking and validation, and provides a concrete plan for integrating OpenMC's best practices into SMRForge to fulfill:

- **SMR_PAIN_POINTS_ASSESSMENT.md (227-230):** Validation Framework requirements
- **NEXT-FEATURES.md (135-136):** Standards Data Parser requirements

**Key Finding:** SMRForge already has a solid validation framework foundation. OpenMC's approaches can enhance it with:
1. **Automated regression testing** with CI/CD integration
2. **Benchmark model libraries** (ICSBEP, reactor physics benchmarks)
3. **Cross-code validation** (MCNP, Serpent comparisons)
4. **Structured benchmark schema** (YAML/JSON declarative definitions)
5. **Automated test discovery** and execution

---

## How OpenMC Does Benchmarking & Validation

### 1. Regression & Unit Test Suite

**OpenMC Approach:**
- Maintains both **unit tests** (isolated functionality) and **regression tests** (full simulations with cross-checked results)
- Tests include: building inputs (geometry, materials, tallies), running full code, comparing outcomes (k_eff, flux, tallies) to known reference values
- Automated CI pipelines run test suites on all pull requests and commits
- Tests cover different build configurations (MPI/OpenMP, different compilers, debug vs release)

**OpenMC Documentation:**
- [OpenMC Testing Guide](https://docs.openmc.org/en/latest/devguide/tests.html)
- Tests triggered on CI for stability assurance

### 2. Benchmark Model Libraries

**OpenMC Approach:**
- Uses benchmarks from **ICSBEP** (International Criticality Safety Benchmark Evaluation Project)
- Includes reactor physics benchmark repositories
- Cross-code comparisons (OpenMC vs MCNP, SERPENT)
- Comparisons to experimental data
- The `mit-crpg/benchmarks` repository includes multiple benchmark model inputs for OpenMC and other Monte Carlo codes

**Sources:**
- ICSBEP benchmarks: Standard criticality safety benchmarks
- Reactor physics benchmarks: Standard reactor physics problems
- `mit-crpg/benchmarks` on GitHub: Open-source benchmark models

### 3. Cross-Code Validation

**OpenMC Approach:**
- Validation against other codes (MCNP, SERPENT, experimental data)
- Examples: OPAL research reactor models compared between OpenMC, MCNP, SERPENT
- Spent fuel canister benchmarks: Comparing OpenMC with MCNP under identical configurations
- Differences typically <1% for key outputs (k_eff, leakage, etc.)

**References:**
- OPAL reactor cross-code comparison study
- Spent fuel canister benchmark comparisons

### 4. Nuclear Data Validation

**OpenMC Approach:**
- Processing and validation of nuclear data sources (ENDF/B-VIII) via NJOY/NJOY21
- Comparing simulation outputs on benchmarks (e.g., VVER-1200) to experimental benchmarks
- Cross-section generation wrappers that optimize energy group structures
- Validation of nuclear data libraries used in simulations

### 5. Automated Test Infrastructure

**OpenMC Approach:**
- CI/CD integration (GitHub Actions)
- Automated test discovery and execution
- Structured test framework with expected inputs and outputs
- Guidelines for contributing new tests

---

## SMRForge Current State

### ✅ Already Implemented

1. **Validation Framework Structure:**
   - `ValidationBenchmarker` class in `tests/validation_benchmarks.py`
   - `BenchmarkDatabase` class in `tests/validation_benchmark_data.py`
   - `ValidationResult` and `TimingResult` data structures
   - Comparison utilities (`compare_with_benchmark`)

2. **Standards Data Parser:**
   - `StandardsParser` class in `smrforge/validation/standards_parser.py`
   - Supports ANSI/ANS-5.1, IAEA benchmarks, MCNP reference data
   - Parsing utilities for JSON/YAML benchmark data
   - Integration with `BenchmarkDatabase`

3. **Benchmark Data Structures:**
   - `BenchmarkValue` (single value with uncertainty)
   - `DecayHeatBenchmark` (ANSI/ANS-5.1)
   - `GammaTransportBenchmark` (MCNP reference)
   - `BurnupBenchmark` (IAEA benchmarks)

4. **Validation Scripts:**
   - `scripts/run_validation.py` - Command-line validation runner
   - `scripts/generate_validation_report.py` - Report generation
   - `scripts/add_benchmark_values.py` - Adding benchmark values
   - `scripts/load_benchmark_references.py` - Loading benchmark references

5. **Validation Tests:**
   - `tests/test_validation_comprehensive.py` - Comprehensive test suite
   - `tests/test_k_eff_benchmarking.py` - k_eff benchmarking
   - Individual validation test files for each module

### ⚠️ Gaps Identified

1. **Automated Regression Testing:**
   - No automated CI/CD integration for validation tests
   - No "expected output" files for regression testing
   - No automated test discovery for benchmarks

2. **Benchmark Model Libraries:**
   - No curated benchmark model collection (similar to `mit-crpg/benchmarks`)
   - Limited SMR-specific benchmark problems
   - No standardized benchmark input formats

3. **Cross-Code Validation:**
   - No direct OpenMC integration for comparison
   - No automated cross-code validation workflows
   - Limited MCNP/Serpent comparison infrastructure

4. **Structured Benchmark Schema:**
   - No declarative YAML/JSON schema for benchmark definitions
   - Benchmarks are programmatically defined, not data-driven

5. **Test Infrastructure:**
   - No pytest fixtures for benchmark setup
   - No parameterized tests for benchmark suites
   - Limited automated test reporting

---

## Integration Plan: OpenMC → SMRForge

### Phase 1: Enhanced Benchmark Schema (2-3 weeks)

**Goal:** Adopt OpenMC-style declarative benchmark definitions

**Actions:**

1. **Define Benchmark Schema (YAML/JSON):**
   ```yaml
   # Example: benchmark_schema.yaml
   benchmark:
     name: "u235_criticality_smr"
     type: "criticality"
     description: "U-235 criticality benchmark for SMR"
     
     geometry:
       type: "prismatic_core"
       core_height: 200.0  # cm
       core_diameter: 100.0  # cm
     
     materials:
       fuel:
         enrichment: 0.195
         fuel_type: "UCO"
     
     solver:
       method: "diffusion"
       energy_groups: 4
       options:
         max_iterations: 100
         tolerance: 1e-5
     
     reference:
       value: 1.0002
       uncertainty: 0.0001
       source: "ICSBEP"
       code: "OpenMC"
       version: "0.13.0"
     
     validation:
       tolerance: 0.01  # 1%
       metrics: ["k_eff"]
   ```

2. **Implement Benchmark Loader:**
   - Extend `StandardsParser` to support YAML/JSON schema
   - Auto-generate SMRForge inputs from schema
   - Support OpenMC-style benchmark directory structure

3. **Create Benchmark Collection:**
   - Start with 5-10 SMR-specific benchmark problems
   - Include criticality, burnup, and thermal benchmarks
   - Store in `validation/benchmarks/` directory

**Files to Create/Modify:**
- `smrforge/validation/benchmark_schema.py` - Schema definition
- `smrforge/validation/benchmark_loader.py` - YAML/JSON loader
- `validation/benchmarks/` - Benchmark collection directory

### Phase 2: Automated Regression Testing (2-3 weeks)

**Goal:** Implement OpenMC-style automated regression testing

**Actions:**

1. **Create Expected Output Files:**
   - Store reference results in JSON/YAML files
   - Version control expected outputs
   - Structure: `validation/benchmarks/<name>/expected_output.json`

2. **Implement Regression Test Framework:**
   ```python
   # Example: tests/test_regression.py
   @pytest.mark.parametrize("benchmark_name", get_benchmark_names())
   def test_benchmark_regression(benchmark_name):
       """Test that benchmark results match expected outputs."""
       benchmark = load_benchmark(benchmark_name)
       results = run_benchmark(benchmark)
       expected = load_expected_output(benchmark_name)
       assert_benchmark_match(results, expected, tolerance=0.01)
   ```

3. **Add CI/CD Integration:**
   - GitHub Actions workflow for running regression tests
   - Compare results against expected outputs
   - Fail on significant deviations (>tolerance)

**Files to Create/Modify:**
- `tests/test_regression.py` - Regression test suite
- `.github/workflows/validation.yml` - CI/CD workflow
- `validation/benchmarks/**/expected_output.json` - Expected outputs

### Phase 3: OpenMC Integration for Cross-Code Validation (3-4 weeks)

**Goal:** Enable direct comparison with OpenMC results

**Actions:**

1. **OpenMC Model Export:**
   - Extend `OpenMCConverter` to export full OpenMC models
   - Support geometry, materials, tallies export
   - Generate OpenMC Python scripts for execution

2. **OpenMC Result Import:**
   - Import OpenMC HDF5 results (statepoint files)
   - Parse k_eff, flux, tallies from OpenMC outputs
   - Compare with SMRForge results

3. **Automated Cross-Code Comparison:**
   ```python
   def compare_with_openmc(smrforge_results, openmc_results, tolerance=0.01):
       """Compare SMRForge results with OpenMC results."""
       comparison = {
           "k_eff_diff": smrforge_results.k_eff - openmc_results.k_eff,
           "k_eff_relative_error": abs(comparison["k_eff_diff"]) / openmc_results.k_eff,
           "flux_correlation": np.corrcoef(smrforge_results.flux, openmc_results.flux),
           "within_tolerance": comparison["k_eff_relative_error"] < tolerance
       }
       return comparison
   ```

4. **Cross-Code Validation Script:**
   - `scripts/compare_with_openmc.py` - Compare SMRForge vs OpenMC
   - Support batch comparison across multiple benchmarks

**Files to Create/Modify:**
- `smrforge/io/openmc_comparison.py` - OpenMC comparison utilities
- `smrforge/io/converters.py` - Enhance `OpenMCConverter`
- `scripts/compare_with_openmc.py` - Comparison script
- `tests/test_openmc_comparison.py` - Cross-code validation tests

### Phase 4: Benchmark Model Library (2-3 weeks)

**Goal:** Create SMR-specific benchmark collection

**Actions:**

1. **Curate SMR Benchmarks:**
   - Criticality benchmarks (ICSBEP SMR-like problems)
   - Burnup benchmarks (IAEA burnup benchmarks)
   - Thermal benchmarks (standard thermal problems)
   - Transient benchmarks (safety transients)

2. **Standardize Benchmark Format:**
   - Use YAML schema from Phase 1
   - Include metadata (source, version, date)
   - Include expected outputs

3. **Create Benchmark Index:**
   - `validation/benchmarks/README.md` - Benchmark catalog
   - `validation/benchmarks/index.yaml` - Machine-readable index

**Files to Create:**
- `validation/benchmarks/criticality/` - Criticality benchmarks
- `validation/benchmarks/burnup/` - Burnup benchmarks
- `validation/benchmarks/thermal/` - Thermal benchmarks
- `validation/benchmarks/index.yaml` - Benchmark index

### Phase 5: Enhanced Test Infrastructure (1-2 weeks)

**Goal:** Improve test infrastructure with OpenMC patterns

**Actions:**

1. **Pytest Fixtures:**
   ```python
   @pytest.fixture
   def benchmark_database():
       """Load benchmark database for tests."""
       return BenchmarkDatabase(data_file="validation/benchmarks/benchmarks.json")
   
   @pytest.fixture
   def standards_parser():
       """Standards parser for tests."""
       return StandardsParser()
   ```

2. **Parameterized Tests:**
   - Use `@pytest.mark.parametrize` for benchmark suites
   - Support test discovery from benchmark directory

3. **Test Reporting:**
   - Enhanced validation report generation
   - HTML reports with plots
   - Comparison tables (SMRForge vs OpenMC vs Expected)

**Files to Modify:**
- `tests/conftest.py` - Pytest fixtures
- `tests/test_validation_comprehensive.py` - Parameterized tests
- `scripts/generate_validation_report.py` - Enhanced reporting

---

## Implementation Details

### 1. Benchmark Schema Definition

**File:** `smrforge/validation/benchmark_schema.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class BenchmarkType(Enum):
    CRITICALITY = "criticality"
    BURNUP = "burnup"
    THERMAL = "thermal"
    TRANSIENT = "transient"
    DECAY_HEAT = "decay_heat"

@dataclass
class BenchmarkSchema:
    """Declarative benchmark schema (OpenMC-style)."""
    name: str
    type: BenchmarkType
    description: str
    geometry: Dict[str, Any]
    materials: Dict[str, Any]
    solver: Dict[str, Any]
    reference: Dict[str, Any]  # Expected outputs
    validation: Dict[str, Any]  # Tolerance, metrics
    metadata: Optional[Dict[str, Any]] = None
```

### 2. Benchmark Loader

**File:** `smrforge/validation/benchmark_loader.py`

```python
import yaml
from pathlib import Path
from typing import Dict, Any
from .benchmark_schema import BenchmarkSchema

def load_benchmark(benchmark_file: Path) -> BenchmarkSchema:
    """Load benchmark from YAML/JSON file (OpenMC-style)."""
    data = yaml.safe_load(benchmark_file.read_text())
    return BenchmarkSchema(**data)

def run_benchmark(benchmark: BenchmarkSchema) -> Dict[str, Any]:
    """Run benchmark and return results."""
    # Auto-generate SMRForge inputs from schema
    # Run calculation
    # Return results
    pass
```

### 3. OpenMC Comparison Utilities

**File:** `smrforge/io/openmc_comparison.py`

```python
import h5py
import numpy as np
from typing import Dict, Any
from pathlib import Path

def load_openmc_statepoint(statepoint_file: Path) -> Dict[str, Any]:
    """Load OpenMC statepoint file (HDF5)."""
    with h5py.File(statepoint_file, 'r') as f:
        k_eff = f['k_combined'][:]
        flux = f['tallies/tally_1/mean'][:]
        return {"k_eff": k_eff, "flux": flux}

def compare_smrforge_openmc(
    smrforge_results: Dict[str, Any],
    openmc_results: Dict[str, Any],
    tolerance: float = 0.01
) -> Dict[str, Any]:
    """Compare SMRForge results with OpenMC results."""
    k_eff_diff = smrforge_results["k_eff"] - openmc_results["k_eff"]
    k_eff_rel_error = abs(k_eff_diff) / openmc_results["k_eff"]
    
    return {
        "k_eff_diff": k_eff_diff,
        "k_eff_relative_error": k_eff_rel_error,
        "within_tolerance": k_eff_rel_error < tolerance,
        "flux_correlation": np.corrcoef(
            smrforge_results["flux"],
            openmc_results["flux"]
        )[0, 1] if "flux" in both else None
    }
```

---

## Benefits of Integration

### 1. Fulfills SMR_PAIN_POINTS Requirements (227-230)

✅ **Validation Framework:**
- Benchmark comparison structure ✅ (Enhanced with OpenMC patterns)
- Accuracy metrics tracking ✅ (Added cross-code comparison)
- Report generation ✅ (Enhanced with comparison reports)

### 2. Fulfills NEXT-FEATURES Requirements (135-136)

✅ **Standards Data Parser:**
- Standards parser implemented ✅ (Enhanced with YAML schema support)
- Benchmark integration complete ✅ (Added OpenMC-style benchmarks)

### 3. Additional Benefits

1. **Reproducibility:** Declarative benchmarks ensure reproducibility
2. **Cross-Validation:** OpenMC comparison provides independent validation
3. **Automation:** CI/CD integration ensures continuous validation
4. **Extensibility:** Schema-based approach makes adding benchmarks easy
5. **Documentation:** Benchmark collection serves as documentation

---

## Timeline and Resources

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Benchmark Schema | 2-3 weeks | High | None |
| Phase 2: Regression Testing | 2-3 weeks | High | Phase 1 |
| Phase 3: OpenMC Integration | 3-4 weeks | Medium | Phase 1, Phase 2 |
| Phase 4: Benchmark Library | 2-3 weeks | Medium | Phase 1 |
| Phase 5: Test Infrastructure | 1-2 weeks | Low | Phase 2 |

**Total Estimated Effort:** 10-15 weeks

---

## Next Steps

1. **Review and Approve Plan** - Get stakeholder approval
2. **Phase 1 Implementation** - Start with benchmark schema
3. **Create Initial Benchmarks** - Add 5-10 SMR benchmarks
4. **Set Up CI/CD** - Integrate automated testing
5. **Documentation** - Update validation documentation

---

## References

- **OpenMC Repository:** https://github.com/openmc-dev/openmc
- **OpenMC Documentation:** https://docs.openmc.org/
- **OpenMC Testing Guide:** https://docs.openmc.org/en/latest/devguide/tests.html
- **mit-crpg/benchmarks:** https://github.com/mit-crpg/benchmarks
- **ICSBEP:** International Criticality Safety Benchmark Evaluation Project
- **OpenMC Fusion Benchmarks:** https://openmc-fusion-benchmarks.readthedocs.io/ (schema examples)

---

**Status:** Ready for implementation  
**Last Updated:** January 2026
