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
        controller = LoadFollowingController(
            base_power=1e6,
            max_ramp_rate=1e5,
        )
        
        # Define and set demand profile
        def demand(t):
            return 1e6 if t < 1.0 else 0.9e6
        
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
