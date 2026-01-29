# Coverage Run Progress Bar

**Status:** ✅ Implemented

A real-time progress bar monitor for pytest coverage runs.

---

## Usage

### Quick Start

```powershell
# Automatically find and monitor the active coverage run
.\scripts\show_coverage_progress.ps1

# Or specify output file and process ID manually
.\scripts\show_coverage_progress.ps1 -OutputFile "path\to\output.txt" -ProcessId 12345
```

---

## Features

### Progress Bar Display

Shows a visual progress bar with:
- **Test Execution Progress:** Current/total tests
- **Percentage Complete:** Real-time completion percentage
- **Test Results:** Passed, Failed, Skipped, Errors counts
- **System Resources:** CPU time and memory usage (every 20 updates)

### Example Output

```
=== Coverage Run Progress Monitor ===
Monitoring PID: 16980
Output file: 701693.txt
Press Ctrl+C to stop monitoring

[████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] Tests: 2156/4336 (49.7%) | Passed: 2140 | Failed: 12 | Skipped: 4 | CPU: 145s | Mem: 512.3MB
```

---

## How It Works

1. **Finds Active Process:** Automatically detects running pytest coverage processes
2. **Monitors Output File:** Reads pytest output file in real-time
3. **Parses Test Results:** Counts PASSED/FAILED/SKIPPED/ERROR results
4. **Updates Progress Bar:** Refreshes every 500ms with latest statistics
5. **Final Summary:** Shows complete results when process finishes

---

## Process Detection

The script automatically:
- Searches for Python processes with pytest/coverage in command line
- Finds the most recent terminal output file
- Detects process completion and shows final summary

---

## Final Summary

When the coverage run completes, the script shows:
- ✅ Total tests executed
- ✅ Passed/Failed/Skipped/Error counts
- ✅ Coverage percentage (if available in output)
- ✅ Automatic analysis of `coverage.json` if freshly created

---

## Stopping the Monitor

Press `Ctrl+C` to stop monitoring at any time.

The coverage run will continue in the background.

---

## Troubleshooting

### No Process Found
```
❌ No active pytest coverage process found.
```
**Solution:** Make sure a coverage run is in progress.

### Output File Not Found
```
⚠️ Output file not found. Searching for active pytest processes...
```
**Solution:** The script will try to find the process manually, or specify the file path.

### No Progress Updates
- Check if the pytest process is actually running
- Verify the output file is being written to
- Ensure you have read permissions on the output file

---

*Created: January 21, 2026*  
*Script: `scripts/show_coverage_progress.ps1`*
