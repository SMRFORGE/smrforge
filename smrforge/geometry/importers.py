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
    """
    Import geometry from various file formats.

    This class provides static methods to import reactor geometries from
    different file formats including JSON, OpenMC XML, and Serpent input files.

    Examples:
        Import from JSON::

            from pathlib import Path
            from smrforge.geometry.importers import GeometryImporter

            core = GeometryImporter.from_json(Path("geometry.json"))
            print(f"Imported core: {core.name}")
            print(f"Blocks: {len(core.blocks)}")

        Import from OpenMC XML::

            core = GeometryImporter.from_openmc_xml(Path("geometry.xml"))
            print(f"Core diameter: {core.core_diameter} cm")

        Import from Serpent input::

            core = GeometryImporter.from_serpent(Path("geometry.inp"))
            print(f"Core height: {core.core_height} cm")

        Validate imported geometry::

            validation = GeometryImporter.validate_imported_geometry(core)
            if validation["valid"]:
                print("Geometry is valid!")
            else:
                print(f"Errors: {validation['errors']}")
    """

    @staticmethod
    def from_json(filepath: Path) -> Union[PrismaticCore, PebbleBedCore]:
        """
        Import geometry from JSON file.

        This method imports reactor geometry from a JSON file that was
        previously exported using ``GeometryExporter.to_json()``. The JSON
        format supports both PrismaticCore and PebbleBedCore geometries.

        Args:
            filepath: Path to JSON file containing geometry data

        Returns:
            PrismaticCore or PebbleBedCore instance with imported geometry

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the JSON format is invalid or core type is unknown

        Example:
            >>> from pathlib import Path
            >>> from smrforge.geometry.importers import GeometryImporter
            >>>
            >>> # Import a previously exported geometry
            >>> core = GeometryImporter.from_json(Path("my_reactor.json"))
            >>> print(f"Imported: {core.name}")
            >>> print(f"Blocks: {len(core.blocks)}")
            >>> print(f"Height: {core.core_height} cm")
            >>>
            >>> # Validate the imported geometry
            >>> validation = GeometryImporter.validate_imported_geometry(core)
            >>> if not validation["valid"]:
            ...     print("Warning: Geometry validation failed")
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

        This implementation handles simple prismatic HTGR geometries with:
        - Cylindrical cores (z-cylinder surfaces)
        - Finite cylinders (z-cylinder with z-plane boundaries)
        - Basic dimension extraction from surface definitions

        The method extracts core dimensions (radius, height) from OpenMC
        surface definitions and creates a simplified PrismaticCore representation.
        Full CSG parsing and lattice reconstruction are not yet implemented.

        Args:
            filepath: Path to OpenMC geometry.xml file

        Returns:
            PrismaticCore instance with extracted dimensions. The geometry
            will be simplified (single center block) rather than full lattice.

        Raises:
            ValueError: If XML is invalid or geometry cannot be converted
            NotImplementedError: If geometry is too complex (no extractable dimensions)

        Note:
            Full OpenMC CSG format conversion is complex. This implementation
            handles common HTGR geometries with simple cylindrical surfaces.
            For complex geometries, use JSON export/import as an alternative.

        Example:
            OpenMC XML format (simplified)::

                <?xml version="1.0"?>
                <geometry>
                    <surface id="1" type="z-cylinder" coeffs="150.0 0.0 0.0"/>
                    <surface id="2" type="z-plane" coeffs="-396.5"/>
                    <surface id="3" type="z-plane" coeffs="396.5"/>
                </geometry>

            Usage::

                >>> from pathlib import Path
                >>> from smrforge.geometry.importers import GeometryImporter
                >>>
                >>> # Import from OpenMC geometry file
                >>> core = GeometryImporter.from_openmc_xml(Path("geometry.xml"))
                >>> print(f"Core diameter: {core.core_diameter} cm")
                >>> print(f"Core height: {core.core_height} cm")
        """
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # OpenMC XML structure: <geometry> contains <cell> elements
            # Cells reference <surface> elements
            # We need to extract dimensions from surfaces

            # Find all surfaces to extract dimensions
            surfaces = {}
            for surface in root.findall(".//surface"):
                surf_id = surface.get("id")
                surf_type = surface.get("type")
                if surf_id and surf_type:
                    surfaces[int(surf_id)] = {"type": surf_type, "element": surface}

            # Try to extract core dimensions
            # Look for cylindrical surfaces (infinite cylinder or z-cylinder)
            core_radius = None
            core_height = None
            lattice_pitch = None

            for surf_id, surf_data in surfaces.items():
                surf_type = surf_data["type"]
                surf_elem = surf_data["element"]

                # Infinite cylinder: <surface id="1" type="z-cylinder" coeffs="r x0 y0"/>
                if surf_type in ["z-cylinder", "zcylinder"]:
                    coeffs_str = surf_elem.get("coeffs", "")
                    try:
                        coeffs = [float(x) for x in coeffs_str.split()]
                        if len(coeffs) >= 1:
                            radius = abs(coeffs[0])
                            if core_radius is None or radius > core_radius:
                                core_radius = radius
                    except (ValueError, IndexError):
                        pass

                # Finite cylinder (cylinder with z-planes): check for z-planes
                elif surf_type in ["z-plane", "zplane", "plane"]:
                    coeffs_str = surf_elem.get("coeffs", "")
                    try:
                        coeffs = [float(x) for x in coeffs_str.split()]
                        if len(coeffs) >= 1:
                            z_pos = coeffs[0]
                            if core_height is None:
                                core_height = abs(z_pos) * 2  # Assume symmetric
                            else:
                                # Update height based on min/max z
                                height_candidate = abs(z_pos) * 2
                                if height_candidate > core_height:
                                    core_height = height_candidate
                    except (ValueError, IndexError):
                        pass

            # If we couldn't extract dimensions, try to find cells that might give hints
            if core_radius is None or core_height is None:
                # Look for cell regions that might indicate dimensions
                cells = root.findall(".//cell")
                for cell in cells:
                    region = cell.get("region")
                    # Region strings like "-1 -2 3" reference surfaces
                    # For now, we can't fully parse CSG, but we can try basic cases
                    pass

            # If we have at least a radius, create a basic core
            if core_radius is None:
                raise NotImplementedError(
                    "Could not extract core dimensions from OpenMC geometry. "
                    "Complex CSG geometries are not fully supported. "
                    "Use JSON export/import as an alternative."
                )

            # Create prismatic core with extracted dimensions
            core = PrismaticCore(name="Imported-OpenMC")
            core.core_diameter = (core_radius * 2) if core_radius else 400.0
            core.core_height = core_height if core_height else 793.0

            # For now, create a simplified single-block representation
            # Full lattice reconstruction would require parsing cell regions
            # This is a basic implementation that can be extended
            from smrforge.geometry.core_geometry import GraphiteBlock, Point3D

            # Create a center block as a placeholder
            # In a full implementation, we would parse cells and regions
            # to reconstruct the full hexagonal lattice
            block = GraphiteBlock(
                id=0,
                position=Point3D(0, 0, core.core_height / 2),
                flat_to_flat=36.0,  # Default
                height=core.core_height,
                block_type="fuel",
            )
            core.blocks.append(block)

            return core

        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}") from e
        except NotImplementedError:
            # Re-raise NotImplementedError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Error parsing OpenMC geometry: {e}. "
                f"For complex geometries, use JSON export/import."
            ) from e

    @staticmethod
    def from_serpent(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from Serpent input file.

        This implementation handles simple prismatic HTGR geometries with:
        - Cylindrical cores (cz surfaces)
        - Finite cylinders (cz with pz boundaries)
        - Hexagonal prisms (hexprism surfaces)
        - Basic dimension extraction from surface definitions

        The method parses Serpent surface definitions and extracts core dimensions
        (radius, height) to create a simplified PrismaticCore representation.
        Full cell parsing and lattice reconstruction are not yet implemented.

        Args:
            filepath: Path to Serpent input file

        Returns:
            PrismaticCore instance with extracted dimensions. The geometry
            will be simplified (single center block) rather than full lattice.

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If file format is invalid or geometry cannot be converted
            NotImplementedError: If geometry is too complex (no extractable dimensions)

        Note:
            Serpent input format is complex and parser-dependent. This implementation
            handles common HTGR geometries with simple surface definitions.
            For complex geometries, use JSON export/import as an alternative.

        Example:
            Serpent input format (simplified)::

                % Simple HTGR geometry
                surf 1 cz 150.0
                surf 2 pz -396.5
                surf 3 pz 396.5

            Usage::

                >>> from pathlib import Path
                >>> from smrforge.geometry.importers import GeometryImporter
                >>>
                >>> # Import from Serpent input file
                >>> core = GeometryImporter.from_serpent(Path("geometry.inp"))
                >>> print(f"Core diameter: {core.core_diameter} cm")
                >>> print(f"Core height: {core.core_height} cm")

            Hexagonal prism example::

                % Hexagonal prism geometry
                surf 1 hexprism 0.0 0.0 0.0 0.0 0.0 1.0 793.0 75.0
                >>> core = GeometryImporter.from_serpent(Path("hex_geometry.inp"))
        """
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            # Serpent format uses surface definitions like:
            # surf <id> <type> <params>
            # Examples:
            # surf 1 pz 0          # z-plane at z=0
            # surf 2 cz 150        # z-cylinder with radius 150
            # surf 3 hexprism ...  # hexagonal prism

            surfaces = {}
            core_radius = None
            core_height = None
            z_min = None
            z_max = None

            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("%"):
                    continue

                parts = line.split()
                if len(parts) < 3:
                    continue

                # Check for surface definition
                if parts[0].lower() == "surf":
                    try:
                        surf_id = int(parts[1])
                        surf_type = parts[2].lower()
                        surf_params = parts[3:] if len(parts) > 3 else []

                        surfaces[surf_id] = {"type": surf_type, "params": surf_params}

                        # Extract dimensions based on surface type
                        if surf_type == "cz":  # z-cylinder
                            if len(surf_params) >= 1:
                                try:
                                    radius = abs(float(surf_params[0]))
                                    if core_radius is None or radius > core_radius:
                                        core_radius = radius
                                except (ValueError, IndexError):
                                    pass

                        elif surf_type == "pz":  # z-plane
                            if len(surf_params) >= 1:
                                try:
                                    z_pos = float(surf_params[0])
                                    if z_min is None or z_pos < z_min:
                                        z_min = z_pos
                                    if z_max is None or z_pos > z_max:
                                        z_max = z_pos
                                except (ValueError, IndexError):
                                    pass

                        elif surf_type == "hexprism":  # hexagonal prism
                            # Hexprism format: hexprism <x0> <y0> <z0> <x1> <y1> <z1> <height> <apothem>
                            if len(surf_params) >= 8:
                                try:
                                    # Extract apothem (flat-to-flat distance / 2)
                                    apothem = abs(float(surf_params[7]))
                                    radius_candidate = apothem * 2  # Approximate
                                    if (
                                        core_radius is None
                                        or radius_candidate > core_radius
                                    ):
                                        core_radius = radius_candidate
                                    # Extract height if available
                                    height = abs(float(surf_params[6]))
                                    if core_height is None or height > core_height:
                                        core_height = height
                                except (ValueError, IndexError):
                                    pass

                    except (ValueError, IndexError):
                        continue

            # Calculate core height from z-planes if available
            if z_min is not None and z_max is not None:
                height_from_planes = abs(z_max - z_min)
                if core_height is None:
                    core_height = height_from_planes
                else:
                    # Use the larger value
                    core_height = max(core_height, height_from_planes)

            # If we couldn't extract dimensions, raise error
            if core_radius is None:
                raise NotImplementedError(
                    "Could not extract core dimensions from Serpent geometry. "
                    "Complex geometries are not fully supported. "
                    "Use JSON export/import as an alternative."
                )

            # Create prismatic core with extracted dimensions
            core = PrismaticCore(name="Imported-Serpent")
            core.core_diameter = core_radius * 2
            core.core_height = core_height if core_height else 793.0

            # For now, create a simplified single-block representation
            # Full lattice reconstruction would require parsing cell definitions
            # This is a basic implementation that can be extended
            from smrforge.geometry.core_geometry import GraphiteBlock, Point3D

            # Create a center block as a placeholder
            # In a full implementation, we would parse cell definitions
            # to reconstruct the full hexagonal lattice
            block = GraphiteBlock(
                id=0,
                position=Point3D(0, 0, core.core_height / 2),
                flat_to_flat=36.0,  # Default
                height=core.core_height,
                block_type="fuel",
            )
            core.blocks.append(block)

            return core

        except FileNotFoundError:
            raise
        except Exception as e:
            if isinstance(e, NotImplementedError):
                raise
            raise ValueError(
                f"Error parsing Serpent geometry: {e}. "
                f"For complex geometries, use JSON export/import."
            ) from e

    @staticmethod
    def validate_imported_geometry(
        core: Union[PrismaticCore, PebbleBedCore],
    ) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate imported geometry for consistency.

        This method performs basic validation checks on imported geometries,
        including dimension checks, overlap detection, and physical consistency.

        Args:
            core: Imported PrismaticCore or PebbleBedCore geometry to validate

        Returns:
            Dictionary with validation results containing:
                - ``valid`` (bool): True if geometry passes all checks
                - ``errors`` (List[str]): List of error messages (if any)
                - ``warnings`` (List[str]): List of warning messages (if any)

        Example:
            >>> from smrforge.geometry.importers import GeometryImporter
            >>>
            >>> # Import geometry
            >>> core = GeometryImporter.from_json(Path("geometry.json"))
            >>>
            >>> # Validate
            >>> result = GeometryImporter.validate_imported_geometry(core)
            >>>
            >>> if result["valid"]:
            ...     print("Geometry is valid!")
            ... else:
            ...     print("Errors found:")
            ...     for error in result["errors"]:
            ...         print(f"  - {error}")
            ...
            >>> if result["warnings"]:
            ...     print("Warnings:")
            ...     for warning in result["warnings"]:
            ...         print(f"  - {warning}")
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
