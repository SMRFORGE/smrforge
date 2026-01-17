# Economics Module Implementation

**Date:** January 2026  
**Status:** ✅ Complete

---

## Executive Summary

This document summarizes the implementation of the economics cost modeling module for SMRForge. The module provides comprehensive cost estimation capabilities including capital costs, operating costs, and Levelized Cost of Electricity (LCOE) calculations.

---

## Implementation

### Module Structure

**Location:** `smrforge/economics/`

**Files Created:**
- `smrforge/economics/__init__.py` - Module exports
- `smrforge/economics/cost_modeling.py` - Core implementation (500+ lines)
- `smrforge/economics/integration.py` - ReactorSpecification integration (100+ lines)

### Classes Implemented

1. **`CapitalCostEstimator`**
   - Overnight capital cost estimation
   - Construction cost with interest during construction
   - SMR-specific factors:
     - Modularity cost reduction (typically 10-15%)
     - Learning curve (cost reduction with nth-of-a-kind)
   - Detailed cost breakdown (direct costs, indirect costs, contingency)
   - Reactor-type specific base costs

2. **`OperatingCostEstimator`**
   - Annual fuel cost calculation
   - Annual O&M cost estimation
   - Staffing costs
   - Total annual operating cost
   - Detailed operating cost breakdown

3. **`LCOECalculator`**
   - Levelized Cost of Electricity (LCOE) calculation
   - Present value calculations with discounting
   - Capital cost amortization
   - Operating cost integration
   - Decommissioning cost inclusion
   - LCOE component breakdown

4. **`CostBreakdown`**
   - Comprehensive cost analysis
   - Combines capital and operating costs
   - Total lifetime cost estimation
   - Complete cost breakdown

5. **Integration Function**
   - `estimate_costs_from_spec()` - Estimates costs from ReactorSpecification

### Features

✅ **Capital Cost Estimation**
- Overnight capital costs
- Construction costs with interest
- Modularity cost reduction (15% default)
- Learning curve (10% reduction per doubling)
- Reactor-type specific base costs
- Detailed cost breakdowns

✅ **Operating Cost Estimation**
- Fuel costs (based on burnup and cycle length)
- O&M costs (per kWe-year)
- Staffing costs
- Capacity factor consideration

✅ **LCOE Calculation**
- Present value calculations
- Discount rate support (WACC)
- Plant lifetime consideration
- Decommissioning costs
- Component breakdown

✅ **SMR-Specific Factors**
- Modularity benefits
- Learning curve effects
- Nth-of-a-kind cost reduction
- Reactor-type specific costs

### Testing

**Test File:** `tests/test_economics_cost_modeling.py`

**Coverage:**
- 16 test cases
- All classes tested
- Edge cases covered
- Integration tests included

**Test Results:** ✅ All 16 tests pass

---

## Usage Examples

### Basic Capital Cost Estimation

```python
from smrforge.economics import CapitalCostEstimator

estimator = CapitalCostEstimator(
    power_electric=100e6,  # 100 MWe
    reactor_type="pwr_smr",
    modularity_factor=0.85,  # 15% reduction
    nth_of_a_kind=4,  # 4th unit
)

overnight_cost = estimator.estimate_overnight_cost()
print(f"Overnight cost: ${overnight_cost/1e9:.2f} billion")

breakdown = estimator.get_cost_breakdown()
print(f"Reactor island: ${breakdown['direct_reactor_island']/1e6:.1f} million")
```

### Operating Cost Estimation

```python
from smrforge.economics import OperatingCostEstimator

op_cost = OperatingCostEstimator(
    power_electric=100e6,  # 100 MWe
    fuel_loading=10000.0,  # kg
    cycle_length=365.0,  # days
    target_burnup=50.0,  # MWd/kg
    capacity_factor=0.90,
    fuel_cost_per_kg=2000.0,  # USD/kg
)

annual_fuel = op_cost.estimate_annual_fuel_cost()
annual_o_m = op_cost.estimate_annual_o_m_cost()
total_annual = op_cost.estimate_total_annual_cost()

print(f"Annual fuel cost: ${annual_fuel/1e6:.2f} million")
print(f"Annual O&M cost: ${annual_o_m/1e6:.2f} million")
print(f"Total annual cost: ${total_annual/1e6:.2f} million")
```

### LCOE Calculation

```python
from smrforge.economics import (
    CapitalCostEstimator,
    OperatingCostEstimator,
    LCOECalculator,
)

# Capital costs
capital = CapitalCostEstimator(power_electric=100e6)
capital_cost = capital.estimate_overnight_cost()

# Operating costs
operating = OperatingCostEstimator(
    power_electric=100e6,
    fuel_loading=10000.0,
    cycle_length=365.0,
    target_burnup=50.0,
)

# LCOE
lcoe_calc = LCOECalculator(
    capital_cost=capital_cost,
    power_electric=100e6,
    capacity_factor=0.90,
    plant_lifetime=60.0,
    discount_rate=0.07,  # 7% WACC
    operating_cost_estimator=operating,
)

lcoe = lcoe_calc.calculate_lcoe()
print(f"LCOE: ${lcoe*1000:.2f}/MWh")

breakdown = lcoe_calc.get_cost_breakdown()
print(f"Capital contribution: ${breakdown['capital_contribution']*1000:.2f}/MWh")
print(f"Operating contribution: ${breakdown['operating_contribution']*1000:.2f}/MWh")
```

### Complete Cost Analysis

```python
from smrforge.economics import CostBreakdown

breakdown = CostBreakdown(
    capital_cost_estimator=capital,
    operating_cost_estimator=operating,
)

complete = breakdown.get_complete_breakdown()
print(f"LCOE: ${complete['lcoe']*1000:.2f}/MWh")
print(f"Total lifetime cost: ${breakdown.estimate_total_lifetime_cost()/1e9:.2f} billion")
```

### Integration with ReactorSpecification

```python
from smrforge.economics.integration import estimate_costs_from_spec
from smrforge.presets.htgr import get_htgr_spec

spec = get_htgr_spec("micro-htgr-1")

costs = estimate_costs_from_spec(
    reactor_spec=spec,
    nth_of_a_kind=4,
    modularity_factor=0.85,
    discount_rate=0.07,
)

print(f"LCOE: ${costs['lcoe']*1000:.2f}/MWh")
print(f"Capital cost: ${costs['capital_costs']['total_overnight_cost']/1e9:.2f} billion")
```

---

## Cost Model Details

### Capital Costs

**Base Costs (USD/kWe, 2024 dollars):**
- Prismatic HTGR: $6,000/kWe
- Pebble bed HTGR: $5,500/kWe
- PWR SMR: $5,000/kWe
- BWR SMR: $5,200/kWe
- Fast reactor SMR: $7,000/kWe
- Molten salt SMR: $6,500/kWe

**Cost Components:**
- Direct costs (80%):
  - Reactor island: 25%
  - Turbine island: 20%
  - Balance of plant: 15%
  - Structures: 10%
  - Instrumentation: 5%
  - Site preparation: 5%
- Indirect costs (20%):
  - Engineering: 10%
  - Construction: 5%
  - Licensing: 3%
  - Owner costs: 2%
- Contingency: 15% (default)

**SMR-Specific Factors:**
- Modularity reduction: 15% (default)
- Learning curve: 10% reduction per doubling of units

### Operating Costs

**Fuel Costs:**
- Calculated from burnup, cycle length, and fuel loading
- Default fuel cost: $2,000/kg (enriched UO2)

**O&M Costs:**
- Default: $100/kWe-year
- Includes maintenance, repairs, supplies

**Staffing:**
- Default: $5 million/year (typical for SMR)

### LCOE Calculation

**Formula:**
```
LCOE = (PV_capital + PV_opex + PV_decommissioning) / PV_electricity
```

**Default Parameters:**
- Plant lifetime: 60 years
- Discount rate: 7% (WACC)
- Capacity factor: 90%
- Decommissioning: 10% of capital cost
- Decommissioning delay: 5 years after shutdown

---

## Integration with Package

### Package Exports

**Updated:** `smrforge/__init__.py`

**New Exports:**
```python
from smrforge.economics import (
    CapitalCostEstimator,
    OperatingCostEstimator,
    LCOECalculator,
    CostBreakdown,
)
```

### Status Update

**Updated:** `smrforge/__init__.py` module status
- Changed from: `economics: Cost modeling (❌ Not implemented)`
- Changed to: `economics: Cost modeling (✅ Implemented - capital, operating, LCOE)`

---

## Test Coverage

### Test Results

- **Total Tests:** 16
- **Status:** ✅ All passing
- **Coverage Areas:**
  - Capital cost estimation (basic, modularity, learning curve, breakdown, construction)
  - Operating cost estimation (fuel, O&M, total, breakdown)
  - LCOE calculation (basic, with operating costs, discount rate effects, capacity factor effects, breakdown)
  - Complete cost breakdown (integration, lifetime costs)

---

## Files Created/Modified

### New Files
1. `smrforge/economics/__init__.py`
2. `smrforge/economics/cost_modeling.py` (500+ lines)
3. `smrforge/economics/integration.py` (100+ lines)
4. `tests/test_economics_cost_modeling.py` (300+ lines, 16 tests)

### Modified Files
1. `smrforge/__init__.py` - Added exports for economics module

---

## Future Enhancements

### Recommended Additions

1. **Sensitivity Analysis**
   - Parameter sensitivity studies
   - Monte Carlo cost uncertainty
   - Tornado diagrams

2. **Advanced Cost Models**
   - Time-dependent cost escalation
   - Regional cost factors
   - Currency conversion
   - Inflation adjustments

3. **Cost Optimization**
   - Design parameter optimization for cost
   - Trade-off analysis
   - Cost-benefit analysis

4. **Reporting**
   - Cost report generation
   - Visualization (cost breakdown charts)
   - Export to Excel/CSV

5. **Fuel Cycle Economics**
   - Fuel cycle cost optimization
   - Refueling strategy costs
   - Spent fuel management costs

---

## Summary

✅ **Economics Module:** Complete implementation with capital costs, operating costs, and LCOE. 16 tests, all passing.

✅ **Integration:** Module exported and ready for use. Integration function provided for ReactorSpecification.

✅ **SMR-Specific:** Includes modularity benefits, learning curves, and reactor-type specific costs.

✅ **Testing:** Comprehensive test coverage (16 tests, all passing).

**Status:** Ready for production use. Provides comprehensive cost modeling capabilities for SMR economic analysis.
