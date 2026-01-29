# Coverage Run Strategy

**Goal:** Full coverage runs must **not fail** when the run completes and we have valid coverage data. Test failures are acceptable.

---

## 1. Definition of Success

| Outcome | Meaning | Script exit |
|--------|---------|-------------|
| **Success** | Pytest ran to completion (exit 0 or 1) **and** `coverage.json` was updated (within last 35 min) | **0** |
| **Failure** | No `coverage.json`, or it's stale, or pytest crashed/interrupted (exit 2, 3, 4, 5) | **1** |

- **Exit 0:** All tests passed.
- **Exit 1:** Some tests failed, but the run finished. pytest-cov still writes `coverage.json`. We treat this as **success** for the coverage run.
- **Exit 2–5:** Interrupted, internal error, usage error, or no tests collected. We do **not** treat these as success.

---

## 2. Process

1. **Run all tests** with coverage. No `-x` (no stop on first failure) and no `--maxfail`.
2. **Produce** `coverage.json` and a timestamped log file (e.g. `coverage_run_YYYYMMDD_HHmmss.txt`).
3. **Decide success** using the table above. If success: run `analyze_coverage.py`, then **exit 0**.
4. **On failure:** Exit 1, log reason (no/stale coverage, pytest exit code).

---

## 3. What We Avoid

- **Stopping early** on test failures (`-x`, `--maxfail`) so we always collect coverage over the full suite.
- **Treating pytest exit 1 as script failure** when we have fresh `coverage.json`.
- **File lock issues** by using a new timestamped log file each run instead of a fixed `coverage_run_output.txt`.
- **Encoding errors** on Windows by setting `PYTHONIOENCODING=utf-8` before invoking pytest.

---

## 4. How to Run

```powershell
# Full run (foreground, exit 0 if coverage OK)
.\scripts\run_coverage_analysis.ps1

# Quick run (subset, faster)
.\scripts\run_coverage_analysis.ps1 -Quick

# Background (long runs)
.\scripts\run_coverage_analysis.ps1 -Background
```

**Monitor:** `Get-Content coverage_run_*.txt -Tail 20 -Wait` or `.\scripts\show_coverage_progress.ps1`

---

## 5. References

- `COVERAGE_RUN_DIAGNOSIS.md` – encoding, logging, monitoring.
- `COVERAGE_FILES_ANALYSIS.md` – baseline files and history.
- `scripts/run_coverage_analysis.ps1` – implementation.

---

*Strategy defined so full coverage runs do not fail when we have valid coverage data.*
