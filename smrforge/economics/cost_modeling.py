"""
Economic cost modeling for SMR designs.

This module provides comprehensive cost estimation capabilities including
capital costs, operating costs, and Levelized Cost of Electricity (LCOE).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.economics.cost_modeling")


@dataclass
class CapitalCostEstimator:
    """
    Capital cost estimation for SMR designs.

    Estimates overnight capital costs based on reactor specifications,
    including SMR-specific factors like modularity and learning curves.

    Attributes:
        power_electric: Electric power output [W]
        reactor_type: Reactor type (affects cost factors)
        modularity_factor: Cost reduction from modular construction (0-1)
        learning_curve_factor: Cost reduction from nth-of-a-kind (0-1)
        nth_of_a_kind: Nth-of-a-kind unit number (1 = FOAK, >1 = NOAK)
        contingency: Contingency factor (default: 0.15 = 15%)
        base_cost_per_kwe: Base cost per kW-electric [USD/kWe]
    """

    power_electric: float  # W
    reactor_type: str = "prismatic"  # prismatic, pebble_bed, pwr_smr, bwr_smr
    modularity_factor: float = 0.85  # 15% reduction from modularity
    learning_curve_factor: float = 1.0  # Will be calculated from nth_of_a_kind
    nth_of_a_kind: int = 1  # 1 = FOAK, >1 = NOAK
    contingency: float = 0.15  # 15% contingency
    base_cost_per_kwe: Optional[float] = None  # USD/kWe

    # Cost breakdown factors (fraction of total)
    direct_costs: Dict[str, float] = field(
        default_factory=lambda: {
            "reactor_island": 0.25,  # Reactor vessel, core, internals
            "turbine_island": 0.20,  # Steam generator, turbine, generator
            "balance_of_plant": 0.15,  # Cooling, electrical, aux systems
            "structures": 0.10,  # Buildings, containment
            "instrumentation": 0.05,  # Control systems, I&C
            "site_preparation": 0.05,  # Site work, foundations
        }
    )

    indirect_costs: Dict[str, float] = field(
        default_factory=lambda: {
            "engineering": 0.10,  # Design, engineering services
            "construction": 0.05,  # Construction management
            "licensing": 0.03,  # Regulatory, licensing
            "owner_costs": 0.02,  # Owner's costs
        }
    )

    def __post_init__(self):
        """Initialize cost estimator."""
        # Set base cost per kWe based on reactor type if not provided
        if self.base_cost_per_kwe is None:
            # Base costs in USD/kWe (2024 dollars, approximate)
            base_costs = {
                "prismatic": 6000.0,  # HTGR SMR
                "pebble_bed": 5500.0,  # Pebble bed HTGR
                "pwr_smr": 5000.0,  # PWR SMR
                "bwr_smr": 5200.0,  # BWR SMR
                "fast_reactor": 7000.0,  # Fast reactor SMR
                "molten_salt": 6500.0,  # Molten salt SMR
            }
            self.base_cost_per_kwe = base_costs.get(self.reactor_type.lower(), 6000.0)

        # Calculate learning curve factor
        if self.nth_of_a_kind > 1:
            # Learning curve: cost reduction with experience
            # Typical: 10-15% reduction per doubling
            learning_rate = 0.10  # 10% reduction per doubling
            doublings = np.log2(self.nth_of_a_kind)
            self.learning_curve_factor = (1.0 - learning_rate) ** doublings
        else:
            self.learning_curve_factor = 1.0

    def estimate_overnight_cost(self) -> float:
        """
        Estimate overnight capital cost.

        Overnight cost = cost if built instantly (no interest during construction).

        Returns:
            Overnight capital cost [USD]
        """
        # Base cost
        power_kwe = self.power_electric / 1000.0  # Convert to kWe
        base_cost = power_kwe * self.base_cost_per_kwe

        # Apply modularity reduction
        modular_cost = base_cost * self.modularity_factor

        # Apply learning curve reduction
        learned_cost = modular_cost * self.learning_curve_factor

        # Add contingency
        overnight_cost = learned_cost * (1.0 + self.contingency)

        return overnight_cost

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get detailed cost breakdown.

        Returns:
            Dictionary with cost components [USD]
        """
        overnight_cost = self.estimate_overnight_cost()
        base_cost = overnight_cost / (1.0 + self.contingency)

        breakdown = {}

        # Direct costs (fractions should sum to direct_total, which is < 1.0)
        direct_total = sum(self.direct_costs.values())
        indirect_total = sum(self.indirect_costs.values())

        # Base cost before contingency = direct + indirect
        # So we need to scale fractions to base_cost
        cost_before_contingency = base_cost

        for component, fraction in self.direct_costs.items():
            breakdown[f"direct_{component}"] = cost_before_contingency * (
                fraction / (direct_total + indirect_total)
            )

        # Indirect costs
        for component, fraction in self.indirect_costs.items():
            breakdown[f"indirect_{component}"] = cost_before_contingency * (
                fraction / (direct_total + indirect_total)
            )

        # Contingency
        breakdown["contingency"] = base_cost * self.contingency

        # Total
        breakdown["total_overnight_cost"] = overnight_cost

        return breakdown

    def estimate_construction_cost(
        self,
        construction_duration: float = 4.0,  # years
        interest_rate: float = 0.05,  # 5% per year
    ) -> float:
        """
        Estimate total construction cost including interest during construction.

        Args:
            construction_duration: Construction duration [years]
            interest_rate: Annual interest rate during construction

        Returns:
            Total construction cost [USD]
        """
        overnight_cost = self.estimate_overnight_cost()

        # Assume uniform spending over construction period
        # Interest accumulates on average half the cost over the period
        average_investment = overnight_cost / 2.0
        interest = average_investment * interest_rate * construction_duration

        total_cost = overnight_cost + interest

        return total_cost


@dataclass
class OperatingCostEstimator:
    """
    Operating cost estimation for SMR designs.

    Estimates annual operating costs including fuel, O&M, and staffing.

    Attributes:
        power_electric: Electric power output [W]
        fuel_loading: Initial fuel loading [kg]
        cycle_length: Fuel cycle length [days]
        target_burnup: Target discharge burnup [MWd/kg]
        capacity_factor: Capacity factor (fraction of time at full power)
        fuel_cost_per_kg: Fuel cost [USD/kg]
        o_m_cost_per_kwe: O&M cost per kW-electric per year [USD/kWe-year]
        staffing_cost: Annual staffing cost [USD/year]
    """

    power_electric: float  # W
    fuel_loading: float  # kg
    cycle_length: float  # days
    target_burnup: float  # MWd/kg
    capacity_factor: float = 0.90  # 90% capacity factor
    fuel_cost_per_kg: float = 2000.0  # USD/kg (typical for enriched UO2)
    o_m_cost_per_kwe: float = 100.0  # USD/kWe-year
    staffing_cost: float = 5e6  # USD/year (typical for SMR)

    def estimate_annual_fuel_cost(self) -> float:
        """
        Estimate annual fuel cost.

        Returns:
            Annual fuel cost [USD/year]
        """
        # Calculate fuel consumption
        power_thermal = self.power_electric / 0.33  # Assume 33% efficiency
        power_thermal_mw = power_thermal / 1e6  # MW

        # Annual energy production
        hours_per_year = 365.25 * 24
        annual_energy_mwd = (
            power_thermal_mw * hours_per_year / 24.0 * self.capacity_factor
        )

        # Fuel consumption (kg/year)
        # Based on burnup: energy = burnup * fuel_mass
        fuel_consumption = annual_energy_mwd / self.target_burnup

        # Annual fuel cost
        annual_fuel_cost = fuel_consumption * self.fuel_cost_per_kg

        return annual_fuel_cost

    def estimate_annual_o_m_cost(self) -> float:
        """
        Estimate annual O&M cost.

        Returns:
            Annual O&M cost [USD/year]
        """
        power_kwe = self.power_electric / 1000.0  # kWe
        annual_o_m = power_kwe * self.o_m_cost_per_kwe

        return annual_o_m

    def estimate_total_annual_cost(self) -> float:
        """
        Estimate total annual operating cost.

        Returns:
            Total annual operating cost [USD/year]
        """
        fuel_cost = self.estimate_annual_fuel_cost()
        o_m_cost = self.estimate_annual_o_m_cost()

        total = fuel_cost + o_m_cost + self.staffing_cost

        return total

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get detailed operating cost breakdown.

        Returns:
            Dictionary with cost components [USD/year]
        """
        return {
            "fuel_cost": self.estimate_annual_fuel_cost(),
            "o_m_cost": self.estimate_annual_o_m_cost(),
            "staffing_cost": self.staffing_cost,
            "total_operating_cost": self.estimate_total_annual_cost(),
        }


@dataclass
class LCOECalculator:
    """
    Levelized Cost of Electricity (LCOE) calculator.

    Calculates the LCOE for an SMR design, accounting for:
    - Capital costs (amortized over plant lifetime)
    - Operating costs (fuel, O&M, staffing)
    - Decommissioning costs
    - Time value of money (discounting)

    Attributes:
        capital_cost: Total capital cost [USD]
        power_electric: Electric power output [W]
        capacity_factor: Capacity factor
        plant_lifetime: Plant operating lifetime [years]
        discount_rate: Discount rate (WACC) [fraction per year]
        operating_cost_estimator: OperatingCostEstimator instance
        decommissioning_cost: Decommissioning cost [USD] (default: 10% of capital)
        decommissioning_delay: Years after shutdown to decommission
    """

    capital_cost: float  # USD
    power_electric: float  # W
    capacity_factor: float = 0.90
    plant_lifetime: float = 60.0  # years
    discount_rate: float = 0.07  # 7% WACC
    operating_cost_estimator: Optional[OperatingCostEstimator] = None
    decommissioning_cost: Optional[float] = None
    decommissioning_delay: float = 5.0  # years

    def __post_init__(self):
        """Initialize LCOE calculator."""
        if self.decommissioning_cost is None:
            # Default: 10% of capital cost
            self.decommissioning_cost = 0.10 * self.capital_cost

    def calculate_lcoe(self) -> float:
        """
        Calculate Levelized Cost of Electricity.

        LCOE = (Total Present Value of Costs) / (Total Present Value of Electricity)

        Returns:
            LCOE [USD/kWh]
        """
        # Annual electricity generation
        power_kw = self.power_electric / 1000.0  # kW
        hours_per_year = 365.25 * 24
        annual_generation_kwh = power_kw * hours_per_year * self.capacity_factor

        # Present value of electricity generation
        pv_electricity = self._present_value_annuity(
            annual_generation_kwh, self.plant_lifetime, self.discount_rate
        )

        # Present value of capital cost (at t=0)
        pv_capital = self.capital_cost

        # Present value of operating costs
        if self.operating_cost_estimator is not None:
            annual_opex = self.operating_cost_estimator.estimate_total_annual_cost()
        else:
            # Estimate from power if no estimator provided
            annual_opex = (self.power_electric / 1000.0) * 100.0  # USD/kWe-year default

        pv_opex = self._present_value_annuity(
            annual_opex, self.plant_lifetime, self.discount_rate
        )

        # Present value of decommissioning
        decommissioning_time = self.plant_lifetime + self.decommissioning_delay
        pv_decommissioning = self.decommissioning_cost / (
            (1.0 + self.discount_rate) ** decommissioning_time
        )

        # Total present value of costs
        total_pv_costs = pv_capital + pv_opex + pv_decommissioning

        # LCOE
        lcoe = total_pv_costs / pv_electricity  # USD/kWh

        return lcoe

    def _present_value_annuity(
        self, annual_value: float, years: float, discount_rate: float
    ) -> float:
        """
        Calculate present value of an annuity.

        PV = A * (1 - (1+r)^(-n)) / r

        Args:
            annual_value: Annual payment [USD/year]
            years: Number of years
            discount_rate: Discount rate [fraction per year]

        Returns:
            Present value [USD]
        """
        if discount_rate == 0.0:
            return annual_value * years

        pv = annual_value * (1.0 - (1.0 + discount_rate) ** (-years)) / discount_rate

        return pv

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get detailed LCOE cost breakdown.

        Returns:
            Dictionary with cost components [USD/kWh]
        """
        # Annual electricity generation
        power_kw = self.power_electric / 1000.0
        hours_per_year = 365.25 * 24
        annual_generation_kwh = power_kw * hours_per_year * self.capacity_factor

        # Present value factors
        pv_factor = self._present_value_annuity(
            1.0, self.plant_lifetime, self.discount_rate
        )

        # Capital cost contribution
        pv_capital = self.capital_cost
        capital_contribution = pv_capital / (annual_generation_kwh * pv_factor)

        # Operating cost contribution
        if self.operating_cost_estimator is not None:
            annual_opex = self.operating_cost_estimator.estimate_total_annual_cost()
        else:
            annual_opex = (self.power_electric / 1000.0) * 100.0

        opex_contribution = annual_opex / annual_generation_kwh

        # Decommissioning contribution
        decommissioning_time = self.plant_lifetime + self.decommissioning_delay
        pv_decommissioning = self.decommissioning_cost / (
            (1.0 + self.discount_rate) ** decommissioning_time
        )
        decommissioning_contribution = pv_decommissioning / (
            annual_generation_kwh * pv_factor
        )

        total_lcoe = self.calculate_lcoe()

        return {
            "capital_contribution": capital_contribution,
            "operating_contribution": opex_contribution,
            "decommissioning_contribution": decommissioning_contribution,
            "total_lcoe": total_lcoe,
        }


@dataclass
class CostBreakdown:
    """
    Comprehensive cost breakdown analysis.

    Combines capital and operating costs for complete economic analysis.

    Attributes:
        capital_cost_estimator: CapitalCostEstimator instance
        operating_cost_estimator: OperatingCostEstimator instance
        lcoe_calculator: LCOECalculator instance
    """

    capital_cost_estimator: CapitalCostEstimator
    operating_cost_estimator: OperatingCostEstimator
    lcoe_calculator: Optional[LCOECalculator] = None

    def __post_init__(self):
        """Initialize cost breakdown."""
        if self.lcoe_calculator is None:
            capital_cost = self.capital_cost_estimator.estimate_overnight_cost()
            self.lcoe_calculator = LCOECalculator(
                capital_cost=capital_cost,
                power_electric=self.capital_cost_estimator.power_electric,
                capacity_factor=self.operating_cost_estimator.capacity_factor,
                operating_cost_estimator=self.operating_cost_estimator,
            )

    def get_complete_breakdown(self) -> Dict:
        """
        Get complete cost breakdown.

        Returns:
            Dictionary with all cost components
        """
        return {
            "capital_costs": self.capital_cost_estimator.get_cost_breakdown(),
            "operating_costs": self.operating_cost_estimator.get_cost_breakdown(),
            "lcoe_breakdown": self.lcoe_calculator.get_cost_breakdown(),
            "lcoe": self.lcoe_calculator.calculate_lcoe(),
        }

    def estimate_total_lifetime_cost(self) -> float:
        """
        Estimate total lifetime cost (undiscounted).

        Returns:
            Total lifetime cost [USD]
        """
        capital = self.capital_cost_estimator.estimate_overnight_cost()
        annual_opex = self.operating_cost_estimator.estimate_total_annual_cost()
        lifetime_opex = annual_opex * self.lcoe_calculator.plant_lifetime
        decommissioning = self.lcoe_calculator.decommissioning_cost

        total = capital + lifetime_opex + decommissioning

        return total
