#!/usr/bin/env python
"""
Run benchmark workloads, measure time and memory, and print suggested
BASELINE_TIMINGS and BASELINE_MEMORY_MB for tests/performance/test_performance_benchmarks.py.

Usage: python scripts/update_performance_baselines.py

After intentional performance or memory changes, run this, then update the
baselines in the test file and re-run the benchmarks.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.utils.profiling import run_with_memory_profile
from smrforge.validation.models import CrossSectionData, SolverOptions


def _keff_small():
    geometry = PrismaticCore(name="MemBenchCore")
    geometry.core_height = 100.0
    geometry.core_diameter = 50.0
    geometry.generate_mesh(n_radial=5, n_axial=3)
    sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
    sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)
    xs_data = CrossSectionData(
        n_groups=4, n_materials=2,
        sigma_t=np.ones((2, 4)), sigma_a=sigma_a,
        sigma_s=np.ones((2, 4, 4)) * 0.5, sigma_f=sigma_f,
        nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
        chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
        D=np.ones((2, 4)),
    )
    options = SolverOptions(max_iterations=50, tolerance=1e-5, skip_solution_validation=True)
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    solver.solve_steady_state()


def _keff_medium():
    geometry = PrismaticCore(name="BenchmarkCoreMedium")
    geometry.core_height = 200.0
    geometry.core_diameter = 100.0
    geometry.generate_mesh(n_radial=10, n_axial=5)
    sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
    sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)
    xs_data = CrossSectionData(
        n_groups=4, n_materials=2,
        sigma_t=np.ones((2, 4)), sigma_a=sigma_a,
        sigma_s=np.ones((2, 4, 4)) * 0.5, sigma_f=sigma_f,
        nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
        chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
        D=np.ones((2, 4)),
    )
    options = SolverOptions(max_iterations=50, tolerance=1e-5, skip_solution_validation=True)
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    solver.solve_steady_state()


def _mesh():
    g = PrismaticCore(name="BenchmarkGeometry")
    g.core_height = 200.0
    g.core_diameter = 100.0
    g.generate_mesh(n_radial=10, n_axial=5)


def main() -> int:
    print("Measuring benchmark workloads for baseline suggestions...")
    print("")

    # Time baselines
    times = {}
    for _ in range(3):
        t0 = time.perf_counter()
        _keff_small()
        times.setdefault("keff_calculation_small", []).append(time.perf_counter() - t0)
    times["keff_calculation_small"] = sum(times["keff_calculation_small"]) / 3

    t0 = time.perf_counter()
    _keff_medium()
    times["keff_calculation_medium"] = time.perf_counter() - t0

    mesh_times = []
    g = PrismaticCore(name="BenchmarkGeometry")
    g.core_height = 200.0
    g.core_diameter = 100.0
    for _ in range(5):
        t0 = time.perf_counter()
        g.generate_mesh(n_radial=10, n_axial=5)
        mesh_times.append(time.perf_counter() - t0)
    times["geometry_mesh_generation"] = sum(mesh_times) / 5

    # Memory baselines
    _, r_keff = run_with_memory_profile(_keff_small, top_n=1)
    _, r_mesh = run_with_memory_profile(_mesh, top_n=1)
    mem = {"keff_small": r_keff["peak_mb"], "mesh_generation": r_mesh["peak_mb"]}

    print("Suggested BASELINE_TIMINGS (seconds):")
    print("BASELINE_TIMINGS = {")
    for k, v in times.items():
        print(f'    "{k}": {max(0.01, round(v, 2))},')
    print("}")
    print("")
    print("Suggested BASELINE_MEMORY_MB (MiB):")
    print("BASELINE_MEMORY_MB = {")
    for k, v in mem.items():
        print(f'    "{k}": {max(0.1, round(v, 1))},')
    print("}")
    print("")
    print("Update tests/performance/test_performance_benchmarks.py with these values,")
    print("then run: pytest tests/performance/... --run-performance -v --override-ini \"addopts=...\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
