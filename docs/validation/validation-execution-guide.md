# Validation Execution Guide

**Last Updated:** February 2026  
**Purpose:** How to run validation with real ENDF files and populate the benchmark database

---

## Prerequisites

1. **ENDF data** — Download nuclear data:
   ```bash
   smrforge data download --library ENDF-B-VIII.1 --nuclide-set common_smr
   ```

2. **Set ENDF directory** — Ensure `SMRFORGE_ENDF_DIR` points to your ENDF location:
   ```bash
   export SMRFORGE_ENDF_DIR=/path/to/ENDF-Data
   ```

---

## Running Community Benchmarks

```bash
# Run all community benchmark cases
smrforge validate benchmark

# With custom benchmarks file
smrforge validate benchmark --benchmarks-file benchmarks/community_benchmarks.json

# Run full validation suite (neutronics + burnup + decay heat)
smrforge validate run --endf-dir $SMRFORGE_ENDF_DIR --output validation_report.json
```

---

## IAEA/ANS Reference Values

| Benchmark | Reference | Source | Typical k-eff | Tolerance |
|-----------|-----------|--------|--------------|-----------|
| Valar-10 | ~1.0–1.1 | SMRForge regression | — | 10% rel |
| GT-MHR-350 | ~1.0 | SMRForge regression | — | 15% rel |
| HTR-PM-200 | ~1.0 | SMRForge regression | — | 15% rel |
| U-235 decay heat | ANSI/ANS-5.1 | Standard | — | 20% rel |
| Pu-239 decay heat | ANSI/ANS-5.1 | Standard | — | 20% rel |
| Single-step burnup | IAEA CRP | SMRForge baseline | — | 15% rel |

**Note:** Community tier includes 3 benchmark cases. Pro tier has 10+ cases with full IAEA/ANS reference data.

---

## Generating Validation Reports

```python
from smrforge import quick_benchmark

# Run benchmarks and get report
out = quick_benchmark(benchmarks_file="benchmarks/community_benchmarks.json")
print(f"Passed: {out['passed']}/{out['total']}")
print(out.get("report", ""))
```

---

## Populating the Benchmark Database

The benchmark database is defined in `benchmarks/community_benchmarks.json`. To add new reference values:

1. Run the calculation with verified ENDF data
2. Record the obtained value (e.g., k-eff, decay heat at t=1h)
3. Update the JSON with `reference_value`, `reference_source`, and `tolerance_rel`
4. Re-run `smrforge validate benchmark` to confirm

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Benchmarks skip (no ENDF) | Run `smrforge data download` and set `SMRFORGE_ENDF_DIR` |
| k-eff out of tolerance | Verify ENDF files; try different solver options |
| Decay heat mismatch | Check decay data (MF=8) and fission yield (MF=8 MT=454/459) |
