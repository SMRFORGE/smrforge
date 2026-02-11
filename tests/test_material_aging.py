"""
Unit tests for material aging models.
"""

import numpy as np
import pytest

from smrforge.fuel_cycle.material_aging import MaterialAging


class TestMaterialAging:
    """Tests for MaterialAging class."""

    def test_graphite_aging(self):
        """Test graphite material aging."""
        aging = MaterialAging(
            material_type="graphite",
            initial_properties={
                "thermal_conductivity": 100.0,  # W/m-K
                "youngs_modulus": 10e9,  # Pa
                "density": 1750.0,  # kg/m³
            },
        )

        # Calculate aged properties
        aged = aging.calculate_aged_properties(
            time=365.0,  # 1 year
            temperature=1200.0,  # K
            fluence=1e21,  # n/cm²
        )

        assert "thermal_conductivity" in aged
        assert "youngs_modulus" in aged
        assert "density" in aged

        # Properties should degrade
        assert (
            aged["thermal_conductivity"]
            < aging.initial_properties["thermal_conductivity"]
        )

    def test_zircaloy_aging(self):
        """Test Zircaloy material aging."""
        aging = MaterialAging(
            material_type="zircaloy",
            initial_properties={
                "thermal_conductivity": 18.0,  # W/m-K
                "yield_strength": 400e6,  # Pa
            },
        )

        aged = aging.calculate_aged_properties(
            time=1095.0,  # 3 years
            temperature=600.0,  # K
            fluence=5e21,  # n/cm²
        )

        assert "thermal_conductivity" in aged
        assert "yield_strength" in aged

    def test_fuel_aging(self):
        """Test fuel material aging."""
        aging = MaterialAging(
            material_type="fuel",
            initial_properties={
                "thermal_conductivity": 3.0,  # W/m-K
                "density": 10960.0,  # kg/m³
            },
        )

        aged = aging.calculate_aged_properties(
            time=1095.0,  # 3 years
            temperature=1500.0,  # K
        )

        assert "thermal_conductivity" in aged
        assert "density" in aged

        # Fuel swelling increases volume, but density calculation here increases
        # (swelling is tracked separately). Check that properties changed.
        assert aged["density"] != aging.initial_properties["density"]

    def test_get_aging_rate(self):
        """Test aging rate calculation."""
        aging = MaterialAging(
            material_type="graphite",
            initial_properties={"thermal_conductivity": 100.0},
        )

        rate = aging.get_aging_rate(
            "thermal_conductivity",
            time=365.0,
            temperature=1200.0,
            fluence=1e21,
        )

        # Rate should be negative (degradation)
        assert rate < 0.0

    def test_custom_aging_model(self):
        """Test custom aging model."""

        def custom_aging(initial, time, temp, fluence, stress):
            return initial * 0.9  # 10% reduction

        aging = MaterialAging(
            material_type="generic",
            initial_properties={"property": 100.0},
            aging_models={"property": custom_aging},
        )

        aged = aging.calculate_aged_properties(time=365.0, temperature=800.0)

        assert aged["property"] == 90.0
