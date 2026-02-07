# Coverage Documentation Quick Reference

## Single Source of Truth

**📌 [COVERAGE_TRACKING.md](COVERAGE_TRACKING.md)** - Main coverage tracking document with current status, module breakdowns, test statistics, and coverage generation instructions.

## Historical Documentation

The following documents contain historical information and detailed implementation notes:

- **`coverage/archive/docs/`** - Archived historical coverage notes (kept for context)
- **`coverage/archive/docs/COVERAGE_SURVEY_REPORT.md`** - Historical survey report (deprecated, see COVERAGE_TRACKING.md)
- **`docs/archive/coverage-inventory-archived-2026-01-29.md`** - Archived; see COVERAGE_TRACKING.md for current status
- **`docs/development/coverage-exclusions.md`** - Explanation of intentional exclusions
- **`docs/archive/coverage-improvements-2026-01.md`** - Historical improvements log

## Coverage Files

**Historical Coverage JSON Files (archived):**
The repository keeps older coverage snapshots under `coverage/archive/json/` (useful for forensic comparisons, but often stale).

**⚠️ Important:** Generate fresh coverage for the current state. Recommended output location:
```bash
pytest tests/ --cov=smrforge --cov-report=json:coverage/generated/coverage.json
```

## Quick Start

1. **Check Current Coverage:**
   ```bash
   pytest tests/ --cov=smrforge --cov-report=term-missing -n auto
   ```

2. **Generate Detailed Report:**
   ```bash
    pytest tests/ --cov=smrforge --cov-report=html:coverage/generated/htmlcov
    open coverage/generated/htmlcov/index.html
   ```

3. **View Coverage Status:**
   - See `COVERAGE_TRACKING.md` for current status
   - See `COVERAGE_TRACKING.md` for detailed history
   - On Windows/OneDrive, see `docs/development/testing-and-coverage.md` for a coverage workaround that avoids `pytest-cov` file-lock issues.

## Coverage Targets

- **Priority Modules:** 75-80% coverage
- **Overall Project:** ~89.7% with standard exclusions (Jan 29 run) — **Target: 90%**
- **Core Modules:** 80-97% coverage ✅ **TARGET EXCEEDED**

For more details, see [COVERAGE_TRACKING.md](COVERAGE_TRACKING.md).
