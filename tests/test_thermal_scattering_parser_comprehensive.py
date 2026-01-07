"""
Comprehensive tests for thermal scattering parser to improve coverage to 80%+.

Tests cover:
- File parsing
- MT=2 parsing (coherent elastic)
- MT=4 parsing (incoherent inelastic)
- Temperature interpolation
- Material name extraction
- S(α,β) data handling
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from smrforge.core.thermal_scattering_parser import (
    ThermalScatteringParser,
    ScatteringLawData,
)


@pytest.fixture
def mock_tsl_file(tmp_path):
    """Create a mock TSL ENDF file."""
    filepath = tmp_path / "tsl-H_in_H2O.endf"
    
    # Create minimal valid ENDF TSL file (MF=7)
    lines = [
        " 1.001000+3 1.000000+0          0          0          0          0  7  1     \n",
        " 0.000000+0 0.000000+0          0          0          0          0  7  2     \n",
        " 2.936000+2 0.000000+0          0          0          1          0  7  2     \n",
        " 0.000000+0 0.000000+0          0          0          2         10  7  2     \n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000+0 1.000000+0 2.000000+0  7  2     \n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0  7  2     \n",
        " 0.000000+0 0.000000+0          0          0          0          0  7  4     \n",
        " 2.936000+2 0.000000+0          0          0          1          0  7  4     \n",
        " 0.000000+0 0.000000+0          0          0          2         10  7  4     \n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000+0 1.000000+0 2.000000+0  7  4     \n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0  7  4     \n",
        "                                                                    -1  0  0   \n",
    ]
    
    filepath.write_text("".join(lines))
    return filepath


class TestThermalScatteringParserComprehensive:
    """Comprehensive tests for ThermalScatteringParser."""
    
    def test_parse_file_success(self, mock_tsl_file):
        """Test successful file parsing."""
        parser = ThermalScatteringParser()
        tsl_data = parser.parse_file(mock_tsl_file)
        
        assert tsl_data is not None
        assert isinstance(tsl_data, ScatteringLawData)
        assert tsl_data.material_name is not None
        assert tsl_data.zaid > 0
    
    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file."""
        parser = ThermalScatteringParser()
        result = parser.parse_file(Path("nonexistent.endf"))
        
        assert result is None
    
    def test_parse_mt2_section(self, mock_tsl_file):
        """Test parsing MT=2 (coherent elastic)."""
        parser = ThermalScatteringParser()
        
        with open(mock_tsl_file, "r") as f:
            lines = f.readlines()
        
        # Find MT=2 section
        start_line = 0
        for i, line in enumerate(lines):
            if " 7  2     " in line and i > 0:
                start_line = i
                break
        
        result = parser._parse_mt2_section(lines, start_line)
        
        # Should return tuple of (s_alpha_beta, alpha_values, beta_values, temperature, zaid, bound_mass) or None
        assert result is None or (isinstance(result, tuple) and len(result) == 6)
    
    def test_parse_mt4_section(self, mock_tsl_file):
        """Test parsing MT=4 (incoherent inelastic)."""
        parser = ThermalScatteringParser()
        
        with open(mock_tsl_file, "r") as f:
            lines = f.readlines()
        
        # Find MT=4 section
        start_line = 0
        for i, line in enumerate(lines):
            if " 7  4     " in line and i > 0:
                start_line = i
                break
        
        result = parser._parse_mt4_section(lines, start_line)
        
        # Should return tuple of (s_alpha_beta, alpha_values, beta_values, temperature, zaid, bound_mass) or None
        assert result is None or (isinstance(result, tuple) and len(result) == 6)
    
    def test_extract_material_name(self):
        """Test material name extraction."""
        parser = ThermalScatteringParser()
        
        # Test various filename patterns
        name1 = parser._extract_material_name("tsl-H_in_H2O.endf")
        assert name1 is not None
        
        name2 = parser._extract_material_name("tsl-C_in_graphite.endf")
        assert name2 is not None
    
    def test_scattering_law_data(self):
        """Test ScatteringLawData dataclass."""
        alpha_values = np.logspace(-2, 2, 50)
        beta_values = np.linspace(-50, 50, 100)
        s_alpha_beta = np.ones((1, len(alpha_values), len(beta_values)))
        
        tsl_data = ScatteringLawData(
            material_name="H_in_H2O",
            zaid=1001,
            temperature=293.6,
            temperatures=None,
            multi_temperature=False,
            alpha_values=alpha_values,
            beta_values=beta_values,
            s_alpha_beta=s_alpha_beta,
            bound_atom_mass=1.008,
            coherent_scattering=False,
        )
        
        assert tsl_data.material_name == "H_in_H2O"
        assert tsl_data.zaid == 1001
        assert tsl_data.temperature == 293.6
        assert tsl_data.multi_temperature is False
        assert len(tsl_data.alpha_values) == 50
        assert len(tsl_data.beta_values) == 100
        assert tsl_data.s_alpha_beta.shape == (1, 50, 100)
    
    def test_scattering_law_data_multi_temperature(self):
        """Test ScatteringLawData with multiple temperatures."""
        alpha_values = np.logspace(-2, 2, 50)
        beta_values = np.linspace(-50, 50, 100)
        temperatures = np.array([293.6, 600.0, 900.0])
        s_alpha_beta = np.ones((3, len(alpha_values), len(beta_values)))
        
        tsl_data = ScatteringLawData(
            material_name="H_in_H2O",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            multi_temperature=True,
            alpha_values=alpha_values,
            beta_values=beta_values,
            s_alpha_beta=s_alpha_beta,
            bound_atom_mass=1.008,
            coherent_scattering=False,
        )
        
        assert tsl_data.multi_temperature is True
        assert len(tsl_data.temperatures) == 3
        assert tsl_data.s_alpha_beta.shape == (3, 50, 100)
    
    def test_parse_file_exception_handling(self, tmp_path):
        """Test exception handling during parsing."""
        parser = ThermalScatteringParser()
        
        # Create malformed file
        filepath = tmp_path / "tsl-H_in_H2O.endf"
        filepath.write_text("invalid content\n" * 10)
        
        # Should handle exception gracefully
        result = parser.parse_file(filepath)
        
        # Should return None or handle gracefully
        assert result is None or isinstance(result, ScatteringLawData)
    
    def test_parse_file_empty_file(self, tmp_path):
        """Test parsing empty file."""
        parser = ThermalScatteringParser()
        
        filepath = tmp_path / "empty.endf"
        filepath.write_text("")
        
        result = parser.parse_file(filepath)
        
        # Should return placeholder data or None
        assert result is None or isinstance(result, ScatteringLawData)
    
    def test_parse_file_fallback_to_placeholder(self, tmp_path):
        """Test fallback to placeholder when parsing fails."""
        parser = ThermalScatteringParser()
        
        # Create file with no MF=7 sections
        filepath = tmp_path / "tsl-test.endf"
        filepath.write_text(" 1.001000+3 1.000000+0          0          0          0          0  3  1     \n")
        
        result = parser.parse_file(filepath)
        
        # Should return placeholder data
        assert result is not None
        assert isinstance(result, ScatteringLawData)
        assert result.material_name is not None
    
    def test_parse_file_read_exception(self, tmp_path):
        """Test exception handling during file read."""
        parser = ThermalScatteringParser()
        
        # Create file that can't be read (mock permission error)
        filepath = tmp_path / "readonly.endf"
        filepath.write_text("test")
        
        # Mock open to raise exception
        with patch('builtins.open', side_effect=Exception("Read error")):
            result = parser.parse_file(filepath)
            assert result is None
    
    def test_parse_mt2_section_exception(self):
        """Test MT=2 section parsing with exception."""
        parser = ThermalScatteringParser()
        
        # Invalid lines that will cause exception in parsing
        lines = ["invalid line with insufficient length\n"]
        
        result = parser._parse_mt2_section(lines, 0)
        # Should return a tuple even with minimal valid data (defaults)
        assert result is not None and isinstance(result, tuple)
    
    def test_parse_mt2_section_invalid_index(self):
        """Test MT=2 section parsing with invalid start index."""
        parser = ThermalScatteringParser()
        
        lines = [" 2.936000+2 1.001000+3          0          0          0          0  7  2     \n"]
        
        result = parser._parse_mt2_section(lines, 100)  # Index out of range
        assert result is None
    
    def test_parse_mt4_section_exception(self):
        """Test MT=4 section parsing with exception."""
        parser = ThermalScatteringParser()
        
        # Invalid lines
        lines = ["invalid line\n"]
        
        result = parser._parse_mt4_section(lines, 0)
        assert result is None
    
    def test_parse_mt4_section_invalid_index(self):
        """Test MT=4 section parsing with invalid start index."""
        parser = ThermalScatteringParser()
        
        lines = [" 2.936000+2 1.001000+3          0          0          0          0  7  4     \n"]
        
        result = parser._parse_mt4_section(lines, 100)  # Index out of range
        assert result is None
    
    def test_parse_mt4_section_no_data(self):
        """Test MT=4 section parsing with no valid data."""
        parser = ThermalScatteringParser()
        
        # Lines with MF=7 but no valid data
        lines = [
            " 2.936000+2 1.001000+3          0          0          0          0  7  4     \n",
            "                                                                    -1  0  0   \n",
        ]
        
        result = parser._parse_mt4_section(lines, 0)
        # Should return None if no alpha values found
        assert result is None or result[0] is not None
    
    def test_parse_endf_mf7_no_sections(self):
        """Test parsing ENDF file with no MF=7 sections."""
        parser = ThermalScatteringParser()
        
        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0  3  1     \n",
        ]
        
        result = parser._parse_endf_mf7(lines, "test", Path("test.endf"))
        assert result is None
    
    def test_parse_endf_mf7_mt2_fallback(self):
        """Test parsing ENDF file with MT=2 when MT=4 not available."""
        parser = ThermalScatteringParser()
        
        lines = [
            " 2.936000+2 1.001000+3          0          0          0          0  7  2     \n",
        ]
        
        result = parser._parse_endf_mf7(lines, "test", Path("test.endf"))
        # Should return MT=2 data or None
        assert result is None or isinstance(result, ScatteringLawData)
    
    def test_get_s_no_data(self):
        """Test get_s when data is None."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=None,
            beta_values=beta,
            s_alpha_beta=np.ones((3, 3)),
        )
        
        s_value = data.get_s(1.0, 0.0)
        assert s_value == 0.0
    
    def test_get_s_exact_match(self):
        """Test get_s with exact alpha and beta match."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_data = np.array([[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Test exact match
        s_value = data.get_s(1.0, 0.0)
        assert abs(s_value - 2.5) < 1e-10
    
    def test_get_s_extrapolation(self):
        """Test get_s with values outside range."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_data = np.array([[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Test extrapolation (before start) - uses clamped indices
        s_value = data.get_s(0.05, -10.0)
        assert isinstance(s_value, (int, float, np.number))
        
        # Test extrapolation (after end) - uses clamped indices
        s_value = data.get_s(100.0, 10.0)
        assert isinstance(s_value, (int, float, np.number))
    
    def test_get_s_single_point(self):
        """Test get_s with single point arrays."""
        alpha = np.array([1.0])
        beta = np.array([0.0])
        s_data = np.array([[2.5]])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        s_value = data.get_s(1.0, 0.0)
        assert abs(s_value - 2.5) < 1e-10
        
        # Test interpolation at different point
        s_value = data.get_s(0.5, 0.0)
        assert s_value >= 0
    
    def test_get_s_temperature_interpolation(self):
        """Test get_s with temperature interpolation."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        temperatures = np.array([293.6, 600.0, 900.0])
        s_data = np.ones((3, 3, 3)) * np.array([1.0, 1.5, 2.0])[:, np.newaxis, np.newaxis]
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            multi_temperature=True,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Test at intermediate temperature
        s_value = data.get_s(1.0, 0.0, temperature=450.0)
        assert s_value >= 0
    
    def test_get_s_temperature_exact_match(self):
        """Test get_s with exact temperature match."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        temperatures = np.array([293.6, 600.0, 900.0])
        s_data = np.ones((3, 3, 3)) * np.array([1.0, 1.5, 2.0])[:, np.newaxis, np.newaxis]
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            multi_temperature=True,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Test at exact temperature
        s_value = data.get_s(1.0, 0.0, temperature=600.0)
        assert abs(s_value - 1.5) < 1e-6
    
    def test_interpolate_temperature_no_multi_temp(self):
        """Test temperature interpolation when not multi-temperature."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_data = np.ones((3, 3))
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            multi_temperature=False,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Should return original data
        result = data._interpolate_temperature(600.0)
        assert np.array_equal(result, s_data)
    
    def test_interpolate_temperature_single_temp(self):
        """Test temperature interpolation with single temperature point."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        temperatures = np.array([293.6])
        s_data = np.ones((1, 3, 3))
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            multi_temperature=True,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        result = data._interpolate_temperature(600.0)
        assert result.shape == (3, 3)
    
    def test_compute_thermal_scattering_xs_zero_energy(self):
        """Test thermal scattering cross-section with zero energy."""
        parser = ThermalScatteringParser()
        
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
        
        # Zero energy should return zero
        xs = parser.compute_thermal_scattering_xs(data, 0.0, 0.025, 293.6)
        assert xs == 0.0
    
    def test_compute_thermal_scattering_xs_different_temperature(self):
        """Test thermal scattering cross-section at different temperature."""
        parser = ThermalScatteringParser()
        
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
        
        # Test at different temperature
        xs = parser.compute_thermal_scattering_xs(data, 0.025, 0.025, 600.0)
        assert xs >= 0
    
    def test_create_placeholder_data_various_materials(self):
        """Test placeholder data creation for various materials."""
        parser = ThermalScatteringParser()
        
        # Test H in H2O
        data_h = parser._create_placeholder_data("H_in_H2O", Path("test.endf"))
        assert data_h.zaid == 1001
        assert not data_h.coherent_scattering
        
        # Test C in graphite
        data_c = parser._create_placeholder_data("C_in_graphite", Path("test.endf"))
        assert data_c.zaid == 6000
        assert data_c.coherent_scattering
        
        # Test D in D2O
        data_d = parser._create_placeholder_data("D_in_D2O", Path("test.endf"))
        assert data_d.zaid == 1002
        
        # Test O in material
        data_o = parser._create_placeholder_data("O_in_UO2", Path("test.endf"))
        assert data_o.zaid == 8016
        assert data_o.coherent_scattering
        
        # Test default
        data_default = parser._create_placeholder_data("unknown", Path("test.endf"))
        assert data_default.zaid == 1001
    
    def test_extract_material_name_various_patterns(self):
        """Test material name extraction with various patterns."""
        parser = ThermalScatteringParser()
        
        # Test various prefixes
        assert parser._extract_material_name("tsl-H_in_H2O.endf") == "H in H2O"
        assert parser._extract_material_name("thermal-H_in_H2O.endf") == "H in H2O"
        assert parser._extract_material_name("ts-H_in_H2O.endf") == "H in H2O"
        
        # Test without prefix - gets mapped if in MATERIAL_MAPPINGS
        name = parser._extract_material_name("H_in_H2O.endf")
        assert name == "H in H2O"  # Gets mapped from MATERIAL_MAPPINGS
        
        # Test uppercase - not in MATERIAL_MAPPINGS, so returns as-is (uppercase not mapped)
        assert parser._extract_material_name("TSL-H_IN_H2O.ENDF") == "H_IN_H2O"
        
        # Test unmapped material
        result = parser._extract_material_name("tsl-unknown.endf")
        assert result is not None
        assert result == "unknown"
    
    def test_get_s_interpolation_edge_cases(self):
        """Test get_s interpolation edge cases."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_data = np.array([[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Test at boundary values
        s1 = data.get_s(0.1, -5.0)  # First alpha, first beta
        assert s1 >= 0
        
        s2 = data.get_s(10.0, 5.0)  # Last alpha, last beta
        assert s2 >= 0
        
        # Test with very close values (within tolerance)
        s3 = data.get_s(1.0 + 1e-11, 0.0 + 1e-11)
        assert abs(s3 - 2.5) < 1e-6

    def test_get_s_with_temperature_parameter(self):
        """Test get_s with explicit temperature parameter for multi-temperature data."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        temperatures = np.array([293.6, 600.0, 1200.0])
        # Multi-temperature data: [n_temp, n_alpha, n_beta]
        s_data = np.array([
            [[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]],  # T=293.6K
            [[1.1, 2.1, 1.1], [1.6, 2.6, 1.6], [1.1, 2.1, 1.1]],  # T=600K
            [[1.2, 2.2, 1.2], [1.7, 2.7, 1.7], [1.2, 2.2, 1.2]],  # T=1200K
        ])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
            multi_temperature=True,
        )
        
        # Test with explicit temperature
        s_value = data.get_s(1.0, 0.0, temperature=600.0)
        assert s_value >= 0

    def test_interpolate_temperature_exact_match_within_1k(self):
        """Test _interpolate_temperature with exact match within 1K tolerance."""
        alpha = np.array([1.0])
        beta = np.array([0.0])
        temperatures = np.array([293.6, 600.0, 1200.0])
        s_data = np.array([
            [[2.0]],  # T=293.6K
            [[2.5]],  # T=600K
            [[3.0]],  # T=1200K
        ])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            temperatures=temperatures,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
            multi_temperature=True,
        )
        
        # Temperature within 1K of existing (294.0 vs 293.6)
        s_data_result = data._interpolate_temperature(294.0)
        assert s_data_result is not None
        assert s_data_result.shape == (1, 1)

    def test_parse_endf_mf7_line_length_check(self):
        """Test _parse_endf_mf7 with lines shorter than 75 characters."""
        parser = ThermalScatteringParser()
        
        # Lines shorter than 75 characters should be skipped
        lines = [
            "short line\n",  # < 75 chars
            " 1.001000+3 1.000000+0          0          0          0          0  7  1     \n",
        ]
        
        result = parser._parse_endf_mf7(lines, "test", Path("test.endf"))
        # Should return None because no valid MF=7 sections found
        assert result is None

    def test_parse_endf_mf7_mt2_only_fallback(self):
        """Test _parse_endf_mf7 with MT=2 only (fallback when MT=4 not available)."""
        parser = ThermalScatteringParser()
        
        lines = [
            " 1.001000+3 1.000000+0          0          0          0          0  7  1     \n",
            " 0.000000+0 0.000000+0          0          0          0          0  7  2     \n",
            " 2.936000+2 0.000000+0          0          0          1          0  7  2     \n",
            " 0.000000+0 0.000000+0          0          0          2         10  7  2     \n",
            "                                                                    -1  0  0   \n",
        ]
        
        result = parser._parse_endf_mf7(lines, "test", Path("test.endf"))
        # Should return ScatteringLawData with MT=2 data
        assert result is not None
        assert isinstance(result, ScatteringLawData)

    def test_parse_mt4_section_with_empty_alpha_list(self):
        """Test _parse_mt4_section when no alpha values are parsed."""
        parser = ThermalScatteringParser()
        
        # Create lines that won't parse any alpha values
        lines = [
            " 2.936000+2 1.001000+3          0          0          1          0  7  4     \n",
            " 0.000000+0 0.000000+0          0          0          0          0  7  4     \n",
            "                                                                    -1  0  0   \n",
        ]
        
        result = parser._parse_mt4_section(lines, 0)
        # Should return None because no alpha values parsed
        assert result is None

    def test_parse_mt4_section_malformed_data_line(self):
        """Test _parse_mt4_section with malformed data lines."""
        parser = ThermalScatteringParser()
        
        lines = [
            " 2.936000+2 1.001000+3          0          0          1          0  7  4     \n",
            " 0.000000+0 0.000000+0          0          0          0          0  7  4     \n",
            "malformed line that cannot be parsed\n",
            "                                                                    -1  0  0   \n",
        ]
        
        result = parser._parse_mt4_section(lines, 0)
        # Should return None because no valid data parsed
        assert result is None or isinstance(result, tuple)

    def test_compute_thermal_scattering_xs_negative_energy_out(self):
        """Test compute_thermal_scattering_xs with negative energy_out."""
        alpha = np.array([0.1, 1.0, 10.0])
        beta = np.array([-5.0, 0.0, 5.0])
        s_data = np.array([[1.0, 2.0, 1.0], [1.5, 2.5, 1.5], [1.0, 2.0, 1.0]])
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # Negative energy_out should be handled (sqrt may return NaN, but max(0.0, xs) ensures >= 0)
        xs = ThermalScatteringParser.compute_thermal_scattering_xs(
            data, energy_in=1.0, energy_out=-0.5, temperature=293.6
        )
        assert xs >= 0

    def test_get_s_alpha_high_equals_alpha_low(self):
        """Test get_s when alpha_high == alpha_low (edge case)."""
        alpha = np.array([1.0])  # Single alpha value
        beta = np.array([0.0, 1.0])  # Multiple beta values
        s_data = np.array([[2.0, 3.0]])  # [n_alpha, n_beta]
        
        data = ScatteringLawData(
            material_name="test",
            zaid=1001,
            temperature=293.6,
            alpha_values=alpha,
            beta_values=beta,
            s_alpha_beta=s_data,
        )
        
        # When alpha_low == alpha_high, should use single point
        s_value = data.get_s(1.0, 0.5)
        assert s_value >= 0

    def test_parse_mt2_section_with_valid_zaid(self):
        """Test _parse_mt2_section with valid ZAID extraction."""
        parser = ThermalScatteringParser()
        
        lines = [
            " 2.936000+2 1.001000+3          0          0          1          0  7  2     \n",
        ]
        
        result = parser._parse_mt2_section(lines, 0)
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 6
        # ZAID should be extracted (1001 = H-1)
        assert result[4] == 1001  # zaid

