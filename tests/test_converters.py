"""
Tests for I/O converters (Serpent and OpenMC).

Tests cover:
- Placeholder export/import methods (Serpent)
- Full OpenMC export/import implementation
- Error handling for unimplemented features
- File format validation
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.io.converters import OpenMCConverter, SerpentConverter


def _prismatic_reactor():
    """Create a minimal PrismaticCore for OpenMC export tests."""
    core = PrismaticCore(name="TestCore")
    core.build_hexagonal_lattice(n_rings=1, pitch=40.0, block_height=50.0, n_axial=2)
    return core


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
        reactor = _prismatic_reactor()
        output_dir = tmp_path / "openmc_output"

        OpenMCConverter.export_reactor(reactor, output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_export_reactor_creates_geometry_xml(self, tmp_path):
        """Test that export creates geometry.xml file."""
        reactor = _prismatic_reactor()
        output_dir = tmp_path / "openmc_output"

        OpenMCConverter.export_reactor(reactor, output_dir)

        geometry_file = output_dir / "geometry.xml"
        assert geometry_file.exists()

        with open(geometry_file) as f:
            content = f.read()
        assert "<?xml" in content
        assert "geometry" in content.lower()
        assert "SMRForge" in content or "PrismaticCore" in content

    def test_export_reactor_creates_materials_xml(self, tmp_path):
        """Test that export creates materials.xml file."""
        reactor = _prismatic_reactor()
        output_dir = tmp_path / "openmc_output"

        OpenMCConverter.export_reactor(reactor, output_dir)

        materials_file = output_dir / "materials.xml"
        assert materials_file.exists()

        with open(materials_file) as f:
            content = f.read()
        assert "<?xml" in content
        assert "materials" in content.lower()
        assert "nuclide" in content.lower()

    def test_export_reactor_xml_structure(self, tmp_path):
        """Test XML file structure."""
        reactor = _prismatic_reactor()
        output_dir = tmp_path / "openmc_output"

        OpenMCConverter.export_reactor(reactor, output_dir)

        geometry_file = output_dir / "geometry.xml"
        with open(geometry_file) as f:
            content = f.read()

        assert content.strip().startswith("<?xml")
        assert "<geometry>" in content or "</geometry>" in content

    def test_export_reactor_creates_settings_xml(self, tmp_path):
        """Test that export creates settings.xml file."""
        reactor = _prismatic_reactor()
        output_dir = tmp_path / "openmc_output"

        OpenMCConverter.export_reactor(reactor, output_dir)

        settings_file = output_dir / "settings.xml"
        assert settings_file.exists()
        with open(settings_file) as f:
            content = f.read()
        assert "particles" in content
        assert "eigenvalue" in content.lower()

    def test_import_reactor_parses_geometry(self, tmp_path):
        """Test that import parses OpenMC geometry."""
        geometry_file = tmp_path / "geometry.xml"
        geometry_file.write_text(
            '<?xml version="1.0"?><geometry>'
            '<surface id="1" type="z-plane" coeffs="0" boundary="vacuum"/>'
            '<surface id="2" type="z-plane" coeffs="200" boundary="vacuum"/>'
            '<surface id="3" type="z-cylinder" coeffs="0 0 50" boundary="vacuum"/>'
            '<cell id="1" material="1" region="-1 2 -3"/>'
            '<cell id="2" material="void" region="1 | -2 | 3"/>'
            "</geometry>"
        )

        result = OpenMCConverter.import_reactor(geometry_file)

        assert "core" in result
        assert result["format"] == "openmc"
        assert result["source"] == str(geometry_file)

    def test_import_reactor_with_materials_file(self, tmp_path):
        """Test that import accepts optional materials file parameter."""
        geometry_file = tmp_path / "geometry.xml"
        materials_file = tmp_path / "materials.xml"
        geometry_file.write_text(
            '<?xml version="1.0"?><geometry>'
            '<surface id="1" type="z-plane" coeffs="0"/>'
            '<surface id="2" type="z-plane" coeffs="200"/>'
            '<surface id="3" type="z-cylinder" coeffs="0 0 50"/>'
            '<cell id="1" material="1" region="-1 2 -3"/>'
            '<cell id="2" material="void" region="1 | -2 | 3"/>'
            "</geometry>"
        )
        materials_file.write_text(
            '<?xml version="1.0"?><materials>'
            '<material id="1" name="fuel"><density value="sum" units="atom/b-cm"/>'
            '<nuclide name="U235" ao="4.5e-5"/><nuclide name="U238" ao="2.2e-4"/>'
            "</material></materials>"
        )

        result = OpenMCConverter.import_reactor(geometry_file, materials_file)

        assert "core" in result
        assert "materials" in result
        assert 1 in result["materials"]

    def test_export_reactor_no_core_raises(self, tmp_path):
        """Test that export raises when reactor has no core."""

        class NoCoreReactor:
            core = None
            _core = None

        with pytest.raises(ValueError, match="no core"):
            OpenMCConverter.export_reactor(NoCoreReactor(), tmp_path / "out")
