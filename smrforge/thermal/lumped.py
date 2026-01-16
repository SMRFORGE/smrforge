"""
Lumped-parameter thermal-hydraulics for fast transient analysis.

Provides lightweight 0-D thermal circuit models for rapid screening
of long transients (72+ hours). Based on PyRK's approach using
material lumps with thermal capacitance and resistance.

Useful for:
- Fast screening calculations
- Long-term transient analysis (decay heat removal, ATWS)
- Preliminary safety assessments
- Complement to detailed 1D thermal-hydraulics models
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from ..utils.logging import get_logger

logger = get_logger("smrforge.thermal.lumped")


@dataclass
class ThermalLump:
    """
    Thermal lump representing a material region.

    A thermal lump is a 0-D representation of a material with:
    - Thermal capacitance (C = m * cp): stores thermal energy
    - Thermal resistance (R = 1/(h*A)): resists heat transfer
    - Temperature (T): state variable

    Attributes:
        name: Name of the thermal lump (e.g., "fuel", "moderator").
        capacitance: Thermal capacitance [J/K] = mass * specific_heat.
        temperature: Initial temperature [K].
        heat_source: Callable function Q(t) returning heat generation [W].
    
    Example:
        >>> fuel_lump = ThermalLump(
        ...     name="fuel",
        ...     capacitance=1e8,  # J/K
        ...     temperature=1200.0,  # K
        ...     heat_source=lambda t: 1e6  # W
        ... )
    """

    name: str
    capacitance: float  # J/K
    temperature: float  # K
    heat_source: Callable[[float], float]  # Q(t) -> W

    def __post_init__(self):
        """Validate inputs."""
        if self.capacitance <= 0:
            raise ValueError(f"capacitance must be > 0, got {self.capacitance}")
        if self.temperature <= 0:
            raise ValueError(f"temperature must be > 0, got {self.temperature}")


@dataclass
class ThermalResistance:
    """
    Thermal resistance between two thermal lumps.

    Represents heat transfer resistance R = 1/(h*A) where:
    - h: heat transfer coefficient [W/(m²·K)]
    - A: heat transfer area [m²]

    Attributes:
        name: Name of the resistance (e.g., "fuel_to_moderator").
        resistance: Thermal resistance [K/W] = 1/(h*A).
        lump1_name: Name of first thermal lump.
        lump2_name: Name of second thermal lump.
    
    Example:
        >>> resistance = ThermalResistance(
        ...     name="fuel_to_moderator",
        ...     resistance=1e-6,  # K/W
        ...     lump1_name="fuel",
        ...     lump2_name="moderator"
        ... )
    """

    name: str
    resistance: float  # K/W
    lump1_name: str
    lump2_name: str

    def __post_init__(self):
        """Validate inputs."""
        if self.resistance <= 0:
            raise ValueError(f"resistance must be > 0, got {self.resistance}")


class LumpedThermalHydraulics:
    """
    Lumped-parameter thermal-hydraulics solver.

    Solves 0-D thermal circuits for fast transient analysis. Uses
    thermal lumps (material regions) connected by thermal resistances
    to model heat transfer in reactor systems.

    Fast and efficient for:
    - Long transients (72+ hours)
    - Screening calculations
    - Preliminary safety analysis
    - Decay heat removal scenarios

    For higher fidelity, use ChannelThermalHydraulics (1D models).

    Attributes:
        lumps: Dictionary of thermal lumps {name: ThermalLump}.
        resistances: List of thermal resistances connecting lumps.
        ambient_temperature: Ambient/sink temperature [K] (default: 300.0).
    
    Example:
        >>> from smrforge.thermal.lumped import (
        ...     LumpedThermalHydraulics,
        ...     ThermalLump,
        ...     ThermalResistance
        ... )
        >>> 
        >>> # Create thermal lumps
        >>> fuel = ThermalLump(
        ...     name="fuel",
        ...     capacitance=1e8,  # J/K
        ...     temperature=1200.0,  # K
        ...     heat_source=lambda t: 1e6 if t < 10 else 0.1e6  # Decay heat
        ... )
        >>> 
        >>> moderator = ThermalLump(
        ...     name="moderator",
        ...     capacitance=5e8,  # J/K
        ...     temperature=800.0,  # K
        ...     heat_source=lambda t: 0.0  # No direct heat source
        ... )
        >>> 
        >>> # Create thermal resistance
        >>> resistance = ThermalResistance(
        ...     name="fuel_to_moderator",
        ...     resistance=1e-6,  # K/W
        ...     lump1_name="fuel",
        ...     lump2_name="moderator"
        ... )
        >>> 
        >>> # Create solver
        >>> solver = LumpedThermalHydraulics(
        ...     lumps={"fuel": fuel, "moderator": moderator},
        ...     resistances=[resistance],
        ...     ambient_temperature=300.0  # K
        ... )
        >>> 
        >>> # Solve transient
        >>> result = solver.solve_transient(
        ...     t_span=(0.0, 72 * 3600),  # 72 hours
        ...     max_step=3600.0  # 1 hour steps
        ... )
        >>> 
        >>> print(f"Final fuel temperature: {result['T_fuel'][-1]:.1f} K")
    """

    def __init__(
        self,
        lumps: Dict[str, ThermalLump],
        resistances: list[ThermalResistance],
        ambient_temperature: float = 300.0,
    ):
        """
        Initialize lumped-parameter thermal hydraulics solver.

        Args:
            lumps: Dictionary of thermal lumps {name: ThermalLump}.
            resistances: List of thermal resistances connecting lumps.
            ambient_temperature: Ambient/sink temperature [K] (default: 300.0).

        Raises:
            ValueError: If inputs are invalid (missing lumps, invalid resistances, etc.).
        """
        if not lumps:
            raise ValueError("lumps dictionary cannot be empty")
        if not isinstance(lumps, dict):
            raise ValueError(f"lumps must be dict, got {type(lumps)}")

        # Validate all resistances reference existing lumps
        lump_names = set(lumps.keys())
        for res in resistances:
            if res.lump1_name not in lump_names:
                raise ValueError(
                    f"Resistance {res.name} references unknown lump: {res.lump1_name}"
                )
            if res.lump2_name not in lump_names:
                raise ValueError(
                    f"Resistance {res.name} references unknown lump: {res.lump2_name}"
                )

        if ambient_temperature <= 0:
            raise ValueError(
                f"ambient_temperature must be > 0, got {ambient_temperature}"
            )

        self.lumps = lumps
        self.resistances = resistances
        self.ambient_temperature = ambient_temperature

        # Build lookup structures
        self.lump_names = list(lumps.keys())
        self.n_lumps = len(lumps)

        logger.debug(
            f"LumpedThermalHydraulics initialized: {self.n_lumps} lumps, "
            f"{len(resistances)} resistances"
        )

    def solve_transient(
        self,
        t_span: Tuple[float, float],
        max_step: Optional[float] = None,
        adaptive: bool = True,
    ) -> Dict[str, np.ndarray]:
        """
        Solve transient thermal response.

        Integrates the system of ODEs:
            C_i * dT_i/dt = Q_i(t) + sum_j[(T_j - T_i) / R_ij]

        where:
            - C_i: Thermal capacitance of lump i
            - T_i: Temperature of lump i
            - Q_i(t): Heat source in lump i (time-dependent)
            - R_ij: Thermal resistance between lumps i and j

        Args:
            t_span: Time span (t_start, t_end) [s].
            max_step: Maximum time step [s]. If None, uses adaptive stepping.
            adaptive: Use adaptive time stepping (default: True).

        Returns:
            Dictionary containing time history with keys:
                - "time": Time array [s]
                - "T_{lump_name}": Temperature array for each lump [K]
                - "Q_{lump_name}": Heat source array for each lump [W]

        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If ODE solver fails.

        Example:
            >>> result = solver.solve_transient(
            ...     t_span=(0.0, 3600.0),  # 1 hour
            ...     max_step=60.0,  # 1 minute
            ...     adaptive=True
            ... )
            >>> T_fuel = result["T_fuel"]
            >>> T_moderator = result["T_moderator"]
        """
        if len(t_span) != 2:
            raise ValueError(f"t_span must be tuple of length 2, got {len(t_span)}")
        if t_span[1] <= t_span[0]:
            raise ValueError(f"t_span[1] must be > t_span[0], got {t_span}")

        # Set default max_step based on time span
        if max_step is None:
            # Use 1% of total time span, but at least 1 second
            max_step = max(1.0, 0.01 * (t_span[1] - t_span[0]))

        logger.debug(
            f"Solving lumped thermal transient: t_span={t_span}, "
            f"max_step={max_step}, adaptive={adaptive}"
        )

        # Initial state vector: [T_1, T_2, ..., T_n]
        T0 = np.array([self.lumps[name].temperature for name in self.lump_names])

        # Build resistance matrix for fast lookup
        resistance_dict = {}
        for res in self.resistances:
            key = (res.lump1_name, res.lump2_name)
            resistance_dict[key] = res.resistance
            # Also store reverse direction
            resistance_dict[(res.lump2_name, res.lump1_name)] = res.resistance

            def dTdt(t: float, T: np.ndarray) -> np.ndarray:
                """Temperature derivatives."""
                dT_dt = np.zeros(self.n_lumps)

                for i, name_i in enumerate(self.lump_names):
                    lump_i = self.lumps[name_i]
                    T_i = T[i]

                    # Heat source
                    Q_i = lump_i.heat_source(t)

                    # Heat transfer from/to other lumps
                    Q_transfer = 0.0
                    for j, name_j in enumerate(self.lump_names):
                        if i != j:
                            key = (name_i, name_j)
                            if key in resistance_dict:
                                R_ij = resistance_dict[key]
                                T_j = T[j]
                                # Heat flow: Q = (T_j - T_i) / R_ij
                                Q_transfer += (T_j - T_i) / R_ij

                    # Heat transfer to ambient (simplified)
                    # Assume lump has resistance to ambient via convection
                    # R_ambient can be added as parameter if needed
                    # For now, assume negligible

                    # Energy balance: C * dT/dt = Q_in - Q_out
                    dT_dt[i] = (Q_i + Q_transfer) / lump_i.capacitance

                return dT_dt

        # Solve ODE system
        try:
            if adaptive:
                # Use adaptive time stepping for efficiency
                sol = solve_ivp(
                    dTdt,
                    t_span,
                    T0,
                    method="BDF",  # Backward differentiation (good for stiff)
                    max_step=max_step,
                    dense_output=True,
                    rtol=1e-6,
                    atol=1e-8,
                )
            else:
                # Fixed time steps
                t_eval = np.arange(t_span[0], t_span[1], max_step)
                sol = solve_ivp(
                    dTdt,
                    t_span,
                    T0,
                    t_eval=t_eval,
                    method="BDF",
                    rtol=1e-6,
                    atol=1e-8,
                )

            if not sol.success:
                raise RuntimeError(
                    f"ODE solver failed: {sol.message}. Try adjusting max_step or t_span."
                )

        except Exception as e:
            raise RuntimeError(f"ODE solver failed: {e}") from e

        # Extract results
        t = sol.t
        T_history = sol.y  # Shape: (n_lumps, n_times)

        # Build result dictionary
        result = {"time": t}

        for i, name in enumerate(self.lump_names):
            result[f"T_{name}"] = T_history[i, :]

            # Also store heat source history
            Q_history = np.array([self.lumps[name].heat_source(ti) for ti in t])
            result[f"Q_{name}"] = Q_history

        logger.info(
            f"Lumped thermal transient solved: {len(t)} time steps, "
            f"t_span=[{t_span[0]:.1f}, {t_span[1]:.1f}] s"
        )

        return result


__all__ = [
    "ThermalLump",
    "ThermalResistance",
    "LumpedThermalHydraulics",
]
