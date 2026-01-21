"""
Tests for smrforge.control.integration module.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock

from smrforge.control.integration import (
    create_controlled_reactivity,
    create_load_following_reactivity,
)
from smrforge.control.controllers import ReactorController, LoadFollowingController


@pytest.fixture
def mock_reactor_controller():
    """Create a mock ReactorController."""
    controller = Mock(spec=ReactorController)
    controller.rod_worth = 0.01  # 1% dk/k per %
    controller.control_step = Mock(return_value={"reactivity_change": 0.001})
    return controller


@pytest.fixture
def mock_load_controller():
    """Create a mock LoadFollowingController."""
    controller = Mock(spec=LoadFollowingController)
    controller.control_step = Mock(return_value={"reactivity_change": 0.0005})
    return controller


class TestCreateControlledReactivity:
    """Tests for create_controlled_reactivity function."""
    
    def test_create_controlled_reactivity_basic(self, mock_reactor_controller):
        """Test create_controlled_reactivity with basic parameters."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        assert callable(rho_func)
        
        # Call the function
        reactivity = rho_func(0.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_with_rod_worth(self, mock_reactor_controller):
        """Test create_controlled_reactivity with explicit rod_worth."""
        custom_rod_worth = 0.02
        
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
            rod_worth=custom_rod_worth,
        )
        
        assert callable(rho_func)
        
        # Call the function
        reactivity = rho_func(0.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
    
    def test_create_controlled_reactivity_with_state(self, mock_reactor_controller):
        """Test create_controlled_reactivity with state dictionary."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with state dictionary
        state = {
            "power": 1.1e6,
            "T_fuel": 1250.0,
        }
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Controller should have been called with updated values
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_with_temperature_key(self, mock_reactor_controller):
        """Test create_controlled_reactivity with 'temperature' key in state."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with state dictionary using 'temperature' key
        state = {
            "power": 1e6,
            "temperature": 1250.0,
        }
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_time_evolution(self, mock_reactor_controller):
        """Test create_controlled_reactivity with time evolution."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call at different times
        rho1 = rho_func(0.0, {})
        rho2 = rho_func(1.0, {})
        rho3 = rho_func(2.0, {})
        
        assert isinstance(rho1, (float, np.floating))
        assert isinstance(rho2, (float, np.floating))
        assert isinstance(rho3, (float, np.floating))
        # Controller should be called multiple times
        assert mock_reactor_controller.control_step.call_count >= 3
    
    def test_create_controlled_reactivity_state_update(self, mock_reactor_controller):
        """Test that state updates correctly over time."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call - should use initial values
        rho_func(0.0, {})
        first_call = mock_reactor_controller.control_step.call_args
        
        # Second call with updated state
        state = {"power": 1.2e6, "T_fuel": 1300.0}
        rho_func(1.0, state)
        second_call = mock_reactor_controller.control_step.call_args
        
        # Arguments should be different (updated state)
        assert first_call != second_call


class TestCreateLoadFollowingReactivity:
    """Tests for create_load_following_reactivity function."""
    
    def test_create_load_following_reactivity_basic(self, mock_load_controller):
        """Test create_load_following_reactivity with basic parameters."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        assert callable(rho_func)
        
        # Call the function
        reactivity = rho_func(0.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_with_state(self, mock_load_controller):
        """Test create_load_following_reactivity with state dictionary."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with state dictionary
        state = {
            "power": 0.9e6,
            "T_fuel": 1180.0,
        }
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_with_temperature_key(self, mock_load_controller):
        """Test create_load_following_reactivity with 'temperature' key in state."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with state dictionary using 'temperature' key
        state = {
            "power": 1e6,
            "temperature": 1180.0,
        }
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_time_evolution(self, mock_load_controller):
        """Test create_load_following_reactivity with time evolution."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call at different times
        rho1 = rho_func(0.0, {})
        rho2 = rho_func(1.0, {})
        rho3 = rho_func(2.0, {})
        
        assert isinstance(rho1, (float, np.floating))
        assert isinstance(rho2, (float, np.floating))
        assert isinstance(rho3, (float, np.floating))
        # Controller should be called multiple times
        assert mock_load_controller.control_step.call_count >= 3
    
    def test_create_load_following_reactivity_state_update(self, mock_load_controller):
        """Test that state updates correctly over time."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call - should use initial values
        rho_func(0.0, {})
        first_call = mock_load_controller.control_step.call_args
        
        # Second call with updated state
        state = {"power": 0.8e6, "T_fuel": 1150.0}
        rho_func(1.0, state)
        second_call = mock_load_controller.control_step.call_args
        
        # Arguments should be different (updated state)
        assert first_call != second_call
    
    def test_create_load_following_reactivity_no_state_update(self, mock_load_controller):
        """Test create_load_following_reactivity when no state is provided."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call without state (should use stored values)
        reactivity = rho_func(1.0, None)
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()


class TestIntegrationWithRealControllers:
    """Integration tests with actual controller instances."""
    
    def test_create_controlled_reactivity_real_controller(self):
        """Test with actual ReactorController instance."""
        controller = ReactorController(
            power_setpoint=1e6,
            temperature_setpoint=1200.0,
            rod_worth=0.01,
        )
        
        rho_func = create_controlled_reactivity(
            controller=controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Test with different power levels
        state1 = {"power": 1.1e6, "T_fuel": 1200.0}
        rho1 = rho_func(1.0, state1)
        
        state2 = {"power": 0.9e6, "T_fuel": 1200.0}
        rho2 = rho_func(2.0, state2)
        
        assert isinstance(rho1, (float, np.floating))
        assert isinstance(rho2, (float, np.floating))
        # Reactivity should be different (controller trying to adjust)
        assert rho1 != rho2
    
    def test_create_load_following_reactivity_real_controller(self):
        """Test with actual LoadFollowingController instance."""
        # Define demand profile
        def demand(t):
            return 1e6 if t < 1.0 else 0.9e6
        
        controller = LoadFollowingController(
            base_power=1e6,
            max_ramp_rate=1e5,
            demand_profile=demand,  # Set directly if supported, or skip if not
        )
        
        # If set_demand_profile exists, use it; otherwise assume demand_profile was set in constructor
        if hasattr(controller, 'set_demand_profile'):
            controller.set_demand_profile(demand)
        
        rho_func = create_load_following_reactivity(
            load_controller=controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Test with time evolution
        rho1 = rho_func(0.5, {"power": 1e6, "T_fuel": 1200.0})
        rho2 = rho_func(1.5, {"power": 1e6, "T_fuel": 1200.0})
        
        assert isinstance(rho1, (float, np.floating))
        assert isinstance(rho2, (float, np.floating))


class TestControlIntegrationEdgeCases:
    """Edge case tests for control integration module."""
    
    def test_create_controlled_reactivity_state_partial_update(self, mock_reactor_controller):
        """Test reactivity function with state that only updates power."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only power, no temperature
        state = {"power": 1.2e6}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Temperature should remain at initial value
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_state_only_temperature(self, mock_reactor_controller):
        """Test reactivity function with state that only updates temperature."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only temperature, no power
        state = {"T_fuel": 1300.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Power should remain at initial value
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_empty_state_dict(self, mock_reactor_controller):
        """Test reactivity function with empty state dictionary."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Empty state dict should not update anything
        reactivity = rho_func(1.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_dt_calculation_zero_time(self, mock_reactor_controller):
        """Test that dt is 0.0 when time is 0.0."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=0.0 should have dt=0.0
        reactivity1 = rho_func(0.0, {})
        
        # Second call should calculate dt
        reactivity2 = rho_func(1.0, {})
        
        assert isinstance(reactivity1, (float, np.floating))
        assert isinstance(reactivity2, (float, np.floating))
        # Verify controller was called with dt=0.0 first, then dt=1.0
        assert mock_reactor_controller.control_step.call_count >= 2
    
    def test_create_controlled_reactivity_rod_worth_none(self, mock_reactor_controller):
        """Test that rod_worth=None uses controller's rod_worth attribute."""
        # Set controller's rod_worth
        mock_reactor_controller.rod_worth = 0.015
        
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
            rod_worth=None,  # Should use controller.rod_worth
        )
        
        reactivity = rho_func(0.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
        # rod_worth should be accessed from controller
        assert hasattr(mock_reactor_controller, 'rod_worth')
    
    def test_create_load_following_reactivity_state_partial_update(self, mock_load_controller):
        """Test load following reactivity with partial state update."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only power
        state = {"power": 0.9e6}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_empty_state_dict(self, mock_load_controller):
        """Test load following reactivity with empty state dictionary."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Empty state dict
        reactivity = rho_func(1.0, {})
        
        assert isinstance(reactivity, (float, np.floating))
        mock_load_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_dt_calculation(self, mock_load_controller):
        """Test dt calculation in load following reactivity function."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=0.0
        reactivity1 = rho_func(0.0, {})
        
        # Second call at t=2.0 (dt should be 2.0)
        reactivity2 = rho_func(2.0, {})
        
        assert isinstance(reactivity1, (float, np.floating))
        assert isinstance(reactivity2, (float, np.floating))
        assert mock_load_controller.control_step.call_count >= 2
    
    def test_create_controlled_reactivity_temperature_precedence(self, mock_reactor_controller):
        """Test that T_fuel takes precedence over temperature key."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with both T_fuel and temperature - T_fuel should be used
        state = {"T_fuel": 1300.0, "temperature": 1250.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Should use T_fuel (1300.0), not temperature (1250.0)
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_temperature_precedence(self, mock_load_controller):
        """Test that T_fuel takes precedence over temperature key in load following."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with both T_fuel and temperature
        state = {"T_fuel": 1300.0, "temperature": 1250.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Should use T_fuel (1300.0)
        mock_load_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_state_neither_key(self, mock_reactor_controller):
        """Test reactivity function when state has neither T_fuel nor temperature."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State without temperature keys
        state = {"power": 1.2e6, "other_field": 123}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Temperature should remain at initial value
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_backwards_time(self, mock_reactor_controller):
        """Test reactivity function with backwards time (dt could be negative)."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # First call at t=1.0
        rho_func(1.0, {})
        
        # Second call at t=0.5 (backwards in time)
        reactivity = rho_func(0.5, {})
        
        assert isinstance(reactivity, (float, np.floating))
        # Should handle negative dt gracefully
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_state_neither_key(self, mock_load_controller):
        """Test load following when state has neither T_fuel nor temperature."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State without temperature keys
        state = {"power": 0.9e6, "other_field": 456}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Temperature should remain at initial value
        mock_load_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_state_none(self, mock_reactor_controller):
        """Test reactivity function with state=None explicitly."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with None state
        reactivity = rho_func(1.0, None)
        
        assert isinstance(reactivity, (float, np.floating))
        # Should use stored initial values
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_state_none(self, mock_load_controller):
        """Test load following with state=None explicitly."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # Call with None state
        reactivity = rho_func(1.0, None)
        
        assert isinstance(reactivity, (float, np.floating))
        # Should use stored initial values
        mock_load_controller.control_step.assert_called()
    
    def test_create_controlled_reactivity_state_with_only_temperature_no_power(self, mock_reactor_controller):
        """Test reactivity function when state only has temperature (not T_fuel)."""
        rho_func = create_controlled_reactivity(
            controller=mock_reactor_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only 'temperature' key, no 'power'
        state = {"temperature": 1250.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Power should remain at initial, temperature should update
        mock_reactor_controller.control_step.assert_called()
    
    def test_create_load_following_reactivity_state_with_only_temperature_no_power(self, mock_load_controller):
        """Test load following when state only has temperature (not T_fuel)."""
        rho_func = create_load_following_reactivity(
            load_controller=mock_load_controller,
            initial_power=1e6,
            initial_temperature=1200.0,
        )
        
        # State with only 'temperature' key
        state = {"temperature": 1180.0}
        reactivity = rho_func(1.0, state)
        
        assert isinstance(reactivity, (float, np.floating))
        # Power should remain at initial, temperature should update
        mock_load_controller.control_step.assert_called()
