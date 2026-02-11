# Coverage

This directory is the entry point for test coverage in SMRForge.

## Quick Start

### Run coverage

```powershell
# Quick check (fast, parallel)
.\scripts\coverage_quick.ps1

# Full report (HTML + JSON, term-missing)
.\scripts\coverage_full.ps1
```

On Linux/macOS, use `./scripts/coverage_quick.sh` or `./scripts/coverage_full.sh`.

### Where output goes

All generated coverage artifacts go to:

- **`coverage/generated/`** — HTML report (`htmlcov/index.html`), JSON reports (`coverage.json`, `coverage_quick.json`)

This directory is gitignored; generate reports locally.

## Configuration

| File | Purpose |
|------|---------|
| `.coveragerc` (root) | Main coverage config (exclusions, fail_under=90) |
| `coverage/config/.coveragerc.cli` | CLI-only coverage runs |
| `coverage/config/.coveragerc-full` | Full-project 100% target runs |
| `coverage/config/coverage_community_100.ini` | Community tier 100% target (in-scope modules) |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/coverage_quick.ps1` / `.sh` | Fast coverage; writes `coverage_quick.json` |
| `scripts/coverage_full.ps1` / `.sh` | Full report; writes `coverage.json` + HTML |
| `scripts/track_coverage.py` | Generate, compare, trend; `--update-doc` updates COVERAGE_TRACKING.md |
| `scripts/analyze_coverage.py` | Analyze JSON; default input: `coverage/generated/coverage.json` |

## Status & docs

- **Root:** [COVERAGE_TRACKING.md](../COVERAGE_TRACKING.md) — Current status, module breakdowns, generation instructions.
- **Root:** [README_COVERAGE.md](../README_COVERAGE.md) — Quick reference and links.
- **Archive:** `coverage/archive/` — Historical JSON snapshot and consolidated docs (for reference only).
