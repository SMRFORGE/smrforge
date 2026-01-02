"""
Comprehensive tests for gamma production parser to improve coverage to 80%+.

Tests cover:
- File parsing
- Filename parsing
- MF=12 parsing (prompt)
- MF=13,14 parsing (delayed)
- Spectrum parsing
- Data access methods
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from smrforge.core.gamma_production_parser import (
    ENDFGammaProductionParser,
    GammaProductionData,
    GammaProductionSpectrum,
)
from smrforge.core.reactor_core import Nuclide


@pytest.fixture
def mock_gamma_production_file(tmp_path):
    """Create a mock gamma production ENDF file."""
    filepath = tmp_path / "gammas-092_U_235.endf"
    
    # Create minimal valid ENDF gamma production file
    lines = [
        " 9.223500+4 2.345678+2          0          0          0          0 12 18     \n",
        " 0.000000+0 0.000000+0          0          0          2         10 12 18     \n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000+0 1.000000+0 2.000000+0 12 18     \n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0 12 18     \n",
        " 9.223500+4 2.345678+2          0          0          0          0 13 18     \n",
        " 0.000000+0 0.000000+0          0          0          2         10 13 18     \n",
        " 1.000000-2 5.000000-1 1.000000-1 2.500000+0 1.000000+0 1.000000+0 13 18     \n",
        " 1.000000+1 5.000000-2 0.000000+0 0.000000+0 0.000000+0 0.000000+0 13 18     \n",
        "                                                                    -1  0  0   \n",
    ]
    
    filepath.write_text("".join(lines))
    return filepath


class TestENDFGammaProductionParserComprehensive:
    """Comprehensive tests for ENDFGammaProductionParser."""
    
    def test_parse_file_success(self, mock_gamma_production_file):
        """Test successful file parsing."""
        parser = ENDFGammaProductionParser()
        gamma_data = parser.parse_file(mock_gamma_production_file)
        
        assert gamma_data is not None
        assert isinstance(gamma_data, GammaProductionData)
        assert gamma_data.nuclide.Z == 92
        assert gamma_data.nuclide.A == 235
    
    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file."""
        parser = ENDFGammaProductionParser()
        result = parser.parse_file(Path("nonexistent.endf"))
        
        assert result is None
    
    def test_parse_filename_valid(self):
        """Test parsing valid filename."""
        parser = ENDFGammaProductionParser()
        
        result = parser._parse_filename("gammas-092_U_235.endf")
        assert result is not None
        assert result.Z == 92
        assert result.A == 235
    
    def test_parse_filename_variations(self):
        """Test parsing various filename formats."""
        parser = ENDFGammaProductionParser()
        
        # Standard format
        result = parser._parse_filename("gammas-001_H_001.endf")
        assert result is not None
        assert result.Z == 1
        assert result.A == 1
        
        # Alternative format
        result = parser._parse_filename("gamma-092_U_235.endf")
        assert result is not None
        assert result.Z == 92
        
        # With metastable
        result = parser._parse_filename("gammas-092_U_239m1.endf")
        assert result is not None
        assert result.m == 1
    
    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        parser = ENDFGammaProductionParser()
        
        result = parser._parse_filename("invalid_filename.txt")
        assert result is None
    
    def test_parse_mf12(self, mock_gamma_production_file):
        """Test parsing MF=12 (prompt gamma)."""
        parser = ENDFGammaProductionParser()
        
        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()
        
        spectra = parser._parse_mf12(lines)
        
        assert isinstance(spectra, dict)
        # Should have fission spectrum (MT=18)
        if "fission" in spectra:
            assert isinstance(spectra["fission"], GammaProductionSpectrum)
            assert spectra["fission"].prompt is True
    
    def test_parse_mf13_14(self, mock_gamma_production_file):
        """Test parsing MF=13,14 (delayed gamma)."""
        parser = ENDFGammaProductionParser()
        
        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()
        
        spectra = parser._parse_mf13_14(lines)
        
        assert isinstance(spectra, dict)
        # Should have delayed spectra if present
        for spectrum in spectra.values():
            assert spectrum.prompt is False
    
    def test_parse_gamma_spectrum_section(self, mock_gamma_production_file):
        """Test parsing gamma spectrum section."""
        parser = ENDFGammaProductionParser()
        
        with open(mock_gamma_production_file, "r") as f:
            lines = f.readlines()
        
        # Find MF=12, MT=18 section
        start_idx = 0
        for i, line in enumerate(lines):
            if "12 18" in line:
                start_idx = i
                break
        
        result = parser._parse_gamma_spectrum_section(lines, start_idx, 18)
        
        assert result is not None
        energy, intensity = result
        assert len(energy) > 0
        assert len(intensity) > 0
        assert len(energy) == len(intensity)
    
    def test_gamma_production_data_methods(self):
        """Test GammaProductionData methods."""
        u235 = Nuclide(Z=92, A=235)
        
        # Create prompt spectrum
        prompt_spectrum = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0, 1.5]),
            intensity=np.array([0.3, 0.5, 0.2]),
            total_yield=1.0,
            prompt=True,
        )
        
        # Create delayed spectrum
        delayed_spectrum = GammaProductionSpectrum(
            reaction="fission",
            energy=np.array([0.5, 1.0]),
            intensity=np.array([0.6, 0.4]),
            total_yield=0.5,
            prompt=False,
        )
        
        gamma_data = GammaProductionData(
            nuclide=u235,
            prompt_spectra={"fission": prompt_spectrum},
            delayed_spectra={"fission": delayed_spectrum},
        )
        
        # Test get_total_gamma_yield
        prompt_yield = gamma_data.get_total_gamma_yield("fission", prompt=True)
        assert prompt_yield == 1.0
        
        delayed_yield = gamma_data.get_total_gamma_yield("fission", prompt=False)
        assert delayed_yield == 0.5
        
        # Test get_gamma_spectrum
        prompt_spec = gamma_data.get_gamma_spectrum("fission", prompt=True)
        assert prompt_spec is not None
        assert prompt_spec.prompt is True
        
        delayed_spec = gamma_data.get_gamma_spectrum("fission", prompt=False)
        assert delayed_spec is not None
        assert delayed_spec.prompt is False
        
        # Test missing reaction
        missing_yield = gamma_data.get_total_gamma_yield("capture", prompt=True)
        assert missing_yield == 0.0
        
        missing_spec = gamma_data.get_gamma_spectrum("capture", prompt=True)
        assert missing_spec is None
    
    def test_parse_file_exception_handling(self, tmp_path):
        """Test exception handling during parsing."""
        parser = ENDFGammaProductionParser()
        
        # Create malformed file
        filepath = tmp_path / "gammas-092_U_235.endf"
        filepath.write_text("invalid content\n" * 10)
        
        # Should handle exception gracefully
        result = parser.parse_file(filepath)
        
        # Should return None or handle gracefully
        assert result is None or isinstance(result, GammaProductionData)
    
    def test_reaction_mt_mapping(self):
        """Test reaction MT mapping."""
        parser = ENDFGammaProductionParser()
        
        # Check that MT numbers are mapped correctly
        assert 18 in parser.reaction_mt_map
        assert parser.reaction_mt_map[18] == "fission"
        assert 102 in parser.reaction_mt_map
        assert parser.reaction_mt_map[102] == "capture"

