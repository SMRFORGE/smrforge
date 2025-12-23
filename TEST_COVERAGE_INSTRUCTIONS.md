# Test Coverage Instructions

This document explains how to check test coverage for SMRForge.

## Prerequisites

Install pytest and coverage:

```bash
pip install pytest pytest-cov
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Check Coverage

### Run Tests with Coverage

```bash
pytest --cov=smrforge --cov-report=html
```

This will:
- Run all tests
- Generate coverage report
- Create HTML report in `htmlcov/index.html`

### View HTML Report

Open `htmlcov/index.html` in your web browser to see:
- Overall coverage percentage
- Coverage by module
- Line-by-line coverage details

### Terminal Report

For a quick terminal report:

```bash
pytest --cov=smrforge --cov-report=term-missing
```

This shows:
- Coverage percentage per module
- Missing lines (if any)

### XML Report (for CI/CD)

For CI/CD integration:

```bash
pytest --cov=smrforge --cov-report=xml
```

Generates `coverage.xml` for tools like Codecov.

## Coverage Targets

**Target: 80%+ coverage on critical modules**

Critical modules:
- `smrforge.neutronics.solver` - Core solver
- `smrforge.validation.models` - Validation framework
- `smrforge.core.reactor_core` - Nuclear data handling

## CI/CD Integration

The GitHub Actions CI pipeline automatically:
- Runs tests with coverage
- Uploads coverage to Codecov (if configured)

See `.github/workflows/ci.yml` for details.

## Improving Coverage

To improve coverage:

1. **Identify gaps:**
   ```bash
   pytest --cov=smrforge --cov-report=term-missing
   ```

2. **Add tests for uncovered code:**
   - Focus on critical modules first
   - Add edge case tests
   - Add integration tests

3. **Re-run coverage:**
   ```bash
   pytest --cov=smrforge --cov-report=html
   ```

## Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[coverage:run]
source = smrforge
omit =
    */tests/*
    */test_*
    */__pycache__/*
```

## Notes

- **Current Status**: Test coverage needs to be verified
- **Goal**: 80%+ on critical modules
- **CI/CD**: Coverage reports are generated automatically in GitHub Actions

## Next Steps

1. Run coverage check: `pytest --cov=smrforge --cov-report=html`
2. Review `htmlcov/index.html` to see current coverage
3. Identify modules with low coverage
4. Add tests to improve coverage
5. Re-run coverage check

