"""
Performance benchmarking tests for regression detection.

These tests measure execution time and memory for key operations and ensure
performance doesn't degrade over time.
"""

import time
from typing import Dict, List

import numpy as np
import pytest

from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.utils.profiling import run_with_memory_profile
from smrforge.validation.models import CrossSectionData, SolverOptions


class PerformanceBenchmark:
    """Base class for performance benchmarks."""

    def __init__(self, name: str):
        self.name = name
        self.results: List[float] = []
        self.threshold_multiplier = 1.5  # 50% slower is acceptable

    def measure(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        self.results.append(elapsed)
        return result, elapsed

    def get_average(self) -> float:
        """Get average execution time."""
        return np.mean(self.results) if self.results else 0.0

    def get_std(self) -> float:
        """Get standard deviation of execution times."""
        return np.std(self.results) if len(self.results) > 1 else 0.0


# Baseline timings (in seconds) - update these after establishing baseline
# These should be updated after initial run with acceptable performance
BASELINE_TIMINGS = {
    "keff_calculation_small": 0.5,  # Small core k-eff calculation
    "keff_calculation_medium": 2.0,  # Medium core k-eff calculation
    "geometry_mesh_generation": 0.1,  # Mesh generation
    "flux_calculation": 1.0,  # Flux calculation
    "burnup_step": 3.0,  # Single burnup step
}

# Baseline peak memory (MiB) - tracemalloc. Update when intentionally changing memory use.
# Threshold: fail if peak > baseline * BASELINE_MEMORY_MULTIPLIER.
BASELINE_MEMORY_MB = {
    "keff_small": 50.0,
    "mesh_generation": 25.0,
}
BASELINE_MEMORY_MULTIPLIER = 1.5


@pytest.mark.performance
class TestKeffCalculationPerformance:
    """Performance benchmarks for k-eff calculations."""

    def test_keff_calculation_small(self):
        """Test k-eff calculation performance for small core."""
        benchmark = PerformanceBenchmark("keff_calculation_small")

        # Create small reactor
        geometry = PrismaticCore(name="BenchmarkCore")
        geometry.core_height = 100.0
        geometry.core_diameter = 50.0
        geometry.generate_mesh(n_radial=5, n_axial=3)

        # Simple cross-section data (mock)
        # Note: sigma_a must be >= sigma_f for validation to pass
        sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
        sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)  # Absorption >= fission
        xs_data = CrossSectionData(
            n_groups=4,
            n_materials=2,
            sigma_t=np.ones((2, 4)),
            sigma_a=sigma_a,  # Absorption cross section (required, must be >= sigma_f)
            sigma_s=np.ones((2, 4, 4)) * 0.5,
            sigma_f=sigma_f,
            nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
            chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
            D=np.ones((2, 4)),
        )

        from smrforge.validation.models import SolverOptions

        options = SolverOptions(
            max_iterations=50, tolerance=1e-5, skip_solution_validation=True
        )
        solver = MultiGroupDiffusion(geometry, xs_data, options)

        # Measure performance (multiple runs for average)
        for _ in range(3):
            _, elapsed = benchmark.measure(solver.solve_steady_state)

        avg_time = benchmark.get_average()
        baseline = BASELINE_TIMINGS.get("keff_calculation_small", 1.0)
        threshold = baseline * benchmark.threshold_multiplier

        print(
            f"\n{benchmark.name}: {avg_time:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)"
        )

        # Performance regression check
        if avg_time > threshold:
            pytest.fail(
                f"Performance regression: {benchmark.name} took {avg_time:.3f}s, "
                f"exceeding threshold of {threshold:.3f}s (baseline: {baseline:.3f}s). "
                f"Performance degraded by {(avg_time/baseline - 1)*100:.1f}%"
            )

    def test_keff_calculation_medium(self):
        """Test k-eff calculation performance for medium core."""
        benchmark = PerformanceBenchmark("keff_calculation_medium")

        # Create medium reactor
        geometry = PrismaticCore(name="BenchmarkCoreMedium")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0
        geometry.generate_mesh(n_radial=10, n_axial=5)

        from smrforge.validation.models import CrossSectionData, SolverOptions

        # Note: sigma_a must be >= sigma_f for validation to pass
        sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
        sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)  # Absorption >= fission
        xs_data = CrossSectionData(
            n_groups=4,
            n_materials=2,
            sigma_t=np.ones((2, 4)),
            sigma_a=sigma_a,  # Absorption cross section (required, must be >= sigma_f)
            sigma_s=np.ones((2, 4, 4)) * 0.5,
            sigma_f=sigma_f,
            nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
            chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
            D=np.ones((2, 4)),
        )

        options = SolverOptions(
            max_iterations=50, tolerance=1e-5, skip_solution_validation=True
        )
        solver = MultiGroupDiffusion(geometry, xs_data, options)

        # Measure performance (single run for medium-sized problem)
        _, elapsed = benchmark.measure(solver.solve_steady_state)

        baseline = BASELINE_TIMINGS.get("keff_calculation_medium", 2.0)
        threshold = baseline * benchmark.threshold_multiplier

        print(
            f"\n{benchmark.name}: {elapsed:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)"
        )

        if elapsed > threshold:
            pytest.fail(
                f"Performance regression: {benchmark.name} took {elapsed:.3f}s, "
                f"exceeding threshold of {threshold:.3f}s (baseline: {baseline:.3f}s)"
            )


@pytest.mark.performance
class TestGeometryPerformance:
    """Performance benchmarks for geometry operations."""

    def test_mesh_generation_performance(self):
        """Test mesh generation performance."""
        benchmark = PerformanceBenchmark("geometry_mesh_generation")

        geometry = PrismaticCore(name="BenchmarkGeometry")
        geometry.core_height = 200.0
        geometry.core_diameter = 100.0

        # Measure mesh generation
        for _ in range(5):
            _, elapsed = benchmark.measure(
                geometry.generate_mesh, n_radial=10, n_axial=5
            )

        avg_time = benchmark.get_average()
        baseline = BASELINE_TIMINGS.get("geometry_mesh_generation", 0.1)
        threshold = baseline * benchmark.threshold_multiplier

        print(
            f"\n{benchmark.name}: {avg_time:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)"
        )

        if avg_time > threshold:
            pytest.fail(
                f"Performance regression: {benchmark.name} took {avg_time:.3f}s, "
                f"exceeding threshold of {threshold:.3f}s"
            )


@pytest.mark.performance
class TestMemoryBenchmarks:
    """Memory benchmarks (tracemalloc). Regression check vs BASELINE_MEMORY_MB."""

    def test_keff_small_memory(self):
        """Peak memory during small keff run must not exceed baseline * multiplier."""

        def workload():
            geometry = PrismaticCore(name="MemBenchCore")
            geometry.core_height = 100.0
            geometry.core_diameter = 50.0
            geometry.generate_mesh(n_radial=5, n_axial=3)
            sigma_f = np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]])
            sigma_a = np.maximum(sigma_f, np.ones((2, 4)) * 0.3)
            xs_data = CrossSectionData(
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
            options = SolverOptions(
                max_iterations=50, tolerance=1e-5, skip_solution_validation=True
            )
            solver = MultiGroupDiffusion(geometry, xs_data, options)
            solver.solve_steady_state()

        _, report = run_with_memory_profile(workload, top_n=3)
        peak_mb = report["peak_mb"]
        baseline = BASELINE_MEMORY_MB.get("keff_small", 50.0)
        threshold = baseline * BASELINE_MEMORY_MULTIPLIER
        print(
            f"\nkeff_small memory: {peak_mb:.2f} MiB (baseline: {baseline:.0f}, threshold: {threshold:.0f})"
        )
        if peak_mb > threshold:
            pytest.fail(
                f"Memory regression: keff_small peak {peak_mb:.2f} MiB "
                f"exceeds threshold {threshold:.0f} MiB (baseline {baseline:.0f})"
            )

    def test_mesh_generation_memory(self):
        """Peak memory during mesh generation must not exceed baseline * multiplier."""

        def workload():
            geometry = PrismaticCore(name="MemBenchMesh")
            geometry.core_height = 200.0
            geometry.core_diameter = 100.0
            geometry.generate_mesh(n_radial=10, n_axial=5)

        _, report = run_with_memory_profile(workload, top_n=3)
        peak_mb = report["peak_mb"]
        baseline = BASELINE_MEMORY_MB.get("mesh_generation", 25.0)
        threshold = baseline * BASELINE_MEMORY_MULTIPLIER
        print(
            f"\nmesh_generation memory: {peak_mb:.2f} MiB (baseline: {baseline:.0f}, threshold: {threshold:.0f})"
        )
        if peak_mb > threshold:
            pytest.fail(
                f"Memory regression: mesh_generation peak {peak_mb:.2f} MiB "
                f"exceeds threshold {threshold:.0f} MiB (baseline {baseline:.0f})"
            )


@pytest.fixture
def performance_report_file(tmp_path):
    """Fixture for performance report file."""
    report_file = tmp_path / "performance_report.json"
    return report_file


# --run-performance, "performance" marker, and skip logic live in tests/conftest.py.
