"""
Validation and error handling tests for safety/transients module.
"""

import numpy as np
import pytest


@pytest.fixture
def simple_kinetics_params():
    """Create simple point kinetics parameters for testing."""
    from smrforge.safety.transients import PointKineticsParameters

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


class TestPointKineticsSolverValidation:
    """Test input validation for PointKineticsSolver."""

    def test_invalid_params_type(self):
        """Test that invalid params type raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        with pytest.raises(ValueError, match="params must be PointKineticsParameters"):
            PointKineticsSolver(params="invalid")

    def test_mismatched_beta_lambda_length(self):
        """Test that mismatched beta and lambda_d lengths raises ValueError."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        params = PointKineticsParameters(
            beta=np.array([0.001, 0.002]),
            lambda_d=np.array([0.1, 0.3, 0.5]),  # Wrong length
            alpha_fuel=-5e-5,
            alpha_moderator=-3e-5,
            Lambda=1e-4,
            fuel_heat_capacity=1e6,
            moderator_heat_capacity=2e6,
        )

        with pytest.raises(ValueError, match="beta and lambda_d must have same length"):
            PointKineticsSolver(params=params)

    def test_empty_beta(self):
        """Test that empty beta raises ValueError."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        params = PointKineticsParameters(
            beta=np.array([]),  # Empty
            lambda_d=np.array([]),
            alpha_fuel=-5e-5,
            alpha_moderator=-3e-5,
            Lambda=1e-4,
            fuel_heat_capacity=1e6,
            moderator_heat_capacity=2e6,
        )

        with pytest.raises(
            ValueError, match="params.beta must have at least one group"
        ):
            PointKineticsSolver(params=params)

    def test_invalid_lambda_negative(self, simple_kinetics_params):
        """Test that negative Lambda raises ValueError."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        # Create params with negative Lambda
        params = PointKineticsParameters(
            beta=simple_kinetics_params.beta,
            lambda_d=simple_kinetics_params.lambda_d,
            alpha_fuel=simple_kinetics_params.alpha_fuel,
            alpha_moderator=simple_kinetics_params.alpha_moderator,
            Lambda=-1e-4,  # Negative
            fuel_heat_capacity=simple_kinetics_params.fuel_heat_capacity,
            moderator_heat_capacity=simple_kinetics_params.moderator_heat_capacity,
        )

        with pytest.raises(ValueError, match="params.Lambda must be > 0"):
            PointKineticsSolver(params=params)

    def test_invalid_fuel_heat_capacity(self, simple_kinetics_params):
        """Test that invalid fuel_heat_capacity raises ValueError."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        params = PointKineticsParameters(
            beta=simple_kinetics_params.beta,
            lambda_d=simple_kinetics_params.lambda_d,
            alpha_fuel=simple_kinetics_params.alpha_fuel,
            alpha_moderator=simple_kinetics_params.alpha_moderator,
            Lambda=simple_kinetics_params.Lambda,
            fuel_heat_capacity=-1e6,  # Negative
            moderator_heat_capacity=simple_kinetics_params.moderator_heat_capacity,
        )

        with pytest.raises(ValueError, match="params.fuel_heat_capacity must be > 0"):
            PointKineticsSolver(params=params)

    def test_invalid_moderator_heat_capacity(self, simple_kinetics_params):
        """Test that invalid moderator_heat_capacity raises ValueError."""
        from smrforge.safety.transients import (
            PointKineticsParameters,
            PointKineticsSolver,
        )

        params = PointKineticsParameters(
            beta=simple_kinetics_params.beta,
            lambda_d=simple_kinetics_params.lambda_d,
            alpha_fuel=simple_kinetics_params.alpha_fuel,
            alpha_moderator=simple_kinetics_params.alpha_moderator,
            Lambda=simple_kinetics_params.Lambda,
            fuel_heat_capacity=simple_kinetics_params.fuel_heat_capacity,
            moderator_heat_capacity=-2e6,  # Negative
        )

        with pytest.raises(
            ValueError, match="params.moderator_heat_capacity must be > 0"
        ):
            PointKineticsSolver(params=params)

    def test_solve_transient_invalid_rho_external(self, simple_kinetics_params):
        """Test that non-callable rho_external raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        initial_state = {
            "power": 10e6,
            "T_fuel": 1200.0,
            "T_mod": 1100.0,
        }

        with pytest.raises(ValueError, match="rho_external must be callable"):
            solver.solve_transient(
                rho_external="invalid",
                power_removal=power_removal,
                initial_state=initial_state,
                t_span=(0.0, 10.0),
            )

    def test_solve_transient_invalid_power_removal(self, simple_kinetics_params):
        """Test that non-callable power_removal raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        initial_state = {
            "power": 10e6,
            "T_fuel": 1200.0,
            "T_mod": 1100.0,
        }

        with pytest.raises(ValueError, match="power_removal must be callable"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal="invalid",
                initial_state=initial_state,
                t_span=(0.0, 10.0),
            )

    def test_solve_transient_invalid_initial_state_type(self, simple_kinetics_params):
        """Test that non-dict initial_state raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        with pytest.raises(ValueError, match="initial_state must be dict"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state="invalid",
                t_span=(0.0, 10.0),
            )

    def test_solve_transient_missing_key(self, simple_kinetics_params):
        """Test that missing required key in initial_state raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        incomplete = {"power": 10e6, "T_fuel": 1200.0}  # Missing T_mod

        with pytest.raises(ValueError, match="initial_state missing required key"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state=incomplete,
                t_span=(0.0, 10.0),
            )

    def test_solve_transient_invalid_power(self, simple_kinetics_params):
        """Test that invalid initial power raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        invalid_state = {
            "power": -10e6,  # Negative
            "T_fuel": 1200.0,
            "T_mod": 1100.0,
        }

        with pytest.raises(ValueError, match="initial_state\['power'\] must be > 0"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state=invalid_state,
                t_span=(0.0, 10.0),
            )

    def test_solve_transient_invalid_t_span(self, simple_kinetics_params):
        """Test that invalid t_span raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        initial_state = {
            "power": 10e6,
            "T_fuel": 1200.0,
            "T_mod": 1100.0,
        }

        # Invalid: t_end <= t_start
        with pytest.raises(ValueError, match="t_span\[1\] must be > t_span\[0\]"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state=initial_state,
                t_span=(10.0, 5.0),  # Backwards
            )

    def test_solve_transient_invalid_max_step(self, simple_kinetics_params):
        """Test that invalid max_step raises ValueError."""
        from smrforge.safety.transients import PointKineticsSolver

        solver = PointKineticsSolver(simple_kinetics_params)

        def rho_external(t):
            return 0.0

        def power_removal(t, T_fuel, T_mod):
            return 10e6

        initial_state = {
            "power": 10e6,
            "T_fuel": 1200.0,
            "T_mod": 1100.0,
        }

        # Our validation catches it before scipy, so we check for our error message
        with pytest.raises(ValueError, match="max_step"):
            solver.solve_transient(
                rho_external=rho_external,
                power_removal=power_removal,
                initial_state=initial_state,
                t_span=(0.0, 10.0),
                max_step=-0.1,  # Negative
            )


class TestTransientValidation:
    """Test validation for transient simulation classes."""

    @pytest.fixture
    def mock_reactor_spec(self):
        """Create a mock reactor specification."""
        from smrforge.validation.pydantic_layer import (
            FuelType,
            ReactorSpecification,
            ReactorType,
        )

        return ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            core_diameter=200.0,
            core_height=400.0,
            enrichment=0.12,
            fuel_type=FuelType.UCO,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            primary_pressure=7.0e6,
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

    @pytest.fixture
    def mock_geometry(self):
        """Create a mock geometry."""

        class MockGeometry:
            def __init__(self):
                self.core_diameter = 200.0
                self.core_height = 400.0

        return MockGeometry()

    def test_lofc_invalid_reactor_spec(self, mock_geometry):
        """Test that None reactor_spec raises ValueError."""
        from smrforge.safety.transients import LOFCTransient

        with pytest.raises(ValueError, match="reactor_spec cannot be None"):
            LOFCTransient(reactor_spec=None, core_geometry=mock_geometry)

    def test_lofc_invalid_geometry(self, mock_reactor_spec):
        """Test that None geometry raises ValueError."""
        from smrforge.safety.transients import LOFCTransient

        with pytest.raises(ValueError, match="core_geometry cannot be None"):
            LOFCTransient(reactor_spec=mock_reactor_spec, core_geometry=None)

    def test_lofc_invalid_conditions_type(self, mock_reactor_spec, mock_geometry):
        """Test that invalid conditions type raises ValueError."""
        from smrforge.safety.transients import LOFCTransient

        transient = LOFCTransient(mock_reactor_spec, mock_geometry)

        with pytest.raises(ValueError, match="conditions must be TransientConditions"):
            transient.simulate(conditions="invalid")

    def test_lofc_invalid_initial_power(self, mock_reactor_spec, mock_geometry):
        """Test that invalid initial_power raises ValueError."""
        from smrforge.safety.transients import (
            LOFCTransient,
            TransientConditions,
            TransientType,
        )

        transient = LOFCTransient(mock_reactor_spec, mock_geometry)

        invalid_conditions = TransientConditions(
            initial_power=-10e6,  # Negative
            initial_temperature=1200.0,
            initial_flow_rate=50.0,
            initial_pressure=7.0e6,
            transient_type=TransientType.LOFC,
            trigger_time=0.0,
        )

        with pytest.raises(ValueError, match="conditions.initial_power must be > 0"):
            transient.simulate(invalid_conditions)

    def test_atws_invalid_reactor_spec(self, mock_geometry):
        """Test that None reactor_spec raises ValueError."""
        from smrforge.safety.transients import ATWSTransient

        with pytest.raises(ValueError, match="reactor_spec cannot be None"):
            ATWSTransient(reactor_spec=None, core_geometry=mock_geometry)

    def test_atws_invalid_conditions_type(self, mock_reactor_spec, mock_geometry):
        """Test that invalid conditions type raises ValueError."""
        from smrforge.safety.transients import ATWSTransient

        transient = ATWSTransient(mock_reactor_spec, mock_geometry)

        with pytest.raises(ValueError, match="conditions must be TransientConditions"):
            transient.simulate(conditions="invalid")
