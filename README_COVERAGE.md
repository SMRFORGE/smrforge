# Coverage Documentation Quick Reference

## Single Source of Truth

**📌 [COVERAGE_TRACKING.md](COVERAGE_TRACKING.md)** - Main coverage tracking document with current status, module breakdowns, test statistics, and coverage generation instructions.

## Historical Documentation

The following documents contain historical information and detailed implementation notes:

- **`COVERAGE_SURVEY_REPORT.md`** - Historical survey report (deprecated, see COVERAGE_TRACKING.md)
- **`docs/development/coverage-inventory.md`** - Detailed implementation history and roadmap
- **`docs/development/coverage-exclusions.md`** - Explanation of intentional exclusions
- **`docs/archive/coverage-improvements-2026-01.md`** - Historical improvements log

## Coverage Files

**Historical Coverage JSON Files:**
The repository contains multiple historical coverage JSON files:
- `coverage.json`, `coverage_final.json`, `coverage_current.json`
- `coverage_reactor.json`, `coverage_reactor_full.json`, `coverage_reactor_final.json`
- `coverage_uq.json`, `coverage_uq_full.json`
- `coverage_after_dedup.json`, `coverage_check.json`, `coverage_new_modules.json`

**⚠️ Important:** These are historical snapshots. To get current coverage:
```bash
pytest tests/ --cov=smrforge --cov-report=json:coverage.json
```

## Quick Start

1. **Check Current Coverage:**
   ```bash
   pytest tests/ --cov=smrforge --cov-report=term-missing -n auto
   ```

2. **Generate Detailed Report:**
   ```bash
   pytest tests/ --cov=smrforge --cov-report=html
   open htmlcov/index.html
   ```

3. **View Coverage Status:**
   - See `COVERAGE_TRACKING.md` for current status
   - See `docs/development/coverage-inventory.md` for detailed history

## Coverage Targets

- **Priority Modules:** 75-80% coverage
- **Overall Project:** 74.36% with standard exclusions ✅ **TARGET MET**
- **Core Modules:** 80-97% coverage ✅ **TARGET EXCEEDED**

For more details, see [COVERAGE_TRACKING.md](COVERAGE_TRACKING.md).
