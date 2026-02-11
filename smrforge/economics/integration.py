"""
Integration of economics module with reactor specifications.

This module provides utilities to estimate costs from ReactorSpecification objects.
"""

from typing import Dict, Optional

from ..utils.logging import get_logger
from .cost_modeling import (
    CapitalCostEstimator,
    CostBreakdown,
    LCOECalculator,
    OperatingCostEstimator,
)

logger = get_logger("smrforge.economics.integration")


def estimate_costs_from_spec(
    reactor_spec,
    nth_of_a_kind: int = 1,
    modularity_factor: float = 0.85,
    discount_rate: float = 0.07,
    plant_lifetime: float = 60.0,
    fuel_cost_per_kg: Optional[float] = None,
) -> Dict:
    """
    Estimate costs from a ReactorSpecification object.

    Args:
        reactor_spec: ReactorSpecification instance
        nth_of_a_kind: Nth-of-a-kind unit number (1 = FOAK)
        modularity_factor: Cost reduction from modularity (0-1)
        discount_rate: Discount rate for LCOE [fraction per year]
        plant_lifetime: Plant operating lifetime [years]
        fuel_cost_per_kg: Fuel cost [USD/kg]. If None, uses spec.fuel_cost or default

    Returns:
        Dictionary with cost estimates:
            - capital_costs: Capital cost breakdown
            - operating_costs: Operating cost breakdown
            - lcoe: Levelized Cost of Electricity [USD/kWh]
            - lcoe_breakdown: LCOE component breakdown
    """
    # Get electric power (use thermal if electric not specified)
    if reactor_spec.power_electric is not None:
        power_electric = reactor_spec.power_electric
    else:
        # Estimate from thermal power (assume 33% efficiency)
        power_electric = reactor_spec.power_thermal * 0.33

    # Capital cost estimation
    capital_estimator = CapitalCostEstimator(
        power_electric=power_electric,
        reactor_type=reactor_spec.reactor_type.value,
        modularity_factor=modularity_factor,
        nth_of_a_kind=nth_of_a_kind,
    )

    # Operating cost estimation
    fuel_cost = fuel_cost_per_kg
    if fuel_cost is None:
        if reactor_spec.fuel_cost is not None:
            fuel_cost = reactor_spec.fuel_cost
        else:
            fuel_cost = 2000.0  # Default USD/kg

    operating_estimator = OperatingCostEstimator(
        power_electric=power_electric,
        fuel_loading=reactor_spec.heavy_metal_loading,
        cycle_length=reactor_spec.cycle_length,
        target_burnup=reactor_spec.target_burnup,
        capacity_factor=reactor_spec.capacity_factor,
        fuel_cost_per_kg=fuel_cost,
    )

    # LCOE calculation
    capital_cost = capital_estimator.estimate_overnight_cost()
    lcoe_calculator = LCOECalculator(
        capital_cost=capital_cost,
        power_electric=power_electric,
        capacity_factor=reactor_spec.capacity_factor,
        plant_lifetime=plant_lifetime,
        discount_rate=discount_rate,
        operating_cost_estimator=operating_estimator,
    )

    # Complete breakdown
    breakdown = CostBreakdown(
        capital_cost_estimator=capital_estimator,
        operating_cost_estimator=operating_estimator,
        lcoe_calculator=lcoe_calculator,
    )

    return breakdown.get_complete_breakdown()
