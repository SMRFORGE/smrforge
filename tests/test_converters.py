"""
Tests for I/O converters (Serpent and OpenMC).

Tests cover:
- Placeholder export/import methods
- Error handling for unimplemented features
- File format validation
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from smrforge.io.converters import (
    SerpentConverter,
    OpenMCConverter
)


class TestSerpentConverter:
    """Tests for SerpentConverter class."""
    
    def test_export_reactor_creates_file(self, tmp_path):
        """Test that export creates a file."""
        mock_reactor = Mock()
        output_file = tmp_path / "reactor.serp"
        
        SerpentConverter.export_reactor(mock_reactor, output_file)
        
        assert output_file.exists()
        
        # Check file contents (Community: upgrade message or "would go here"; Pro: SMRForge Pro)
        with open(output_file) as f:
            content = f.read()
        assert "Serpent" in content
        assert (
            "placeholder" in content.lower()
            or "smrforge pro" in content.lower()
            or "upgrade to pro" in content.lower()
            or "would go here" in content.lower()
        )
    
    def test_export_reactor_content(self, tmp_path):
        """Test export file content structure."""
        mock_reactor = Mock()
        output_file = tmp_path / "reactor.serp"
        
        SerpentConverter.export_reactor(mock_reactor, output_file)
        
        with open(output_file) as f:
            lines = f.readlines()
        
        # Should have comment header
        assert any("%" in line for line in lines)
        assert any("SMRForge" in line for line in lines)
    
    def test_import_reactor_raises_not_implemented(self, tmp_path):
        """Test that import raises NotImplementedError (Community) or Pro stub (Pro)."""
        input_file = tmp_path / "x.serp"
        input_file.write_text("")
        with pytest.raises(NotImplementedError, match="Serpent"):
            SerpentConverter.import_reactor(input_file)


class TestOpenMCConverter:
    """Tests for OpenMCConverter class."""
    
    def test_export_reactor_creates_directory(self, tmp_path):
        """Test that export creates output directory."""
        mock_reactor = Mock()
        output_dir = tmp_path / "openmc_output"
        
        OpenMCConverter.export_reactor(mock_reactor, output_dir)
        
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_export_reactor_creates_geometry_xml(self, tmp_path):
        """Test that export creates geometry.xml file."""
        mock_reactor = Mock()
        output_dir = tmp_path / "openmc_output"
        
        OpenMCConverter.export_reactor(mock_reactor, output_dir)
        
        geometry_file = output_dir / "geometry.xml"
        assert geometry_file.exists()
        
        with open(geometry_file) as f:
            content = f.read()
        assert "<?xml" in content
        assert "geometry" in content.lower()
        assert "SMRForge" in content
    
    def test_export_reactor_creates_materials_xml(self, tmp_path):
        """Test that export creates materials.xml file."""
        mock_reactor = Mock()
        output_dir = tmp_path / "openmc_output"
        
        OpenMCConverter.export_reactor(mock_reactor, output_dir)
        
        materials_file = output_dir / "materials.xml"
        assert materials_file.exists()
        
        with open(materials_file) as f:
            content = f.read()
        assert "<?xml" in content
        assert "materials" in content.lower()
        assert "SMRForge" in content
    
    def test_export_reactor_xml_structure(self, tmp_path):
        """Test XML file structure."""
        mock_reactor = Mock()
        output_dir = tmp_path / "openmc_output"
        
        OpenMCConverter.export_reactor(mock_reactor, output_dir)
        
        geometry_file = output_dir / "geometry.xml"
        with open(geometry_file) as f:
            content = f.read()
        
        # Should be valid XML structure
        assert content.strip().startswith('<?xml')
        assert '<geometry>' in content or '</geometry>' in content
    
    def test_import_reactor_raises_not_implemented(self, tmp_path):
        """Test that import raises NotImplementedError."""
        geometry_file = tmp_path / "geometry.xml"
        geometry_file.write_text('<?xml version="1.0"?><geometry></geometry>')
        
        with pytest.raises(NotImplementedError, match="OpenMC"):
            OpenMCConverter.import_reactor(geometry_file)
    
    def test_import_reactor_with_materials_file(self, tmp_path):
        """Test that import accepts optional materials file parameter."""
        geometry_file = tmp_path / "geometry.xml"
        materials_file = tmp_path / "materials.xml"
        geometry_file.write_text('<?xml version="1.0"?><geometry></geometry>')
        materials_file.write_text('<?xml version="1.0"?><materials></materials>')
        
        with pytest.raises(NotImplementedError, match="OpenMC"):
            OpenMCConverter.import_reactor(geometry_file, materials_file)
