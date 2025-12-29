"""
Geometry import utilities for reading geometry from various formats.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

from smrforge.geometry.core_geometry import (
    GraphiteBlock,
    MaterialRegion,
    PebbleBedCore,
    Point3D,
    PrismaticCore,
)


class GeometryImporter:
    """Import geometry from various file formats."""

    @staticmethod
    def from_json(filepath: Path) -> Union[PrismaticCore, PebbleBedCore]:
        """
        Import geometry from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            PrismaticCore or PebbleBedCore instance
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        core_type = data.get("type", "PrismaticCore")

        if core_type == "PrismaticCore":
            core = PrismaticCore(name=data.get("name", "Imported-Core"))
            core.core_height = data.get("core_height", 0.0)
            core.core_diameter = data.get("core_diameter", 0.0)

            # Reconstruct blocks
            blocks_data = data.get("blocks", [])
            for block_data in blocks_data:
                position = Point3D(*block_data.get("position", [0, 0, 0]))
                block = GraphiteBlock(
                    id=block_data.get("id", 0),
                    position=position,
                    flat_to_flat=block_data.get("flat_to_flat", 36.0),
                    height=block_data.get("height", 79.3),
                    block_type=block_data.get("type", "fuel"),
                )
                core.blocks.append(block)

            return core

        elif core_type == "PebbleBedCore":
            core = PebbleBedCore(name=data.get("name", "Imported-PebbleBed"))
            core.core_height = data.get("core_height", 0.0)
            core.core_diameter = data.get("core_diameter", 0.0)

            # Note: Full pebble reconstruction would need more data
            # This is a simplified import

            return core

        else:
            raise ValueError(f"Unknown core type: {core_type}")

    @staticmethod
    def from_openmc_xml(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from OpenMC XML geometry file.

        Note: This is a simplified implementation. OpenMC geometries
        are complex and full conversion may require additional work.

        Args:
            filepath: Path to OpenMC geometry.xml file

        Returns:
            PrismaticCore instance (if conversion possible)
        """
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Look for geometry information
            # OpenMC uses a different structure, so this is a placeholder
            # Full implementation would parse OpenMC's CSG format

            # For now, return None to indicate incomplete implementation
            raise NotImplementedError(
                "OpenMC XML import is not fully implemented. "
                "Use JSON export/import as an alternative."
            )

        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")

    @staticmethod
    def from_serpent(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from Serpent input file.

        Note: This is a placeholder. Serpent input format is complex.

        Args:
            filepath: Path to Serpent input file

        Returns:
            PrismaticCore instance (if conversion possible)
        """
        raise NotImplementedError(
            "Serpent import is not implemented. "
            "Use JSON export/import as an alternative."
        )

    @staticmethod
    def validate_imported_geometry(
        core: Union[PrismaticCore, PebbleBedCore]
    ) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate imported geometry for consistency.

        Args:
            core: Imported geometry

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        if isinstance(core, PrismaticCore):
            # Check for overlapping blocks
            for i, block1 in enumerate(core.blocks):
                for block2 in core.blocks[i + 1 :]:
                    dist = block1.position.distance_to(block2.position)
                    min_separation = (block1.flat_to_flat + block2.flat_to_flat) / 2
                    if dist < min_separation * 0.9:  # 10% tolerance
                        warnings.append(
                            f"Blocks {block1.id} and {block2.id} may overlap "
                            f"(distance: {dist:.2f} cm, expected: {min_separation:.2f} cm)"
                        )

            # Check for missing blocks in lattice
            if core.n_rings > 0:
                expected_blocks = sum(6 * ring + 1 for ring in range(core.n_rings + 1))
                if len(core.blocks) < expected_blocks:
                    warnings.append(
                        f"Fewer blocks than expected: {len(core.blocks)} vs {expected_blocks}"
                    )

            # Check dimensions
            if core.core_height <= 0:
                errors.append("Core height must be positive")
            if core.core_diameter <= 0:
                errors.append("Core diameter must be positive")

        elif isinstance(core, PebbleBedCore):
            # Check pebble packing
            if core.packing_fraction < 0.5 or core.packing_fraction > 0.75:
                warnings.append(
                    f"Unusual packing fraction: {core.packing_fraction:.3f} "
                    f"(typical range: 0.55-0.65)"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

