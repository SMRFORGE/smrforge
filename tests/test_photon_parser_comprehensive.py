"""
Comprehensive tests for photon parser to improve coverage to 80%+.

Tests cover:
- File parsing
- Filename parsing
- MT section parsing
- Interpolation
- Energy grid creation
- Error handling
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from smrforge.core.photon_parser import ENDFPhotonParser, PhotonCrossSection


@pytest.fixture
def mock_photon_file(tmp_path):
    """Create a mock photon ENDF file."""
    filepath = tmp_path / "p-001_H_001.endf"
    
    # Create minimal valid ENDF photon file
    lines = [
        " 1.001000+3 1.000000+0          0          0          0          0 23  1     \n",
        " 0.000000+0 0.000000+0          0          0          0          0 23  501   \n",
        " 0.000000+0 0.000000+0          0          0          2         10 23  501   \n",
        " 1.000000-2 1.000000+1 1.000000-1 5.000000+0 1.000000+0 2.000000+0 23  501   \n",
        " 1.000000+1 1.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0 23  501   \n",
        " 0.000000+0 0.000000+0          0          0          0          0 23  502   \n",
        " 0.000000+0 0.000000+0          0          0          2         10 23  502   \n",
        " 1.000000-2 2.000000+1 1.000000-1 1.000000+1 1.000000+0 5.000000+0 23  502   \n",
        " 1.000000+1 2.000000+0 0.000000+0 0.000000+0 0.000000+0 0.000000+0 23  502   \n",
        " 0.000000+0 0.000000+0          0          0          0          0 23  516   \n",
        " 0.000000+0 0.000000+0          0          0          2         10 23  516   \n",
        " 1.000000-2 1.000000+0 1.000000-1 5.000000-1 1.000000+0 2.000000-1 23  516   \n",
        " 1.000000+1 1.000000-1 0.000000+0 0.000000+0 0.000000+0 0.000000+0 23  516   \n",
        "                                                                    -1  0  0   \n",
    ]
    
    filepath.write_text("".join(lines))
    return filepath


class TestENDFPhotonParserComprehensive:
    """Comprehensive tests for ENDFPhotonParser."""
    
    def test_parse_file_success(self, mock_photon_file):
        """Test successful file parsing."""
        parser = ENDFPhotonParser()
        photon_data = parser.parse_file(mock_photon_file)
        
        assert photon_data is not None
        assert isinstance(photon_data, PhotonCrossSection)
        assert photon_data.element == "H"
        assert photon_data.Z == 1
        assert len(photon_data.energy) > 0
        assert len(photon_data.sigma_photoelectric) > 0
        assert len(photon_data.sigma_compton) > 0
        assert len(photon_data.sigma_pair) > 0
        assert len(photon_data.sigma_total) > 0
    
    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file."""
        parser = ENDFPhotonParser()
        result = parser.parse_file(Path("nonexistent.endf"))
        
        assert result is None
    
    def test_parse_filename_valid(self):
        """Test parsing valid filename."""
        parser = ENDFPhotonParser()
        
        result = parser._parse_filename("p-001_H_001.endf")
        assert result is not None
        element, Z = result
        assert element == "H"
        assert Z == 1
    
    def test_parse_filename_variations(self):
        """Test parsing various filename formats."""
        parser = ENDFPhotonParser()
        
        # Standard format
        result = parser._parse_filename("p-092_U_235.endf")
        assert result is not None
        element, Z = result
        assert element == "U"
        assert Z == 92
        
        # Without isotope number
        result = parser._parse_filename("p-001_H.endf")
        assert result is not None
        element, Z = result
        assert element == "H"
        assert Z == 1
    
    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        parser = ENDFPhotonParser()
        
        result = parser._parse_filename("invalid_filename.txt")
        assert result is None
        
        result = parser._parse_filename("not_a_photon_file.endf")
        assert result is None
    
    def test_parse_mt_section(self, mock_photon_file):
        """Test parsing MT section."""
        parser = ENDFPhotonParser()
        
        with open(mock_photon_file, "r") as f:
            lines = f.readlines()
        
        # Parse photoelectric section (MT=501)
        result = parser._parse_mt_section(lines, 501)
        
        assert result is not None
        energy, xs = result
        assert len(energy) > 0
        assert len(xs) > 0
        assert len(energy) == len(xs)
    
    def test_parse_mt_section_not_found(self, mock_photon_file):
        """Test parsing non-existent MT section."""
        parser = ENDFPhotonParser()
        
        with open(mock_photon_file, "r") as f:
            lines = f.readlines()
        
        # Try to parse non-existent section
        result = parser._parse_mt_section(lines, 999)
        
        assert result is None
    
    def test_interpolate_to_grid(self):
        """Test interpolating to target energy grid."""
        parser = ENDFPhotonParser()
        
        source_energy = np.array([0.01, 0.1, 1.0, 10.0])
        source_xs = np.array([1.0, 2.0, 3.0, 4.0])
        source_data = (source_energy, source_xs)
        
        target_energy = np.array([0.05, 0.5, 5.0])
        
        interpolated = parser._interpolate_to_grid(target_energy, source_data)
        
        assert len(interpolated) == len(target_energy)
        assert np.all(interpolated >= 0)
    
    def test_interpolate_to_grid_empty(self):
        """Test interpolating empty data."""
        parser = ENDFPhotonParser()
        
        source_data = (np.array([]), np.array([]))
        target_energy = np.array([0.1, 1.0])
        
        interpolated = parser._interpolate_to_grid(target_energy, source_data)
        
        assert len(interpolated) == len(target_energy)
        assert np.all(interpolated == 0)
    
    def test_photon_cross_section_interpolate(self):
        """Test PhotonCrossSection interpolation."""
        energy = np.array([0.01, 0.1, 1.0, 10.0])
        sigma_pe = np.array([1.0, 2.0, 3.0, 4.0])
        sigma_comp = np.array([2.0, 4.0, 6.0, 8.0])
        sigma_pair = np.array([0.1, 0.2, 0.3, 0.4])
        sigma_total = sigma_pe + sigma_comp + sigma_pair
        
        photon_data = PhotonCrossSection(
            element="H",
            Z=1,
            energy=energy,
            sigma_photoelectric=sigma_pe,
            sigma_compton=sigma_comp,
            sigma_pair=sigma_pair,
            sigma_total=sigma_total,
        )
        
        # Interpolate at various energies
        pe, comp, pair, tot = photon_data.interpolate(0.05)
        assert pe > 0
        assert comp > 0
        assert pair > 0
        assert tot > 0
        
        # Below minimum
        pe, comp, pair, tot = photon_data.interpolate(0.001)
        assert pe == sigma_pe[0]
        assert comp == sigma_comp[0]
        
        # Above maximum
        pe, comp, pair, tot = photon_data.interpolate(100.0)
        assert pe == sigma_pe[-1]
        assert comp == sigma_comp[-1]
    
    def test_parse_file_missing_sections(self, tmp_path):
        """Test parsing file with missing sections."""
        parser = ENDFPhotonParser()
        
        # Create file with only header
        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text(" 1.001000+3 1.000000+0          0          0          0          0 23  1     \n")
        
        result = parser.parse_file(filepath)
        
        # Should return None if no data sections
        assert result is None
    
    def test_parse_file_exception_handling(self, tmp_path):
        """Test exception handling during parsing."""
        parser = ENDFPhotonParser()
        
        # Create malformed file
        filepath = tmp_path / "p-001_H_001.endf"
        filepath.write_text("invalid content\n" * 10)
        
        # Should handle exception gracefully
        result = parser.parse_file(filepath)
        
        # Should return None or handle gracefully
        assert result is None or isinstance(result, PhotonCrossSection)

