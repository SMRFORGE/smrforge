# Adding Benchmark Reference Values

This guide explains how to add benchmark reference values from various sources to the validation benchmark database.

---

## Overview

The validation framework supports benchmark values from three main sources:
1. **ANSI/ANS-5.1 Standards** - Decay heat benchmark values
2. **MCNP Calculations** - Gamma transport benchmark values
3. **IAEA Benchmark Problems** - Burnup benchmark values

---

## Quick Start

### Step 1: Create Template Files

Create template files for the benchmark format you want to use:

```bash
python scripts/add_benchmark_from_sources.py --create-templates templates/
```

This creates three template files:
- `templates/ansi_ans_template.json` - ANSI/ANS-5.1 format
- `templates/mcnp_template.json` - MCNP format
- `templates/iaea_template.json` - IAEA format

### Step 2: Fill in Benchmark Values

Edit the template files with actual benchmark values from your source:
- ANSI/ANS-5.1: Values from the ANSI/ANS-5.1 standard
- MCNP: Results from MCNP calculations
- IAEA: Values from IAEA benchmark problems

### Step 3: Add to Database

Add the benchmark values to the database:

```bash
# Add ANSI/ANS-5.1 benchmarks
python scripts/add_benchmark_from_sources.py --ansi-ans --file templates/ansi_ans_data.json --output benchmarks.json

# Add MCNP benchmarks
python scripts/add_benchmark_from_sources.py --mcnp --file templates/mcnp_data.json --output benchmarks.json --append

# Add IAEA benchmarks
python scripts/add_benchmark_from_sources.py --iaea --file templates/iaea_data.json --output benchmarks.json --append
```

---

## ANSI/ANS-5.1 Format

### Structure

```json
{
  "test_cases": [
    {
      "test_case": "u235_thermal_100mw",
      "nuclides": {"U235": 1e20},
      "initial_power": 100.0,
      "shutdown_time": 0.0,
      "time_points": [3600, 86400, 604800, 2592000],
      "benchmark_values": [
        {
          "value": 7.0,
          "uncertainty": 0.5,
          "unit": "MW",
          "source": "ANSI/ANS-5.1",
          "notes": "Decay heat at 1 hour after shutdown"
        }
      ]
    }
  ]
}
```

### Fields

- **test_case**: Unique identifier for the test case
- **nuclides**: Dictionary mapping nuclide names (e.g., "U235") to concentrations [atoms/cm³]
- **initial_power**: Initial reactor power [MW]
- **shutdown_time**: Time at shutdown [seconds]
- **time_points**: List of time points after shutdown [seconds]
- **benchmark_values**: List of benchmark values (one per time point)
  - **value**: Benchmark value [MW]
  - **uncertainty**: Uncertainty in benchmark value [MW] (optional)
  - **unit**: Unit of measurement (default: "MW")
  - **source**: Source of benchmark value (default: "ANSI/ANS-5.1")
  - **notes**: Additional notes (optional)

### Where to Find ANSI/ANS-5.1 Values

- ANSI/ANS-5.1 standard document (ANSI/ANS-5.1-2014)
- Standard decay heat tables
- Published validation studies

---

## MCNP Format

### Structure

```json
{
  "test_cases": [
    {
      "test_case": "simple_shielding",
      "geometry_description": "Cylindrical geometry, 10 cm radius, 20 cm height",
      "source_description": "Point source at center, 1 MeV gamma, 1e10 photons/s",
      "energy_groups": [0.1, 1.0, 10.0],
      "benchmark_flux": [
        {
          "value": 1e10,
          "uncertainty": 1e8,
          "unit": "photons/cm²/s",
          "source": "MCNP 6.2"
        }
      ],
      "benchmark_dose_rate": {
        "value": 1.23,
        "uncertainty": 0.01,
        "unit": "Sv/h",
        "source": "MCNP 6.2"
      },
      "reference_version": "6.2"
    }
  ]
}
```

### Fields

- **test_case**: Unique identifier for the test case
- **geometry_description**: Description of geometry
- **source_description**: Description of gamma source
- **energy_groups**: Energy group boundaries [MeV]
- **benchmark_flux**: List of benchmark flux values
  - **value**: Flux value
  - **uncertainty**: Uncertainty (optional)
  - **unit**: Unit (default: "photons/cm²/s")
  - **source**: Source (default: "MCNP")
- **benchmark_dose_rate**: Benchmark dose rate value
  - **value**: Dose rate value
  - **uncertainty**: Uncertainty (optional)
  - **unit**: Unit (default: "Sv/h")
  - **source**: Source (default: "MCNP")
- **reference_version**: MCNP version used (optional)

### Where to Find MCNP Values

- MCNP calculation results
- Published MCNP benchmark problems
- MCNP validation studies

---

## IAEA Format

### Structure

```json
{
  "test_cases": [
    {
      "test_case": "u235_pin_30days",
      "problem_description": "Simple UO2 fuel pin burnup problem - 30 days at constant power",
      "initial_composition": {"U235": 0.02, "U238": 0.98},
      "time_steps": [0, 30, 60, 90],
      "benchmark_k_eff": [
        {
          "value": 1.0,
          "uncertainty": 0.001,
          "unit": "",
          "source": "IAEA Benchmark"
        }
      ],
      "benchmark_compositions": [
        {"U235": 0.02, "U238": 0.98}
      ]
    }
  ]
}
```

### Fields

- **test_case**: Unique identifier for the test case
- **problem_description**: Description of benchmark problem
- **initial_composition**: Dictionary mapping nuclide names to initial atom fractions
- **time_steps**: List of time steps [days]
- **benchmark_k_eff**: List of benchmark k-eff values (one per time step)
  - **value**: k-eff value
  - **uncertainty**: Uncertainty (optional)
  - **unit**: Unit (default: "")
  - **source**: Source (default: "IAEA Benchmark")
- **benchmark_compositions**: List of benchmark compositions (one per time step) (optional)

### Where to Find IAEA Values

- IAEA benchmark problem specifications
- IAEA benchmark problem results
- Published IAEA benchmark studies

---

## Using Python API

You can also add benchmarks programmatically:

```python
from pathlib import Path
from tests.validation_benchmark_data import (
    BenchmarkDatabase,
    DecayHeatBenchmark,
    BenchmarkValue,
)

# Create or load database
db = BenchmarkDatabase(Path("benchmarks.json"))

# Add decay heat benchmark
benchmark = DecayHeatBenchmark(
    test_case="u235_shutdown",
    nuclides={"U235": 1e20},
    initial_power=100.0,
    shutdown_time=0.0,
    time_points=[3600, 86400],
    benchmark_values=[
        BenchmarkValue(
            value=7.0,
            uncertainty=0.5,
            unit="MW",
            source="ANSI/ANS-5.1",
        ),
        BenchmarkValue(
            value=4.5,
            uncertainty=0.4,
            unit="MW",
            source="ANSI/ANS-5.1",
        ),
    ],
)
db.add_decay_heat_benchmark(benchmark)

# Save database
db.save(Path("benchmarks.json"))
```

---

## Validation

After adding benchmarks, validate the database:

```bash
python scripts/add_benchmark_values.py validate benchmarks.json
```

---

## Using Benchmarks in Validation

Once benchmarks are added to the database, they can be used in validation:

```python
from pathlib import Path
from tests.validation_benchmark_data import BenchmarkDatabase
from tests.validation_benchmarks import ValidationBenchmarker
from smrforge.core.reactor_core import NuclearDataCache

# Load benchmark database
db = BenchmarkDatabase(Path("benchmarks.json"))

# Create benchmarker with database
cache = NuclearDataCache()
benchmarker = ValidationBenchmarker(cache, benchmark_database=db)

# Run validations (benchmarks will be automatically used for comparison)
# ...
```

---

## References

- ANSI/ANS-5.1-2014: "Decay Heat Power in Light Water Reactors"
- MCNP User Manual
- IAEA Benchmark Problem Specifications
