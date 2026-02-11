# Performance and Benchmarking Assessment

**Last Updated:** January 2026  
**Based on:** Memory and Performance Assessment Plan (`.cursor/plans/memory_and_performance_assessment_*.plan.md`).

This report assesses SMRForge’s **performance and benchmarking** setup and **current results**, relative to the plan’s deliverables and existing optimization work.

---

## 1. Plan vs. Implementation Status

| Plan deliverable | Status | Notes |
|------------------|--------|--------|
| **Tracemalloc helper + CLI** | ✅ Done | `smrforge.utils.profiling`: `run_with_memory_profile`, `format_memory_report`. Used by `profile_performance` and memory benchmarks. |
| **`profile_performance.py` extensions** | ✅ Done | `--mode cpu | memory | both`; `--function keff | mesh`; `--output` for reports. |
| **`memory-and-performance-assessment.md`** | ✅ Done | How to assess memory/CPU, where to optimize, quick reference. |
| **Memory regression tests** | ✅ Done | `TestMemoryBenchmarks`: keff small, mesh; tracemalloc baselines, 1.5× threshold. |
| **`memory_profiler` (optional)** | ✅ Added | In requirements-dev; use for line-level inspection when needed. |
| **Cross-links** | ✅ Done | OPTIMIZATION-STATUS-REPORT, OPTIMIZATION-QUICK-REFERENCE, DOCUMENTATION_INDEX. |
| **`monte_carlo` / `cache_fetch` workloads** | ⏸️ Partial | `monte_carlo` wired (`--function monte_carlo`); `cache_fetch` not yet. |

**Summary:** Core plan items (memory profiling, unified workflow, docs, regression tests) are in place. Optional pieces (memory_profiler, extra workloads) are deferred.

---

## 2. Profiling Results (Current Run)

**Environment:** Windows, Python 3.12; profile script and benchmarks run from repo root.

### 2.1 K-eff calculation (profile workload)

- **Geometry:** PrismaticCore, 200 cm height × 100 cm diameter; mesh 10 radial × 5 axial.
- **Solver:** MultiGroupDiffusion, 4 groups, 2 materials; `solve_steady_state` (power iteration).

| Metric | Value |
|--------|--------|
| **Wall time** | ~1.96 s |
| **Peak traced memory** | **14.83 MiB** |
| **Function calls** | ~378k (370k primitive) |

**CPU hotspots (cProfile, cumulative):** `solve_steady_state` → `_power_iteration` → `_solve_groups_parallel_red_black`; thread-pool wait (`threading.wait`, `as_completed`) dominates wall time, as expected for the parallel red–black solver.

**Top memory allocations (tracemalloc):** importlib (~4.5 MiB), `abc` (~2.9 MiB), Numba typing/templates (~0.5–0.2 MiB each). First run carries import/JIT overhead; subsequent runs would reflect mainly solver allocations.

### 2.2 Mesh generation (profile workload)

- **Geometry:** Same as above; `generate_mesh(n_radial=10, n_axial=5)` only.

| Metric | Value |
|--------|--------|
| **Wall time** | &lt;1 ms |
| **Peak traced memory** | **~0.01 MiB** |

Mesh generation is very fast and low-memory; top allocs are from numpy `linspace`/array ops and profiler overhead.

---

## 3. Benchmark Regression Results

**Command:**  
`pytest tests/performance/test_performance_benchmarks.py --run-performance -v --override-ini "addopts=-v --strict-markers --tb=short -ra"`

| Test | Baseline | Threshold (1.5×) | Result |
|------|----------|-------------------|--------|
| **keff_calculation_small** | 0.5 s | 0.75 s | ✅ PASS |
| **keff_calculation_medium** | 2.0 s | 3.0 s | ✅ PASS |
| **geometry_mesh_generation** | 0.1 s | 0.15 s | ✅ PASS |
| **keff_small_memory** | 50 MiB | 75 MiB | ✅ PASS |
| **mesh_generation_memory** | 25 MiB | 37.5 MiB | ✅ PASS |

All five performance benchmarks passed. Time baselines use `BASELINE_TIMINGS`; memory baselines use `BASELINE_MEMORY_MB` and `BASELINE_MEMORY_MULTIPLIER` (1.5×).

---

## 4. Gaps Addressed vs. Original Plan

| Original gap | Resolution |
|--------------|------------|
| No memory profiling | tracemalloc helper + `--mode memory` / `both` in profile script. |
| No “assess memory → optimize” workflow | `memory-and-performance-assessment.md` documents workflow, commands, and where to optimize. |
| CPU-only profile script | `--mode memory` and `both`; optional `--output` for reports. |
| No memory regression checks | `TestMemoryBenchmarks` with tracemalloc baselines and 1.5× threshold. |

---

## 5. Existing Assets (Plan “Current State”)

- **Memory:** `memory_pool`, `memory_mapped`, `NuclearDataCache`, `optimization_utils` (ensure_contiguous, smart_array_copy, etc.), [zero-copy audit](../technical/zero-copy-audit.md).
- **CPU:** Numba/JIT (`monte_carlo_optimized`, solver helpers), vectorization, parallel batch, [OPTIMIZATION-STATUS-REPORT](../technical/OPTIMIZATION-STATUS-REPORT.md) (90–95% of C++ performance).
- **Docs:** OPTIMIZATION-QUICK-REFERENCE, OPTIMIZATION-ROADMAP.

These remain the foundation for optimization; the new tooling supports **measuring** and **regressing** on both time and memory.

---

## 6. Recommendations

1. **Regular profiling:** Run `scripts/run_performance_profile.ps1` (Windows) or `scripts/run_performance_profile.sh` (Linux/macOS) for keff + optional mesh with `--mode both`. Or run `python scripts/profile_performance.py --function keff --mode both` (and optionally `--function mesh`) when changing solver, mesh, or data handling; check both CPU and memory reports.
2. **CI/benchmarks:** The workflow [`.github/workflows/performance.yml`](../../.github/workflows/performance.yml) runs performance tests with `--run-performance` and `--override-ini` on a **weekly schedule** and via **workflow_dispatch**. Keep them excluded from default `pytest` so day-to-day runs stay fast.
3. **Baseline updates:** After intentional performance or memory changes, run `python scripts/update_performance_baselines.py` to get suggested `BASELINE_TIMINGS` and `BASELINE_MEMORY_MB`. Update those dicts in `tests/performance/test_performance_benchmarks.py`, then re-run the performance benchmarks. See [Updating baselines](#updating-baselines) below.
4. **Optional workloads:** `monte_carlo` is wired: `python scripts/profile_performance.py --function monte_carlo --mode both`. `cache_fetch` is not yet wired; add it if that path becomes important to track.
5. **Line-level memory:** `memory_profiler` is in `requirements-dev.txt`. Use `@profile` or `memory_usage()` for line-by-line or temporal memory inspection when needed; see [memory-and-performance-assessment](memory-and-performance-assessment.md).

---

## 7. Updating baselines

When you intentionally change performance or memory behavior:

1. Run `python scripts/update_performance_baselines.py`. It runs the same workloads as the benchmarks and prints suggested `BASELINE_TIMINGS` and `BASELINE_MEMORY_MB`.
2. Edit `tests/performance/test_performance_benchmarks.py` and replace the `BASELINE_TIMINGS` and `BASELINE_MEMORY_MB` dicts with the suggested values (or adjusted values you accept).
3. Re-run the performance benchmarks:  
   `pytest tests/performance/test_performance_benchmarks.py --run-performance -v --override-ini "addopts=-v --strict-markers --tb=short -ra"`

---

## 8. Quick Reference

| Task | Command |
|------|---------|
| Regular profile (keff ± mesh) | `.\scripts\run_performance_profile.ps1` or `./scripts/run_performance_profile.sh`; use `--Mesh`/`--mesh` and `--Output`/`--output` as needed |
| CPU + memory profile (keff) | `python scripts/profile_performance.py --function keff --mode both` |
| Profile monte_carlo | `python scripts/profile_performance.py --function monte_carlo --mode both` |
| Memory-only profile (keff) | `python scripts/profile_performance.py --function keff --mode memory` |
| Save reports | Scripts default to `output/profiling/report` → `report_cpu.txt`, `report_memory.txt`; override with `--Output`/`--output` |
| Run performance benchmarks | `pytest tests/performance/test_performance_benchmarks.py --run-performance -v --override-ini "addopts=-v --strict-markers --tb=short -ra"`; or use CI workflow `performance.yml` (schedule / manual) |
| Memory-only benchmarks | Same as above, add `-k memory` |
| Update baselines | `python scripts/update_performance_baselines.py` then edit test file and re-run benchmarks |

**See also:** [Memory and Performance Assessment](memory-and-performance-assessment.md), [OPTIMIZATION-STATUS-REPORT](../technical/OPTIMIZATION-STATUS-REPORT.md), [OPTIMIZATION-QUICK-REFERENCE](../technical/OPTIMIZATION-QUICK-REFERENCE.md).
