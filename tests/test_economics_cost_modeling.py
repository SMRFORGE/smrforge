"""
Unit tests for economics cost modeling module.
"""

import numpy as np
import pytest

from smrforge.economics.cost_modeling import (
    CapitalCostEstimator,
    CostBreakdown,
    LCOECalculator,
    OperatingCostEstimator,
)


class TestCapitalCostEstimator:
    """Tests for CapitalCostEstimator class."""

    def test_overnight_cost_basic(self):
        """Test basic overnight cost calculation."""
        estimator = CapitalCostEstimator(
            power_electric=100e6,  # 100 MWe
            reactor_type="pwr_smr",
            base_cost_per_kwe=5000.0,
            modularity_factor=1.0,  # No modularity reduction for this test
        )

        cost = estimator.estimate_overnight_cost()

        # Should be approximately 100,000 kWe * 5000 USD/kWe * 1.15 (contingency)
        expected = 100000 * 5000 * 1.15
        assert np.isclose(cost, expected, rtol=0.1)

    def test_modularity_factor(self):
        """Test modularity cost reduction."""
        estimator1 = CapitalCostEstimator(
            power_electric=100e6,
            modularity_factor=1.0,  # No reduction
        )

        estimator2 = CapitalCostEstimator(
            power_electric=100e6,
            modularity_factor=0.85,  # 15% reduction
        )

        cost1 = estimator1.estimate_overnight_cost()
        cost2 = estimator2.estimate_overnight_cost()

        # Cost2 should be lower
        assert cost2 < cost1
        # Should be approximately 15% lower (before contingency)
        ratio = cost2 / cost1
        assert ratio < 0.90  # After contingency, still lower

    def test_learning_curve(self):
        """Test learning curve cost reduction."""
        estimator1 = CapitalCostEstimator(
            power_electric=100e6,
            nth_of_a_kind=1,  # FOAK
        )

        estimator2 = CapitalCostEstimator(
            power_electric=100e6,
            nth_of_a_kind=8,  # 8th unit
        )

        cost1 = estimator1.estimate_overnight_cost()
        cost2 = estimator2.estimate_overnight_cost()

        # Cost2 should be lower due to learning
        assert cost2 < cost1

    def test_cost_breakdown(self):
        """Test cost breakdown."""
        estimator = CapitalCostEstimator(power_electric=100e6)

        breakdown = estimator.get_cost_breakdown()

        # Should have all components
        assert "total_overnight_cost" in breakdown
        assert "contingency" in breakdown

        # Total should match overnight cost (sum of all components)
        total = sum(v for k, v in breakdown.items() if k != "total_overnight_cost")
        # Allow some tolerance due to rounding
        assert np.isclose(total, breakdown["total_overnight_cost"], rtol=0.05)

    def test_construction_cost(self):
        """Test construction cost with interest."""
        estimator = CapitalCostEstimator(power_electric=100e6)

        overnight = estimator.estimate_overnight_cost()
        construction = estimator.estimate_construction_cost(
            construction_duration=4.0, interest_rate=0.05
        )

        # Construction cost should be higher due to interest
        assert construction > overnight


class TestOperatingCostEstimator:
    """Tests for OperatingCostEstimator class."""

    def test_annual_fuel_cost(self):
        """Test annual fuel cost calculation."""
        estimator = OperatingCostEstimator(
            power_electric=100e6,  # 100 MWe
            capacity_factor=0.90,
            fuel_cost_per_kg=2000.0,
            fuel_loading=10000.0,  # kg
            cycle_length=365.0,  # days
            target_burnup=50.0,  # MWd/kg
        )

        fuel_cost = estimator.estimate_annual_fuel_cost()

        # Should be positive
        assert fuel_cost > 0
        # Should be reasonable (order of millions for 100 MWe)
        assert fuel_cost > 1e6
        assert fuel_cost < 1e9

    def test_annual_o_m_cost(self):
        """Test annual O&M cost calculation."""
        estimator = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
            o_m_cost_per_kwe=100.0,
        )

        o_m_cost = estimator.estimate_annual_o_m_cost()

        # Should be 100,000 kWe * 100 USD/kWe-year = 10 million
        expected = 100000 * 100.0
        assert np.isclose(o_m_cost, expected, rtol=0.1)

    def test_total_annual_cost(self):
        """Test total annual operating cost."""
        estimator = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
            staffing_cost=5e6,
        )

        total = estimator.estimate_total_annual_cost()

        # Should include fuel, O&M, and staffing
        assert total > 5e6  # At least staffing cost
        assert total > estimator.staffing_cost

    def test_cost_breakdown(self):
        """Test operating cost breakdown."""
        estimator = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
        )

        breakdown = estimator.get_cost_breakdown()

        # Should have all components
        assert "fuel_cost" in breakdown
        assert "o_m_cost" in breakdown
        assert "staffing_cost" in breakdown
        assert "total_operating_cost" in breakdown

        # Total should match sum
        total = (
            breakdown["fuel_cost"] + breakdown["o_m_cost"] + breakdown["staffing_cost"]
        )
        assert np.isclose(total, breakdown["total_operating_cost"], rtol=0.01)


class TestLCOECalculator:
    """Tests for LCOECalculator class."""

    def test_lcoe_basic(self):
        """Test basic LCOE calculation."""
        calculator = LCOECalculator(
            capital_cost=1e9,  # 1 billion USD
            power_electric=100e6,  # 100 MWe
            capacity_factor=0.90,
            plant_lifetime=60.0,
            discount_rate=0.07,
        )

        lcoe = calculator.calculate_lcoe()

        # Should be positive
        assert lcoe > 0
        # Should be reasonable (typically 50-150 USD/MWh = 0.05-0.15 USD/kWh)
        assert lcoe > 0.01  # At least 1 cent/kWh
        assert lcoe < 1.0  # Less than 1 USD/kWh

    def test_lcoe_with_operating_costs(self):
        """Test LCOE with operating cost estimator."""
        op_cost = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
        )

        calculator = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
            operating_cost_estimator=op_cost,
        )

        lcoe = calculator.calculate_lcoe()

        # Should be positive and reasonable
        assert lcoe > 0
        assert lcoe < 1.0

    def test_discount_rate_effect(self):
        """Test effect of discount rate on LCOE."""
        calculator1 = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
            discount_rate=0.05,  # Lower discount rate
        )

        calculator2 = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
            discount_rate=0.10,  # Higher discount rate
        )

        lcoe1 = calculator1.calculate_lcoe()
        lcoe2 = calculator2.calculate_lcoe()

        # Lower discount rate should give lower LCOE (capital costs less penalized)
        assert lcoe1 < lcoe2

    def test_capacity_factor_effect(self):
        """Test effect of capacity factor on LCOE."""
        calculator1 = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
            capacity_factor=0.80,  # Lower capacity factor
        )

        calculator2 = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
            capacity_factor=0.95,  # Higher capacity factor
        )

        lcoe1 = calculator1.calculate_lcoe()
        lcoe2 = calculator2.calculate_lcoe()

        # Higher capacity factor should give lower LCOE (more electricity)
        assert lcoe2 < lcoe1

    def test_cost_breakdown(self):
        """Test LCOE cost breakdown."""
        calculator = LCOECalculator(
            capital_cost=1e9,
            power_electric=100e6,
        )

        breakdown = calculator.get_cost_breakdown()

        # Should have all components
        assert "capital_contribution" in breakdown
        assert "operating_contribution" in breakdown
        assert "decommissioning_contribution" in breakdown
        assert "total_lcoe" in breakdown

        # Total should match calculated LCOE
        assert np.isclose(
            breakdown["total_lcoe"], calculator.calculate_lcoe(), rtol=0.01
        )


class TestCostBreakdown:
    """Tests for CostBreakdown class."""

    def test_complete_breakdown(self):
        """Test complete cost breakdown."""
        capital = CapitalCostEstimator(power_electric=100e6)
        operating = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
        )

        breakdown = CostBreakdown(
            capital_cost_estimator=capital,
            operating_cost_estimator=operating,
        )

        complete = breakdown.get_complete_breakdown()

        # Should have all sections
        assert "capital_costs" in complete
        assert "operating_costs" in complete
        assert "lcoe_breakdown" in complete
        assert "lcoe" in complete

    def test_total_lifetime_cost(self):
        """Test total lifetime cost calculation."""
        capital = CapitalCostEstimator(power_electric=100e6)
        operating = OperatingCostEstimator(
            power_electric=100e6,
            fuel_loading=10000.0,
            cycle_length=365.0,
            target_burnup=50.0,
        )

        breakdown = CostBreakdown(
            capital_cost_estimator=capital,
            operating_cost_estimator=operating,
        )

        total = breakdown.estimate_total_lifetime_cost()

        # Should be positive and large (billions for 60-year lifetime)
        assert total > 1e9
        assert total > breakdown.lcoe_calculator.capital_cost
