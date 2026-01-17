"""
Advanced control system controllers for reactor operation.

This module implements PID controllers, reactor control systems, and
load-following algorithms for operational transient analysis.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger("smrforge.control.controllers")


@dataclass
class PIDController:
    """
    Proportional-Integral-Derivative (PID) controller.
    
    Standard PID controller implementation with anti-windup protection
    and output limiting.
    
    Attributes:
        Kp: Proportional gain
        Ki: Integral gain
        Kd: Derivative gain
        setpoint: Target value for the controlled variable
        output_min: Minimum controller output (for limiting)
        output_max: Maximum controller output (for limiting)
        integral: Current integral term (internal state)
        last_error: Previous error value (internal state)
        last_time: Previous time value (internal state)
    """
    
    Kp: float
    Ki: float
    Kd: float
    setpoint: float = 0.0
    output_min: float = -np.inf
    output_max: float = np.inf
    integral: float = field(default=0.0, init=False)
    last_error: float = field(default=0.0, init=False)
    last_time: Optional[float] = field(default=None, init=False)
    
    def update(
        self,
        measurement: float,
        time: float,
        dt: Optional[float] = None,
    ) -> float:
        """
        Update PID controller and compute control output.
        
        Args:
            measurement: Current process variable value
            time: Current time [s]
            dt: Time step [s]. If None, computed from last_time
            
        Returns:
            Control output
        """
        error = self.setpoint - measurement
        
        # Calculate time step
        if dt is None:
            if self.last_time is not None:
                dt = time - self.last_time
            else:
                dt = 0.0
        
        if dt <= 0.0:
            dt = 1e-6  # Avoid division by zero
        
        # Proportional term
        P = self.Kp * error
        
        # Integral term (with anti-windup)
        self.integral += error * dt
        
        # Anti-windup: limit integral if output is saturated
        I_unlimited = self.Ki * self.integral
        output_unlimited = P + I_unlimited
        
        if output_unlimited > self.output_max:
            self.integral = (self.output_max - P) / self.Ki if self.Ki != 0 else 0.0
        elif output_unlimited < self.output_min:
            self.integral = (self.output_min - P) / self.Ki if self.Ki != 0 else 0.0
        
        I = self.Ki * self.integral
        
        # Derivative term
        if self.last_time is not None and dt > 0:
            derivative = (error - self.last_error) / dt
        else:
            derivative = 0.0
        
        D = self.Kd * derivative
        
        # Total output
        output = P + I + D
        
        # Limit output
        output = np.clip(output, self.output_min, self.output_max)
        
        # Update state
        self.last_error = error
        self.last_time = time
        
        return output
    
    def reset(self):
        """Reset controller state (integral, error, time)."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = None
    
    def set_setpoint(self, setpoint: float):
        """Update setpoint value."""
        self.setpoint = setpoint


@dataclass
class ReactorController:
    """
    Reactor power and temperature control system.
    
    Implements multi-loop control for reactor operation with:
    - Power control (via control rod position)
    - Temperature control (via coolant flow or power)
    - Coordinated control logic
    
    Attributes:
        power_setpoint: Target power level [W]
        temperature_setpoint: Target temperature [K]
        power_controller: PID controller for power
        temperature_controller: PID controller for temperature
        rod_worth: Control rod reactivity worth [dk/k per % insertion]
        max_rod_speed: Maximum rod insertion/withdrawal speed [%/s]
        control_mode: Control mode ('power', 'temperature', 'coordinated')
    """
    
    power_setpoint: float  # W
    temperature_setpoint: float  # K
    power_controller: PIDController = field(init=False)
    temperature_controller: PIDController = field(init=False)
    rod_worth: float = -1e-3  # dk/k per % insertion (negative = shutdown)
    max_rod_speed: float = 1.0  # %/s
    control_mode: str = "coordinated"  # 'power', 'temperature', 'coordinated'
    
    def __post_init__(self):
        """Initialize PID controllers."""
        # Power controller: moderate gains for stability
        self.power_controller = PIDController(
            Kp=0.5,
            Ki=0.1,
            Kd=0.05,
            setpoint=self.power_setpoint,
            output_min=-100.0,  # % rod position
            output_max=100.0,
        )
        
        # Temperature controller: higher gains for faster response
        self.temperature_controller = PIDController(
            Kp=1.0,
            Ki=0.2,
            Kd=0.1,
            setpoint=self.temperature_setpoint,
            output_min=-100.0,
            output_max=100.0,
        )
    
    def control_step(
        self,
        power: float,
        temperature: float,
        time: float,
        dt: Optional[float] = None,
    ) -> Dict:
        """
        Execute one control step.
        
        Args:
            power: Current reactor power [W]
            temperature: Current average temperature [K]
            time: Current time [s]
            dt: Time step [s]
            
        Returns:
            Dictionary with control actions:
                - rod_position: Control rod position [%]
                - rod_speed: Rod insertion/withdrawal speed [%/s]
                - reactivity_change: Reactivity change [dk/k]
                - power_error: Power error [W]
                - temperature_error: Temperature error [K]
        """
        # Update setpoints if changed
        self.power_controller.set_setpoint(self.power_setpoint)
        self.temperature_controller.set_setpoint(self.temperature_setpoint)
        
        # Compute control signals
        power_signal = self.power_controller.update(power, time, dt)
        temp_signal = self.temperature_controller.update(temperature, time, dt)
        
        # Determine control action based on mode
        if self.control_mode == "power":
            rod_position = power_signal
        elif self.control_mode == "temperature":
            rod_position = temp_signal
        else:  # coordinated
            # Weighted combination: prioritize power but respond to temperature
            rod_position = 0.7 * power_signal + 0.3 * temp_signal
        
        # Limit rod position
        rod_position = np.clip(rod_position, 0.0, 100.0)
        
        # Calculate rod speed (rate-limited)
        rod_change = 0.0
        if hasattr(self, "_last_rod_position"):
            rod_change = rod_position - self._last_rod_position
            max_change = self.max_rod_speed * (dt if dt else 1.0)
            rod_change = np.clip(rod_change, -max_change, max_change)
            rod_position = self._last_rod_position + rod_change
        else:
            self._last_rod_position = 0.0
        
        self._last_rod_position = rod_position
        
        # Calculate reactivity change
        reactivity_change = rod_position * self.rod_worth
        
        # Calculate rod speed
        rod_speed = rod_change / (dt if dt else 1.0) if dt and dt > 0 else 0.0
        
        return {
            "rod_position": rod_position,
            "rod_speed": rod_speed,
            "reactivity_change": reactivity_change,
            "power_error": self.power_controller.last_error,
            "temperature_error": self.temperature_controller.last_error,
            "power_signal": power_signal,
            "temperature_signal": temp_signal,
        }
    
    def set_power_setpoint(self, setpoint: float):
        """Update power setpoint."""
        self.power_setpoint = setpoint
        self.power_controller.set_setpoint(setpoint)
    
    def set_temperature_setpoint(self, setpoint: float):
        """Update temperature setpoint."""
        self.temperature_setpoint = setpoint
        self.temperature_controller.set_setpoint(setpoint)
    
    def reset(self):
        """Reset all controllers."""
        self.power_controller.reset()
        self.temperature_controller.reset()
        if hasattr(self, "_last_rod_position"):
            self._last_rod_position = 0.0


@dataclass
class LoadFollowingController:
    """
    Load-following control algorithms.
    
    Implements algorithms for following electrical grid demand,
    including ramp rate limiting and power setpoint scheduling.
    
    Attributes:
        base_power: Base power level [W]
        max_ramp_rate: Maximum power ramp rate [W/s]
        demand_profile: Function that returns demand vs time [W]
        controller: ReactorController for power control
    """
    
    base_power: float  # W
    max_ramp_rate: float = 1e6  # W/s (typical: 1 MW/s for 100 MW reactor)
    demand_profile: Optional[Callable[[float], float]] = None
    controller: ReactorController = field(init=False)
    
    def __post_init__(self):
        """Initialize reactor controller."""
        self.controller = ReactorController(
            power_setpoint=self.base_power,
            temperature_setpoint=600.0,  # Default temperature setpoint
        )
    
    def get_demand(self, time: float) -> float:
        """
        Get power demand at given time.
        
        Args:
            time: Current time [s]
            
        Returns:
            Power demand [W]
        """
        if self.demand_profile is not None:
            return self.demand_profile(time)
        return self.base_power
    
    def ramp_limited_setpoint(
        self,
        target_power: float,
        current_power: float,
        dt: float,
    ) -> float:
        """
        Calculate ramp-limited power setpoint.
        
        Limits the rate of change of power setpoint to prevent
        excessive thermal stresses.
        
        Args:
            target_power: Desired power level [W]
            current_power: Current power setpoint [W]
            dt: Time step [s]
            
        Returns:
            Ramp-limited power setpoint [W]
        """
        power_change = target_power - current_power
        max_change = self.max_ramp_rate * dt
        
        if abs(power_change) <= max_change:
            return target_power
        
        # Limit the change
        limited_change = np.sign(power_change) * max_change
        return current_power + limited_change
    
    def control_step(
        self,
        power: float,
        temperature: float,
        time: float,
        dt: Optional[float] = None,
    ) -> Dict:
        """
        Execute load-following control step.
        
        Args:
            power: Current reactor power [W]
            temperature: Current average temperature [K]
            time: Current time [s]
            dt: Time step [s]
            
        Returns:
            Dictionary with control actions and load-following info
        """
        # Get demand
        demand = self.get_demand(time)
        
        # Calculate ramp-limited setpoint
        current_setpoint = self.controller.power_setpoint
        if dt is not None:
            new_setpoint = self.ramp_limited_setpoint(
                demand, current_setpoint, dt
            )
        else:
            new_setpoint = demand
        
        # Update controller setpoint
        self.controller.set_power_setpoint(new_setpoint)
        
        # Execute control step
        control_action = self.controller.control_step(power, temperature, time, dt)
        
        # Add load-following information
        control_action.update(
            {
                "demand": demand,
                "setpoint": new_setpoint,
                "ramp_rate": (new_setpoint - current_setpoint) / (dt if dt else 1.0),
            }
        )
        
        return control_action
    
    def set_demand_profile(self, profile: Callable[[float], float]):
        """Set demand profile function."""
        self.demand_profile = profile
    
    def reset(self):
        """Reset controller."""
        self.controller.reset()
