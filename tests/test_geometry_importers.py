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

    def test_from_openmc_xml_not_implemented(self, temp_dir):
        """Test that OpenMC XML import raises NotImplementedError."""
        xml_file = temp_dir / "test.xml"
        xml_file.write_text("<geometry></geometry>")

        with pytest.raises(NotImplementedError):
            GeometryImporter.from_openmc_xml(xml_file)

    def test_from_serpent_not_implemented(self, temp_dir):
        """Test that Serpent import raises NotImplementedError."""
        serpent_file = temp_dir / "test.inp"
        serpent_file.write_text("surf 1 pz 0")

        with pytest.raises(NotImplementedError):
            GeometryImporter.from_serpent(serpent_file)

