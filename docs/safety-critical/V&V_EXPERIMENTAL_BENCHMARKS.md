# Full V&V Against Experimental Benchmarks (SC-1)

**Status:** Framework implemented; experimental benchmark comparison available.

## Overview

SMRForge provides a Verification & Validation (V&V) framework for comparing calculated results against experimental and published benchmark data.

## Benchmark Sources

| Source | Type | Usage |
|--------|------|-------|
| **ANSI/ANS-5.1** | Decay heat | `standards_parser.parse_ansi_ans_5_1()` |
| **IAEA benchmarks** | Burnup, k-eff | `standards_parser.parse_iaea_benchmark()` |
| **Community benchmarks** | Neutronics regression | `CommunityBenchmarkRunner` |
| **Validation benchmarks** | Cross-section, burnup | `BenchmarkDatabase`, `ValidationBenchmarker` |

## Running V&V

### 1. Community Benchmark Runner (neutronics)

```bash
python -c "
from smrforge.benchmarks import CommunityBenchmarkRunner
runner = CommunityBenchmarkRunner()
results = runner.run_all()
runner.generate_report(results, 'vv_report.md')
"
```

Or use the example:

```bash
python examples/community_benchmark_example.py
```

### 2. Full V&V Script

```bash
python scripts/run_vv_benchmarks.py --output vv_report.md
```

### 3. Validation Tests (with ENDF data)

```bash
pytest tests/test_validation_comprehensive.py -v
pytest tests/test_validation_benchmarks.py -v
```

## Benchmark Data Locations

- `benchmarks/community_benchmarks.json` - Neutronics regression (10+ cases)
- `benchmarks/validation_benchmarks.json` - Burnup, cross-section
- `docs/validation/benchmark_reference_values.json` - Reference values
- `tests/validation_benchmark_data.py` - Benchmark data structures

## Experimental Benchmark Integration

For full experimental V&V, integrate benchmark data from:

- **OECD-NEA** (https://www.oecd-nea.org/) - ICSBEP, IRPhEP
- **IAEA** - Benchmark problem libraries
- **ANSI/ANS-5.1** - Decay heat standard values

See `docs/validation/QUICK_START_VALIDATION.md` and `docs/validation/validation-execution-guide.md` for details.
