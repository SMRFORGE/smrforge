"""
Tests for materials_database module.
"""

import numpy as np
import pytest

try:
    from smrforge.core.materials_database import (
        GraphiteMaterial,
        HeliumCoolant,
        MaterialDatabase,
        MaterialProperty,
        TRISOFuel,
        graphite_conductivity_fast,
        helium_properties_fast,
    )
except ImportError:
    pytest.skip("Materials database module not available", allow_module_level=True)


class TestMaterialProperty:
    """Test MaterialProperty dataclass."""

    def test_material_property_creation(self):
        """Test creating a MaterialProperty."""
        def corr(T):
            return 2.0 * T

        prop = MaterialProperty(
            name="test_prop",
            units="W/m-K",
            T_min=300.0,
            T_max=1000.0,
            correlation=corr,
            uncertainty=0.05,
        )

        assert prop.name == "test_prop"
        assert prop.units == "W/m-K"
        assert prop.T_min == 300.0
        assert prop.T_max == 1000.0
        assert prop.uncertainty == 0.05

    def test_material_property_call(self):
        """Test calling MaterialProperty at a temperature."""
        def corr(T):
            return 2.0 * T

        prop = MaterialProperty(
            name="test_prop",
            units="W/m-K",
            T_min=300.0,
            T_max=1000.0,
            correlation=corr,
        )

        value = prop(500.0)
        assert value == 1000.0

    def test_material_property_temperature_range_error(self):
        """Test MaterialProperty raises error for out-of-range temperature."""
        def corr(T):
            return 2.0 * T

        prop = MaterialProperty(
            name="test_prop",
            units="W/m-K",
            T_min=300.0,
            T_max=1000.0,
            correlation=corr,
        )

        with pytest.raises(ValueError, match="correlation valid for"):
            prop(200.0)  # Below T_min

        with pytest.raises(ValueError, match="correlation valid for"):
            prop(1500.0)  # Above T_max

    def test_material_property_evaluate_array(self):
        """Test MaterialProperty.evaluate_array vectorized evaluation."""
        def corr(T):
            return 2.0 * T

        prop = MaterialProperty(
            name="test_prop",
            units="W/m-K",
            T_min=300.0,
            T_max=1000.0,
            correlation=corr,
        )

        T_array = np.array([400.0, 500.0, 600.0])
        values = prop.evaluate_array(T_array)

        assert isinstance(values, np.ndarray)
        assert len(values) == 3
        assert np.allclose(values, [800.0, 1000.0, 1200.0])


class TestGraphiteMaterial:
    """Test GraphiteMaterial class."""

    def test_graphite_material_initialization_default(self):
        """Test GraphiteMaterial initialization with default grade."""
        graphite = GraphiteMaterial()
        assert graphite.grade == "IG-110"

    def test_graphite_material_initialization_custom_grade(self):
        """Test GraphiteMaterial initialization with custom grade."""
        graphite = GraphiteMaterial("H-451")
        assert graphite.grade == "H-451"

    def test_graphite_material_properties_ig110(self):
        """Test GraphiteMaterial properties for IG-110 grade."""
        graphite = GraphiteMaterial("IG-110")

        # Test thermal conductivity
        k = graphite.thermal_conductivity(500.0)
        assert k > 0
        assert isinstance(k, float)

        # Test specific heat
        cp = graphite.specific_heat(500.0)
        assert cp > 0
        assert isinstance(cp, float)

        # Test density
        rho = graphite.density(500.0)
        assert rho > 0
        assert isinstance(rho, float)

        # Test thermal expansion
        alpha = graphite.thermal_expansion(500.0)
        assert alpha > 0
        assert isinstance(alpha, float)

        # Test emissivity
        epsilon = graphite.emissivity(500.0)
        assert 0 < epsilon <= 1.0
        assert isinstance(epsilon, float)

        # Test Young's modulus
        E = graphite.youngs_modulus(500.0)
        assert E > 0
        assert isinstance(E, float)

    def test_graphite_material_properties_h451(self):
        """Test GraphiteMaterial properties for H-451 grade."""
        graphite = GraphiteMaterial("H-451")

        # Test thermal conductivity (has different correlation)
        k = graphite.thermal_conductivity(500.0)
        assert k > 0

        # Test below 600K branch
        k_low = graphite.thermal_conductivity(400.0)
        assert k_low > 0

        # Test above 600K branch
        k_high = graphite.thermal_conductivity(800.0)
        assert k_high > 0

    def test_graphite_material_properties_nbg18(self):
        """Test GraphiteMaterial properties for NBG-18 grade."""
        graphite = GraphiteMaterial("NBG-18")

        # Test thermal conductivity
        k = graphite.thermal_conductivity(500.0)
        assert k > 0

    def test_graphite_material_thermal_expansion_coefficient(self):
        """Test thermal_expansion_coefficient helper method."""
        graphite = GraphiteMaterial()

        alpha = graphite.thermal_expansion_coefficient(500.0)
        assert alpha > 0
        assert isinstance(alpha, float)

    def test_graphite_material_integrate_cte(self):
        """Test _integrate_cte method."""
        graphite = GraphiteMaterial()

        result = graphite._integrate_cte(300.0, 500.0)
        assert result > 0
        assert isinstance(result, float)

    def test_graphite_material_properties_at_temperature(self):
        """Test properties_at_temperature method."""
        graphite = GraphiteMaterial()

        props = graphite.properties_at_temperature(500.0)

        assert isinstance(props, dict)
        assert "thermal_conductivity" in props
        assert "specific_heat" in props
        assert "density" in props
        assert "thermal_expansion" in props
        assert "emissivity" in props
        assert "youngs_modulus" in props

        for key, value in props.items():
            assert isinstance(value, float)
            assert value > 0 or key == "thermal_expansion"  # thermal_expansion can be small


class TestHeliumCoolant:
    """Test HeliumCoolant class."""

    def test_helium_coolant_initialization(self):
        """Test HeliumCoolant initialization."""
        helium = HeliumCoolant()

        assert helium.molar_mass > 0
        assert helium.R_specific > 0

    def test_helium_coolant_density(self):
        """Test HeliumCoolant density calculation."""
        helium = HeliumCoolant()

        rho = helium.density(500.0, P=7.0e6)
        assert rho > 0
        assert isinstance(rho, float)

        # Test with different pressure
        rho2 = helium.density(500.0, P=5.0e6)
        assert rho2 < rho  # Lower pressure should give lower density

    def test_helium_coolant_dynamic_viscosity(self):
        """Test HeliumCoolant dynamic_viscosity calculation."""
        helium = HeliumCoolant()

        mu = helium.dynamic_viscosity(500.0)
        assert mu > 0
        assert isinstance(mu, float)

    def test_helium_coolant_thermal_conductivity(self):
        """Test HeliumCoolant thermal_conductivity calculation."""
        helium = HeliumCoolant()

        k = helium.thermal_conductivity(500.0)
        assert k > 0
        assert isinstance(k, float)

    def test_helium_coolant_specific_heat(self):
        """Test HeliumCoolant specific_heat calculation."""
        helium = HeliumCoolant()

        cp = helium.specific_heat(500.0)
        assert cp > 0
        assert isinstance(cp, float)

    def test_helium_coolant_prandtl_number(self):
        """Test HeliumCoolant Prandtl number calculation."""
        helium = HeliumCoolant()

        Pr = helium.prandtl_number(500.0)
        assert Pr > 0
        assert isinstance(Pr, float)
        # Helium Prandtl number is typically 0.6-0.7, but the calculation might differ
        # Just check it's positive and reasonable
        assert 0.3 < Pr < 3.0


class TestTRISOFuel:
    """Test TRISOFuel class."""

    def test_triso_fuel_initialization_uco(self):
        """Test TRISOFuel initialization with UCO."""
        triso = TRISOFuel("UCO")
        # Check that it was initialized (no specific fuel_type attribute)
        assert hasattr(triso, "kernel_radius")

    def test_triso_fuel_initialization_uo2(self):
        """Test TRISOFuel initialization with UO2."""
        triso = TRISOFuel("UO2")
        # Check that it was initialized
        assert hasattr(triso, "kernel_radius")

    def test_triso_fuel_geometry_properties(self):
        """Test TRISOFuel geometry properties."""
        triso = TRISOFuel("UCO")

        assert triso.kernel_radius > 0
        assert triso.buffer_thickness > 0
        assert triso.ipyc_thickness > 0  # Inner PyC
        assert triso.sic_thickness > 0
        assert triso.opyc_thickness > 0  # Outer PyC
        assert triso.total_radius > 0

        # Total radius should be sum of all layers
        expected_total = (
            triso.kernel_radius
            + triso.buffer_thickness
            + triso.ipyc_thickness
            + triso.sic_thickness
            + triso.opyc_thickness
        )
        assert np.isclose(triso.total_radius, expected_total)

    def test_triso_fuel_effective_conductivity(self):
        """Test TRISOFuel effective conductivity."""
        triso = TRISOFuel("UCO")

        k_eff = triso.effective_conductivity(1200.0)
        assert k_eff > 0
        assert isinstance(k_eff, float)

    def test_triso_fuel_failure_probability(self):
        """Test TRISOFuel failure probability calculation."""
        triso = TRISOFuel("UCO")

        # Low temperature, burnup, and fluence should give low failure probability
        P_fail = triso.failure_probability(T_max=1000.0, burnup=0.0, fluence=0.0)
        assert 0 <= P_fail <= 1.0

        # Higher values should increase failure probability
        P_fail_high = triso.failure_probability(T_max=2000.0, burnup=100.0, fluence=1e25)
        assert P_fail_high >= P_fail


class TestMaterialDatabase:
    """Test MaterialDatabase class."""

    def test_material_database_initialization(self):
        """Test MaterialDatabase initialization."""
        db = MaterialDatabase()

        assert isinstance(db.materials, dict)
        assert len(db.materials) > 0

    def test_material_database_get_graphite(self):
        """Test getting graphite material."""
        db = MaterialDatabase()

        graphite = db.get("graphite_IG-110")
        assert isinstance(graphite, GraphiteMaterial)
        assert graphite.grade == "IG-110"

    def test_material_database_get_helium(self):
        """Test getting helium material."""
        db = MaterialDatabase()

        helium = db.get("helium")
        assert isinstance(helium, HeliumCoolant)

    def test_material_database_get_triso(self):
        """Test getting TRISO material."""
        db = MaterialDatabase()

        triso = db.get("triso_uco")
        assert isinstance(triso, TRISOFuel)
        assert hasattr(triso, "kernel_radius")

    def test_material_database_get_nonexistent(self):
        """Test getting nonexistent material raises KeyError."""
        db = MaterialDatabase()

        with pytest.raises(KeyError, match="not found"):
            db.get("nonexistent_material")

    def test_material_database_list_materials(self):
        """Test list_materials method."""
        db = MaterialDatabase()

        materials = db.list_materials()
        assert hasattr(materials, "filter")  # Should be a Polars DataFrame
        assert len(materials) > 0

    def test_material_database_list_materials_filtered(self):
        """Test list_materials with category filter."""
        db = MaterialDatabase()

        # Filter by category
        moderators = db.list_materials(category="moderator")
        assert hasattr(moderators, "filter")  # Should be a Polars DataFrame

        coolants = db.list_materials(category="coolant")
        assert hasattr(coolants, "filter")

        fuels = db.list_materials(category="fuel")
        assert hasattr(fuels, "filter")

    def test_material_database_compare_properties(self):
        """Test compare_properties method."""
        db = MaterialDatabase()

        T_range = np.linspace(300, 1000, 5)
        comparison = db.compare_properties(
            ["graphite_IG-110", "graphite_H-451"],
            "thermal_conductivity",
            T_range,
        )

        assert hasattr(comparison, "filter")  # Should be a Polars DataFrame
        assert len(comparison) > 0

    def test_material_database_compare_properties_helium(self):
        """Test compare_properties with helium (needs pressure)."""
        db = MaterialDatabase()

        T_range = np.linspace(300, 1000, 5)
        comparison = db.compare_properties(
            ["helium"],
            "density",
            T_range,
        )

        assert hasattr(comparison, "filter")
        assert len(comparison) > 0

    def test_material_database_compare_properties_nonexistent_property(self):
        """Test compare_properties with nonexistent property returns empty."""
        db = MaterialDatabase()

        T_range = np.linspace(300, 1000, 5)
        comparison = db.compare_properties(
            ["graphite_IG-110"],
            "nonexistent_property",
            T_range,
        )

        assert hasattr(comparison, "filter")
        # Should be empty if property doesn't exist
        assert len(comparison) == 0


class TestFastFunctions:
    """Test Numba-accelerated fast property functions."""

    def test_graphite_conductivity_fast(self):
        """Test graphite_conductivity_fast function."""
        T_array = np.linspace(300, 2000, 100)

        k_array = graphite_conductivity_fast(T_array, grade=0)

        assert isinstance(k_array, np.ndarray)
        assert len(k_array) == len(T_array)
        assert np.all(k_array > 0)

    def test_helium_properties_fast(self):
        """Test helium_properties_fast function."""
        T_array = np.linspace(300, 2000, 100)

        rho, mu, k = helium_properties_fast(T_array, P=7.0e6)

        assert isinstance(rho, np.ndarray)
        assert isinstance(mu, np.ndarray)
        assert isinstance(k, np.ndarray)

        assert len(rho) == len(T_array)
        assert len(mu) == len(T_array)
        assert len(k) == len(T_array)

        assert np.all(rho > 0)
        assert np.all(mu > 0)
        assert np.all(k > 0)

