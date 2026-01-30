# Memory and Performance Assessment

**Last Updated:** January 2026

This guide describes how to **assess** memory usage and CPU efficiency in SMRForge, and **where to optimize** using existing utilities.

---

## 1. How to Assess Memory

### Run the profile script (memory mode)

```bash
python scripts/profile_performance.py --function keff --mode memory
python scripts/profile_performance.py --function mesh --mode memory
```

Reports **peak traced memory (MiB)** and **top allocations** by file:line during the run.

### Combined CPU + memory

```bash
python scripts/profile_performance.py --function keff --mode both
```

Runs the workload once and outputs both cProfile (CPU) and tracemalloc (memory) reports.

### Custom workflows (tracemalloc helper)

Use the profiling helper from code:

```python
from smrforge.utils.profiling import run_with_memory_profile, format_memory_report

def my_workload():
    # e.g. burnup loop, parameter sweep, cache fetches
    ...

result, report = run_with_memory_profile(my_workload, top_n=10)
print(format_memory_report(report))
# report["peak_mb"], report["top_allocations"]
```

### Optional: line-level memory (memory_profiler)

`memory_profiler` is listed in `requirements-dev.txt` (`pip install -r requirements-dev.txt` or `.[dev]`). Use `@profile` or `memory_usage()` for line-by-line or temporal memory inspection when you need finer detail than tracemalloc. See [openmc-improvement-recommendations](../technical/openmc-improvement-recommendations.md) for references.

---

## 2. How to Assess CPU / Efficiency

### Profile script (CPU mode)

```bash
python scripts/profile_performance.py --function keff --mode cpu
python scripts/profile_performance.py --function mesh --mode cpu
```

Outputs **cProfile** cumulative-time report (top 20 functions).

### Time-based and memory regression tests

```bash
pytest tests/performance/test_performance_benchmarks.py --run-performance -v --override-ini "addopts=-v --strict-markers --tb=short -ra"
```

These tests measure execution time (keff, mesh, flux, burnup) and peak memory (keff small, mesh generation). They fail if runs exceed baseline thresholds. They are **excluded from the default pytest run** via `pytest.ini`; use `--run-performance` and `--override-ini` as above to run them. Narrow to memory-only with `-k memory`.

### Save reports to files

```bash
python scripts/profile_performance.py --function keff --mode both --output report.txt
```

Writes `report_cpu.txt` and `report_memory.txt` (for `--mode both`).

---

## 3. Where to Optimize

### Memory

| Goal | Use | Location |
|------|-----|----------|
| Large cross-section / flux data | `MemoryMappedArray`, `create_memory_mapped_cross_sections` | `smrforge/utils/memory_mapped.py` |
| Repeated particle-bank allocations | `ParticleMemoryPool`, `MemoryPoolManager` | `smrforge/utils/memory_pool.py` |
| Avoid unnecessary copies | `ensure_contiguous`, `zero_copy_slice`, `smart_array_copy` | `smrforge/utils/optimization_utils.py` |
| Cache hot data | `NuclearDataCache` in-memory + Zarr | `smrforge/core/reactor_core.py` |

Note: `NuclearDataCache` uses a **bounded in-memory LRU** to avoid unbounded growth when many nuclide/reaction/temperature combinations are requested. Tune with `SMRFORGE_NUCDATA_MEMORY_CACHE_ENTRIES` (set to `0` to disable the in-memory bound).

See [Zero-Copy Audit](../technical/zero-copy-audit.md) for which copies are necessary and how to use the optimization utilities.

### CPU

| Area | Notes |
|------|--------|
| Numba / JIT hotspots | `monte_carlo_optimized`, solver helpers | Vectorization, `@njit` |
| Solver loops | `MultiGroupDiffusion`, power iteration, red–black | Already vectorized / parallel |
| Geometry, mesh | `PrismaticCore`, mesh generation | Vectorized where applicable |
| Parameter sweeps | `batch_process`, `batch_solve_keff` | `smrforge/utils/parallel_batch.py` |

See [OPTIMIZATION-STATUS-REPORT](../technical/OPTIMIZATION-STATUS-REPORT.md) and [OPTIMIZATION-QUICK-REFERENCE](../technical/OPTIMIZATION-QUICK-REFERENCE.md) for completed optimizations and metrics.

---

## 4. Quick Reference

### Commands

| Task | Command |
|------|---------|
| CPU profile (keff) | `python scripts/profile_performance.py --function keff --mode cpu` |
| Memory profile (keff) | `python scripts/profile_performance.py --function keff --mode memory` |
| CPU + memory (keff) | `python scripts/profile_performance.py --function keff --mode both` |
| CPU profile (mesh) | `python scripts/profile_performance.py --function mesh --mode cpu` |
| Perf + memory regression | `pytest tests/performance/... --run-performance --override-ini "addopts=..."` (see doc) |

### Key docs

- [OPTIMIZATION-STATUS-REPORT](../technical/OPTIMIZATION-STATUS-REPORT.md) – status and metrics  
- [OPTIMIZATION-QUICK-REFERENCE](../technical/OPTIMIZATION-QUICK-REFERENCE.md) – summary and key files  
- [Zero-Copy Audit](../technical/zero-copy-audit.md) – copy audit and optimization utils  
- [OPTIMIZATION-ROADMAP](../technical/OPTIMIZATION-ROADMAP.md) – future plans  

### Key modules

- `smrforge/utils/profiling.py` – `run_with_memory_profile`, `format_memory_report`  
- `smrforge/utils/memory_pool.py` – `ParticleMemoryPool`, `MemoryPoolManager`  
- `smrforge/utils/memory_mapped.py` – `MemoryMappedArray`, cross-section helpers  
- `smrforge/utils/optimization_utils.py` – `ensure_contiguous`, `smart_array_copy`, etc.  

---

**See also:** [testing-and-coverage](testing-and-coverage.md) for test and coverage workflows; [performance-and-benchmarking-assessment](performance-and-benchmarking-assessment.md) for a results-based assessment vs. the plan.
