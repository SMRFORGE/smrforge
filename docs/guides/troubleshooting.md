# SMRForge Troubleshooting Guide

**Last Updated:** March 2026

---

## ENDF Data Issues

### "ENDF file not found for U235"

**Cause:** Nuclear data not installed or path not configured.

**Fix:**
```bash
# Quick start (U235, U238, Pu239 only)
smrforge data download --library ENDF-B-VIII.1 --nuclide-set quickstart

# Full SMR set (~30 nuclides)
smrforge data download --library ENDF-B-VIII.1 --nuclide-set common_smr
```

Or run the setup wizard:
```bash
smrforge data setup
```

### "SMRFORGE_ENDF_DIR not set" or "local_endf_dir is None"

**Fix:** Set the environment variable or pass the path:
```bash
export SMRFORGE_ENDF_DIR=/path/to/ENDF-Data
# Or on Windows:
set SMRFORGE_ENDF_DIR=C:\path\to\ENDF-Data
```

Or in Python:
```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache

cache = NuclearDataCache(local_endf_dir=Path("/path/to/ENDF-Data"))
```

### "Local ENDF file failed validation"

**Cause:** Corrupted file or not a valid ENDF file (size < 1KB, missing ENDF markers).

**Fix:** Re-download the file:
```bash
smrforge data download --library ENDF-B-VIII.1 --nuclides U235 U238 --resume
```

---

## Solver Issues

### Diffusion solver doesn't converge

**Cause:** Tolerance too tight, insufficient iterations, or problematic cross-sections.

**Fix:** Relax tolerance or increase iterations:
```python
from smrforge.validation.models import SolverOptions

options = SolverOptions(
    max_iterations=200,
    tolerance=1e-4,  # Looser than default 1e-5
)
```

### k-eff too high (> 1.5) or diverging

**Cause:** Cross-section or geometry mismatch; often with mock or placeholder data.

**Fix:** Use real ENDF data; verify geometry and material assignments.

---

## Export / I/O Issues

### "Serpent export not available" or "MCNP export not available"

**Cause:** Full Serpent/MCNP round-trip export is **Pro tier** only.

**Community tier** has:
- Serpent run + parse (round-trip with Pro export)
- OpenMC full export/import

**Fix:** Use OpenMC export in Community, or consider SMRForge Pro for Serpent/MCNP.

---

## Optional Dependencies

### Plotly / Matplotlib not available

**Cause:** Optional visualization dependencies not installed.

**Fix:** Install as needed:
```bash
pip install plotly matplotlib
```

### h5py not available (checkpointing)

**Cause:** Burnup checkpointing requires h5py.

**Fix:**
```bash
pip install h5py
```

### Polars not available

**Cause:** Some data operations use Polars for performance.

**Fix:**
```bash
pip install polars
```

---

## Parallelism and Performance (Windows, macOS, Linux)

For platform-specific behavior of batch processing, multiprocessing, and Numba parallel loops, see **[Platform Notes: Parallelism and Performance](../technical/platform-parallelism.md)**. It covers:

- **Windows:** ProcessPoolExecutor fallback to ThreadPoolExecutor (GIL limits CPU-bound speedup); use WSL for better performance
- **Windows:** Need for `if __name__ == "__main__":` in scripts that use multiprocessing
- **All platforms:** Numba `prange` and OpenMP library availability (e.g. `brew install libomp` on macOS)

---

## Common Pitfalls

| Pitfall | Recommendation |
|---------|----------------|
| Running full suite with `--timeout` | Some tests are `@pytest.mark.isolated`; run without xdist or with higher timeout |
| ENDF path with spaces | Use quotes: `SMRFORGE_ENDF_DIR="C:\My Data\ENDF"` |
| Missing nuclide in burnup | Ensure nuclide is in `COMMON_SMR_NUCLIDES` or add to custom set |
| GUI port 8050 in use | Use `smrforge serve --port 8051` |

---

## Getting Help

- **Docs:** [Documentation Index](../DOCUMENTATION_INDEX.md)
- **Community vs Pro:** [community_vs_pro.md](../community_vs_pro.md)
- **API Reference:** [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
