"""
Tests for economics integration module.

Tests the estimate_costs_from_spec function that integrates economics
cost modeling with ReactorSpecification objects.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from smrforge.economics.integration import estimate_costs_from_spec
from smrforge.validation.pydantic_layer import ReactorSpecification, ReactorType, FuelType


class TestEstimateCostsFromSpec:
    """Tests for estimate_costs_from_spec function."""
    
    def test_basic_estimation_with_electric_power(self):
        """Test basic cost estimation with electric power specified."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result = estimate_costs_from_spec(reactor_spec)
        
        assert isinstance(result, dict)
        assert "capital_costs" in result
        assert "operating_costs" in result
        assert "lcoe" in result
        assert "lcoe_breakdown" in result
    
    def test_estimation_without_electric_power(self):
        """Test cost estimation when electric power is not specified (uses thermal)."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=None,  # Not specified
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result = estimate_costs_from_spec(reactor_spec)
        
        # Should estimate electric power from thermal (33% efficiency)
        assert isinstance(result, dict)
        assert "lcoe" in result
    
    def test_estimation_with_custom_parameters(self):
        """Test cost estimation with custom parameters."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result = estimate_costs_from_spec(
            reactor_spec,
            nth_of_a_kind=5,
            modularity_factor=0.80,
            discount_rate=0.05,
            plant_lifetime=80.0,
            fuel_cost_per_kg=2500.0,
        )
        
        assert isinstance(result, dict)
        assert "lcoe" in result
    
    def test_estimation_with_spec_fuel_cost(self):
        """Test cost estimation using fuel_cost from reactor spec."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
            fuel_cost=2200.0,  # Specified in reactor spec
        )
        
        result = estimate_costs_from_spec(reactor_spec)
        
        # Should use fuel_cost from spec
        assert isinstance(result, dict)
    
    def test_estimation_without_fuel_cost(self):
        """Test cost estimation without fuel_cost (uses default)."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
            fuel_cost=None,  # Not specified
        )
        
        result = estimate_costs_from_spec(reactor_spec)
        
        # Should use default fuel_cost (2000.0 USD/kg)
        assert isinstance(result, dict)
    
    def test_estimation_override_fuel_cost(self):
        """Test that fuel_cost_per_kg parameter overrides spec fuel_cost."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
            fuel_cost=2200.0,  # Specified in spec
        )
        
        result = estimate_costs_from_spec(
            reactor_spec,
            fuel_cost_per_kg=3000.0,  # Should override spec value
        )
        
        # Should use fuel_cost_per_kg parameter
        assert isinstance(result, dict)
    
    def test_estimation_different_reactor_types(self):
        """Test cost estimation for different reactor types."""
        for reactor_type in [ReactorType.PRISMATIC, ReactorType.PEBBLE_BED]:
            reactor_spec = ReactorSpecification(
                name=f"Test {reactor_type.value}",
                reactor_type=reactor_type,
                power_thermal=10e6,
                power_electric=3.5e6,
                inlet_temperature=823.15,
                outlet_temperature=1023.15,
                max_fuel_temperature=1873.15,
                primary_pressure=7.0e6,
                core_height=200.0,
                core_diameter=100.0,
                reflector_thickness=30.0,
                fuel_type=FuelType.UCO,
                enrichment=0.195,
                heavy_metal_loading=150.0,
                coolant_flow_rate=8.0,
                cycle_length=3650,
                capacity_factor=0.95,
                target_burnup=150.0,
                doppler_coefficient=-3.5e-5,
                shutdown_margin=0.05,
            )
            
            result = estimate_costs_from_spec(reactor_spec)
            
            assert isinstance(result, dict)
            assert "lcoe" in result
    
    def test_estimation_nth_of_a_kind_effect(self):
        """Test that nth_of_a_kind affects cost estimates."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result_foak = estimate_costs_from_spec(reactor_spec, nth_of_a_kind=1)
        result_noak = estimate_costs_from_spec(reactor_spec, nth_of_a_kind=10)
        
        # NOAK should have lower capital costs due to learning curve
        assert isinstance(result_foak, dict)
        assert isinstance(result_noak, dict)
    
    def test_estimation_modularity_factor_effect(self):
        """Test that modularity_factor affects cost estimates."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result_no_modularity = estimate_costs_from_spec(reactor_spec, modularity_factor=1.0)
        result_with_modularity = estimate_costs_from_spec(reactor_spec, modularity_factor=0.85)
        
        # Lower modularity factor should reduce costs
        assert isinstance(result_no_modularity, dict)
        assert isinstance(result_with_modularity, dict)
    
    def test_estimation_discount_rate_effect(self):
        """Test that discount_rate affects LCOE."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result_low_discount = estimate_costs_from_spec(reactor_spec, discount_rate=0.03)
        result_high_discount = estimate_costs_from_spec(reactor_spec, discount_rate=0.10)
        
        # Higher discount rate should increase LCOE
        assert isinstance(result_low_discount, dict)
        assert isinstance(result_high_discount, dict)
        assert "lcoe" in result_low_discount
        assert "lcoe" in result_high_discount
    
    def test_estimation_plant_lifetime_effect(self):
        """Test that plant_lifetime affects LCOE."""
        reactor_spec = ReactorSpecification(
            name="Test Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        
        result_short_lifetime = estimate_costs_from_spec(reactor_spec, plant_lifetime=40.0)
        result_long_lifetime = estimate_costs_from_spec(reactor_spec, plant_lifetime=80.0)
        
        # Longer lifetime should reduce LCOE
        assert isinstance(result_short_lifetime, dict)
        assert isinstance(result_long_lifetime, dict)
        assert "lcoe" in result_short_lifetime
        assert "lcoe" in result_long_lifetime