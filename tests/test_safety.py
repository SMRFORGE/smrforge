"""
Tests for safety analysis module
"""

import numpy as np
import pytest


def test_import():
    """Test that safety module can be imported"""
    from smrforge import safety

    assert safety is not None


class TestTransientType:
    """Test TransientType enum."""

    def test_transient_type_values(self):
        """Test TransientType enum values."""
        try:
            from smrforge.safety.transients import TransientType

            assert TransientType.LOFC.value == "loss_of_forced_cooling"
            assert TransientType.ATWS.value == "anticipated_transient_without_scram"
            assert TransientType.RIA.value == "reactivity_insertion_accident"
            assert TransientType.LOCA.value == "loss_of_coolant_accident"
            assert TransientType.AIR_INGRESS.value == "air_ingress"
            assert TransientType.WATER_INGRESS.value == "water_ingress"
            assert TransientType.LOAD_FOLLOWING.value == "load_following"
        except ImportError:
            pytest.skip("Transients not available")


class TestTransientConditions:
    """Test TransientConditions class."""

    def test_transient_conditions_creation(self):
        """Test creating TransientConditions."""
        try:
            from smrforge.safety.transients import TransientConditions, TransientType

            conditions = TransientConditions(
                initial_power=10e6,  # W
                initial_temperature=1200.0,  # K
                initial_flow_rate=50.0,  # kg/s
                initial_pressure=7.0e6,  # Pa
                transient_type=TransientType.LOFC,
                trigger_time=0.0,  # s
            )

            assert conditions.initial_power == 10e6
            assert conditions.initial_temperature == 1200.0
            assert conditions.transient_type == TransientType.LOFC
            assert conditions.scram_available is True  # Default
        except ImportError:
            pytest.skip("Transients not available")


class TestPointKineticsParameters:
    """Test PointKineticsParameters class."""

    def test_parameters_creation(self):
        """Test creating PointKineticsParameters."""
        try:
            from smrforge.safety.transients import PointKineticsParameters

            # 6-group delayed neutron data
            beta = np.array([0.00021, 0.00142, 0.00127, 0.00257, 0.00075, 0.00027])
            lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

            params = PointKineticsParameters(
                beta=beta,
                lambda_d=lambda_d,
                alpha_fuel=-5e-5,  # dk/k/K
                alpha_moderator=-3e-5,
                Lambda=1e-4,  # s
                fuel_heat_capacity=1e6,  # J/K
                moderator_heat_capacity=2e6,  # J/K
            )

            assert len(params.beta) == 6
            assert len(params.lambda_d) == 6
            assert params.alpha_fuel < 0  # Negative feedback
            assert params.Lambda > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_beta_total(self):
        """Test beta_total property."""
        try:
            from smrforge.safety.transients import PointKineticsParameters

            beta = np.array([0.00021, 0.00142, 0.00127, 0.00257, 0.00075, 0.00027])
            lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

            params = PointKineticsParameters(
                beta=beta,
                lambda_d=lambda_d,
                alpha_fuel=-5e-5,
                alpha_moderator=-3e-5,
                Lambda=1e-4,
                fuel_heat_capacity=1e6,
                moderator_heat_capacity=2e6,
            )

            beta_total = params.beta_total
            assert np.isclose(beta_total, np.sum(beta))
        except ImportError:
            pytest.skip("Transients not available")


class TestPointKineticsSolver:
    """Test PointKineticsSolver class."""

    @pytest.fixture
    def simple_params(self):
        """Create simple point kinetics parameters."""
        try:
            from smrforge.safety.transients import PointKineticsParameters

            # 2-group delayed neutrons (simplified)
            beta = np.array([0.001, 0.002])
            lambda_d = np.array([0.1, 0.3])

            return PointKineticsParameters(
                beta=beta,
                lambda_d=lambda_d,
                alpha_fuel=-5e-5,
                alpha_moderator=-3e-5,
                Lambda=1e-4,
                fuel_heat_capacity=1e6,
                moderator_heat_capacity=2e6,
            )
        except ImportError:
            pytest.skip("Transients not available")

    def test_solver_creation(self, simple_params):
        """Test creating PointKineticsSolver."""
        try:
            from smrforge.safety.transients import PointKineticsSolver

            solver = PointKineticsSolver(simple_params)

            assert solver.params == simple_params
            assert solver.n_groups == 2
        except ImportError:
            pytest.skip("Transients not available")

    def test_solve_transient(self, simple_params):
        """Test solving a simple transient."""
        try:
            from smrforge.safety.transients import PointKineticsSolver

            solver = PointKineticsSolver(simple_params)

            # Constant reactivity and power removal
            def rho_external(t):
                return 0.0

            def power_removal(t, T_fuel, T_mod):
                return 10e6  # Constant removal

            initial_state = {
                "power": 10e6,  # W
                "T_fuel": 1200.0,  # K
                "T_mod": 1100.0,  # K
            }

            result = solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state=initial_state,
                t_span=(0.0, 10.0),
                max_step=0.1,
            )

            assert "t" in result
            assert "power" in result
            assert "T_fuel" in result
            assert "T_moderator" in result
            assert "rho_external" in result
            assert len(result["t"]) > 0
            assert len(result["power"]) == len(result["t"])
        except ImportError:
            pytest.skip("Transients not available")


class TestDecayHeat:
    """Test decay heat functions."""

    def test_decay_heat_ans_standard(self):
        """Test ANS decay heat standard."""
        try:
            from smrforge.safety.transients import decay_heat_ans_standard

            t = np.array([1.0, 10.0, 100.0, 1000.0, 3600.0])  # seconds
            P0 = 10e6  # W
            t_operate = 86400.0 * 365 * 2  # 2 years

            decay_power = decay_heat_ans_standard(t, P0, t_operate)

            assert len(decay_power) == len(t)
            # Decay heat should decrease with time
            assert decay_power[0] > decay_power[-1]
            # All values should be positive
            assert np.all(decay_power > 0)
        except ImportError:
            pytest.skip("Transients not available")


class TestTransientSimulations:
    """Test transient simulation classes."""

    @pytest.fixture
    def mock_reactor_spec(self):
        """Create a mock reactor specification."""
        try:
            from smrforge.validation.pydantic_layer import (
                ReactorSpecification,
                ReactorType,
                FuelType,
            )

            return ReactorSpecification(
                name="Test Reactor",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,  # W
                core_diameter=200.0,  # cm
                core_height=400.0,  # cm
                enrichment=0.12,
                fuel_type=FuelType.UCO,
                inlet_temperature=823.15,  # K
                outlet_temperature=1023.15,  # K
                primary_pressure=7.0e6,  # Pa
                max_fuel_temperature=1600.0,
                reflector_thickness=50.0,
                heavy_metal_loading=1000.0,
                coolant_flow_rate=50.0,
                cycle_length=365.0,
                capacity_factor=0.9,
                target_burnup=100.0,
                doppler_coefficient=-5e-5,
                shutdown_margin=0.05,
            )
        except ImportError:
            pytest.skip("Validation models not available")

    @pytest.fixture
    def mock_geometry(self):
        """Create a mock geometry."""
        try:
            from smrforge.geometry.core_geometry import PrismaticCore

            # Create a simple mock geometry object for testing
            # PrismaticCore may have different parameters, so create a minimal mock
            class MockGeometry:
                def __init__(self):
                    self.core_diameter = 200.0
                    self.core_height = 400.0

            return MockGeometry()
        except ImportError:
            pytest.skip("Geometry not available")

    def test_lofc_transient_creation(self, mock_reactor_spec, mock_geometry):
        """Test creating LOFCTransient."""
        try:
            from smrforge.safety.transients import LOFCTransient

            transient = LOFCTransient(mock_reactor_spec, mock_geometry)

            assert transient.spec == mock_reactor_spec
            assert transient.geometry == mock_geometry
        except ImportError:
            pytest.skip("Transients not available")

    def test_atws_transient_creation(self, mock_reactor_spec, mock_geometry):
        """Test creating ATWSTransient."""
        try:
            from smrforge.safety.transients import ATWSTransient

            transient = ATWSTransient(mock_reactor_spec, mock_geometry)

            assert transient.spec == mock_reactor_spec
            assert transient.geometry == mock_geometry
        except ImportError:
            pytest.skip("Transients not available")
