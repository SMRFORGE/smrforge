# Coverage Documentation Quick Reference

## Single Source of Truth

**📌 [COVERAGE_TRACKING.md](COVERAGE_TRACKING.md)** — Main coverage tracking document: current status, module breakdowns, test statistics, coverage generation instructions.

## Entry Point

**📌 [coverage/README.md](coverage/README.md)** — How to run coverage, where output goes, scripts, and config.

## Related

- **`docs/development/COVERAGE_100_PLAN.md`** — Path to 100% in-scope coverage
- **`docs/development/coverage-exclusions.md`** — Explanation of intentional exclusions
- **`coverage/archive/`** — Historical JSON snapshot and consolidated docs (reference only)

## Quick Start

```bash
# Quick check (fast)
.\scripts\coverage_quick.ps1

# Full report (HTML + JSON)
.\scripts\coverage_full.ps1
```

Output: `coverage/generated/` (gitignored). See [coverage/README.md](coverage/README.md) for details.
