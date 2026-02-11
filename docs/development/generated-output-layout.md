# Generated Output Layout

Generated artifacts (reports, profiling data, workflow results) go to `output/` by default to keep the project root clean.

## Directory Structure

| Path | Contents |
|------|----------|
| `output/` | All generated artifacts (gitignored) |
| `output/profiling/` | CPU/memory profile reports (`report_cpu.txt`, `report_memory.txt`) from `run_performance_profile.ps1` |
| `output/validation/` | Validation benchmark reports (optional; create before use) |
| `output/` | Community benchmark reports, design summaries, workflow results (from examples and CLI) |
| `output/.smrforge_runs.json` | Workflow audit log (append_run) |
| `output/smrforge_project.json` | GUI project save/load state |

## Examples

```powershell
# Profiling (default: output/profiling/report_cpu.txt, report_memory.txt)
.\scripts\run_performance_profile.ps1
.\scripts\run_performance_profile.ps1 -Mesh

# Validation reports
python scripts/run_validation.py --output output/validation/report.txt --json-output output/validation/report.json

# Community benchmark example (writes to output/)
python examples/community_benchmark_example.py
```

## CLI Output

For CLI commands, pass `--output` to write to `output/`:

```bash
smrforge reactor analyze --reactor reactor.json --neutronics --output output/results.json
smrforge workflow sweep --preset valar-10 --output output/sweep_results
smrforge report design --preset valar-10 -o output/design_report.md
```

## Related

- `results/` — Alternative location for batch/run results (gitignored)
- `testing/results/` — Manual testing output (gitignored)
