"""
Integration of control systems with transient solvers.

This module provides utilities to integrate PID controllers and load-following
controllers with the point kinetics transient solver.
"""

from typing import Callable, Dict, Optional

from ..utils.logging import get_logger
from .controllers import LoadFollowingController, ReactorController

logger = get_logger("smrforge.control.integration")


def create_controlled_reactivity(
    controller: ReactorController,
    initial_power: float,
    initial_temperature: float,
    rod_worth: Optional[float] = None,
) -> Callable[[float, Dict], float]:
    """
    Create a reactivity function that uses a reactor controller.

    This function returns a callable that can be used as `rho_external`
    in `PointKineticsSolver.solve_transient()`. The controller will
    automatically adjust control rod position based on power and temperature.

    Args:
        controller: ReactorController instance
        initial_power: Initial reactor power [W]
        initial_temperature: Initial average temperature [K]
        rod_worth: Control rod reactivity worth [dk/k per %]. If None, uses
            controller's rod_worth attribute.

    Returns:
        Callable function rho(t, state) that returns reactivity [dk/k]

    Example:
        >>> from smrforge.control import ReactorController
        >>> from smrforge.control.integration import create_controlled_reactivity
        >>> from smrforge.safety.transients import PointKineticsSolver
        >>>
        >>> controller = ReactorController(
        ...     power_setpoint=1e6,  # 1 MW
        ...     temperature_setpoint=1200.0  # K
        ... )
        >>>
        >>> rho_controlled = create_controlled_reactivity(
        ...     controller,
        ...     initial_power=1e6,
        ...     initial_temperature=1200.0
        ... )
        >>>
        >>> # Use in transient solver
        >>> result = solver.solve_transient(
        ...     rho_external=lambda t: rho_controlled(t, {}),
        ...     ...
        ... )
    """
    if rod_worth is None:
        rod_worth = controller.rod_worth

    # Store state for controller
    state_store = {
        "power": initial_power,
        "temperature": initial_temperature,
        "time": 0.0,
    }

    def reactivity_function(t: float, state: Optional[Dict] = None) -> float:
        """
        Compute reactivity from controller.

        Args:
            t: Current time [s]
            state: Optional state dictionary with 'power' and 'temperature'

        Returns:
            Reactivity [dk/k]
        """
        # Update state if provided
        if state is not None:
            if "power" in state:
                state_store["power"] = state["power"]
            if "T_fuel" in state or "temperature" in state:
                state_store["temperature"] = state.get(
                    "T_fuel", state.get("temperature", state_store["temperature"])
                )

        # Calculate time step
        dt = t - state_store["time"] if state_store["time"] > 0 else 0.0

        # Get control action
        control_action = controller.control_step(
            state_store["power"],
            state_store["temperature"],
            t,
            dt,
        )

        # Update stored state
        state_store["time"] = t

        # Return reactivity change
        return control_action["reactivity_change"]

    return reactivity_function


def create_load_following_reactivity(
    load_controller: LoadFollowingController,
    initial_power: float,
    initial_temperature: float,
) -> Callable[[float, Dict], float]:
    """
    Create a reactivity function for load-following operation.

    This function returns a callable that implements load-following control,
    automatically adjusting reactor power to follow grid demand.

    Args:
        load_controller: LoadFollowingController instance
        initial_power: Initial reactor power [W]
        initial_temperature: Initial average temperature [K]

    Returns:
        Callable function rho(t, state) that returns reactivity [dk/k]

    Example:
        >>> from smrforge.control import LoadFollowingController
        >>> from smrforge.control.integration import create_load_following_reactivity
        >>>
        >>> # Define demand profile
        >>> def demand(t):
        ...     if t < 3600:
        ...         return 1e6  # 1 MW
        ...     elif t < 7200:
        ...         return 0.8e6  # 0.8 MW (80% power)
        ...     else:
        ...         return 1.2e6  # 1.2 MW (120% power)
        >>>
        >>> controller = LoadFollowingController(
        ...     base_power=1e6,
        ...     max_ramp_rate=1e5  # 100 kW/s
        ... )
        >>> controller.set_demand_profile(demand)
        >>>
        >>> rho_load_following = create_load_following_reactivity(
        ...     controller,
        ...     initial_power=1e6,
        ...     initial_temperature=1200.0
        ... )
    """
    # Store state for controller
    state_store = {
        "power": initial_power,
        "temperature": initial_temperature,
        "time": 0.0,
    }

    def reactivity_function(t: float, state: Optional[Dict] = None) -> float:
        """
        Compute reactivity from load-following controller.

        Args:
            t: Current time [s]
            state: Optional state dictionary with 'power' and 'temperature'

        Returns:
            Reactivity [dk/k]
        """
        # Update state if provided
        if state is not None:
            if "power" in state:
                state_store["power"] = state["power"]
            if "T_fuel" in state or "temperature" in state:
                state_store["temperature"] = state.get(
                    "T_fuel", state.get("temperature", state_store["temperature"])
                )

        # Calculate time step
        dt = t - state_store["time"] if state_store["time"] > 0 else 0.0

        # Get control action
        control_action = load_controller.control_step(
            state_store["power"],
            state_store["temperature"],
            t,
            dt,
        )

        # Update stored state
        state_store["time"] = t

        # Return reactivity change
        return control_action["reactivity_change"]

    return reactivity_function
