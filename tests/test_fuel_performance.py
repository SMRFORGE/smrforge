"""
Unit tests for fuel performance module.
"""

import numpy as np
import pytest

from smrforge.fuel.performance import (
    CladProperties,
    FuelPerformance,
    FuelProperties,
)


class TestFuelProperties:
    """Tests for FuelProperties class."""

    def test_fuel_properties_creation(self):
        """Test creating FuelProperties."""
        fuel = FuelProperties(
            diameter=0.8, height=10.0, density=10.96, enrichment=4.5, burnup=30.0
        )

        assert fuel.diameter == 0.8
        assert fuel.height == 10.0
        assert fuel.density == 10.96
        assert fuel.enrichment == 4.5
        assert fuel.burnup == 30.0

    def test_fuel_properties_default_burnup(self):
        """Test FuelProperties with default burnup."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)

        assert fuel.burnup == 0.0


class TestCladProperties:
    """Tests for CladProperties class."""

    def test_clad_properties_creation(self):
        """Test creating CladProperties."""
        clad = CladProperties(
            inner_diameter=0.82, outer_diameter=0.95, material="Zircaloy-4"
        )

        assert clad.inner_diameter == 0.82
        assert clad.outer_diameter == 0.95
        assert clad.material == "Zircaloy-4"

    def test_clad_properties_default_material(self):
        """Test CladProperties with default material."""
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        assert clad.material == "Zircaloy-4"


class TestFuelPerformance:
    """Tests for FuelPerformance class."""

    def test_fuel_performance_initialization(self):
        """Test FuelPerformance initialization."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        assert perf.fuel == fuel
        assert perf.clad == clad

    def test_fuel_centerline_temperature(self):
        """Test fuel centerline temperature calculation."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        T_centerline = perf.fuel_centerline_temperature(
            linear_power=20.0, coolant_temp=600.0
        )

        # Should be higher than coolant temperature
        assert T_centerline > 600.0
        # Should be reasonable (less than 2000 K for typical conditions)
        assert T_centerline < 2000.0

    def test_fission_gas_release_low_temp(self):
        """Test fission gas release at low temperature."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        # Low temperature (< 1273 K)
        fgr = perf.fission_gas_release(temperature=1000.0, burnup=50000.0)

        # Should be small but positive
        assert fgr >= 0.0
        assert fgr <= 0.15  # Cap at 15%

    def test_fission_gas_release_high_temp(self):
        """Test fission gas release at high temperature."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        # High temperature (> 1273 K)
        fgr = perf.fission_gas_release(temperature=1500.0, burnup=30000.0)

        # Should be higher than low temp case
        assert fgr >= 0.0
        assert fgr <= 0.15  # Cap at 15%

    def test_fuel_swelling(self):
        """Test fuel swelling calculation."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        swelling = perf.fuel_swelling(burnup=10000.0, temperature=1200.0)

        # Should be positive
        assert swelling >= 0.0
        # Should be reasonable (typically < 10% for these conditions)
        assert swelling < 10.0

    def test_fuel_swelling_high_temp(self):
        """Test fuel swelling at high temperature."""
        fuel = FuelProperties(diameter=0.8, height=10.0, density=10.96, enrichment=4.5)
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        # High temperature (> 1500 K) should enhance swelling
        swelling_high = perf.fuel_swelling(burnup=10000.0, temperature=1600.0)
        swelling_low = perf.fuel_swelling(burnup=10000.0, temperature=1200.0)

        assert swelling_high >= swelling_low

    def test_analyze_comprehensive(self):
        """Test comprehensive fuel performance analysis."""
        fuel = FuelProperties(
            diameter=0.8, height=10.0, density=10.96, enrichment=4.5, burnup=30000.0
        )
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        result = perf.analyze(linear_power=20.0, coolant_temp=600.0, burnup=30000.0)

        assert "centerline_temperature" in result
        assert "surface_temperature" in result
        assert "fission_gas_release" in result
        assert "fuel_swelling" in result
        assert "burnup" in result

        assert result["centerline_temperature"] > result["surface_temperature"]
        assert result["centerline_temperature"] > 600.0
        assert result["fission_gas_release"] >= 0.0
        assert result["fuel_swelling"] >= 0.0
        assert result["burnup"] == 30000.0

    def test_analyze_with_default_burnup(self):
        """Test analysis using fuel's default burnup."""
        fuel = FuelProperties(
            diameter=0.8, height=10.0, density=10.96, enrichment=4.5, burnup=25000.0
        )
        clad = CladProperties(inner_diameter=0.82, outer_diameter=0.95)

        perf = FuelPerformance(fuel, clad)

        result = perf.analyze(linear_power=20.0, coolant_temp=600.0)

        assert result["burnup"] == 25000.0
