"""Tests for geometry importers module."""

import json
from pathlib import Path

import pytest

from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.geometry.importers import GeometryImporter


class TestGeometryImporter:
    """Test GeometryImporter class."""

    def test_import_from_json_prismatic(self, temp_dir):
        """Test importing prismatic core from JSON."""
        # Create test JSON file
        json_file = temp_dir / "test_core.json"
        json_data = {
            "name": "Test-Core",
            "type": "PrismaticCore",
            "core_height": 793.0,
            "core_diameter": 400.0,
            "blocks": [
                {
                    "id": 0,
                    "position": [0.0, 0.0, 0.0],
                    "type": "fuel",
                    "flat_to_flat": 36.0,
                    "height": 79.3,
                    "n_fuel_channels": 210,
                },
                {
                    "id": 1,
                    "position": [40.0, 0.0, 0.0],
                    "type": "fuel",
                    "flat_to_flat": 36.0,
                    "height": 79.3,
                    "n_fuel_channels": 210,
                },
            ],
        }

        with open(json_file, "w") as f:
            json.dump(json_data, f)

        # Import
        core = GeometryImporter.from_json(json_file)

        assert isinstance(core, PrismaticCore)
        assert core.name == "Test-Core"
        assert core.core_height == 793.0
        assert core.core_diameter == 400.0
        assert len(core.blocks) == 2
        assert core.blocks[0].id == 0
        assert core.blocks[1].id == 1

    def test_import_from_json_pebble_bed(self, temp_dir):
        """Test importing pebble bed core from JSON."""
        json_file = temp_dir / "test_pebble.json"
        json_data = {
            "name": "Test-Pebble",
            "type": "PebbleBedCore",
            "core_height": 1100.0,
            "core_diameter": 300.0,
            "n_pebbles": 1000,
            "packing_fraction": 0.61,
        }

        with open(json_file, "w") as f:
            json.dump(json_data, f)

        # Import
        core = GeometryImporter.from_json(json_file)

        assert core.name == "Test-Pebble"
        assert core.core_height == 1100.0
        assert core.core_diameter == 300.0

    def test_import_from_json_invalid_type(self, temp_dir):
        """Test importing with invalid core type."""
        json_file = temp_dir / "test_invalid.json"
        json_data = {
            "name": "Invalid",
            "type": "UnknownCore",
            "core_height": 100.0,
            "core_diameter": 200.0,
        }

        with open(json_file, "w") as f:
            json.dump(json_data, f)

        with pytest.raises(ValueError, match="Unknown core type"):
            GeometryImporter.from_json(json_file)

    def test_import_from_json_missing_file(self):
        """Test importing from non-existent file."""
        with pytest.raises(FileNotFoundError):
            GeometryImporter.from_json(Path("nonexistent.json"))

    def test_validate_imported_geometry_prismatic(self):
        """Test validation of prismatic core."""
        core = PrismaticCore(name="Test")
        core.core_height = 793.0
        core.core_diameter = 400.0

        # Add blocks that might overlap
        from smrforge.geometry.core_geometry import GraphiteBlock, Point3D

        block1 = GraphiteBlock(
            id=0, position=Point3D(0, 0, 0), flat_to_flat=36.0, height=79.3
        )
        block2 = GraphiteBlock(
            id=1, position=Point3D(40, 0, 0), flat_to_flat=36.0, height=79.3
        )
        core.blocks = [block1, block2]

        validation = GeometryImporter.validate_imported_geometry(core)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_imported_geometry_invalid_dimensions(self):
        """Test validation with invalid dimensions."""
        core = PrismaticCore(name="Test")
        core.core_height = 0.0  # Invalid
        core.core_diameter = -100.0  # Invalid

        validation = GeometryImporter.validate_imported_geometry(core)
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert any("height" in error.lower() for error in validation["errors"])
        assert any("diameter" in error.lower() for error in validation["errors"])

    def test_validate_imported_geometry_overlapping_blocks(self):
        """Test validation detects overlapping blocks."""
        core = PrismaticCore(name="Test")
        core.core_height = 793.0
        core.core_diameter = 400.0

        from smrforge.geometry.core_geometry import GraphiteBlock, Point3D

        # Create overlapping blocks (very close together)
        block1 = GraphiteBlock(
            id=0, position=Point3D(0, 0, 0), flat_to_flat=36.0, height=79.3
        )
        block2 = GraphiteBlock(
            id=1, position=Point3D(1, 0, 0), flat_to_flat=36.0, height=79.3
        )  # Too close!
        core.blocks = [block1, block2]

        validation = GeometryImporter.validate_imported_geometry(core)
        # Should have warnings about potential overlap
        assert len(validation["warnings"]) > 0

    def test_validate_imported_geometry_pebble_bed(self):
        """Test validation of pebble bed core."""
        from smrforge.geometry.core_geometry import PebbleBedCore

        core = PebbleBedCore(name="Test")
        core.core_height = 1100.0
        core.core_diameter = 300.0
        core.packing_fraction = 0.61

        validation = GeometryImporter.validate_imported_geometry(core)
        assert validation["valid"] is True

    def test_validate_imported_geometry_unusual_packing(self):
        """Test validation detects unusual packing fraction."""
        from smrforge.geometry.core_geometry import PebbleBedCore

        core = PebbleBedCore(name="Test")
        core.core_height = 1100.0
        core.core_diameter = 300.0
        core.packing_fraction = 0.90  # Unusually high

        validation = GeometryImporter.validate_imported_geometry(core)
        assert len(validation["warnings"]) > 0
        assert any("packing" in warning.lower() for warning in validation["warnings"])

    def test_from_openmc_xml_basic(self, temp_dir):
        """Test OpenMC XML import with basic geometry."""
        xml_file = temp_dir / "test.xml"
        # Simple OpenMC geometry with z-cylinder
        xml_content = """<?xml version="1.0"?>
<geometry>
    <surface id="1" type="z-cylinder" coeffs="150.0 0.0 0.0"/>
    <surface id="2" type="z-plane" coeffs="-396.5"/>
    <surface id="3" type="z-plane" coeffs="396.5"/>
</geometry>
"""
        xml_file.write_text(xml_content)

        core = GeometryImporter.from_openmc_xml(xml_file)

        assert core is not None
        assert isinstance(core, PrismaticCore)
        assert core.name == "Imported-OpenMC"
        assert core.core_diameter == pytest.approx(300.0, rel=0.01)  # radius * 2
        assert core.core_height == pytest.approx(793.0, rel=0.01)  # z_max - z_min

    def test_from_openmc_xml_no_dimensions(self, temp_dir):
        """Test OpenMC XML import with no extractable dimensions."""
        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<geometry>
    <surface id="1" type="plane" coeffs="1.0 0.0 0.0 0.0"/>
</geometry>
"""
        xml_file.write_text(xml_content)

        with pytest.raises(
            NotImplementedError, match="Could not extract core dimensions"
        ):
            GeometryImporter.from_openmc_xml(xml_file)

    def test_from_openmc_xml_invalid_xml(self, temp_dir):
        """Test OpenMC XML import with invalid XML."""
        xml_file = temp_dir / "test.xml"
        xml_file.write_text("not valid xml <")

        with pytest.raises(ValueError, match="Invalid XML"):
            GeometryImporter.from_openmc_xml(xml_file)

    def test_from_serpent_basic(self, temp_dir):
        """Test Serpent import with basic geometry."""
        serpent_file = temp_dir / "test.inp"
        # Simple Serpent geometry with cz and pz surfaces
        serpent_content = """% Simple HTGR geometry
surf 1 cz 150.0
surf 2 pz -396.5
surf 3 pz 396.5
"""
        serpent_file.write_text(serpent_content)

        core = GeometryImporter.from_serpent(serpent_file)

        assert core is not None
        assert isinstance(core, PrismaticCore)
        assert core.name == "Imported-Serpent"
        assert core.core_diameter == pytest.approx(300.0, rel=0.01)  # radius * 2
        assert core.core_height == pytest.approx(793.0, rel=0.01)  # z_max - z_min

    def test_from_serpent_hexprism(self, temp_dir):
        """Test Serpent import with hexprism surface."""
        serpent_file = temp_dir / "test.inp"
        # Serpent geometry with hexprism
        serpent_content = """% Hexagonal prism geometry
surf 1 hexprism 0.0 0.0 0.0 0.0 0.0 1.0 793.0 75.0
"""
        serpent_file.write_text(serpent_content)

        core = GeometryImporter.from_serpent(serpent_file)

        assert core is not None
        assert isinstance(core, PrismaticCore)
        assert core.core_height == pytest.approx(793.0, rel=0.01)
        # hexprism apothem 75.0 gives approximate radius 150.0
        assert core.core_diameter > 0

    def test_from_serpent_no_dimensions(self, temp_dir):
        """Test Serpent import with no extractable dimensions."""
        serpent_file = temp_dir / "test.inp"
        serpent_content = """% No useful surfaces
surf 1 px 0.0
"""
        serpent_file.write_text(serpent_content)

        with pytest.raises(
            NotImplementedError, match="Could not extract core dimensions"
        ):
            GeometryImporter.from_serpent(serpent_file)

    def test_from_serpent_file_not_found(self):
        """Test Serpent import with non-existent file."""
        with pytest.raises(FileNotFoundError):
            GeometryImporter.from_serpent(Path("nonexistent.inp"))
