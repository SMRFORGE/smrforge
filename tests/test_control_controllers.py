"""
Unit tests for control system controllers.
"""

import numpy as np
import pytest

from smrforge.control.controllers import (
    LoadFollowingController,
    PIDController,
    ReactorController,
)


class TestPIDController:
    """Tests for PIDController class."""

    def test_pid_basic(self):
        """Test basic PID controller operation."""
        controller = PIDController(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=100.0)

        # Start at setpoint
        output = controller.update(100.0, time=0.0, dt=1.0)
        assert output == 0.0  # No error, no output

        # Below setpoint
        output = controller.update(90.0, time=1.0, dt=1.0)
        assert output > 0  # Should increase output

        # Above setpoint
        output = controller.update(110.0, time=2.0, dt=1.0)
        assert output < 0  # Should decrease output

    def test_pid_integral_windup(self):
        """Test anti-windup protection."""
        controller = PIDController(
            Kp=1.0, Ki=10.0, Kd=0.0, setpoint=100.0, output_max=50.0
        )

        # Large error should saturate output
        output1 = controller.update(0.0, time=0.0, dt=1.0)
        output2 = controller.update(0.0, time=1.0, dt=1.0)

        # Output should be limited
        assert output1 <= 50.0
        assert output2 <= 50.0

    def test_pid_reset(self):
        """Test controller reset."""
        controller = PIDController(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=100.0)

        # Update a few times
        controller.update(90.0, time=0.0, dt=1.0)
        controller.update(95.0, time=1.0, dt=1.0)

        # Reset
        controller.reset()

        # Check state is reset
        assert controller.integral == 0.0
        assert controller.last_error == 0.0
        assert controller.last_time is None

    def test_pid_setpoint_change(self):
        """Test setpoint update."""
        controller = PIDController(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=100.0)

        controller.set_setpoint(150.0)
        assert controller.setpoint == 150.0

        # Should now try to reach new setpoint
        output = controller.update(100.0, time=0.0, dt=1.0)
        assert output > 0  # Should increase to reach 150


class TestReactorController:
    """Tests for ReactorController class."""

    def test_reactor_controller_init(self):
        """Test reactor controller initialization."""
        controller = ReactorController(power_setpoint=1e6, temperature_setpoint=1200.0)

        assert controller.power_setpoint == 1e6
        assert controller.temperature_setpoint == 1200.0
        assert controller.power_controller is not None
        assert controller.temperature_controller is not None

    def test_control_step_power_mode(self):
        """Test control step in power mode."""
        controller = ReactorController(
            power_setpoint=1e6, temperature_setpoint=1200.0, control_mode="power"
        )

        action = controller.control_step(
            power=0.9e6, temperature=1200.0, time=0.0, dt=1.0
        )

        assert "rod_position" in action
        assert "reactivity_change" in action
        assert "power_error" in action
        assert action["rod_position"] >= 0
        assert action["rod_position"] <= 100.0

    def test_control_step_temperature_mode(self):
        """Test control step in temperature mode."""
        controller = ReactorController(
            power_setpoint=1e6, temperature_setpoint=1200.0, control_mode="temperature"
        )

        action = controller.control_step(
            power=1e6, temperature=1300.0, time=0.0, dt=1.0
        )

        # High temperature should reduce power (insert rods)
        assert action["rod_position"] >= 0

    def test_control_step_coordinated_mode(self):
        """Test control step in coordinated mode."""
        controller = ReactorController(
            power_setpoint=1e6,
            temperature_setpoint=1200.0,
            control_mode="coordinated",
        )

        action = controller.control_step(
            power=0.9e6, temperature=1300.0, time=0.0, dt=1.0
        )

        # Should consider both power and temperature
        assert "power_signal" in action
        assert "temperature_signal" in action

    def test_setpoint_updates(self):
        """Test setpoint update methods."""
        controller = ReactorController(power_setpoint=1e6, temperature_setpoint=1200.0)

        controller.set_power_setpoint(1.2e6)
        assert controller.power_setpoint == 1.2e6
        assert controller.power_controller.setpoint == 1.2e6

        controller.set_temperature_setpoint(1300.0)
        assert controller.temperature_setpoint == 1300.0
        assert controller.temperature_controller.setpoint == 1300.0

    def test_reset(self):
        """Test controller reset."""
        controller = ReactorController(power_setpoint=1e6, temperature_setpoint=1200.0)

        # Update a few times
        controller.control_step(1e6, 1200.0, 0.0, 1.0)
        controller.control_step(1e6, 1200.0, 1.0, 1.0)

        controller.reset()

        # Check controllers are reset
        assert controller.power_controller.integral == 0.0
        assert controller.temperature_controller.integral == 0.0


class TestLoadFollowingController:
    """Tests for LoadFollowingController class."""

    def test_load_following_init(self):
        """Test load-following controller initialization."""
        controller = LoadFollowingController(base_power=1e6, max_ramp_rate=1e5)

        assert controller.base_power == 1e6
        assert controller.max_ramp_rate == 1e5
        assert controller.controller is not None

    def test_get_demand_no_profile(self):
        """Test demand retrieval without profile."""
        controller = LoadFollowingController(base_power=1e6)

        demand = controller.get_demand(0.0)
        assert demand == 1e6

    def test_get_demand_with_profile(self):
        """Test demand retrieval with profile."""

        def profile(t):
            return 1e6 if t < 100 else 1.2e6

        controller = LoadFollowingController(base_power=1e6)
        controller.set_demand_profile(profile)

        assert controller.get_demand(50.0) == 1e6
        assert controller.get_demand(150.0) == 1.2e6

    def test_ramp_limited_setpoint(self):
        """Test ramp-limited setpoint calculation."""
        controller = LoadFollowingController(base_power=1e6, max_ramp_rate=1e5)

        # Small change: should allow full change
        setpoint = controller.ramp_limited_setpoint(
            target_power=1.05e6, current_power=1e6, dt=1.0
        )
        assert setpoint == 1.05e6

        # Large change: should limit ramp rate
        setpoint = controller.ramp_limited_setpoint(
            target_power=2e6, current_power=1e6, dt=1.0
        )
        # Should be limited to max_ramp_rate * dt = 1e5
        assert setpoint == 1.1e6

    def test_control_step(self):
        """Test load-following control step."""

        def profile(t):
            return 1e6 if t < 10 else 1.2e6

        controller = LoadFollowingController(base_power=1e6, max_ramp_rate=1e5)
        controller.set_demand_profile(profile)

        action = controller.control_step(
            power=1e6, temperature=1200.0, time=5.0, dt=1.0
        )

        assert "demand" in action
        assert "setpoint" in action
        assert "ramp_rate" in action
        assert action["demand"] == 1e6

    def test_reset(self):
        """Test controller reset."""
        controller = LoadFollowingController(base_power=1e6)

        controller.control_step(1e6, 1200.0, 0.0, 1.0)
        controller.reset()

        # Controller should be reset
        assert controller.controller.power_controller.integral == 0.0
