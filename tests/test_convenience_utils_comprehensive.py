"""
Comprehensive tests for convenience_utils.py to improve coverage to 75-80%.

Tests cover:
- Geometry convenience functions (create_simple_core, quick_mesh_extraction)
- Neutronics convenience functions (create_simple_solver, create_simple_xs_data, quick_keff_calculation)
- Burnup convenience functions (create_simple_burnup_solver, quick_burnup_calculation)
- Decay heat convenience functions (create_simple_decay_heat_calculator, quick_decay_heat)
- Gamma transport convenience functions (create_simple_gamma_solver, quick_gamma_transport)
- Error handling and edge cases
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from smrforge.convenience_utils import (
    create_simple_core,
    quick_mesh_extraction,
    create_simple_solver,
    create_simple_xs_data,
    quick_keff_calculation,
    create_simple_burnup_solver,
    quick_burnup_calculation,
    create_simple_decay_heat_calculator,
    quick_decay_heat,
    create_simple_gamma_solver,
    quick_gamma_transport,
)


@pytest.fixture
def mock_core():
    """Create a mock PrismaticCore."""
    from smrforge.geometry.core_geometry import PrismaticCore
    core = PrismaticCore(name="TestCore")
    core.core_height = 100.0
    core.core_diameter = 50.0
    core.build_mesh(n_radial=5, n_axial=3)
    return core


@pytest.fixture
def mock_xs_data():
    """Create mock cross-section data."""
    from smrforge.validation.models import CrossSectionData
    return CrossSectionData(
        n_groups=2,
        n_materials=2,
        sigma_t=np.array([[0.30, 0.90], [0.28, 0.75]]),
        sigma_a=np.array([[0.008, 0.12], [0.002, 0.025]]),
        sigma_f=np.array([[0.006, 0.10], [0.0, 0.0]]),
        nu_sigma_f=np.array([[0.008, 0.10], [0.0, 0.0]]),
        sigma_s=np.array([[[0.29, 0.01], [0.0, 0.78]], [[0.28, 0.0], [0.0, 0.73]]]),
        chi=np.array([[1.0, 0.0], [0.0, 0.0]]),
        D=np.array([[1.0, 0.4], [1.2, 0.5]]),
    )


class TestGeometryConvenienceFunctions:
    """Test geometry convenience functions."""

    def test_create_simple_core_defaults(self):
        """Test create_simple_core with default parameters."""
        core = create_simple_core()
        assert core is not None
        assert core.name == "SimpleCore"
        assert len(core.blocks) > 0

    def test_create_simple_core_custom(self):
        """Test create_simple_core with custom parameters."""
        core = create_simple_core(
            name="CustomCore",
            n_rings=2,
            pitch=30.0,
            block_height=60.0,
            n_axial=1,
            n_radial=10,
            n_axial_mesh=15,
        )
        assert core.name == "CustomCore"
        assert core.core_height == 60.0

    def test_create_simple_core_import_error(self):
        """Test create_simple_core when geometry module is not available."""
        with patch('smrforge.convenience_utils._CORE_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                create_simple_core()

    def test_quick_mesh_extraction_volume(self, mock_core):
        """Test quick_mesh_extraction with volume mesh."""
        mesh = quick_mesh_extraction(mock_core, mesh_type="volume")
        assert mesh is not None
        assert hasattr(mesh, 'vertices')
        assert hasattr(mesh, 'n_vertices')

    def test_quick_mesh_extraction_surface(self, mock_core):
        """Test quick_mesh_extraction with surface mesh."""
        mesh = quick_mesh_extraction(mock_core, mesh_type="surface")
        assert mesh is not None

    def test_quick_mesh_extraction_with_channels(self, mock_core):
        """Test quick_mesh_extraction with channels included."""
        mesh = quick_mesh_extraction(mock_core, mesh_type="volume", include_channels=True)
        assert mesh is not None

    def test_quick_mesh_extraction_invalid_type(self, mock_core):
        """Test quick_mesh_extraction with invalid mesh type."""
        with pytest.raises(ValueError, match="Unknown mesh_type"):
            quick_mesh_extraction(mock_core, mesh_type="invalid")

    def test_quick_mesh_extraction_import_error(self):
        """Test quick_mesh_extraction when geometry module is not available."""
        with patch('smrforge.convenience_utils._CORE_AVAILABLE', False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                quick_mesh_extraction(Mock(), mesh_type="volume")


class TestNeutronicsConvenienceFunctions:
    """Test neutronics convenience functions."""

    def test_create_simple_solver_defaults(self):
        """Test create_simple_solver with default parameters."""
        solver = create_simple_solver()
        assert solver is not None
        assert hasattr(solver, 'solve_steady_state')

    def test_create_simple_solver_with_core(self, mock_core):
        """Test create_simple_solver with provided core."""
        solver = create_simple_solver(core=mock_core)
        assert solver is not None

    def test_create_simple_solver_with_xs_data(self, mock_xs_data):
        """Test create_simple_solver with provided xs_data."""
        solver = create_simple_solver(xs_data=mock_xs_data)
        assert solver is not None

    def test_create_simple_solver_custom_params(self):
        """Test create_simple_solver with custom parameters."""
        solver = create_simple_solver(
            n_groups=4,
            max_iterations=500,
            tolerance=1e-5,
            verbose=True,
            skip_validation=False,
        )
        assert solver is not None
        assert solver.options.max_iterations == 500
        assert solver.options.tolerance == 1e-5

    def test_create_simple_solver_import_error(self):
        """Test create_simple_solver when neutronics module is not available."""
        with patch('smrforge.convenience_utils._CORE_AVAILABLE', False):
            with pytest.raises(ImportError, match="Neutronics module not available"):
                create_simple_solver()

    def test_create_simple_xs_data_2_groups(self):
        """Test create_simple_xs_data with 2 groups."""
        xs_data = create_simple_xs_data(n_groups=2)
        assert xs_data is not None
        assert xs_data.n_groups == 2
        assert xs_data.n_materials == 2

    def test_create_simple_xs_data_custom_materials(self):
        """Test create_simple_xs_data with custom number of materials."""
        xs_data = create_simple_xs_data(n_groups=2, n_materials=1)
        assert xs_data.n_materials == 1

    def test_create_simple_xs_data_k_eff_target(self):
        """Test create_simple_xs_data with k_eff_target."""
        xs_data = create_simple_xs_data(n_groups=2, k_eff_target=1.05)
        assert xs_data is not None
        # Check that nu_sigma_f is scaled
        assert np.all(xs_data.nu_sigma_f[0] > 0)

    def test_create_simple_xs_data_invalid_groups(self):
        """Test create_simple_xs_data with invalid number of groups."""
        with pytest.raises(ValueError, match="Simple cross-sections only available for 2 groups"):
            create_simple_xs_data(n_groups=4)

    def test_create_simple_xs_data_import_error(self):
        """Test create_simple_xs_data when validation module is not available."""
        with patch('smrforge.convenience_utils._CORE_AVAILABLE', False):
            with pytest.raises(ImportError, match="Validation module not available"):
                create_simple_xs_data(n_groups=2)

    def test_quick_keff_calculation_defaults(self):
        """Test quick_keff_calculation with default parameters."""
        k_eff, flux = quick_keff_calculation()
        assert isinstance(k_eff, (float, np.floating))
        assert k_eff > 0
        assert isinstance(flux, np.ndarray)
        assert len(flux) > 0

    def test_quick_keff_calculation_with_core(self, mock_core):
        """Test quick_keff_calculation with provided core."""
        k_eff, flux = quick_keff_calculation(core=mock_core)
        assert isinstance(k_eff, (float, np.floating))
        assert isinstance(flux, np.ndarray)

    def test_quick_keff_calculation_with_xs_data(self, mock_xs_data):
        """Test quick_keff_calculation with provided xs_data."""
        k_eff, flux = quick_keff_calculation(xs_data=mock_xs_data)
        assert isinstance(k_eff, (float, np.floating))
        assert isinstance(flux, np.ndarray)

    def test_quick_keff_calculation_custom_params(self):
        """Test quick_keff_calculation with custom solver parameters."""
        k_eff, flux = quick_keff_calculation(
            max_iterations=200,
            tolerance=1e-5,
            verbose=False,
        )
        assert isinstance(k_eff, (float, np.floating))
        assert isinstance(flux, np.ndarray)

    def test_quick_keff_calculation_skip_validation(self):
        """Test quick_keff_calculation with skip_validation=False."""
        k_eff, flux = quick_keff_calculation(skip_validation=False)
        assert isinstance(k_eff, (float, np.floating))
        assert isinstance(flux, np.ndarray)


class TestBurnupConvenienceFunctions:
    """Test burnup convenience functions."""

    def test_create_simple_burnup_solver_defaults(self):
        """Test create_simple_burnup_solver with default parameters."""
        solver = create_simple_burnup_solver()
        assert solver is not None
        assert hasattr(solver, 'solve_time_step')

    def test_create_simple_burnup_solver_with_core(self, mock_core):
        """Test create_simple_burnup_solver with provided core."""
        solver = create_simple_burnup_solver(core=mock_core)
        assert solver is not None

    def test_create_simple_burnup_solver_custom_params(self):
        """Test create_simple_burnup_solver with custom parameters."""
        solver = create_simple_burnup_solver(
            time_step_days=10.0,
            max_iterations=100,
            tolerance=1e-5,
        )
        assert solver is not None

    def test_quick_burnup_calculation_defaults(self):
        """Test quick_burnup_calculation with default parameters."""
        results = quick_burnup_calculation(time_days=10.0)
        assert isinstance(results, dict)
        assert 'inventory' in results or 'k_eff' in results

    def test_quick_burnup_calculation_with_core(self, mock_core):
        """Test quick_burnup_calculation with provided core."""
        results = quick_burnup_calculation(core=mock_core, time_days=5.0)
        assert isinstance(results, dict)

    def test_quick_burnup_calculation_custom_params(self):
        """Test quick_burnup_calculation with custom parameters."""
        results = quick_burnup_calculation(
            time_days=20.0,
            time_step_days=5.0,
            max_iterations=50,
        )
        assert isinstance(results, dict)


class TestDecayHeatConvenienceFunctions:
    """Test decay heat convenience functions."""

    def test_create_simple_decay_heat_calculator_defaults(self):
        """Test create_simple_decay_heat_calculator with default parameters."""
        calculator = create_simple_decay_heat_calculator()
        assert calculator is not None
        assert hasattr(calculator, 'calculate_decay_heat')

    def test_create_simple_decay_heat_calculator_with_inventory(self):
        """Test create_simple_decay_heat_calculator with provided inventory."""
        from smrforge.burnup import NuclideInventory
        inventory = NuclideInventory()
        calculator = create_simple_decay_heat_calculator(inventory=inventory)
        assert calculator is not None

    def test_quick_decay_heat_defaults(self):
        """Test quick_decay_heat with default parameters."""
        heat = quick_decay_heat(time_days=1.0)
        assert isinstance(heat, (float, np.floating))
        assert heat >= 0

    def test_quick_decay_heat_custom_time(self):
        """Test quick_decay_heat with custom time."""
        heat = quick_decay_heat(time_days=10.0)
        assert isinstance(heat, (float, np.floating))
        assert heat >= 0

    def test_quick_decay_heat_with_inventory(self):
        """Test quick_decay_heat with provided inventory."""
        from smrforge.burnup import NuclideInventory
        inventory = NuclideInventory()
        heat = quick_decay_heat(inventory=inventory, time_days=1.0)
        assert isinstance(heat, (float, np.floating))


class TestGammaTransportConvenienceFunctions:
    """Test gamma transport convenience functions."""

    def test_create_simple_gamma_solver_defaults(self):
        """Test create_simple_gamma_solver with default parameters."""
        solver = create_simple_gamma_solver()
        assert solver is not None
        assert hasattr(solver, 'solve')

    def test_create_simple_gamma_solver_with_core(self, mock_core):
        """Test create_simple_gamma_solver with provided core."""
        solver = create_simple_gamma_solver(core=mock_core)
        assert solver is not None

    def test_create_simple_gamma_solver_custom_params(self):
        """Test create_simple_gamma_solver with custom parameters."""
        solver = create_simple_gamma_solver(
            n_groups=10,
            max_iterations=100,
            tolerance=1e-5,
        )
        assert solver is not None

    def test_quick_gamma_transport_defaults(self):
        """Test quick_gamma_transport with default parameters."""
        results = quick_gamma_transport()
        assert isinstance(results, dict)
        assert 'flux' in results or 'dose_rate' in results

    def test_quick_gamma_transport_with_core(self, mock_core):
        """Test quick_gamma_transport with provided core."""
        results = quick_gamma_transport(core=mock_core)
        assert isinstance(results, dict)

    def test_quick_gamma_transport_custom_params(self):
        """Test quick_gamma_transport with custom parameters."""
        results = quick_gamma_transport(
            n_groups=8,
            max_iterations=50,
        )
        assert isinstance(results, dict)

