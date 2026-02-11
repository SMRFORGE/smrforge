"""
Enhanced thermal-hydraulics coupling for long-term transients.

This module provides enhanced coupling between neutronics and thermal-hydraulics
for long-term simulations (years), including:
- Time-dependent material property updates
- Long-term temperature evolution
- Thermal expansion effects on geometry
- Material property degradation feedback
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.fuel_cycle.long_term")


@dataclass
class LongTermThermalCoupling:
    """
    Enhanced thermal-hydraulics coupling for long-term simulations.

    Provides time-dependent coupling between neutronics and thermal-hydraulics
    for simulations spanning years, accounting for:
    - Material property degradation over time
    - Thermal expansion effects
    - Long-term temperature evolution
    - Feedback to neutronics (temperature-dependent cross-sections)

    Attributes:
        initial_temperature: Initial temperature distribution [K]
        time_span: Time span for simulation (t_start, t_end) [days]
        update_frequency: Frequency of thermal-hydraulics updates [days]
        material_aging_model: Optional material aging model
        thermal_expansion_model: Optional thermal expansion model
    """

    initial_temperature: np.ndarray  # [K] - spatial distribution
    time_span: Tuple[float, float]  # (t_start, t_end) [days]
    update_frequency: float = 30.0  # days
    material_aging_model: Optional[Callable] = None
    thermal_expansion_model: Optional[Callable] = None

    def __post_init__(self):
        """Initialize coupling state."""
        self.temperature_history: List[np.ndarray] = [self.initial_temperature.copy()]
        self.time_history: List[float] = [self.time_span[0]]
        self.material_properties_history: List[Dict] = []

    def update_temperature(
        self,
        power_distribution: np.ndarray,
        time: float,
        coolant_flow_rate: float,
        coolant_temperature: float,
    ) -> np.ndarray:
        """
        Update temperature distribution based on power and thermal-hydraulics.

        Args:
            power_distribution: Power distribution [W/cm³]
            time: Current time [days]
            coolant_flow_rate: Coolant flow rate [kg/s]
            coolant_temperature: Coolant inlet temperature [K]

        Returns:
            Updated temperature distribution [K]
        """
        # Simplified thermal-hydraulics update
        # In practice, this would call a full TH solver

        # Heat generation
        heat_generation = power_distribution  # W/cm³

        # Heat removal (simplified - would use full TH solver)
        heat_removal = self._calculate_heat_removal(
            self.temperature_history[-1],
            coolant_flow_rate,
            coolant_temperature,
        )

        # Temperature change
        dt_days = time - self.time_history[-1] if len(self.time_history) > 1 else 1.0
        dt_seconds = dt_days * 24.0 * 3600.0

        # Simplified: assume constant heat capacity
        heat_capacity = 1e6  # J/(cm³·K) - typical for fuel
        delta_T = (heat_generation - heat_removal) * dt_seconds / heat_capacity

        new_temperature = self.temperature_history[-1] + delta_T

        # Store history
        self.temperature_history.append(new_temperature.copy())
        self.time_history.append(time)

        return new_temperature

    def _calculate_heat_removal(
        self,
        temperature: np.ndarray,
        coolant_flow_rate: float,
        coolant_temperature: float,
    ) -> np.ndarray:
        """
        Calculate heat removal rate.

        Simplified model - in practice would use full thermal-hydraulics solver.

        Args:
            temperature: Temperature distribution [K]
            coolant_flow_rate: Coolant flow rate [kg/s]
            coolant_temperature: Coolant temperature [K]

        Returns:
            Heat removal rate [W/cm³]
        """
        # Simplified: linear heat transfer
        h = 1000.0  # W/(m²·K) - heat transfer coefficient
        A = 1.0  # m²/cm³ - surface area per volume (simplified)

        # Convert to W/cm³
        h_vol = h * A * 1e-4  # Convert m² to cm²

        heat_removal = h_vol * (temperature - coolant_temperature)

        return heat_removal

    def update_material_properties(
        self,
        time: float,
        temperature: np.ndarray,
        fluence: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Update material properties based on aging.

        Args:
            time: Current time [days]
            temperature: Temperature distribution [K]
            fluence: Optional neutron fluence [n/cm²]

        Returns:
            Dictionary with updated material properties
        """
        if self.material_aging_model is None:
            # Default: no aging
            return {}

        # Call material aging model
        properties = self.material_aging_model(time, temperature, fluence)

        # Store history
        self.material_properties_history.append(properties)

        return properties

    def get_temperature_feedback(
        self,
        time: float,
    ) -> Dict:
        """
        Get temperature feedback for neutronics solver.

        Args:
            time: Current time [days]

        Returns:
            Dictionary with temperature feedback data
        """
        # Find closest time in history
        if len(self.time_history) == 0:
            temperature = self.initial_temperature
        else:
            idx = min(
                range(len(self.time_history)),
                key=lambda i: abs(self.time_history[i] - time),
            )
            temperature = self.temperature_history[idx]

        # Calculate average temperature
        avg_temperature = np.mean(temperature)

        # Calculate temperature coefficients (simplified)
        # In practice, would calculate from cross-section data
        doppler_coefficient = -3.5e-5  # dk/k per K (typical for HTGR)
        moderator_coefficient = -2.0e-5  # dk/k per K

        # Temperature feedback reactivity
        T_ref = 900.0  # Reference temperature [K]
        delta_T = avg_temperature - T_ref
        reactivity_feedback = (
            doppler_coefficient * delta_T + moderator_coefficient * delta_T
        )

        return {
            "temperature": temperature,
            "average_temperature": avg_temperature,
            "reactivity_feedback": reactivity_feedback,
            "doppler_coefficient": doppler_coefficient,
            "moderator_coefficient": moderator_coefficient,
        }

    def get_thermal_expansion_effects(
        self,
        time: float,
    ) -> Dict:
        """
        Get thermal expansion effects on geometry.

        Args:
            time: Current time [days]

        Returns:
            Dictionary with expansion data
        """
        if self.thermal_expansion_model is None:
            return {}

        # Get current temperature
        if len(self.time_history) == 0:
            temperature = self.initial_temperature
        else:
            idx = min(
                range(len(self.time_history)),
                key=lambda i: abs(self.time_history[i] - time),
            )
            temperature = self.temperature_history[idx]

        # Calculate expansion
        expansion = self.thermal_expansion_model(temperature)

        return {
            "temperature": temperature,
            "expansion": expansion,
        }

    def solve_long_term_coupled(
        self,
        neutronics_solver: Callable,
        thermal_solver: Callable,
        power_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        Solve long-term coupled neutronics-thermal-hydraulics problem.

        Args:
            neutronics_solver: Callable that solves neutronics and returns power distribution
            thermal_solver: Callable that solves thermal-hydraulics and returns temperature
            power_callback: Optional callback for power distribution

        Returns:
            Dictionary with solution history
        """
        t_start, t_end = self.time_span
        time_points = np.arange(t_start, t_end, self.update_frequency)
        time_points = np.append(time_points, t_end)

        power_history = []
        temperature_history = []
        keff_history = []

        current_temperature = self.initial_temperature.copy()

        for t in time_points:
            # Solve neutronics
            result = neutronics_solver(current_temperature)
            power_dist = result.get(
                "power_distribution", np.zeros_like(current_temperature)
            )
            keff = result.get("k_eff", 1.0)

            # Solve thermal-hydraulics
            current_temperature = thermal_solver(power_dist, t, current_temperature)

            # Store history
            power_history.append(power_dist.copy())
            temperature_history.append(current_temperature.copy())
            keff_history.append(keff)

            # Update material properties
            self.update_material_properties(t, current_temperature)

            # Callback
            if power_callback is not None:
                power_callback(t, power_dist, current_temperature, keff)

        return {
            "time": time_points,
            "power_history": power_history,
            "temperature_history": temperature_history,
            "k_eff_history": keff_history,
        }
