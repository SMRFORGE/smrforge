# Coverage Archive (Historical Reference)

**⚠️ Deprecated: For current coverage status, see [COVERAGE_TRACKING.md](../../../COVERAGE_TRACKING.md)**

This document consolidates historical coverage notes from January 2026. Original files were merged during the Feb 2026 reorganization.

---

## Archive Contents

### Run Instructions (historical)

- **Quick check:** `python scripts/track_coverage.py --summary`
- **Full run:** `pytest tests/ --cov=smrforge --cov-report=json:coverage/generated/coverage.json --cov-report=term-missing`
- **Tracking:** `scripts/track_coverage.py` — `--generate`, `--summary`, `--compare`, `--report`

### Analysis Summary (Jan 2026)

- 201 new tests across 6 modules: `utils/logging`, `validation/regulatory_traceability`, `validation/standards_parser`, `geometry/validation`, `geometry/advanced_import`, `data_downloader`
- Documented baseline ~74–79% with standard exclusions; target 80%
- Modules improved: logging ~75%+, validation modules ~75%+, geometry 50–75%, data_downloader ~20–30%

### Completion Summary (Jan 20, 2026)

- 215 new tests added
- Modules: logging, regulatory_traceability, standards_parser, geometry/validation, geometry/advanced_import, data_downloader, control/integration, core/self_shielding_integration
- Documented ~79.2% current; gap ~0.8% to 80%

### Consolidation Summary (Jan 2026)

- `COVERAGE_TRACKING.md` established as single source of truth
- `README_COVERAGE.md` created as quick reference
- Historical JSON files documented (now archived as `coverage/archive/json/latest.json`)

### Implementation Status (Jan 20, 2026)

- Scripts: `track_coverage.py`, `analyze_coverage.py`
- Test improvements in place; full coverage run ~10–30 min
- Fresh run needed to verify improvements

### Improvements Implemented (Jan 2026)

- `utils/logging.py`: 27 tests → ~75%+
- `validation/regulatory_traceability.py`: 31 tests → ~75%+
- `validation/standards_parser.py`: 31 tests → ~75%+
- `geometry/validation.py`: 46 tests → ~65–75%
- `geometry/advanced_import.py`: 36 tests → ~50–60%
- `data_downloader.py`: 30 tests → ~20–30%
- Additional: control/integration, core/self_shielding_integration

### Status as of Jan 20, 2026

- Baseline: 61.25% (older report); estimated after improvements: ~79.2%+
- Target 80%; gap ~0.8% (~83 statements)

### Survey Report (historical)

- Full project: ~62%; with exclusions: ~74%
- Gap to 80%: ~5.64% with standard exclusions
- Deprecated; COVERAGE_TRACKING.md is authoritative

---

## JSON Archive

- **`coverage/archive/json/latest.json`** — Single retained historical snapshot
- For current coverage, generate fresh: `scripts/coverage_full.ps1` → `coverage/generated/coverage.json`
