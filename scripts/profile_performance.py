#!/usr/bin/env python
"""
Performance and memory profiling script for SMRForge.

Generates CPU (cProfile) and/or memory (tracemalloc) reports for key operations.

Usage:
    python scripts/profile_performance.py [--function keff|mesh] [--mode cpu|memory|both] [--output OUTPUT]
"""

from __future__ import annotations

import argparse
import cProfile
import io
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.utils.profiling import format_memory_report, run_with_memory_profile
from smrforge.validation.models import CrossSectionData, SolverOptions

try:
    from smrforge.neutronics.monte_carlo import SimplifiedGeometry
    from smrforge.neutronics.monte_carlo_optimized import OptimizedMonteCarloSolver
    _MONTE_CARLO_AVAILABLE = True
except ImportError:
    _MONTE_CARLO_AVAILABLE = False

try:
    import pstats
except ImportError:
    pstats = None


def _make_geometry():
    g = PrismaticCore(name="ProfileCore")
    g.core_height = 200.0
    g.core_diameter = 100.0
    return g


def _make_xs_data():
    sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
    sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)
    return CrossSectionData(
        n_groups=4,
        n_materials=2,
        sigma_t=np.ones((2, 4)),
        sigma_a=sigma_a,
        sigma_s=np.ones((2, 4, 4)) * 0.5,
        sigma_f=sigma_f,
        nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
        chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
        D=np.ones((2, 4)),
    )


def run_keff() -> dict[str, Any]:
    """Run k-eff calculation (geometry + mesh + solve_steady_state). Returns result dict."""
    geometry = _make_geometry()
    geometry.generate_mesh(n_radial=10, n_axial=5)
    xs_data = _make_xs_data()
    options = SolverOptions(max_iterations=50, tolerance=1e-5, skip_solution_validation=True)
    solver = MultiGroupDiffusion(geometry, xs_data, options)
    k_eff, _ = solver.solve_steady_state()
    return {"k_eff": k_eff}


def run_mesh() -> None:
    """Run mesh generation only."""
    geometry = _make_geometry()
    geometry.generate_mesh(n_radial=10, n_axial=5)


def run_monte_carlo() -> dict[str, Any]:
    """Run optimized Monte Carlo eigenvalue (minimal n_particles/n_generations)."""
    if not _MONTE_CARLO_AVAILABLE:
        raise RuntimeError("monte_carlo workload requires SimplifiedGeometry and OptimizedMonteCarloSolver")
    geom = SimplifiedGeometry(core_diameter=100.0, core_height=200.0, reflector_thickness=20.0)
    xs_data = _make_xs_data()
    solver = OptimizedMonteCarloSolver(geom, xs_data, n_particles=200, n_generations=25, parallel=False)
    out = solver.run_eigenvalue()
    return {"k_eff": out["k_eff"], "k_std": out.get("k_std", 0.0)}


def _run_cpu(workload: Callable[[], Any], top_n: int = 20) -> str:
    profiler = cProfile.Profile()
    profiler.enable()
    result = workload()
    profiler.disable()
    s = io.StringIO()
    if pstats:
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats("cumulative")
        stats.print_stats(top_n)
    return s.getvalue(), result


def _run_memory(workload: Callable[[], Any], top_n: int = 10) -> tuple[dict[str, Any], Any]:
    result, report = run_with_memory_profile(workload, top_n=top_n)
    return report, result


def profile_keff(
    mode: str,
    output_file: Optional[Path] = None,
) -> None:
    """Profile k-eff calculation (CPU and/or memory)."""
    label = "k-eff calculation"
    workload = run_keff

    if mode == "cpu":
        report, result = _run_cpu(workload)
        text = "Performance Profile Report - " + label + "\n" + "=" * 70 + "\n" + report
        if output_file:
            output_file.write_text(text)
            print(f"Profile report saved to {output_file}")
        else:
            print("\n" + text)
        print(f"\nK-eff result: {result['k_eff']:.6f}")

    elif mode == "memory":
        report, result = _run_memory(workload)
        text = format_memory_report(report)
        if output_file:
            output_file.write_text(text)
            print(f"Memory report saved to {output_file}")
        else:
            print("\n" + "=" * 70 + "\n" + text)
        print(f"\nK-eff result: {result['k_eff']:.6f}")

    else:  # both
        tracemalloc = __import__("tracemalloc")
        tracemalloc.start(10)
        try:
            s1 = tracemalloc.take_snapshot()
            profiler = cProfile.Profile()
            profiler.enable()
            result = workload()
            profiler.disable()
            s2 = tracemalloc.take_snapshot()
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        cpu_s = io.StringIO()
        if pstats:
            stats = pstats.Stats(profiler, stream=cpu_s)
            stats.sort_stats("cumulative")
            stats.print_stats(20)
        cpu_report = cpu_s.getvalue()

        stats_diff = s2.compare_to(s1, "lineno")
        mem_report = {
            "peak_mb": peak / (1024 * 1024),
            "current_mb": current / (1024 * 1024),
            "top_allocations": [],
        }
        for i, stat in enumerate(stats_diff):
            if i >= 10:
                break
            mem_report["top_allocations"].append(
                {
                    "size_mb": stat.size_diff / (1024 * 1024),
                    "count": stat.count_diff,
                    "traceback": "\n".join(stat.traceback.format()) if stat.traceback else "",
                }
            )

        out_cpu = "Performance Profile - " + label + "\n" + "=" * 70 + "\n" + cpu_report
        out_mem = "Memory Profile - " + label + "\n" + "=" * 70 + "\n" + format_memory_report(mem_report)

        if output_file:
            base = output_file.stem
            suf = output_file.suffix or ".txt"
            parent = output_file.parent
            path_cpu = parent / f"{base}_cpu{suf}"
            path_mem = parent / f"{base}_memory{suf}"
            path_cpu.write_text(out_cpu)
            path_mem.write_text(out_mem)
            print(f"CPU report saved to {path_cpu}")
            print(f"Memory report saved to {path_mem}")
        else:
            print("\n" + out_cpu)
            print("\n" + out_mem)
        print(f"\nK-eff result: {result['k_eff']:.6f}")


def profile_mesh(
    mode: str,
    output_file: Optional[Path] = None,
) -> None:
    """Profile mesh generation (CPU and/or memory)."""
    label = "mesh generation"
    workload = run_mesh

    if mode == "cpu":
        report, _ = _run_cpu(workload)
        text = "Performance Profile Report - " + label + "\n" + "=" * 70 + "\n" + report
        if output_file:
            output_file.write_text(text)
            print(f"Profile report saved to {output_file}")
        else:
            print("\n" + text)

    elif mode == "memory":
        report, _ = _run_memory(workload)
        text = format_memory_report(report)
        if output_file:
            output_file.write_text(text)
            print(f"Memory report saved to {output_file}")
        else:
            print("\n" + "=" * 70 + "\n" + text)

    else:  # both
        tracemalloc = __import__("tracemalloc")
        tracemalloc.start(10)
        try:
            s1 = tracemalloc.take_snapshot()
            profiler = cProfile.Profile()
            profiler.enable()
            workload()
            profiler.disable()
            s2 = tracemalloc.take_snapshot()
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        cpu_s = io.StringIO()
        if pstats:
            stats = pstats.Stats(profiler, stream=cpu_s)
            stats.sort_stats("cumulative")
            stats.print_stats(20)
        cpu_report = cpu_s.getvalue()

        stats_diff = s2.compare_to(s1, "lineno")
        mem_report = {
            "peak_mb": peak / (1024 * 1024),
            "current_mb": current / (1024 * 1024),
            "top_allocations": [],
        }
        for i, stat in enumerate(stats_diff):
            if i >= 10:
                break
            mem_report["top_allocations"].append(
                {
                    "size_mb": stat.size_diff / (1024 * 1024),
                    "count": stat.count_diff,
                    "traceback": "\n".join(stat.traceback.format()) if stat.traceback else "",
                }
            )

        out_cpu = "Performance Profile - " + label + "\n" + "=" * 70 + "\n" + cpu_report
        out_mem = "Memory Profile - " + label + "\n" + "=" * 70 + "\n" + format_memory_report(mem_report)

        if output_file:
            base = output_file.stem
            suf = output_file.suffix or ".txt"
            parent = output_file.parent
            path_cpu = parent / f"{base}_cpu{suf}"
            path_mem = parent / f"{base}_memory{suf}"
            path_cpu.write_text(out_cpu)
            path_mem.write_text(out_mem)
            print(f"CPU report saved to {path_cpu}")
            print(f"Memory report saved to {path_mem}")
        else:
            print("\n" + out_cpu)
            print("\n" + out_mem)


def profile_monte_carlo(
    mode: str,
    output_file: Optional[Path] = None,
) -> None:
    """Profile optimized Monte Carlo eigenvalue (CPU and/or memory)."""
    if not _MONTE_CARLO_AVAILABLE:
        raise RuntimeError(
            "monte_carlo workload requires SimplifiedGeometry and OptimizedMonteCarloSolver"
        )
    label = "monte_carlo eigenvalue"
    workload = run_monte_carlo

    if mode == "cpu":
        report, result = _run_cpu(workload)
        text = "Performance Profile Report - " + label + "\n" + "=" * 70 + "\n" + report
        if output_file:
            output_file.write_text(text)
            print(f"Profile report saved to {output_file}")
        else:
            print("\n" + text)
        print(f"\nK-eff: {result['k_eff']:.6f} ± {result.get('k_std', 0):.6f}")

    elif mode == "memory":
        report, result = _run_memory(workload)
        text = format_memory_report(report)
        if output_file:
            output_file.write_text(text)
            print(f"Memory report saved to {output_file}")
        else:
            print("\n" + "=" * 70 + "\n" + text)
        print(f"\nK-eff: {result['k_eff']:.6f} ± {result.get('k_std', 0):.6f}")

    else:
        tracemalloc = __import__("tracemalloc")
        tracemalloc.start(10)
        try:
            s1 = tracemalloc.take_snapshot()
            profiler = cProfile.Profile()
            profiler.enable()
            result = workload()
            profiler.disable()
            s2 = tracemalloc.take_snapshot()
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        cpu_s = io.StringIO()
        if pstats:
            stats = pstats.Stats(profiler, stream=cpu_s)
            stats.sort_stats("cumulative")
            stats.print_stats(20)
        cpu_report = cpu_s.getvalue()
        stats_diff = s2.compare_to(s1, "lineno")
        mem_report = {
            "peak_mb": peak / (1024 * 1024),
            "current_mb": current / (1024 * 1024),
            "top_allocations": [],
        }
        for i, stat in enumerate(stats_diff):
            if i >= 10:
                break
            mem_report["top_allocations"].append(
                {
                    "size_mb": stat.size_diff / (1024 * 1024),
                    "count": stat.count_diff,
                    "traceback": "\n".join(stat.traceback.format()) if stat.traceback else "",
                }
            )
        out_cpu = "Performance Profile - " + label + "\n" + "=" * 70 + "\n" + cpu_report
        out_mem = "Memory Profile - " + label + "\n" + "=" * 70 + "\n" + format_memory_report(mem_report)
        if output_file:
            base = output_file.stem
            suf = output_file.suffix or ".txt"
            parent = output_file.parent
            path_cpu = parent / f"{base}_cpu{suf}"
            path_mem = parent / f"{base}_memory{suf}"
            path_cpu.write_text(out_cpu)
            path_mem.write_text(out_mem)
            print(f"CPU report saved to {path_cpu}")
            print(f"Memory report saved to {path_mem}")
        else:
            print("\n" + out_cpu)
            print("\n" + out_mem)
        print(f"\nK-eff: {result['k_eff']:.6f} ± {result.get('k_std', 0):.6f}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile SMRForge performance and/or memory",
    )
    parser.add_argument(
        "--function",
        choices=["keff", "mesh", "monte_carlo"],
        default="keff",
        help="Workload to profile: keff, mesh, or monte_carlo (default: keff)",
    )
    parser.add_argument(
        "--mode",
        choices=["cpu", "memory", "both"],
        default="cpu",
        help="Report type: cpu (cProfile), memory (tracemalloc), or both (default: cpu)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for report(s). For --mode both, _cpu and _memory suffixes are used.",
    )
    args = parser.parse_args()

    if args.function == "keff":
        profile_keff(args.mode, args.output)
    elif args.function == "mesh":
        profile_mesh(args.mode, args.output)
    else:
        profile_monte_carlo(args.mode, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
