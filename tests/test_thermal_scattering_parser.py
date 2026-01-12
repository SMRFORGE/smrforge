"""
Tests for thermal scattering law (TSL) parser.
"""

import numpy as np
import pytest
from pathlib import Path

from smrforge.core.reactor_core import Nuclide
from smrforge.core.thermal_scattering_parser import (
    ScatteringLawData,
    ThermalScatteringParser,
    get_tsl_material_name,
)


class TestScatteringLawData:
    """Test ScatteringLawData dataclass."""

    def test_scattering_law_data_creation(self):
        """Test creating ScatteringLawData."""
        alpha = np.logspace(-2, 2, 10)
        beta = np.linspace(-10, 10, 20)
        s_alpha_beta = np.ones((10, 20))

        data = ScatteringLawData(
            material_name="H_in_H2O",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_alpha_beta,
            bound_atom_mass=1.008,
            coherent_scattering=False,
        )

        assert data.material_name == "H_in_H2O"
        assert data.zaid == 1001
        assert data.temperature == 293.6
        assert len(data.alpha_values) == 10
        assert len(data.beta_values) == 20
        assert data.s_alpha_beta.shape == (10, 20)

    def test_get_s_interpolation(self):
        """Test S(α,β) interpolation."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_alpha_beta = np.array([[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]])

        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_alpha_beta,
        )

        # Test exact match
        s_exact = data.get_s(1.0, 0.0)
        assert abs(s_exact - 2.5) < 1e-10

        # Test interpolation
        s_interp = data.get_s(0.5, 0.0)
        assert 1.0 < s_interp < 2.5

    def test_get_s_temperature_interpolation(self):
        """Test temperature interpolation in get_s()."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        
        # Multi-temperature data
        temperatures = np.array([293.6, 600.0, 900.0])
        s_alpha_beta = np.zeros((3, 3, 3))  # [n_temp, n_alpha, n_beta]
        s_alpha_beta[0, :, :] = 1.0  # 293.6 K
        s_alpha_beta[1, :, :] = 1.5  # 600 K
        s_alpha_beta[2, :, :] = 2.0  # 900 K

        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_alpha_beta,
            multi_temperature=True,
        )

        # Test interpolation at intermediate temperature
        s_interp = data.get_s(1.0, 0.0, temperature=450.0)
        assert 1.0 < s_interp < 1.5


class TestThermalScatteringParser:
    """Test ThermalScatteringParser."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = ThermalScatteringParser()
        assert parser is not None

    def test_extract_material_name(self):
        """Test material name extraction from filename."""
        parser = ThermalScatteringParser()

        assert parser._extract_material_name("tsl-H_in_H2O.endf") == "H in H2O"
        assert parser._extract_material_name("thermal-C_in_graphite.endf") == "C in graphite"
        assert parser._extract_material_name("ts-D_in_D2O.endf") == "D in D2O"

    def test_create_placeholder_data(self):
        """Test placeholder data creation."""
        parser = ThermalScatteringParser()
        # _create_placeholder_data uses the material_name parameter as-is
        # It checks for substrings to determine zaid/bound_mass but doesn't change material_name
        data = parser._create_placeholder_data("H_in_H2O", Path("tsl-H_in_H2O.endf"))

        # material_name is used as passed, not mapped
        assert data.material_name == "H_in_H2O"
        assert data.zaid == 1001
        assert data.bound_atom_mass == 1.008
        assert not data.coherent_scattering
        assert len(data.alpha_values) > 0
        assert len(data.beta_values) > 0
        assert data.s_alpha_beta.shape == (len(data.alpha_values), len(data.beta_values))

    def test_compute_thermal_scattering_xs(self):
        """Test thermal scattering cross-section calculation."""
        parser = ThermalScatteringParser()
        
        # Create test data
        alpha = np.logspace(-2, 2, 10)
        beta = np.linspace(-10, 10, 20)
        s_alpha_beta = np.ones((10, 20))

        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_alpha_beta,
            bound_atom_mass=1.008,
        )

        # Test cross-section calculation
        xs = parser.compute_thermal_scattering_xs(data, 0.025, 0.025, 293.6)
        assert xs > 0
        assert np.isfinite(xs)


class TestTSLMaterialMapping:
    """Test material name mapping."""

    def test_get_tsl_material_name(self):
        """Test material name mapping."""
        assert get_tsl_material_name("H2O") == "H_in_H2O"
        assert get_tsl_material_name("water") == "H_in_H2O"
        assert get_tsl_material_name("graphite") == "C_in_graphite"
        assert get_tsl_material_name("C") == "C_in_graphite"
        assert get_tsl_material_name("D2O") == "D_in_D2O"
        assert get_tsl_material_name("BeO") == "Be_in_BeO"

    def test_get_tsl_material_name_unknown(self):
        """Test unknown material returns None."""
        assert get_tsl_material_name("unknown_material") is None


class TestTSLIntegration:
    """Test TSL integration with NuclearDataCache."""

    def test_get_thermal_scattering_data(self):
        """Test getting TSL data via reactor_core."""
        from smrforge.core.reactor_core import NuclearDataCache, get_thermal_scattering_data

        cache = NuclearDataCache()
        tsl_data = get_thermal_scattering_data("H_in_H2O", cache=cache)
        
        # Should return None if files not available, or ScatteringLawData if available
        assert tsl_data is None or isinstance(tsl_data, ScatteringLawData)

    def test_tsl_file_discovery(self):
        """Test TSL file discovery."""
        from smrforge.core.reactor_core import NuclearDataCache

        cache = NuclearDataCache()
        materials = cache.list_available_tsl_materials()
        
        # Should return a list (may be empty if no files)
        assert isinstance(materials, list)

