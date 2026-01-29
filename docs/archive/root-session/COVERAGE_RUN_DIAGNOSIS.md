# Coverage Run Diagnosis

**See also:** [COVERAGE_STRATEGY.md](COVERAGE_STRATEGY.md) — success = completed run + fresh `coverage.json`; test failures are allowed.

---

## Coverage run failing (test failures)

**Issue:** Full coverage run hits failing tests and stops (when using `-x`) or exits with code 1.

### 1. `test_reactor_create_save_json` — **FIXED**

| Symptom | `JSONDecodeError: Expecting value` when reading output file; stdout: `Failed to create reactor: Object of type Mock is not JSON serializable` |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **Cause** | The test uses `Mock(spec=Mock(name='valar-10', ...))`. In `unittest.mock`, the `name` keyword sets the Mock’s **repr name**, not a `.name` attribute. So `reactor.spec.name` is a `MagicMock`, and other spec fields can be too. The CLI builds `reactor_dict` from `reactor.spec` and calls `json.dump()`; Mock values are not JSON-serializable, so `json.dump` raises, no valid JSON is written, and the test fails when reading the file. |
| **Fix** | Use `types.SimpleNamespace` for `reactor.spec` instead of `Mock`, so all fields are plain Python types and JSON-serializable. |

### 2. `test_burnup_run_basic` — **FIXED**

| Symptom | `AssertionError: assert mock_solver.solve.called`; stdout: `unsupported format string passed to Mock.__format__` |
|--------|------------------------------------------------------------------------------------------------------------------|
| **Cause** | (a) `args` is a `Mock` with missing attributes (`adaptive_tracking`, `power_density`, etc.). Those Mocks are passed into `BurnupOptions` and then used in f-strings (e.g. `{burnup_options.adaptive_tracking}`), which triggers `Mock.__format__` and raises. (b) The test expects `mock_solver.solve` to be called, but `burnup_run` never instantiates `BurnupSolver` or calls `solve`; it only prints a “use Python API” note and optionally saves options. |
| **Fix** | (a) Pass explicit, JSON‑friendly values for all `args` used in `BurnupOptions` or format strings (e.g. `adaptive_tracking=False`, `power_density=None`). (b) Stop asserting `solve.called`; instead assert that the handler runs without exiting (e.g. `sys.exit` not called with 1). |

### 3. `test_config_show_no_config_file` — **FIXED**

| Symptom | `TypeError: unsupported operand type(s) for /: 'Mock' and 'str'` at `config_dir / "config.yaml"` |
|--------|--------------------------------------------------------------------------------------------------|
| **Cause** | The test mocks `Path.home()` to return a Mock with `__truediv__` so `Path.home() / ".smrforge"` works. The result of that (`config_dir`) is used again as `config_dir / "config.yaml"`. The mock only supported the first `/`; the second operand was on a plain Mock, so `Mock / str` raised. |
| **Fix** | Use a chain of mocks: `Path.home() / ".smrforge"` → `mock_config_dir`, and `mock_config_dir / "config.yaml"` → `mock_config_file` with `exists.return_value = False`. |

---

## Why No Progress Was Made (Jan 2026)

**Date:** January 21, 2026  
**Issue:** Coverage run failed immediately after start

---

## 🔍 Root Cause

### The Problem

The background coverage run (PID 16980) **failed immediately** after starting:

```
Exception ignored in: <_io.TextIOWrapper name='<stdout>' mode='w' encoding='cp1252'>
OSError: [Errno 22] Invalid argument
```

**Duration:** Only 0.744 seconds  
**Tests Executed:** 0 (none)  
**Status:** Process exited immediately with encoding error

---

## 📊 Evidence

### Process Status
- ❌ **PID 16980:** Exited after 0.744 seconds
- ⚠️ **5 other pytest processes:** Still running from previous attempts (started Jan 20-21)
- ⚠️ **coverage.json:** Stale file from Jan 19 (3,119 minutes old)

### Output File Analysis
- **Total tests collected:** None (process died before collection)
- **Tests passed:** 0
- **Tests failed:** 0
- **Error:** Encoding issue with stdout in Windows PowerShell

---

## 🔧 Solution Implemented

### Fix: Set UTF-8 Encoding

Started a fresh run with proper encoding:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/ --cov=smrforge \
    --cov-report=json:coverage.json \
    --cov-report=term-missing \
    --ignore=tests/performance/test_performance_benchmarks.py \
    --maxfail=10 \
    -q
```

**Changes:**
1. ✅ Set `PYTHONIOENCODING=utf-8` environment variable
2. ✅ Running in background with output captured
3. ✅ Output also saved to `coverage_run_output.txt` for monitoring

---

## 📝 Additional Findings

### Multiple Old Processes

Found 5 pytest processes still running from previous attempts:
- PID 11664: Started Jan 20, 21:47 (220s CPU time)
- PID 13628: Started Jan 20, 21:40 (223s CPU time)
- PID 14428: Started Jan 20, 21:56 (218s CPU time)
- PID 19656: Started Jan 20, 22:37 (244s CPU time)
- PID 23864: Started Jan 21, 15:16 (242s CPU time)

**Recommendation:** These may be stuck or hanging. Consider:
- Checking if they're making progress
- Terminating if they're stuck
- Using one that's actively running

---

## ✅ Implementation Complete

### Scripts Updated

1. **`scripts/run_coverage_analysis.ps1`** - ✅ Updated with UTF-8 encoding fix
   - Sets `PYTHONIOENCODING=utf-8` automatically
   - Proper output file capture
   - Background process support with PID tracking

2. **`scripts/track_coverage.py`** - ✅ Updated with encoding fix
   - Sets UTF-8 encoding in environment
   - Prevents Windows stdout encoding errors

3. **`scripts/check_old_processes.ps1`** - ✅ New script created
   - Detects old/stuck pytest processes
   - Identifies processes running >30 min with low CPU
   - Option to kill stuck processes: `-KillStuck`

4. **`scripts/monitor_coverage_run.ps1`** - ✅ New monitoring script
   - Monitors active coverage runs
   - Tracks output file updates
   - Detects completion automatically

### Usage

**Start Coverage Run:**
```powershell
# With encoding fix (recommended)
.\scripts\run_coverage_analysis.ps1 -Background

# Or foreground with output capture
.\scripts\run_coverage_analysis.ps1
```

**Monitor Progress:**
```powershell
# Use dedicated monitor
.\scripts\monitor_coverage_run.ps1

# Or check output file
Get-Content coverage_run_output.txt -Tail 20 -Wait

# Or use progress bar
.\scripts\show_coverage_progress.ps1
```

**Check Old Processes:**
```powershell
# List old processes
.\scripts\check_old_processes.ps1

# Kill stuck processes
.\scripts\check_old_processes.ps1 -KillStuck
```

**Verify Process:**
```powershell
Get-Process python | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-5) }
```

**Check Results:**
```powershell
# When complete, analyze
python scripts/analyze_coverage.py coverage.json
```

---

## 🎯 Expected Outcome

With proper encoding:
- ✅ Process should start successfully
- ✅ Tests should begin executing
- ✅ Progress should be visible in output file
- ✅ Coverage.json should be updated when complete

**Expected Duration:** 10-30+ minutes for 4,336 tests

---

*Diagnosis Date: January 21, 2026*  
*Status: Fresh run started with encoding fix*
