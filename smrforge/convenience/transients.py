"""
Simplified point kinetics API for easy transient analysis.

Provides high-level convenience functions for common transient scenarios,
wrapping the more complex PointKineticsSolver API for easier adoption.

Based on PyRK's clean, simple API design while maintaining full access
to advanced features via the underlying solver.
"""

from typing import Callable, Dict, Optional, Tuple

import numpy as np

try:
    from ..safety.transients import (
        PointKineticsParameters,
        PointKineticsSolver,
        TransientConditions,
        TransientType,
    )

    _SAFETY_AVAILABLE = True
except ImportError:
    _SAFETY_AVAILABLE = False


def quick_transient(
    power: float,
    temperature: float,
    reactivity_insertion: Optional[float] = None,
    transient_type: str = "reactivity_insertion",
    duration: float = 100.0,
    scram_available: bool = True,
    scram_delay: float = 1.0,
    **kwargs,
) -> Dict:
    """
    Quick transient analysis with sensible defaults.

    Simplified API for point kinetics transients. Provides common
    transient scenarios with default parameters while allowing
    customization for advanced users.

    Args:
        power: Initial reactor power [W].
        temperature: Initial temperature [K] (average of fuel and moderator).
        reactivity_insertion: Reactivity inserted [dk/k] (default: 0.001 = 1 m$).
            Only used for reactivity_insertion transient type.
        transient_type: Type of transient scenario:
            - "reactivity_insertion": Reactivity insertion accident (RIA)
            - "reactivity_step": Step change in reactivity
            - "power_change": Power change transient
            - "decay_heat": Decay heat removal (long-term)
        duration: Simulation duration [s] (default: 100.0).
        scram_available: Whether scram is available (default: True).
        scram_delay: Scram delay time [s] (default: 1.0).
        **kwargs: Additional parameters passed to PointKineticsSolver.

    Returns:
        Dictionary containing time history with keys:
            - "time": Time array [s]
            - "power": Power array [W]
            - "T_fuel": Fuel temperature array [K]
            - "T_moderator": Moderator temperature array [K]
            - "reactivity": Total reactivity array [dk/k]

    Raises:
        ImportError: If safety module is not available.
        ValueError: If inputs are invalid.

    Example:
        Basic reactivity insertion:
        >>> from smrforge.convenience.transients import quick_transient
        >>> result = quick_transient(
        ...     power=1e6,  # 1 MWth
        ...     temperature=1200.0,  # K
        ...     reactivity_insertion=0.002,  # 2 m$
        ...     duration=100.0  # 100 seconds
        ... )
        >>> peak_power = np.max(result["power"])
        >>> print(f"Peak power: {peak_power/1e6:.2f} MW")

        Long-term decay heat removal:
        >>> result = quick_transient(
        ...     power=1e6,
        ...     temperature=1200.0,
        ...     transient_type="decay_heat",
        ...     duration=72*3600,  # 72 hours
        ...     long_term_optimization=True  # Enable optimizations
        ... )
        >>> final_temp = result["T_fuel"][-1]
        >>> print(f"Final temperature: {final_temp:.1f} K")
    """
    if not _SAFETY_AVAILABLE:
        raise ImportError(
            "Safety module not available. Install required dependencies."
        )

    if power <= 0:
        raise ValueError(f"power must be > 0, got {power}")
    if temperature <= 0:
        raise ValueError(f"temperature must be > 0, got {temperature}")
    if duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration}")

    # Default reactivity insertion for reactivity_insertion type
    if reactivity_insertion is None:
        if transient_type == "reactivity_insertion":
            reactivity_insertion = 0.001  # 1 m$ default
        else:
            reactivity_insertion = 0.0

    # Create point kinetics parameters with default HTGR values
    beta = np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4])
    lambda_d = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])

    params = PointKineticsParameters(
        beta=beta,
        lambda_d=lambda_d,
        alpha_fuel=kwargs.pop("alpha_fuel", -3.5e-5),  # Negative = stable
        alpha_moderator=kwargs.pop("alpha_moderator", -1.0e-5),
        Lambda=kwargs.pop("Lambda", 5e-4),  # Prompt neutron lifetime [s]
        fuel_heat_capacity=kwargs.pop("fuel_heat_capacity", 1e8),  # J/K
        moderator_heat_capacity=kwargs.pop("moderator_heat_capacity", 5e8),  # J/K
    )

    # Create solver
    solver = PointKineticsSolver(params)

    # Define reactivity function based on transient type
    if transient_type == "reactivity_insertion":
        # Reactivity insertion followed by scram (if available)
        def rho_external(t):
            if t < 1.0:  # 1 second insertion time
                return reactivity_insertion * (t / 1.0)  # Ramp insertion
            elif scram_available and t >= 1.0 + scram_delay:
                # Scram: large negative reactivity
                scram_time = 2.0  # 2 seconds to fully insert
                if t < 1.0 + scram_delay + scram_time:
                    fraction = (t - 1.0 - scram_delay) / scram_time
                    return reactivity_insertion - 0.20 * fraction  # -20% dk/k
                else:
                    return reactivity_insertion - 0.20  # Fully inserted
            else:
                return reactivity_insertion
    elif transient_type == "reactivity_step":
        # Step change in reactivity
        def rho_external(t):
            return reactivity_insertion if t > 0 else 0.0
    elif transient_type == "power_change":
        # Power change transient (no reactivity, just temperature feedback)
        def rho_external(t):
            return 0.0
    elif transient_type == "decay_heat":
        # Decay heat removal (no reactivity, just decay heat)
        def rho_external(t):
            return -0.05 if scram_available and t >= scram_delay else 0.0  # Scram
    else:
        raise ValueError(
            f"Unknown transient_type: {transient_type}. "
            f"Must be one of: reactivity_insertion, reactivity_step, "
            f"power_change, decay_heat"
        )

    # Define power removal function
    if transient_type == "decay_heat":
        # Long-term decay heat removal (simplified)
        from ..safety.transients import decay_heat_ans_standard

        def power_removal(t, T_fuel, T_mod):
            # Decay heat follows ANS standard
            P_decay = decay_heat_ans_standard(np.array([t]), power, duration)[0]
            # Heat removal proportional to temperature difference
            T_ambient = 300.0  # K
            h_effective = 100.0  # W/(m²·K) effective heat transfer
            A = 100.0  # m² effective area
            Q_removal = h_effective * A * (T_mod - T_ambient)
            return min(P_decay, Q_removal)  # Can't remove more than decay heat
    else:
        # Normal operation (constant heat removal)
        def power_removal(t, T_fuel, T_mod):
            if transient_type == "power_change":
                # Heat removal adjusts to power
                return power * (1.0 - 0.1 * np.tanh(t / 10.0))  # Gradual reduction
            else:
                # Constant heat removal
                return 0.9 * power  # 90% of initial power

    # Initial state
    initial_state = {
        "power": power,
        "T_fuel": temperature + 100.0,  # Fuel hotter than average
        "T_mod": temperature,
    }

    # Determine optimization mode based on duration
    long_term_optimization = kwargs.pop("long_term_optimization", duration > 86400)

    # Solve transient
    result = solver.solve_transient(
        rho_external=rho_external,
        power_removal=power_removal,
        initial_state=initial_state,
        t_span=(0.0, duration),
        adaptive=kwargs.pop("adaptive", True),
        long_term_optimization=long_term_optimization,
        max_step=kwargs.pop("max_step", None),
        **kwargs,  # Pass any remaining kwargs
    )

    return result


def reactivity_insertion(
    power: float,
    temperature: float,
    reactivity: float = 0.001,
    duration: float = 100.0,
    scram_available: bool = True,
    **kwargs,
) -> Dict:
    """
    Reactivity insertion accident (RIA) analysis.

    Convenience wrapper for reactivity insertion transients.

    Args:
        power: Initial reactor power [W].
        temperature: Initial temperature [K].
        reactivity: Reactivity inserted [dk/k] (default: 0.001 = 1 m$).
        duration: Simulation duration [s] (default: 100.0).
        scram_available: Whether scram is available (default: True).
        **kwargs: Additional parameters passed to quick_transient.

    Returns:
        Dictionary containing time history.

    Example:
        >>> from smrforge.convenience.transients import reactivity_insertion
        >>> result = reactivity_insertion(
        ...     power=1e6,
        ...     temperature=1200.0,
        ...     reactivity=0.002  # 2 m$
        ... )
        >>> peak_power = np.max(result["power"])
    """
    return quick_transient(
        power=power,
        temperature=temperature,
        reactivity_insertion=reactivity,
        transient_type="reactivity_insertion",
        duration=duration,
        scram_available=scram_available,
        **kwargs,
    )


def decay_heat_removal(
    power: float,
    temperature: float,
    duration: float = 72 * 3600,
    **kwargs,
) -> Dict:
    """
    Decay heat removal analysis (long-term transient).

    Convenience wrapper for decay heat removal scenarios (72+ hours).

    Args:
        power: Initial reactor power [W] before shutdown.
        temperature: Initial temperature [K].
        duration: Simulation duration [s] (default: 72 hours).
        **kwargs: Additional parameters passed to quick_transient.

    Returns:
        Dictionary containing time history.

    Example:
        >>> from smrforge.convenience.transients import decay_heat_removal
        >>> result = decay_heat_removal(
        ...     power=1e6,
        ...     temperature=1200.0,
        ...     duration=72*3600  # 72 hours
        ... )
        >>> final_temp = result["T_fuel"][-1]
    """
    return quick_transient(
        power=power,
        temperature=temperature,
        transient_type="decay_heat",
        duration=duration,
        long_term_optimization=True,  # Enable optimizations for long transients
        **kwargs,
    )


__all__ = [
    "quick_transient",
    "reactivity_insertion",
    "decay_heat_removal",
]
