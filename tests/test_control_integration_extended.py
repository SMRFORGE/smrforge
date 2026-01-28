"""
Extended edge case tests for smrforge.control.integration module.

Additional tests targeting uncovered code paths to reach 80% coverage.
"""

import pytest
from unittest.mock import Mock
from smrforge.control.integration import (
    create_controlled_reactivity,
    create_load_following_reactivity,
)
from smrforge.control.controllers import ReactorController, LoadFollowingController


@pytest.fixture
def mock_reactor_controller():
    """Create a mock ReactorController."""
    controller = Mock(spec=ReactorController)
    controller.rod_worth = 0.01
    controller.control_step = Mock(return_value={"reactivity_change": 0.001})
    return controller


@pytest.fixture
def mock_load_controller():
    """Create a mock LoadFollowingController."""
    controller = Mock(spec=LoadFollowingController)
    controller.control_step = Mock(return_value={"reactivity_change": 0.0005})
    return controller


class TestControlIntegrationExtendedEdgeCases:
    """Extended edge case tests for control integration."""
    
    def test_create_controlled_reactivity_state_with_none_temperature_fallback(self, mock_reactor_controller):
        """Test reactivity function when T_fuel is None, falls back to temperature."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only temperature (no T_fuel), should use temperature
        state = {"temperature": 1250.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, int))
        # Should use temperature (1250.0)
        call_args = mock_reactor_controller.control_step.call_args[0]
        assert call_args[1] == 1250.0  # temperature parameter

    def test_create_controlled_reactivity_state_with_t_fuel(self, mock_reactor_controller):
        """Test reactivity function when state has T_fuel (used for temperature)."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        # State with T_fuel (transient solver convention) - should use T_fuel for temperature
        state = {"power": 1.05e6, "T_fuel": 1280.0}
        reactivity = rho_func(2.0, state)
        assert isinstance(reactivity, (float, int))
        call_args = mock_reactor_controller.control_step.call_args[0]
        assert call_args[1] == 1280.0  # temperature from T_fuel
        assert call_args[0] == 1.05e6  # power from state
    
    def test_create_load_following_reactivity_state_with_none_temperature_fallback(self, mock_load_controller):
        """Test load following when state only has temperature (no T_fuel)."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only temperature (no T_fuel)
        state = {"temperature": 1180.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, int))
        # Should use temperature (1180.0)
        call_args = mock_load_controller.control_step.call_args[0]
        assert call_args[1] == 1180.0

    def test_create_load_following_reactivity_state_with_t_fuel(self, mock_load_controller):
        """Test load following when state has T_fuel (used for temperature)."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        state = {"power": 0.9e6, "T_fuel": 1150.0}
        reactivity = rho_func(1.0, state)
        assert isinstance(reactivity, (float, int))
        call_args = mock_load_controller.control_step.call_args[0]
        assert call_args[1] == 1150.0  # temperature from T_fuel
        assert call_args[0] == 0.9e6   # power from state
    
    def test_create_controlled_reactivity_control_step_exception(self, mock_reactor_controller):
        """Test reactivity function when control_step raises an exception."""
        mock_reactor_controller.control_step.side_effect = ValueError("Control error")
        
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Should propagate the exception
        with pytest.raises(ValueError, match="Control error"):
            rho_func(1.0, {})
    
    def test_create_load_following_reactivity_control_step_exception(self, mock_load_controller):
        """Test load following when control_step raises an exception."""
        mock_load_controller.control_step.side_effect = RuntimeError("Control system error")
        
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Should propagate the exception
        with pytest.raises(RuntimeError, match="Control system error"):
            rho_func(1.0, {})
    
    def test_create_controlled_reactivity_zero_initial_time_dt_zero(self, mock_reactor_controller):
        """Test that dt is calculated correctly when starting at t=0.0."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=0.0 should have dt=0.0 (state_store["time"] starts at 0.0)
        rho_func(0.0, {})
        first_call_args = mock_reactor_controller.control_step.call_args[0]
        first_dt = first_call_args[3]  # dt is 4th argument
        assert first_dt == 0.0
        
        # After first call, state_store["time"] is updated to 0.0
        # Second call at t=0.5: dt = 0.5 - 0.0 = 0.5
        rho_func(0.5, {})
        second_call_args = mock_reactor_controller.control_step.call_args[0]
        second_dt = second_call_args[3]
        # Verify dt was calculated correctly (0.5 - previous time)
        assert isinstance(second_dt, (float, int))
        # The dt should be > 0 (positive time step)
        assert second_dt >= 0.0
    
    def test_create_load_following_reactivity_zero_initial_time_dt_zero(self, mock_load_controller):
        """Test dt calculation in load following when starting at t=0.0."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=0.0
        rho_func(0.0, {})
        first_call_args = mock_load_controller.control_step.call_args[0]
        first_dt = first_call_args[3]
        assert first_dt == 0.0
        
        # After first call, state_store["time"] is updated
        # Second call should calculate dt correctly
        rho_func(1.0, {})
        second_call_args = mock_load_controller.control_step.call_args[0]
        second_dt = second_call_args[3]
        # Verify dt was calculated correctly
        assert isinstance(second_dt, (float, int))
        # The dt should be > 0 (positive time step)
        assert second_dt >= 0.0
    
    def test_create_controlled_reactivity_negative_dt(self, mock_reactor_controller):
        """Test reactivity function handles negative dt (backwards time)."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=1.0
        rho_func(1.0, {})
        
        # Second call at t=0.5 (backwards)
        # This will result in negative dt, but should still work
        reactivity = rho_func(0.5, {})
        
        assert isinstance(reactivity, (float, int))
        # Verify dt was negative
        call_args = mock_reactor_controller.control_step.call_args[0]
        dt = call_args[3]
        assert dt < 0  # Negative dt
    
    def test_create_load_following_reactivity_state_temperature_only_via_get(self, mock_load_controller):
        """Test load following when state.get() is needed for temperature."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only temperature (no T_fuel), should use .get()
        state = {"temperature": 1220.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, int))
        call_args = mock_load_controller.control_step.call_args[0]
        assert call_args[1] == 1220.0  # Should use temperature

    def test_create_controlled_reactivity_state_power_only_no_temp_update(self, mock_reactor_controller):
        """Test reactivity when state has only 'power' (no T_fuel/temperature); temp stays initial."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        state = {"power": 0.95e6}  # No temperature or T_fuel
        reactivity = rho_func(1.0, state)
        assert isinstance(reactivity, (float, int))
        call_args = mock_reactor_controller.control_step.call_args[0]
        assert call_args[0] == 0.95e6
        assert call_args[1] == 1200.0  # Unchanged from initial

    def test_create_load_following_reactivity_state_power_only_no_temp_update(self, mock_load_controller):
        """Test load following when state has only 'power'; temperature stays initial."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        state = {"power": 1.1e6}
        reactivity = rho_func(1.0, state)
        assert isinstance(reactivity, (float, int))
        call_args = mock_load_controller.control_step.call_args[0]
        assert call_args[0] == 1.1e6
        assert call_args[1] == 1200.0
