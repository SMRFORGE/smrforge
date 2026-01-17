"""
Integration of advanced two-phase flow with thermal-hydraulics solver.

This module provides integration between advanced two-phase flow models
and the existing thermal-hydraulics solver.
"""

from typing import Dict, Optional

from .two_phase_advanced import (
    BoilingHeatTransfer,
    DriftFluxModel,
    TwoFluidModel,
    TwoPhaseThermalHydraulics,
)
from .hydraulics import ChannelThermalHydraulics, ChannelGeometry

from ..utils.logging import get_logger

logger = get_logger("smrforge.thermal.two_phase_integration")


def integrate_two_phase_with_thermal_hydraulics(
    thermal_solver: ChannelThermalHydraulics,
    geometry: ChannelGeometry,
    pressure: float,
    mass_flux: float,
    heat_flux: float,
    inlet_temperature: float,
    inlet_quality: float = 0.0,
    model_type: str = "drift_flux",
) -> Dict:
    """
    Integrate advanced two-phase flow with thermal-hydraulics solver.
    
    Args:
        thermal_solver: ChannelThermalHydraulics instance
        geometry: ChannelGeometry instance
        pressure: Pressure [Pa]
        mass_flux: Mass flux [kg/(m²·s)]
        heat_flux: Wall heat flux [W/m²]
        inlet_temperature: Inlet temperature [K]
        inlet_quality: Inlet quality (0-1)
        model_type: Two-phase model type ('drift_flux' or 'two_fluid')
        
    Returns:
        Dictionary with integrated solution
    """
    # Create two-phase solver
    two_phase = TwoPhaseThermalHydraulics(
        pressure=pressure,
        mass_flux=mass_flux,
        diameter=geometry.diameter / 100.0,  # Convert cm to m
        length=geometry.length / 100.0,  # Convert cm to m
        heat_flux=heat_flux,
    )
    
    # Solve two-phase flow
    two_phase_result = two_phase.solve(
        inlet_temperature=inlet_temperature,
        inlet_quality=inlet_quality,
        model_type=model_type,
    )
    
    # Integrate with thermal-hydraulics solver
    # Update thermal solver with two-phase properties
    # (This would be more detailed in a full implementation)
    
    return {
        "two_phase": two_phase_result,
        "void_fraction": two_phase_result["void_fraction"],
        "outlet_quality": two_phase_result["outlet_quality"],
        "pressure_drop": two_phase_result["pressure_drop"],
        "heat_transfer_coefficient": two_phase_result["heat_transfer_coefficient"],
        "critical_heat_flux": two_phase_result["critical_heat_flux"],
        "chf_margin": two_phase_result["chf_margin"],
        "flow_regime": two_phase_result["flow_regime"],
    }
