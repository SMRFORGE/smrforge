"""
Pytest configuration and shared fixtures for SMRForge tests.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Pytest configuration
pytest_plugins = []


@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing path to test data directory."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp(prefix="smrforge_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def rng():
    """Fixture providing random number generator with fixed seed for reproducible tests."""
    return np.random.default_rng(42)


@pytest.fixture
def rng_seed_123():
    """Alternative RNG with different seed for testing randomness."""
    return np.random.default_rng(123)


# Geometry fixtures
@pytest.fixture
def simple_geometry():
    """Create a simple cylindrical geometry for testing."""
    from tests.test_utilities import SimpleGeometry

    return SimpleGeometry()


@pytest.fixture
def small_geometry():
    """Create a small geometry (fewer mesh points) for fast tests."""
    from tests.test_utilities import SimpleGeometry

    geometry = SimpleGeometry(core_diameter=100.0, core_height=200.0)
    geometry.radial_mesh = np.linspace(0, 50, 6)
    geometry.axial_mesh = np.linspace(0, 200, 11)
    return geometry


@pytest.fixture
def large_geometry():
    """Create a large geometry (more mesh points) for scaling tests."""
    from tests.test_utilities import SimpleGeometry

    geometry = SimpleGeometry(core_diameter=300.0, core_height=600.0)
    geometry.radial_mesh = np.linspace(0, 150, 51)
    geometry.axial_mesh = np.linspace(0, 600, 101)
    return geometry


# Cross-section data fixtures
@pytest.fixture
def simple_xs_data():
    """Create simple 2-group cross section data (fuel + reflector)."""
    from smrforge.validation.models import CrossSectionData

    return CrossSectionData(
        n_groups=2,
        n_materials=2,
        sigma_t=np.array(
            [
                [0.30, 0.90],  # Fuel
                [0.28, 0.75],  # Reflector
            ]
        ),
        sigma_a=np.array(
            [
                [0.008, 0.12],  # Fuel
                [0.002, 0.025],  # Reflector
            ]
        ),
        sigma_f=np.array(
            [
                [0.006, 0.10],  # Fuel
                [0.0, 0.0],  # Reflector
            ]
        ),
        nu_sigma_f=np.array(
            [
                [0.015, 0.25],  # Fuel
                [0.0, 0.0],  # Reflector
            ]
        ),
        sigma_s=np.array(
            [
                [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering
                [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering
            ]
        ),
        chi=np.array(
            [
                [1.0, 0.0],  # Fission spectrum
                [1.0, 0.0],  # Reflector (not used)
            ]
        ),
        D=np.array(
            [
                [1.0, 0.4],  # Diffusion coefficients
                [1.2, 0.5],
            ]
        ),
    )


@pytest.fixture
def multi_group_xs_data():
    """Create 4-group cross section data for testing multi-group capabilities."""
    from smrforge.validation.models import CrossSectionData

    n_groups = 4
    n_materials = 2

    # Generate realistic-looking 4-group data
    sigma_t = np.array(
        [
            [0.20, 0.50, 0.90, 1.20],  # Fuel
            [0.18, 0.45, 0.75, 1.00],  # Reflector
        ]
    )

    sigma_a = np.array(
        [
            [0.005, 0.08, 0.15, 0.20],  # Fuel
            [0.001, 0.015, 0.03, 0.04],  # Reflector
        ]
    )

    sigma_f = np.array(
        [
            [0.004, 0.06, 0.12, 0.18],  # Fuel
            [0.0, 0.0, 0.0, 0.0],  # Reflector
        ]
    )

    nu_sigma_f = np.array(
        [
            [0.010, 0.15, 0.30, 0.45],  # Fuel
            [0.0, 0.0, 0.0, 0.0],  # Reflector
        ]
    )

    # Scattering matrix (4x4 for each material)
    sigma_s = np.array(
        [
            [
                [0.19, 0.01, 0.00, 0.00],
                [0.00, 0.40, 0.02, 0.00],
                [0.00, 0.00, 0.70, 0.03],
                [0.00, 0.00, 0.00, 0.95],
            ],  # Fuel
            [
                [0.18, 0.00, 0.00, 0.00],
                [0.00, 0.43, 0.00, 0.00],
                [0.00, 0.00, 0.70, 0.00],
                [0.00, 0.00, 0.00, 0.94],
            ],  # Reflector
        ]
    )

    chi = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],  # Fission spectrum (all fast)
            [1.0, 0.0, 0.0, 0.0],  # Reflector (not used)
        ]
    )

    D = np.array(
        [
            [1.5, 0.6, 0.5, 0.4],  # Diffusion coefficients
            [1.8, 0.8, 0.6, 0.5],
        ]
    )

    return CrossSectionData(
        n_groups=n_groups,
        n_materials=n_materials,
        sigma_t=sigma_t,
        sigma_a=sigma_a,
        sigma_f=sigma_f,
        nu_sigma_f=nu_sigma_f,
        sigma_s=sigma_s,
        chi=chi,
        D=D,
    )


@pytest.fixture
def subcritical_xs_data():
    """Create subcritical cross section data (k_eff < 1.0)."""
    from smrforge.validation.models import CrossSectionData

    return CrossSectionData(
        n_groups=2,
        n_materials=1,
        sigma_t=np.array([[0.30, 0.90]]),
        sigma_a=np.array([[0.020, 0.20]]),  # Higher absorption
        sigma_f=np.array([[0.003, 0.05]]),  # Lower fission (must be <= absorption)
        nu_sigma_f=np.array([[0.006, 0.10]]),  # Lower nu_sigma_f for subcritical
        sigma_s=np.array([[[0.28, 0.01], [0.0, 0.70]]]),
        chi=np.array([[1.0, 0.0]]),
        D=np.array([[1.0, 0.4]]),
    )


@pytest.fixture
def supercritical_xs_data():
    """Create supercritical cross section data (k_eff > 1.0)."""
    from smrforge.validation.models import CrossSectionData

    return CrossSectionData(
        n_groups=2,
        n_materials=1,
        sigma_t=np.array([[0.30, 0.90]]),
        sigma_a=np.array([[0.008, 0.12]]),  # Absorption
        sigma_f=np.array([[0.006, 0.10]]),  # Fission (must be <= absorption)
        nu_sigma_f=np.array([[0.018, 0.30]]),  # Higher nu_sigma_f for supercritical
        sigma_s=np.array([[[0.29, 0.01], [0.0, 0.78]]]),
        chi=np.array([[1.0, 0.0]]),
        D=np.array([[1.0, 0.4]]),
    )


# Solver options fixtures
@pytest.fixture
def solver_options():
    """Create standard solver options for testing."""
    from smrforge.validation.models import SolverOptions

    return SolverOptions(
        max_iterations=100,
        tolerance=1e-5,
        eigen_method="power",
        inner_solver="bicgstab",
        verbose=False,
        skip_solution_validation=True,  # Skip strict validation for test data
    )


@pytest.fixture
def fast_solver_options():
    """Create solver options for fast tests (loose tolerance)."""
    from smrforge.validation.models import SolverOptions

    return SolverOptions(
        max_iterations=50,
        tolerance=1e-3,
        eigen_method="power",
        inner_solver="bicgstab",
        verbose=False,
        skip_solution_validation=True,  # Skip strict validation for test data
    )


@pytest.fixture
def tight_solver_options():
    """Create solver options with tight tolerance for accuracy tests."""
    from smrforge.validation.models import SolverOptions

    return SolverOptions(
        max_iterations=1000,
        tolerance=1e-8,
        eigen_method="power",
        inner_solver="bicgstab",
        verbose=False,
        skip_solution_validation=True,  # Skip strict validation for test data
    )


# Solver fixtures
@pytest.fixture
def solver(simple_geometry, simple_xs_data, solver_options):
    """Create a solver instance for testing."""
    from smrforge.neutronics.solver import MultiGroupDiffusion

    return MultiGroupDiffusion(simple_geometry, simple_xs_data, solver_options)


@pytest.fixture
def solved_solver(solver):
    """Create a solver instance and solve it."""
    solver.solve_steady_state()
    return solver


# Reactor specification fixtures
@pytest.fixture
def sample_reactor_spec():
    """Create a sample reactor specification."""
    from smrforge.validation.models import (
        FuelType,
        ReactorSpecification,
        ReactorType,
    )

    return ReactorSpecification(
        name="Test-Reactor",
        reactor_type=ReactorType.PRISMATIC,
        power_thermal=10e6,
        inlet_temperature=823.15,
        outlet_temperature=1023.15,
        max_fuel_temperature=1873.15,
        primary_pressure=7.0e6,
        core_height=200.0,
        core_diameter=100.0,
        reflector_thickness=30.0,
        fuel_type=FuelType.UCO,
        enrichment=0.195,
        heavy_metal_loading=150.0,
        coolant_flow_rate=8.0,
        cycle_length=3650,
        capacity_factor=0.95,
        target_burnup=150.0,
        doppler_coefficient=-3.5e-5,
        shutdown_margin=0.05,
    )


# Nuclear data fixtures for testing
@pytest.fixture
def mock_endf_file_content():
    """Create minimal valid ENDF file content for testing."""
    # Minimal ENDF format structure (MF=1, MT=451 - header)
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0  125 1451    1
 2.224631+6 2.224631+6          0          0          0          6  125 1451    2
 0.000000+0 9.991673-1          0          0          0          0  125 1451    3
                                                                   125 1451    4
                                                                   125 1451    5
                                                                   125 1451    6
 1.001000+3 9.991673-1          0          0          0          0  125 1451  451
                                                                   125 1451    0
 0.000000+0 0.000000+0          0          0          0          3  125 1451    0
 3.000000+0 0.000000+0          0          0          0          0  125 1451    3
 1.000000+0 2.530000-2          0          0          0          0  125 1451    0
                                                                   125 1451    0
 0.000000+0 0.000000+0          0          0          0          1  125 1451  3  1
 1.000000+0 2.530000-2          0          0          0          0  125 1451  3  2
                                                                   125 1451  3  3
                                                                   125 0  0    0
"""
    return endf_content


@pytest.fixture
def mock_endf_file(temp_dir, mock_endf_file_content):
    """Create a mock ENDF file for testing."""
    endf_path = temp_dir / "U235.endf"
    endf_path.write_text(mock_endf_file_content)
    return endf_path


@pytest.fixture
def mock_endf_file_generated(tmp_path):
    """Create a properly formatted mock ENDF file using the generator utility."""
    from tests.test_utilities_endf import create_mock_endf_file_minimal
    from smrforge.core.reactor_core import Nuclide
    
    u235 = Nuclide(Z=92, A=235)
    return create_mock_endf_file_minimal(u235, "total", tmp_path)


@pytest.fixture
def realistic_endf_file(temp_dir):
    """Create a realistic mock ENDF file with proper format for testing _simple_endf_parse."""
    endf_path = temp_dir / "U235_realistic.endf"
    
    # Build ENDF file content with proper format
    # Using simpler format that matches the existing mock file style
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  1    1
 0.000000+0 0.000000+0          0          0          0          6 125 3  1    2
 1.000000+5 1.000000+1 1.000000+6 1.200000+1 5.000000+6 1.500000+1 125 3  1    3
 1.000000+7 1.800000+1 2.000000+7 2.000000+1 5.000000+7 2.200000+1 125 3  1    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  2    1
 0.000000+0 0.000000+0          0          0          0          4 125 3  2    2
 1.000000+5 8.000000+0 1.000000+6 9.000000+0 1.000000+7 1.000000+1 125 3  2    3
 5.000000+7 1.100000+1 0.000000+0 0.000000+0 0.000000+0 0.000000+0 125 3  2    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3 18    1
 0.000000+0 0.000000+0          0          0          0          5 125 3 18    2
 1.000000+5 1.500000+0 1.000000+6 2.000000+0 5.000000+6 2.500000+0 125 3 18    3
 1.000000+7 3.000000+0 2.000000+7 3.500000+0 0.000000+0 0.000000+0 125 3 18    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3102    1
 0.000000+0 0.000000+0          0          0          0          4 125 3102    2
 1.000000+5 5.000000-1 1.000000+6 1.000000+0 1.000000+7 1.500000+0 125 3102    3
 5.000000+7 2.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0 125 3102    4
                                                                   125 0  0    0
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


@pytest.fixture
def mock_requests_get(monkeypatch, mock_endf_file_content):
    """Mock requests.get to return mock ENDF file content."""
    from unittest.mock import Mock

    def mock_get(url, **kwargs):
        response = Mock()
        response.content = mock_endf_file_content.encode("utf-8")
        response.status_code = 200
        response.ok = True
        return response

    monkeypatch.setattr("requests.get", mock_get)
    return mock_get


@pytest.fixture
def mock_sandy_unavailable(monkeypatch):
    """Mock SANDY as unavailable (ImportError)."""
    import sys

    if "sandy" in sys.modules:
        # Don't patch if already imported
        return

    def raise_import_error(*args, **kwargs):
        raise ImportError("SANDY not available")

    # Patch the import in the module
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "sandy":
            raise ImportError("SANDY not available")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)


@pytest.fixture
def mock_endf_parserpy_unavailable(monkeypatch):
    """Mock endf-parserpy as unavailable (ImportError)."""
    import sys

    if "endf_parserpy" in sys.modules:
        # Don't patch if already imported
        return

    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "endf_parserpy":
            raise ImportError("endf-parserpy not available")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)


@pytest.fixture
def pre_populated_cache(temp_dir):
    """Create a NuclearDataCache with pre-populated test data."""
    from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
    import numpy as np
    import zarr

    cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")

    # Pre-populate with test cross-section data
    nuc = Nuclide(Z=92, A=235, m=0)
    key = f"{Library.ENDF_B_VIII.value}/{nuc.name}/total/293.6K"

    # Create test energy and cross-section arrays
    energy = np.logspace(5, 7, 100)  # 100 keV to 10 MeV
    xs = np.ones_like(energy) * 10.0  # Constant 10 barns

    # Store in memory cache
    cache._memory_cache[key] = (energy, xs)

    return cache


# Session-scoped cleanup for parallel executors
@pytest.fixture(scope="session", autouse=True)
def cleanup_parallel_executors():
    """Ensure all parallel executors are cleaned up after test session."""
    yield
    # Force cleanup of any lingering executors
    import gc
    import time
    import threading
    
    # Force garbage collection multiple times
    for _ in range(5):  # More aggressive cleanup
        gc.collect()
        time.sleep(0.1)  # Longer delay between GC passes on Windows
    
    # Wait for all threads to finish (more time on Windows)
    wait_time = 0.5 if sys.platform == 'win32' else 0.2
    time.sleep(wait_time)
    
    # Check for active threads (debugging)
    active_threads = [t for t in threading.enumerate() if t.is_alive() and t != threading.main_thread()]
    if active_threads:
        import warnings
        warnings.warn(f"Found {len(active_threads)} active threads after test session: {[t.name for t in active_threads[:5]]}")
    
    # Final cleanup
    for _ in range(2):
        gc.collect()
        time.sleep(0.05)


# Markers for test organization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "parallel_batch: marks tests that use parallel batch processing (run serially)")
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks (deselect with '-m \"not performance\"'; use --run-performance to run)"
    )


def pytest_addoption(parser):
    """Add options for performance and other optional test groups."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance benchmark tests (otherwise skipped).",
    )


# Ensure parallel_batch tests run serially to avoid resource contention
def pytest_collection_modifyitems(config, items):
    """Modify test collection: parallel_batch serialization; skip performance unless --run-performance."""
    # Skip performance tests unless --run-performance
    if not config.getoption("--run-performance", False):
        skip_perf = pytest.mark.skip(reason="need --run-performance to run")
        for item in items:
            if item.get_closest_marker("performance"):
                item.add_marker(skip_perf)

    # Add serial marker to parallel_batch tests if pytest-xdist is being used
    try:
        from xdist import is_xdist_worker
        if is_xdist_worker(config):
            for item in items:
                if item.get_closest_marker("parallel_batch"):
                    item.add_marker(pytest.mark.serial)
    except ImportError:
        pass
