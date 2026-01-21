# Coverage Analysis Instructions

## Running Full Coverage Analysis

Due to the size of the test suite (4000+ tests), full coverage analysis can take 10-30+ minutes to complete.

### Quick Coverage Check (Fast)

For a quick summary without waiting for full completion:

```bash
# Windows PowerShell
python scripts/track_coverage.py --summary

# This reads from existing coverage_current.json if available
```

### Full Coverage Analysis (Complete)

To generate a fresh coverage report with all our recent test improvements:

```bash
# Windows PowerShell
pytest tests/ --cov=smrforge --cov-report=json:coverage.json --cov-report=term-missing

# Or use the script
python scripts/track_coverage.py --generate
```

**Note:** This may take 10-30+ minutes depending on system resources.

### Excluding Slow/Failing Tests

To speed up coverage analysis by excluding known slow tests:

```bash
pytest tests/ --cov=smrforge --cov-report=json:coverage.json `
    --ignore=tests/performance/test_performance_benchmarks.py `
    -m "not slow"
```

### Using Coverage Tracking Script

The `scripts/track_coverage.py` script provides automated coverage tracking:

```bash
# Generate new coverage and store in history
python scripts/track_coverage.py --generate

# Show summary of current/latest coverage
python scripts/track_coverage.py --summary

# Compare with previous run
python scripts/track_coverage.py --compare

# Generate trend report
python scripts/track_coverage.py --report
```

## Coverage Files

- `coverage.json` - Latest full coverage report
- `coverage_current.json` - Current run coverage (used by tracking script)
- `coverage_data/coverage_history.json` - Historical coverage data
- `htmlcov/` - HTML coverage report (if generated with `--cov-report=html`)

## Recent Improvements (Jan 2026)

The following modules have received significant test coverage improvements:

1. `utils/logging.py` - 27 new tests → ~75%+
2. `validation/regulatory_traceability.py` - 31 new tests → ~75%+
3. `validation/standards_parser.py` - 31 new tests → ~75%+
4. `geometry/validation.py` - 46 new tests → ~65-75%
5. `geometry/advanced_import.py` - 36 new tests → ~50-60%
6. `data_downloader.py` - 30 new tests → ~20-30%

**Total: 201 new tests added**

## Expected Coverage Impact

Based on documentation and recent improvements:
- **Documented Current:** 79.2% (with standard exclusions)
- **Target:** 80%
- **Gap:** ~83 statements (0.8%)

## Verifying Improvements

To see the impact of recent test additions, compare before and after:

```bash
# Generate new coverage
python scripts/track_coverage.py --generate

# Compare with previous
python scripts/track_coverage.py --compare
```

This will show the delta in coverage percentage and identify which modules improved.
