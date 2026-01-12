"""
Cross-section temperature interpolation for nuclear data.

Provides methods to interpolate cross-sections at different temperatures
using linear, log-log, and spline interpolation methods. Supports
multi-temperature libraries and interpolation between temperature points.
"""

from enum import Enum
from typing import TYPE_CHECKING, Optional

import numpy as np
from scipy.interpolate import interp1d, UnivariateSpline

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .reactor_core import NuclearDataCache, Nuclide

logger = get_logger("smrforge.core.temperature_interpolation")


class InterpolationMethod(Enum):
    """Interpolation methods for cross-section temperature interpolation."""

    LINEAR = "linear"  # Linear interpolation
    LOG_LOG = "log_log"  # Log-log interpolation (log energy, log cross-section)
    SPLINE = "spline"  # Cubic spline interpolation


class CrossSectionTemperatureInterpolator:
    """
    Interpolate cross-sections at different temperatures.
    
    Supports interpolation between multiple temperature points using
    various interpolation methods (linear, log-log, spline).
    
    Attributes:
        temperatures: Array of available temperatures [K]
        energies: Energy grid [eV] (same for all temperatures)
        cross_sections: Cross-section arrays [n_temps, n_energies] [barn]
        method: Interpolation method to use
    """

    def __init__(
        self,
        temperatures: np.ndarray,
        energies: np.ndarray,
        cross_sections: np.ndarray,
        method: InterpolationMethod = InterpolationMethod.LINEAR,
    ):
        """
        Initialize temperature interpolator.
        
        Args:
            temperatures: Available temperatures [K] [n_temps]
            energies: Energy grid [eV] [n_energies]
            cross_sections: Cross-sections at each temperature [n_temps, n_energies] [barn]
            method: Interpolation method (default: LINEAR)
        """
        if len(temperatures) != cross_sections.shape[0]:
            raise ValueError(
                f"Number of temperatures ({len(temperatures)}) must match "
                f"first dimension of cross_sections ({cross_sections.shape[0]})"
            )
        if len(energies) != cross_sections.shape[1]:
            raise ValueError(
                f"Number of energies ({len(energies)}) must match "
                f"second dimension of cross_sections ({cross_sections.shape[1]})"
            )

        self.temperatures = np.array(temperatures)
        self.energies = np.array(energies)
        self.cross_sections = np.array(cross_sections)
        self.method = method

        # Sort temperatures for interpolation
        sort_idx = np.argsort(self.temperatures)
        self.temperatures = self.temperatures[sort_idx]
        self.cross_sections = self.cross_sections[sort_idx, :]

    def interpolate(
        self, temperature: float, energy: Optional[float] = None
    ) -> np.ndarray:
        """
        Interpolate cross-section at requested temperature.
        
        Args:
            temperature: Requested temperature [K]
            energy: Optional energy point [eV]. If None, returns full energy grid.
        
        Returns:
            Interpolated cross-section [barn]
            - If energy is None: array of shape [n_energies]
            - If energy is provided: scalar value
        """
        # Clamp temperature to available range
        if temperature < self.temperatures[0]:
            logger.warning(
                f"Temperature {temperature:.1f} K below minimum "
                f"{self.temperatures[0]:.1f} K, using minimum"
            )
            temperature = self.temperatures[0]
        elif temperature > self.temperatures[-1]:
            logger.warning(
                f"Temperature {temperature:.1f} K above maximum "
                f"{self.temperatures[-1]:.1f} K, using maximum"
            )
            temperature = self.temperatures[-1]

        # If exact match, return that temperature's data
        if np.any(np.abs(self.temperatures - temperature) < 0.1):  # Within 0.1 K
            idx = np.argmin(np.abs(self.temperatures - temperature))
            xs = self.cross_sections[idx, :]
            if energy is not None:
                return np.interp(energy, self.energies, xs)
            return xs

        # Interpolate in temperature
        if self.method == InterpolationMethod.LINEAR:
            xs = self._interpolate_linear(temperature)
        elif self.method == InterpolationMethod.LOG_LOG:
            xs = self._interpolate_log_log(temperature)
        elif self.method == InterpolationMethod.SPLINE:
            xs = self._interpolate_spline(temperature)
        else:
            raise ValueError(f"Unknown interpolation method: {self.method}")

        # If energy specified, interpolate in energy
        if energy is not None:
            return np.interp(energy, self.energies, xs)

        return xs

    def _interpolate_linear(self, temperature: float) -> np.ndarray:
        """Linear interpolation in temperature."""
        # Find temperature indices
        temp_idx = np.searchsorted(self.temperatures, temperature)
        temp_idx = max(1, min(temp_idx, len(self.temperatures) - 1))

        temp_low = temp_idx - 1
        temp_high = temp_idx

        if temp_low == temp_high:
            return self.cross_sections[temp_low, :]

        # Linear interpolation
        temp_frac = (temperature - self.temperatures[temp_low]) / (
            self.temperatures[temp_high] - self.temperatures[temp_low]
        )

        xs_low = self.cross_sections[temp_low, :]
        xs_high = self.cross_sections[temp_high, :]

        return xs_low + temp_frac * (xs_high - xs_low)

    def _interpolate_log_log(self, temperature: float) -> np.ndarray:
        """Log-log interpolation in temperature (log T, log XS)."""
        # Find temperature indices
        temp_idx = np.searchsorted(self.temperatures, temperature)
        temp_idx = max(1, min(temp_idx, len(self.temperatures) - 1))

        temp_low = temp_idx - 1
        temp_high = temp_idx

        if temp_low == temp_high:
            return self.cross_sections[temp_low, :]

        # Log-log interpolation: log(xs) = a + b * log(T)
        log_temp = np.log(temperature)
        log_temp_low = np.log(self.temperatures[temp_low])
        log_temp_high = np.log(self.temperatures[temp_high])

        xs_low = self.cross_sections[temp_low, :]
        xs_high = self.cross_sections[temp_high, :]

        # Avoid log(0) for zero cross-sections
        xs_low_safe = np.maximum(xs_low, 1e-30)
        xs_high_safe = np.maximum(xs_high, 1e-30)

        log_xs_low = np.log(xs_low_safe)
        log_xs_high = np.log(xs_high_safe)

        # Interpolate in log space
        if abs(log_temp_high - log_temp_low) < 1e-10:
            log_xs = log_xs_low
        else:
            log_temp_frac = (log_temp - log_temp_low) / (
                log_temp_high - log_temp_low
            )
            log_xs = log_xs_low + log_temp_frac * (log_xs_high - log_xs_low)

        # Convert back to linear space
        xs = np.exp(log_xs)

        # Handle zero cross-sections
        zero_mask = (xs_low == 0) & (xs_high == 0)
        xs[zero_mask] = 0.0

        return xs

    def _interpolate_spline(self, temperature: float) -> np.ndarray:
        """Cubic spline interpolation in temperature."""
        n_energies = len(self.energies)
        xs_interp = np.zeros(n_energies)

        # Interpolate each energy point separately
        for i in range(n_energies):
            xs_at_energy = self.cross_sections[:, i]

            # Create spline interpolator
            try:
                spline = UnivariateSpline(
                    self.temperatures, xs_at_energy, s=0, k=min(3, len(self.temperatures) - 1)
                )
                xs_interp[i] = spline(temperature)
            except Exception:
                # Fallback to linear if spline fails
                xs_interp[i] = np.interp(
                    temperature, self.temperatures, xs_at_energy
                )

        return xs_interp


def interpolate_cross_section_temperature(
    cache: "NuclearDataCache",
    nuclide: "Nuclide",
    reaction: str,
    target_temperature: float,
    available_temperatures: Optional[np.ndarray] = None,
    method: InterpolationMethod = InterpolationMethod.LINEAR,
    library: Optional[str] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Interpolate cross-section at target temperature using multi-temperature data.
    
    If multiple temperatures are available, interpolates between them.
    Otherwise, uses Doppler broadening from nearest temperature.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        reaction: Reaction name (e.g., "fission", "capture")
        target_temperature: Target temperature [K]
        available_temperatures: Optional array of available temperatures [K].
            If None, will use default temperatures [293.6, 600.0, 900.0, 1200.0] K
        method: Interpolation method (default: LINEAR)
        library: Optional nuclear data library name (e.g., "endfb8.0")
    
    Returns:
        Tuple of (energy [eV], cross_section [barn]) arrays at target temperature
    
    Raises:
        ValueError: If cross-sections cannot be retrieved at any temperature

    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> from smrforge.core.temperature_interpolation import (
        ...     interpolate_cross_section_temperature, InterpolationMethod
        ... )
        >>> cache = NuclearDataCache()
        >>> u235 = Nuclide(Z=92, A=235)
        >>> energy, xs = interpolate_cross_section_temperature(
        ...     cache=cache,
        ...     nuclide=u235,
        ...     reaction="fission",
        ...     target_temperature=900.0,
        ...     method=InterpolationMethod.LINEAR,
        ... )
    """
    if available_temperatures is None:
        # Default temperature grid
        available_temperatures = np.array([293.6, 600.0, 900.0, 1200.0])

    # Get cross-sections at multiple temperatures
    energies_list = []
    cross_sections_list = []

    for temp in available_temperatures:
        try:
            if library is not None:
                energy, xs = cache.get_cross_section(
                    nuclide, reaction, temp, library
                )
            else:
                energy, xs = cache.get_cross_section(nuclide, reaction, temp)

            energies_list.append(energy)
            cross_sections_list.append(xs)
        except Exception as e:
            logger.warning(
                f"Could not get cross-section at {temp:.1f} K: {e}, skipping"
            )
            continue

    if len(cross_sections_list) == 0:
        raise ValueError(
            f"Could not get cross-sections at any temperature for "
            f"{nuclide.name}/{reaction}"
        )

    # Use first energy grid (assume all are similar)
    energies = energies_list[0]

    # Interpolate cross-sections to common energy grid if needed
    if len(cross_sections_list) > 1:
        # Check if energy grids are similar
        energy_grids_match = all(
            np.allclose(energies, e, rtol=1e-6) for e in energies_list
        )

        if not energy_grids_match:
            # Interpolate all to first energy grid
            for i in range(1, len(cross_sections_list)):
                cross_sections_list[i] = np.interp(
                    energies, energies_list[i], cross_sections_list[i]
                )

    # Stack cross-sections
    cross_sections = np.array(cross_sections_list)
    temps_used = np.array(
        [available_temperatures[i] for i in range(len(cross_sections_list))]
    )

    # Create interpolator
    interpolator = CrossSectionTemperatureInterpolator(
        temperatures=temps_used,
        energies=energies,
        cross_sections=cross_sections,
        method=method,
    )

    # Interpolate to target temperature
    xs_interp = interpolator.interpolate(target_temperature)

    return energies, xs_interp
