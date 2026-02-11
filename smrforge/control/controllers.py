"""
Advanced control system controllers for reactor operation.

This module implements PID controllers, reactor control systems,
load-following algorithms, and Model Predictive Control (MPC) for
operational transient analysis.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.control.controllers")

try:
    from scipy.optimize import minimize

    _SCIPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SCIPY_AVAILABLE = False
    logger.warning("scipy not available, MPC will use simplified optimization")


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
            new_setpoint = self.ramp_limited_setpoint(demand, current_setpoint, dt)
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


@dataclass
class ModelPredictiveController:
    """
    Model Predictive Control (MPC) for advanced reactor control.

    MPC is an advanced control strategy that:
    - Uses a model to predict future system behavior
    - Optimizes control actions over a prediction horizon
    - Handles constraints on inputs and states
    - Applies only the first control action (receding horizon)

    Attributes:
        prediction_horizon: Number of steps in prediction horizon
        control_horizon: Number of control steps to optimize (≤ prediction_horizon)
        dt: Time step [s]
        power_setpoint: Target power level [W]
        temperature_setpoint: Target temperature [K]
        Q: State weighting matrix (for power and temperature)
        R: Control weighting matrix (for rod position)
        rod_worth: Control rod reactivity worth [dk/k per % insertion]
        max_rod_position: Maximum rod position [%]
        min_rod_position: Minimum rod position [%]
        max_rod_rate: Maximum rod movement rate [%/s]
        max_power: Maximum allowed power [W]
        min_power: Minimum allowed power [W]
        max_temperature: Maximum allowed temperature [K]
        min_temperature: Minimum allowed temperature [K]
        system_model: Optional custom system model function
    """

    prediction_horizon: int = 10
    control_horizon: int = 5
    dt: float = 1.0  # s
    power_setpoint: float = 1e8  # W
    temperature_setpoint: float = 600.0  # K
    Q: Optional[np.ndarray] = None  # State weights [power, temperature]
    R: Optional[float] = None  # Control weight
    rod_worth: float = -1e-3  # dk/k per % insertion
    max_rod_position: float = 100.0  # %
    min_rod_position: float = 0.0  # %
    max_rod_rate: float = 1.0  # %/s
    max_power: float = 1.2e8  # W (120% of nominal)
    min_power: float = 0.0  # W
    max_temperature: float = 1000.0  # K
    min_temperature: float = 300.0  # K
    system_model: Optional[Callable] = None

    def __post_init__(self):
        """Initialize MPC parameters."""
        if self.control_horizon > self.prediction_horizon:
            self.control_horizon = self.prediction_horizon

        # Default state weighting: prioritize power tracking
        if self.Q is None:
            self.Q = np.array([1.0, 0.1])  # [power_weight, temperature_weight]

        # Default control weighting: penalize large control actions
        if self.R is None:
            self.R = 0.01

        # Initialize state history
        self.state_history: List[Dict] = []
        self.control_history: List[float] = []

    def _predict_system(
        self,
        initial_power: float,
        initial_temperature: float,
        initial_rod_position: float,
        control_sequence: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict system behavior over prediction horizon.

        Uses a simplified reactor model:
        - Power dynamics: dP/dt = (rho - beta)/Lambda * P
        - Temperature dynamics: dT/dt = (P - Q_cool) / C

        Args:
            initial_power: Initial power [W]
            initial_temperature: Initial temperature [K]
            initial_rod_position: Initial rod position [%]
            control_sequence: Sequence of rod positions [%] (length = control_horizon)

        Returns:
            Tuple of (power_prediction, temperature_prediction) arrays
        """
        if self.system_model is not None:
            # Use custom system model
            return self.system_model(
                initial_power,
                initial_temperature,
                initial_rod_position,
                control_sequence,
            )

        # Simplified reactor model
        power_pred = np.zeros(self.prediction_horizon + 1)
        temp_pred = np.zeros(self.prediction_horizon + 1)

        power_pred[0] = initial_power
        temp_pred[0] = initial_temperature

        # Reactor parameters (simplified)
        Lambda = 1e-3  # s (neutron generation time)
        beta = 0.007  # delayed neutron fraction
        rho_0 = 0.0  # Initial reactivity (critical)

        # Thermal parameters
        C = 1e8  # J/K (thermal capacitance)
        Q_cool_base = initial_power * 0.9  # Cooling capacity

        rod_pos = initial_rod_position

        for k in range(self.prediction_horizon):
            # Control action (hold last value if beyond control horizon)
            if k < self.control_horizon:
                rod_pos = control_sequence[k]
            # Else: hold last control value

            # Reactivity from rod position
            rho = rho_0 + self.rod_worth * rod_pos

            # Power dynamics: dP/dt = (rho - beta)/Lambda * P
            # Simplified: P[k+1] = P[k] * (1 + (rho - beta) * dt / Lambda)
            power_rate = (rho - beta) / Lambda
            power_pred[k + 1] = power_pred[k] * (1.0 + power_rate * self.dt)
            power_pred[k + 1] = max(0.0, power_pred[k + 1])  # Non-negative

            # Temperature dynamics: dT/dt = (P - Q_cool) / C
            # Cooling increases with temperature
            Q_cool = Q_cool_base * (1.0 + 0.001 * (temp_pred[k] - initial_temperature))
            temp_rate = (power_pred[k] - Q_cool) / C
            temp_pred[k + 1] = temp_pred[k] + temp_rate * self.dt
            temp_pred[k + 1] = max(self.min_temperature, temp_pred[k + 1])

        return (
            power_pred[1:],
            temp_pred[1:],
        )  # Return predictions (exclude initial state)

    def _objective_function(
        self,
        control_sequence: np.ndarray,
        current_power: float,
        current_temperature: float,
        current_rod_position: float,
    ) -> float:
        """
        Objective function for MPC optimization.

        Minimizes:
        - Tracking error (power and temperature)
        - Control effort (rod movement)
        - Constraint violations

        Args:
            control_sequence: Control sequence to evaluate [%]
            current_power: Current power [W]
            current_temperature: Current temperature [K]
            current_rod_position: Current rod position [%]

        Returns:
            Objective function value (to minimize)
        """
        # Predict system behavior
        power_pred, temp_pred = self._predict_system(
            current_power, current_temperature, current_rod_position, control_sequence
        )

        # Tracking error
        power_error = power_pred - self.power_setpoint
        temp_error = temp_pred - self.temperature_setpoint

        # Normalize errors
        power_error_norm = (
            power_error / self.power_setpoint
            if self.power_setpoint > 0
            else power_error
        )
        temp_error_norm = (
            temp_error / self.temperature_setpoint
            if self.temperature_setpoint > 0
            else temp_error
        )

        # Tracking cost
        tracking_cost = self.Q[0] * np.sum(power_error_norm**2) + self.Q[1] * np.sum(
            temp_error_norm**2
        )

        # Control effort cost
        control_changes = np.diff(
            np.concatenate([[current_rod_position], control_sequence])
        )
        control_cost = self.R * np.sum(control_changes**2)

        # Constraint violations (soft constraints)
        penalty = 0.0

        # Power constraints
        power_violations = np.maximum(0, power_pred - self.max_power) + np.maximum(
            0, self.min_power - power_pred
        )
        penalty += 1000.0 * np.sum(power_violations**2)

        # Temperature constraints
        temp_violations = np.maximum(0, temp_pred - self.max_temperature) + np.maximum(
            0, self.min_temperature - temp_pred
        )
        penalty += 1000.0 * np.sum(temp_violations**2)

        # Rod position constraints
        rod_violations = np.maximum(
            0, control_sequence - self.max_rod_position
        ) + np.maximum(0, self.min_rod_position - control_sequence)
        penalty += 1000.0 * np.sum(rod_violations**2)

        # Rod rate constraints
        max_change = self.max_rod_rate * self.dt
        rate_violations = np.maximum(0, np.abs(control_changes) - max_change)
        penalty += 1000.0 * np.sum(rate_violations**2)

        return tracking_cost + control_cost + penalty

    def _optimize_control(
        self,
        current_power: float,
        current_temperature: float,
        current_rod_position: float,
    ) -> np.ndarray:
        """
        Optimize control sequence.

        Args:
            current_power: Current power [W]
            current_temperature: Current temperature [K]
            current_rod_position: Current rod position [%]

        Returns:
            Optimal control sequence [%]
        """
        # Initial guess: current rod position
        initial_guess = np.full(self.control_horizon, current_rod_position)

        # Bounds: rod position limits
        bounds = [(self.min_rod_position, self.max_rod_position)] * self.control_horizon

        # Constraints: rod rate limits
        constraints = []
        for i in range(self.control_horizon):
            max_change = self.max_rod_rate * self.dt
            if i == 0:
                # First step: limit change from current position
                constraints.append(
                    {
                        "type": "ineq",
                        "fun": lambda x, idx=i: max_change
                        - abs(x[idx] - current_rod_position),
                    }
                )
            else:
                # Subsequent steps: limit change from previous step
                constraints.append(
                    {
                        "type": "ineq",
                        "fun": lambda x, idx=i: max_change - abs(x[idx] - x[idx - 1]),
                    }
                )

        if _SCIPY_AVAILABLE:
            # Use scipy optimization
            result = minimize(
                self._objective_function,
                initial_guess,
                args=(current_power, current_temperature, current_rod_position),
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 100, "ftol": 1e-6},
            )

            if result.success:
                return result.x
            else:
                logger.warning(f"MPC optimization did not converge: {result.message}")
                # Fallback to initial guess
                return initial_guess
        else:
            # Simplified optimization: gradient descent
            return self._simple_optimize(
                current_power, current_temperature, current_rod_position, initial_guess
            )

    def _simple_optimize(
        self,
        current_power: float,
        current_temperature: float,
        current_rod_position: float,
        initial_guess: np.ndarray,
    ) -> np.ndarray:
        """
        Simplified optimization when scipy is not available.

        Uses gradient-free search with multiple random restarts.
        """
        best_control = initial_guess.copy()
        best_cost = self._objective_function(
            best_control, current_power, current_temperature, current_rod_position
        )

        # Random search with multiple restarts
        n_restarts = 20
        for _ in range(n_restarts):
            # Random initial guess
            candidate = np.random.uniform(
                self.min_rod_position, self.max_rod_position, self.control_horizon
            )

            # Local search: try small perturbations
            for _ in range(10):
                perturbation = np.random.normal(0, 1.0, self.control_horizon)
                candidate_new = candidate + perturbation
                candidate_new = np.clip(
                    candidate_new, self.min_rod_position, self.max_rod_position
                )

                cost = self._objective_function(
                    candidate_new,
                    current_power,
                    current_temperature,
                    current_rod_position,
                )

                if cost < best_cost:
                    best_cost = cost
                    best_control = candidate_new.copy()
                    candidate = candidate_new

        return best_control

    def control_step(
        self,
        power: float,
        temperature: float,
        rod_position: float,
        time: Optional[float] = None,
    ) -> Dict:
        """
        Execute MPC control step.

        Args:
            power: Current reactor power [W]
            temperature: Current average temperature [K]
            rod_position: Current rod position [%]
            time: Current time [s] (optional, for logging)

        Returns:
            Dictionary with control action and MPC information:
                - rod_position: Optimal rod position [%]
                - rod_rate: Rod movement rate [%/s]
                - predicted_power: Predicted power trajectory
                - predicted_temperature: Predicted temperature trajectory
                - control_sequence: Full optimized control sequence
                - cost: Objective function value
        """
        # Optimize control sequence
        control_sequence = self._optimize_control(power, temperature, rod_position)

        # Apply first control action (receding horizon)
        optimal_rod_position = control_sequence[0]

        # Limit rod movement rate
        max_change = self.max_rod_rate * self.dt
        rod_change = optimal_rod_position - rod_position
        if abs(rod_change) > max_change:
            optimal_rod_position = rod_position + np.sign(rod_change) * max_change

        # Clip to bounds
        optimal_rod_position = np.clip(
            optimal_rod_position, self.min_rod_position, self.max_rod_position
        )

        # Calculate rod rate
        rod_rate = (optimal_rod_position - rod_position) / self.dt

        # Get predictions for visualization
        power_pred, temp_pred = self._predict_system(
            power, temperature, rod_position, control_sequence
        )

        # Calculate cost
        cost = self._objective_function(
            control_sequence, power, temperature, rod_position
        )

        # Store history
        self.state_history.append(
            {
                "power": power,
                "temperature": temperature,
                "rod_position": rod_position,
                "time": time,
            }
        )
        self.control_history.append(optimal_rod_position)

        return {
            "rod_position": optimal_rod_position,
            "rod_rate": rod_rate,
            "predicted_power": power_pred,
            "predicted_temperature": temp_pred,
            "control_sequence": control_sequence,
            "cost": cost,
            "setpoint_power": self.power_setpoint,
            "setpoint_temperature": self.temperature_setpoint,
        }

    def set_setpoints(
        self,
        power_setpoint: Optional[float] = None,
        temperature_setpoint: Optional[float] = None,
    ):
        """Update setpoints."""
        if power_setpoint is not None:
            self.power_setpoint = power_setpoint
        if temperature_setpoint is not None:
            self.temperature_setpoint = temperature_setpoint

    def reset(self):
        """Reset controller state."""
        self.state_history = []
        self.control_history = []

    def set_demand_profile(self, profile: Callable[[float], float]):
        """Set demand profile function."""
        self.demand_profile = profile

    def reset(self):
        """Reset controller."""
        self.controller.reset()
