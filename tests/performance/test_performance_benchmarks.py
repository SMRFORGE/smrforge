"""
Performance benchmarking tests for regression detection.

These tests measure execution time for key operations and ensure
performance doesn't degrade over time.
"""

import time
from typing import Dict, List
import pytest
import numpy as np

from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion


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
    "keff_calculation_small": 0.5,      # Small core k-eff calculation
    "keff_calculation_medium": 2.0,     # Medium core k-eff calculation
    "geometry_mesh_generation": 0.1,    # Mesh generation
    "flux_calculation": 1.0,            # Flux calculation
    "burnup_step": 3.0,                 # Single burnup step
}


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
        from smrforge.neutronics.solver import CrossSectionData
        xs_data = CrossSectionData(
            n_groups=4,
            n_materials=2,
            sigma_t=np.ones((2, 4)),
            sigma_s=np.ones((2, 4, 4)) * 0.5,
            sigma_f=np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]]),
            nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
            chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
            D=np.ones((2, 4)),
        )
        
        solver = MultiGroupDiffusion(geometry, xs_data)
        
        # Measure performance (multiple runs for average)
        for _ in range(3):
            _, elapsed = benchmark.measure(solver.solve_eigenvalue)
        
        avg_time = benchmark.get_average()
        baseline = BASELINE_TIMINGS.get("keff_calculation_small", 1.0)
        threshold = baseline * benchmark.threshold_multiplier
        
        print(f"\n{benchmark.name}: {avg_time:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)")
        
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
        
        from smrforge.neutronics.solver import CrossSectionData
        xs_data = CrossSectionData(
            n_groups=4,
            n_materials=2,
            sigma_t=np.ones((2, 4)),
            sigma_s=np.ones((2, 4, 4)) * 0.5,
            sigma_f=np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]]),
            nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
            chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
            D=np.ones((2, 4)),
        )
        
        solver = MultiGroupDiffusion(geometry, xs_data)
        
        # Measure performance (single run for medium-sized problem)
        _, elapsed = benchmark.measure(solver.solve_eigenvalue)
        
        baseline = BASELINE_TIMINGS.get("keff_calculation_medium", 2.0)
        threshold = baseline * benchmark.threshold_multiplier
        
        print(f"\n{benchmark.name}: {elapsed:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)")
        
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
        
        print(f"\n{benchmark.name}: {avg_time:.3f}s (baseline: {baseline:.3f}s, threshold: {threshold:.3f}s)")
        
        if avg_time > threshold:
            pytest.fail(
                f"Performance regression: {benchmark.name} took {avg_time:.3f}s, "
                f"exceeding threshold of {threshold:.3f}s"
            )


@pytest.fixture
def performance_report_file(tmp_path):
    """Fixture for performance report file."""
    report_file = tmp_path / "performance_report.json"
    return report_file


def pytest_configure(config):
    """Configure pytest for performance tests."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks (deselect with '-m \"not performance\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Skip performance tests if not explicitly requested."""
    if not config.getoption("--run-performance", default=False):
        skip_performance = pytest.mark.skip(reason="need --run-performance option to run")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)


def pytest_addoption(parser):
    """Add command-line option for performance tests."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="run performance benchmark tests",
    )
