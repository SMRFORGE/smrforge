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
                FuelType,
                ReactorSpecification,
                ReactorType,
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

    def test_lofc_transient_get_kinetics_parameters(
        self, mock_reactor_spec, mock_geometry
    ):
        """Test LOFCTransient._get_kinetics_parameters."""
        try:
            from smrforge.safety.transients import LOFCTransient

            transient = LOFCTransient(mock_reactor_spec, mock_geometry)
            params = transient._get_kinetics_parameters()

            assert params is not None
            assert len(params.beta) == 6
            assert len(params.lambda_d) == 6
            assert params.alpha_fuel < 0  # Negative feedback
        except ImportError:
            pytest.skip("Transients not available")

    def test_lofc_transient_forced_convection_removal(
        self, mock_reactor_spec, mock_geometry
    ):
        """Test LOFCTransient._forced_convection_removal."""
        try:
            from smrforge.safety.transients import LOFCTransient

            transient = LOFCTransient(mock_reactor_spec, mock_geometry)

            # Test with flow
            Q = transient._forced_convection_removal(mdot=10.0, T_coolant=1000.0)
            assert Q > 0

            # Test with zero flow
            Q_zero = transient._forced_convection_removal(mdot=0.0, T_coolant=1000.0)
            assert Q_zero == 0.0

            # Test with very low flow
            Q_low = transient._forced_convection_removal(mdot=0.001, T_coolant=1000.0)
            assert Q_low == 0.0
        except ImportError:
            pytest.skip("Transients not available")

    def test_lofc_transient_passive_cooling(self, mock_reactor_spec, mock_geometry):
        """Test LOFCTransient._passive_cooling."""
        try:
            from smrforge.safety.transients import LOFCTransient

            transient = LOFCTransient(mock_reactor_spec, mock_geometry)

            Q = transient._passive_cooling(T_fuel=1500.0, T_mod=1400.0, T_ambient=300.0)
            assert Q > 0  # Should be positive (heat removal)

            # Higher temperature should give more cooling
            Q_higher = transient._passive_cooling(
                T_fuel=1600.0, T_mod=1500.0, T_ambient=300.0
            )
            assert Q_higher > Q
        except ImportError:
            pytest.skip("Transients not available")

    def test_lofc_transient_simulate(self, mock_reactor_spec, mock_geometry):
        """Test LOFCTransient.simulate method."""
        try:
            from smrforge.safety.transients import (
                LOFCTransient,
                TransientConditions,
                TransientType,
            )

            transient = LOFCTransient(mock_reactor_spec, mock_geometry)

            conditions = TransientConditions(
                initial_power=10e6,
                initial_temperature=1200.0,
                initial_flow_rate=50.0,
                initial_pressure=7.0e6,
                transient_type=TransientType.LOFC,
                trigger_time=0.0,
                scram_available=True,
                t_end=100.0,  # Short simulation for testing
            )

            result = transient.simulate(conditions)

            assert "t" in result
            assert "power" in result
            assert "T_fuel" in result
            assert len(result["t"]) > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_atws_transient_get_kinetics_parameters(
        self, mock_reactor_spec, mock_geometry
    ):
        """Test ATWSTransient._get_kinetics_parameters."""
        try:
            from smrforge.safety.transients import ATWSTransient

            transient = ATWSTransient(mock_reactor_spec, mock_geometry)
            params = transient._get_kinetics_parameters()

            assert params is not None
            assert len(params.beta) == 6
            assert params.alpha_fuel < 0  # Strong negative feedback for ATWS
        except ImportError:
            pytest.skip("Transients not available")

    def test_atws_transient_passive_cooling(self, mock_reactor_spec, mock_geometry):
        """Test ATWSTransient._passive_cooling."""
        try:
            from smrforge.safety.transients import ATWSTransient

            transient = ATWSTransient(mock_reactor_spec, mock_geometry)

            Q = transient._passive_cooling(T_fuel=1500.0, T_mod=1400.0, T_ambient=300.0)
            assert Q > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_atws_transient_simulate(self, mock_reactor_spec, mock_geometry):
        """Test ATWSTransient.simulate method."""
        try:
            from smrforge.safety.transients import (
                ATWSTransient,
                TransientConditions,
                TransientType,
            )

            transient = ATWSTransient(mock_reactor_spec, mock_geometry)

            conditions = TransientConditions(
                initial_power=10e6,
                initial_temperature=1200.0,
                initial_flow_rate=50.0,
                initial_pressure=7.0e6,
                transient_type=TransientType.ATWS,
                trigger_time=0.0,
                scram_available=False,  # ATWS - no scram
                t_end=100.0,  # Short simulation
            )

            result = transient.simulate(conditions)

            assert "t" in result
            assert "power" in result
            assert "T_fuel" in result
            assert len(result["t"]) > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_reactivity_insertion_accident_creation(self, mock_reactor_spec):
        """Test creating ReactivityInsertionAccident."""
        try:
            from smrforge.safety.transients import ReactivityInsertionAccident

            ria = ReactivityInsertionAccident(mock_reactor_spec)

            assert ria.spec == mock_reactor_spec
        except ImportError:
            pytest.skip("Transients not available")

    def test_reactivity_insertion_accident_get_kinetics_parameters(
        self, mock_reactor_spec
    ):
        """Test ReactivityInsertionAccident._get_kinetics_parameters."""
        try:
            from smrforge.safety.transients import ReactivityInsertionAccident

            ria = ReactivityInsertionAccident(mock_reactor_spec)
            params = ria._get_kinetics_parameters()

            assert params is not None
            assert len(params.beta) == 6
        except ImportError:
            pytest.skip("Transients not available")

    def test_reactivity_insertion_accident_simulate(self, mock_reactor_spec):
        """Test ReactivityInsertionAccident.simulate method."""
        try:
            from smrforge.safety.transients import (
                ReactivityInsertionAccident,
                TransientConditions,
                TransientType,
            )

            ria = ReactivityInsertionAccident(mock_reactor_spec)

            conditions = TransientConditions(
                initial_power=10e6,
                initial_temperature=1200.0,
                initial_flow_rate=50.0,
                initial_pressure=7.0e6,
                transient_type=TransientType.RIA,
                trigger_time=0.0,
            )

            result = ria.simulate(
                rho_inserted=0.01,  # 1% dk/k
                insertion_time=0.1,  # 100 ms
                conditions=conditions,
            )

            assert "t" in result
            assert "power" in result
            assert "T_fuel" in result
            assert len(result["t"]) > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_air_water_ingress_analysis_creation(
        self, mock_reactor_spec, mock_geometry
    ):
        """Test creating AirWaterIngressAnalysis."""
        try:
            from smrforge.safety.transients import AirWaterIngressAnalysis

            analysis = AirWaterIngressAnalysis(mock_reactor_spec, mock_geometry)

            assert analysis.spec == mock_reactor_spec
            assert analysis.geometry == mock_geometry
        except ImportError:
            pytest.skip("Transients not available")

    def test_air_water_ingress_analysis_simulate_air_ingress(
        self, mock_reactor_spec, mock_geometry
    ):
        """Test AirWaterIngressAnalysis.simulate_air_ingress method."""
        try:
            from smrforge.safety.transients import (
                AirWaterIngressAnalysis,
                TransientConditions,
                TransientType,
            )

            analysis = AirWaterIngressAnalysis(mock_reactor_spec, mock_geometry)

            conditions = TransientConditions(
                initial_power=10e6,
                initial_temperature=1200.0,
                initial_flow_rate=50.0,
                initial_pressure=7.0e6,
                transient_type=TransientType.AIR_INGRESS,
                trigger_time=0.0,
                t_end=3600.0,  # 1 hour for testing
            )

            result = analysis.simulate_air_ingress(
                break_size=100.0, conditions=conditions
            )

            assert "t" in result
            assert "T_graphite" in result
            assert "mass_oxidized" in result
            assert "pressure" in result
            assert len(result["t"]) > 0
        except ImportError:
            pytest.skip("Transients not available")

    def test_decay_heat_ans_standard_edge_cases(self):
        """Test decay_heat_ans_standard with edge cases."""
        try:
            from smrforge.safety.transients import decay_heat_ans_standard

            # Test with very short time
            t_short = np.array([0.1, 0.5, 1.0])
            P_decay = decay_heat_ans_standard(t_short, P0=10e6, t_operate=86400.0)
            assert len(P_decay) == len(t_short)
            assert np.all(P_decay >= 0)

            # Test with long time
            t_long = np.array([3600.0, 86400.0, 604800.0])  # 1 hour, 1 day, 1 week
            P_decay_long = decay_heat_ans_standard(
                t_long, P0=10e6, t_operate=86400.0 * 365
            )
            assert len(P_decay_long) == len(t_long)
            assert np.all(P_decay_long >= 0)

            # Decay heat should decrease with time
            assert P_decay_long[0] > P_decay_long[-1]
        except ImportError:
            pytest.skip("Transients not available")
