"""
Pytest configuration and shared fixtures for SMRForge tests.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

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
        sigma_t=np.array([
            [0.30, 0.90],  # Fuel
            [0.28, 0.75],  # Reflector
        ]),
        sigma_a=np.array([
            [0.008, 0.12],  # Fuel
            [0.002, 0.025],  # Reflector
        ]),
        sigma_f=np.array([
            [0.006, 0.10],  # Fuel
            [0.0, 0.0],  # Reflector
        ]),
        nu_sigma_f=np.array([
            [0.015, 0.25],  # Fuel
            [0.0, 0.0],  # Reflector
        ]),
        sigma_s=np.array([
            [[0.29, 0.01], [0.0, 0.78]],  # Fuel scattering
            [[0.28, 0.0], [0.0, 0.73]],  # Reflector scattering
        ]),
        chi=np.array([
            [1.0, 0.0],  # Fission spectrum
            [1.0, 0.0],  # Reflector (not used)
        ]),
        D=np.array([
            [1.0, 0.4],  # Diffusion coefficients
            [1.2, 0.5],
        ]),
    )


@pytest.fixture
def multi_group_xs_data():
    """Create 4-group cross section data for testing multi-group capabilities."""
    from smrforge.validation.models import CrossSectionData
    n_groups = 4
    n_materials = 2
    
    # Generate realistic-looking 4-group data
    sigma_t = np.array([
        [0.20, 0.50, 0.90, 1.20],  # Fuel
        [0.18, 0.45, 0.75, 1.00],  # Reflector
    ])
    
    sigma_a = np.array([
        [0.005, 0.08, 0.15, 0.20],  # Fuel
        [0.001, 0.015, 0.03, 0.04],  # Reflector
    ])
    
    sigma_f = np.array([
        [0.004, 0.06, 0.12, 0.18],  # Fuel
        [0.0, 0.0, 0.0, 0.0],  # Reflector
    ])
    
    nu_sigma_f = np.array([
        [0.010, 0.15, 0.30, 0.45],  # Fuel
        [0.0, 0.0, 0.0, 0.0],  # Reflector
    ])
    
    # Scattering matrix (4x4 for each material)
    sigma_s = np.array([
        [[0.19, 0.01, 0.00, 0.00],
         [0.00, 0.40, 0.02, 0.00],
         [0.00, 0.00, 0.70, 0.03],
         [0.00, 0.00, 0.00, 0.95]],  # Fuel
        [[0.18, 0.00, 0.00, 0.00],
         [0.00, 0.43, 0.00, 0.00],
         [0.00, 0.00, 0.70, 0.00],
         [0.00, 0.00, 0.00, 0.94]],  # Reflector
    ])
    
    chi = np.array([
        [1.0, 0.0, 0.0, 0.0],  # Fission spectrum (all fast)
        [1.0, 0.0, 0.0, 0.0],  # Reflector (not used)
    ])
    
    D = np.array([
        [1.5, 0.6, 0.5, 0.4],  # Diffusion coefficients
        [1.8, 0.8, 0.6, 0.5],
    ])
    
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
        sigma_a=np.array([[0.015, 0.15]]),  # Higher absorption
        sigma_f=np.array([[0.005, 0.08]]),  # Lower fission
        nu_sigma_f=np.array([[0.012, 0.20]]),
        sigma_s=np.array([[[0.28, 0.01], [0.0, 0.75]]]),
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
        sigma_a=np.array([[0.006, 0.10]]),  # Lower absorption
        sigma_f=np.array([[0.007, 0.12]]),  # Higher fission
        nu_sigma_f=np.array([[0.018, 0.30]]),
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
        verbose=False
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
        verbose=False
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
        verbose=False
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
        ReactorSpecification,
        ReactorType,
        FuelType,
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


# Markers for test organization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
