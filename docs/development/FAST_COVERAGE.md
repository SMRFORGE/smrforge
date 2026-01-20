# Fast Coverage Assessment Guide

## Quick Tips for Faster Coverage

### 1. Use Parallel Execution
pytest-xdist is already installed. Use `-n auto` to run tests in parallel:

```bash
# Quick coverage check (parallel, minimal output)
pytest -n auto --cov=smrforge --cov-report=term -q

# Full coverage with parallel execution
pytest -n auto --cov=smrforge --cov-report=term-missing
```

### 2. Use Convenience Scripts

**Quick Coverage Check** (fast, summary only):
```bash
# Linux/Mac
./scripts/coverage_quick.sh

# Windows PowerShell
.\scripts\coverage_quick.ps1
```

**Full Coverage Report** (slower, detailed):
```bash
# Linux/Mac
./scripts/coverage_full.sh

# Windows PowerShell
.\scripts\coverage_full.ps1
```

### 3. Test Specific Modules

Instead of running all tests, focus on specific modules:

```bash
# Test only utility modules
pytest -n auto --cov=smrforge.utils --cov-report=term tests/test_utils_*.py -q

# Test only CLI
pytest -n auto --cov=smrforge.cli --cov-report=term tests/test_cli.py -q

# Test specific file
pytest -n auto --cov=smrforge.utils.error_messages --cov-report=term tests/test_utils_error_messages.py -q
```

### 4. Skip Slow Tests

Use markers to skip slow tests during coverage checks:

```bash
# Skip slow/integration tests
pytest -n auto --cov=smrforge --cov-report=term -m "not slow" -q
```

### 5. Use Coverage Caching

Coverage.py caches results. Subsequent runs are faster:

```bash
# First run (slower)
pytest --cov=smrforge --cov-report=term

# Subsequent runs (faster due to caching)
pytest --cov=smrforge --cov-report=term
```

### 6. Minimal Coverage Reports

For quick checks, use minimal reporting:

```bash
# Just percentage (fastest)
pytest -n auto --cov=smrforge --cov-report=term -q

# JSON only (for scripts)
pytest -n auto --cov=smrforge --cov-report=json:coverage.json -q
```

### 7. Exclude Files from Coverage

Files excluded in `pytest.ini`:
- GUI modules (hard to test)
- Visualization modules
- Large parser files (tested separately)
- CLI (tested separately)

### Performance Comparison

| Method | Time | Detail Level |
|--------|------|--------------|
| `pytest --cov=smrforge --cov-report=term-missing` | ~5-10 min | Full detail |
| `pytest -n auto --cov=smrforge --cov-report=term-missing` | ~2-5 min | Full detail |
| `pytest -n auto --cov=smrforge --cov-report=term -q` | ~1-3 min | Summary only |
| `pytest -n auto --cov=smrforge.utils --cov-report=term -q` | ~30 sec | Module-specific |

### Recommended Workflow

1. **During Development**: Use quick checks on specific modules
   ```bash
   pytest -n auto --cov=smrforge.utils --cov-report=term tests/test_utils_*.py -q
   ```

2. **Before Committing**: Run full coverage on changed modules
   ```bash
   pytest -n auto --cov=smrforge --cov-report=term-missing tests/test_utils_*.py tests/test_help.py
   ```

3. **CI/CD**: Run full coverage report
   ```bash
   pytest -n auto --cov=smrforge --cov-report=term-missing --cov-report=html
   ```

### Troubleshooting

**If parallel execution causes issues:**
- Remove `-n auto` for sequential execution
- Some tests may need to run sequentially (use `pytest-xdist` markers)

**If coverage is too slow:**
- Use `--cov-report=term` instead of `--cov-report=term-missing`
- Test specific modules instead of entire codebase
- Use `-q` for quieter output
