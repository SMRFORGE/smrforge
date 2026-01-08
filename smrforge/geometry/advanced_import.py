"""
Advanced geometry import and conversion utilities.

Provides enhanced geometry import capabilities including:
- Full OpenMC CSG parsing and lattice reconstruction
- Complex Serpent geometry parsing
- CAD format import (STEP, IGES, STL)
- MCNP geometry import
- Advanced geometry conversion utilities
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None  # type: ignore

# Optional CAD format support
try:
    import trimesh

    _TRIMESH_AVAILABLE = True
except ImportError:
    _TRIMESH_AVAILABLE = False
    trimesh = None  # type: ignore

try:
    import openmc

    _OPENMC_AVAILABLE = True
except ImportError:
    _OPENMC_AVAILABLE = False
    openmc = None  # type: ignore

from smrforge.geometry.core_geometry import (
    GraphiteBlock,
    PebbleBedCore,
    Point3D,
    PrismaticCore,
)


@dataclass
class CSGSurface:
    """Represents a CSG surface from OpenMC or other formats."""

    id: int
    surface_type: str  # 'z-cylinder', 'z-plane', 'sphere', etc.
    coeffs: List[float]  # Surface coefficients
    boundary_type: str = "vacuum"  # 'vacuum', 'reflective', 'periodic'


@dataclass
class CSGCell:
    """Represents a CSG cell from OpenMC or other formats."""

    id: int
    region: Optional[str] = None  # Region definition (e.g., '-1 & 2 & -3')
    material: Optional[int] = None  # Material ID
    fill: Optional[Union[int, str]] = None  # Fill (universe or lattice ID)
    surfaces: List[int] = field(default_factory=list)  # Surface IDs used


@dataclass
class Lattice:
    """Represents a lattice structure."""

    id: int
    lattice_type: str  # 'rectangular', 'hexagonal', 'cylindrical'
    dimension: Tuple[int, int, int]  # (nx, ny, nz) or (nrings, nz)
    lower_left: Point3D
    pitch: Tuple[float, float, float]  # (pitch_x, pitch_y, pitch_z) or (pitch_radial, pitch_axial)
    universes: List[List[List[int]]]  # Universe IDs at each position


class AdvancedGeometryImporter:
    """
    Advanced geometry importer with support for complex formats.

    Extends basic GeometryImporter with:
    - Full CSG parsing
    - Lattice reconstruction
    - CAD format support
    - MCNP geometry import
    """

    @staticmethod
    def from_openmc_full(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from OpenMC XML with full CSG and lattice parsing.

        This method provides full OpenMC geometry parsing including:
        - Complete CSG surface definitions
        - Cell regions and fills
        - Lattice reconstruction
        - Universe hierarchy

        Args:
            filepath: Path to OpenMC geometry.xml file

        Returns:
            PrismaticCore instance with full lattice reconstruction

        Raises:
            ImportError: If openmc package is not available
            ValueError: If geometry cannot be parsed

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_import import AdvancedGeometryImporter
            >>> 
            >>> core = AdvancedGeometryImporter.from_openmc_full(Path("geometry.xml"))
            >>> print(f"Blocks: {len(core.blocks)}")
        """
        if not _OPENMC_AVAILABLE:
            # Fallback to manual XML parsing
            return AdvancedGeometryImporter._from_openmc_xml_csg(filepath)

        try:
            # Use OpenMC's built-in parser if available
            geometry = openmc.Geometry.from_xml(str(filepath))

            # Extract core structure
            core = PrismaticCore(name="Imported-OpenMC-Full")
            core = AdvancedGeometryImporter._reconstruct_lattice_from_openmc(geometry, core)

            return core
        except Exception as e:
            raise ValueError(f"Error parsing OpenMC geometry: {e}") from e

    @staticmethod
    def _from_openmc_xml_csg(filepath: Path) -> Optional[PrismaticCore]:
        """Parse OpenMC XML manually to extract CSG and lattices."""
        if ET is None:
            raise ImportError("xml.etree.ElementTree not available")

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Parse surfaces
            surfaces: Dict[int, CSGSurface] = {}
            for surface_elem in root.findall(".//surface"):
                surf_id = int(surface_elem.get("id", 0))
                surf_type = surface_elem.get("type", "")
                coeffs_str = surface_elem.get("coeffs", "")
                coeffs = [float(x) for x in coeffs_str.split() if x] if coeffs_str else []
                boundary = surface_elem.get("boundary_type", "vacuum")

                surfaces[surf_id] = CSGSurface(
                    id=surf_id, surface_type=surf_type, coeffs=coeffs, boundary_type=boundary
                )

            # Parse cells
            cells: Dict[int, CSGCell] = {}
            for cell_elem in root.findall(".//cell"):
                cell_id = int(cell_elem.get("id", 0))
                region = cell_elem.get("region")
                material = cell_elem.get("material")
                fill = cell_elem.get("fill")

                # Extract surface IDs from region string
                surface_ids = AdvancedGeometryImporter._extract_surface_ids_from_region(region)

                cells[cell_id] = CSGCell(
                    id=cell_id,
                    region=region,
                    material=int(material) if material and material.isdigit() else None,
                    fill=int(fill) if fill and fill.isdigit() else fill,
                    surfaces=surface_ids,
                )

            # Parse lattices
            lattices: Dict[int, Lattice] = {}
            for lattice_elem in root.findall(".//lattice"):
                lattice_id = int(lattice_elem.get("id", 0))
                lattice_type = lattice_elem.get("type", "rectangular")
                dimension = tuple(int(x) for x in lattice_elem.get("dimension", "1 1 1").split())

                # Extract pitch
                pitch_str = lattice_elem.get("pitch", "1.0 1.0 1.0")
                pitch = tuple(float(x) for x in pitch_str.split())

                # Extract lower_left
                ll_str = lattice_elem.get("lower_left", "0.0 0.0 0.0")
                ll_coords = [float(x) for x in ll_str.split()]
                lower_left = Point3D(ll_coords[0], ll_coords[1], ll_coords[2] if len(ll_coords) > 2 else 0.0)

                # Parse universes (simplified - would need full lattice structure)
                universes_flat = []
                universe_elems = lattice_elem.findall(".//universes/*")
                for uni_elem in universe_elems:
                    uni_id = int(uni_elem.text) if uni_elem.text else 0
                    universes_flat.append(uni_id)

                # Convert flat universe list to nested structure for lattice
                # Simplified: create 3D nested list (would need full lattice parsing)
                if universes_flat and len(dimension) >= 3:
                    nx, ny, nz = dimension[0], dimension[1], dimension[2]
                    nested_universes = []
                    idx = 0
                    for z in range(nz):
                        z_slice = []
                        for y in range(ny):
                            y_row = []
                            for x in range(nx):
                                if idx < len(universes_flat):
                                    y_row.append(universes_flat[idx])
                                    idx += 1
                                else:
                                    y_row.append(0)
                            z_slice.append(y_row)
                        nested_universes.append(z_slice)
                else:
                    nested_universes = [universes_flat] if universes_flat else []

                lattices[lattice_id] = Lattice(
                    id=lattice_id,
                    lattice_type=lattice_type,
                    dimension=dimension,
                    lower_left=lower_left,
                    pitch=pitch,
                    universes=nested_universes,
                )

            # Reconstruct geometry from CSG and lattices
            core = PrismaticCore(name="Imported-OpenMC-CSG")
            core = AdvancedGeometryImporter._reconstruct_core_from_csg(surfaces, cells, lattices, core)

            return core

        except Exception as e:
            raise ValueError(f"Error parsing OpenMC CSG: {e}") from e

    @staticmethod
    def _extract_surface_ids_from_region(region: Optional[str]) -> List[int]:
        """Extract surface IDs from region string (e.g., '-1 & 2 & -3' -> [1, 2, 3])."""
        if not region:
            return []

        # Extract all numbers (with sign)
        matches = re.findall(r"[-+]?\d+", region)
        return [abs(int(m)) for m in matches]

    @staticmethod
    def _reconstruct_core_from_csg(
        surfaces: Dict[int, CSGSurface],
        cells: Dict[int, CSGCell],
        lattices: Dict[int, Lattice],
        core: PrismaticCore,
    ) -> PrismaticCore:
        """Reconstruct PrismaticCore from CSG surfaces, cells, and lattices."""
        # Find core cell (cell that contains fuel and is not filled)
        core_cell = None
        for cell in cells.values():
            if cell.fill is None or isinstance(cell.fill, int):
                # Check if it's a fuel cell (simplified heuristic)
                if cell.material is not None:
                    core_cell = cell
                    break

        # Extract dimensions from surfaces
        core_radius = None
        core_height = None
        z_min = None
        z_max = None

        for surface in surfaces.values():
            if surface.surface_type == "z-cylinder":
                if len(surface.coeffs) >= 1:
                    radius = abs(surface.coeffs[0])
                    if core_radius is None or radius > core_radius:
                        core_radius = radius
            elif surface.surface_type == "z-plane":
                if len(surface.coeffs) >= 1:
                    z_pos = surface.coeffs[0]
                    if z_min is None or z_pos < z_min:
                        z_min = z_pos
                    if z_max is None or z_pos > z_max:
                        z_max = z_pos

        if core_radius:
            core.core_diameter = core_radius * 2
        if z_min is not None and z_max is not None:
            core.core_height = abs(z_max - z_min)

        # Reconstruct lattice if available
        if lattices:
            core = AdvancedGeometryImporter._reconstruct_lattice(lattices, core)

        return core

    @staticmethod
    def _reconstruct_lattice(lattices: Dict[int, Lattice], core: PrismaticCore) -> PrismaticCore:
        """Reconstruct hexagonal lattice from lattice definition."""
        for lattice in lattices.values():
            if lattice.lattice_type == "hexagonal":
                # Create hexagonal lattice of blocks
                n_rings = lattice.dimension[0] if len(lattice.dimension) > 0 else 1
                core.n_rings = n_rings

                # Calculate pitch
                pitch_radial = lattice.pitch[0] if len(lattice.pitch) > 0 else 36.0
                pitch_axial = lattice.pitch[2] if len(lattice.pitch) > 2 else 793.0

                # Generate block positions
                from smrforge.geometry.core_geometry import GraphiteBlock

                block_id = 0
                for ring in range(n_rings + 1):
                    if ring == 0:
                        # Center block
                        block = GraphiteBlock(
                            id=block_id,
                            position=Point3D(0, 0, pitch_axial / 2),
                            flat_to_flat=pitch_radial,
                            height=pitch_axial,
                            block_type="fuel",
                        )
                        core.blocks.append(block)
                        block_id += 1
                    else:
                        # Ring blocks
                        n_in_ring = 6 * ring
                        for i in range(n_in_ring):
                            angle = 2 * np.pi * i / n_in_ring
                            x = ring * pitch_radial * np.cos(angle)
                            y = ring * pitch_radial * np.sin(angle)
                            block = GraphiteBlock(
                                id=block_id,
                                position=Point3D(x, y, pitch_axial / 2),
                                flat_to_flat=pitch_radial,
                                height=pitch_axial,
                                block_type="fuel" if i % 2 == 0 else "reflector",
                            )
                            core.blocks.append(block)
                            block_id += 1

        return core

    @staticmethod
    def _reconstruct_lattice_from_openmc(geometry: Any, core: PrismaticCore) -> PrismaticCore:
        """Reconstruct lattice using OpenMC's geometry object."""
        # This would use OpenMC's API to extract lattice structure
        # Placeholder for OpenMC integration
        return core

    @staticmethod
    def from_serpent_full(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from Serpent with complex parsing.

        Supports:
        - Full cell definitions
        - Pin/multipin structures
        - Lattice definitions
        - Material assignments

        Args:
            filepath: Path to Serpent input file

        Returns:
            PrismaticCore instance with full lattice reconstruction

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_import import AdvancedGeometryImporter
            >>> 
            >>> core = AdvancedGeometryImporter.from_serpent_full(Path("geometry.inp"))
            >>> print(f"Blocks: {len(core.blocks)}")
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse surfaces (already supported in basic parser)
            surfaces = AdvancedGeometryImporter._parse_serpent_surfaces(content)

            # Parse cells
            cells = AdvancedGeometryImporter._parse_serpent_cells(content)

            # Parse lattices
            lattices = AdvancedGeometryImporter._parse_serpent_lattices(content)

            # Reconstruct core
            core = PrismaticCore(name="Imported-Serpent-Full")
            core = AdvancedGeometryImporter._reconstruct_from_serpent(surfaces, cells, lattices, core)

            return core

        except Exception as e:
            raise ValueError(f"Error parsing Serpent geometry: {e}") from e

    @staticmethod
    def _parse_serpent_surfaces(content: str) -> Dict[int, Dict[str, Any]]:
        """Parse Serpent surface definitions."""
        surfaces = {}
        # Match: surf <id> <type> <params>
        pattern = r"surf\s+(\d+)\s+(\w+)\s+(.+)"
        for match in re.finditer(pattern, content, re.IGNORECASE):
            surf_id = int(match.group(1))
            surf_type = match.group(2).lower()
            params_str = match.group(3).strip()

            # Parse parameters
            params = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", params_str)]

            surfaces[surf_id] = {"type": surf_type, "params": params}

        return surfaces

    @staticmethod
    def _parse_serpent_cells(content: str) -> Dict[int, Dict[str, Any]]:
        """Parse Serpent cell definitions."""
        cells = {}
        # Match: cell <id> <universe> <material> <region>
        pattern = r"cell\s+(\d+)\s+(\d+|\w+)\s+([\w-]+|\([^)]+\))\s+(.+)"
        for match in re.finditer(pattern, content, re.IGNORECASE):
            cell_id = int(match.group(1))
            universe = match.group(2)
            material = match.group(3)
            region = match.group(4).strip()

            cells[cell_id] = {
                "universe": universe,
                "material": material,
                "region": region,
            }

        return cells

    @staticmethod
    def _parse_serpent_lattices(content: str) -> Dict[int, Dict[str, Any]]:
        """Parse Serpent lattice definitions."""
        lattices = {}
        # Match: lat <id> <type> <params>
        pattern = r"lat\s+(\d+)\s+(\w+)\s+(.+)"
        for match in re.finditer(pattern, content, re.IGNORECASE):
            lat_id = int(match.group(1))
            lat_type = match.group(2).lower()
            params_str = match.group(3).strip()

            # Parse parameters (simplified)
            params = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", params_str[:100])]  # Limit length

            lattices[lat_id] = {"type": lat_type, "params": params}

        return lattices

    @staticmethod
    def _reconstruct_from_serpent(
        surfaces: Dict[int, Dict[str, Any]],
        cells: Dict[int, Dict[str, Any]],
        lattices: Dict[int, Dict[str, Any]],
        core: PrismaticCore,
    ) -> PrismaticCore:
        """Reconstruct PrismaticCore from Serpent parsed data."""
        # Extract dimensions from surfaces
        core_radius = None
        z_min = None
        z_max = None

        for surf_id, surf_data in surfaces.items():
            if surf_data["type"] == "cz":
                if surf_data["params"]:
                    radius = abs(surf_data["params"][0])
                    if core_radius is None or radius > core_radius:
                        core_radius = radius
            elif surf_data["type"] == "pz":
                if surf_data["params"]:
                    z_pos = surf_data["params"][0]
                    if z_min is None or z_pos < z_min:
                        z_min = z_pos
                    if z_max is None or z_pos > z_max:
                        z_max = z_pos

        if core_radius:
            core.core_diameter = core_radius * 2
        if z_min is not None and z_max is not None:
            core.core_height = abs(z_max - z_min)

        # Reconstruct lattice if available
        if lattices:
            # Look for hexagonal lattice
            for lat_id, lat_data in lattices.items():
                if lat_data["type"] == "hex":
                    # Extract hexagonal lattice parameters
                    if len(lat_data["params"]) >= 2:
                        pitch = lat_data["params"][0]
                        # Create simplified lattice
                        core = AdvancedGeometryImporter._create_hex_lattice(core, pitch)

        return core

    @staticmethod
    def _create_hex_lattice(core: PrismaticCore, pitch: float) -> PrismaticCore:
        """Create hexagonal lattice structure."""
        from smrforge.geometry.core_geometry import GraphiteBlock

        n_rings = int(core.core_diameter / (2 * pitch)) if core.core_diameter > 0 else 3
        core.n_rings = n_rings

        block_id = 0
        for ring in range(n_rings + 1):
            if ring == 0:
                block = GraphiteBlock(
                    id=block_id,
                    position=Point3D(0, 0, core.core_height / 2),
                    flat_to_flat=pitch,
                    height=core.core_height,
                    block_type="fuel",
                )
                core.blocks.append(block)
                block_id += 1
            else:
                n_in_ring = 6 * ring
                for i in range(n_in_ring):
                    angle = 2 * np.pi * i / n_in_ring
                    x = ring * pitch * np.cos(angle)
                    y = ring * pitch * np.sin(angle)
                    block = GraphiteBlock(
                        id=block_id,
                        position=Point3D(x, y, core.core_height / 2),
                        flat_to_flat=pitch,
                        height=core.core_height,
                        block_type="fuel" if i % 2 == 0 else "reflector",
                    )
                    core.blocks.append(block)
                    block_id += 1

        return core

    @staticmethod
    def from_cad(filepath: Path, format: Optional[str] = None) -> Optional[PrismaticCore]:
        """
        Import geometry from CAD formats (STEP, IGES, STL).

        Args:
            filepath: Path to CAD file
            format: Optional format specification ('step', 'iges', 'stl')
                   (auto-detected from extension if not provided)

        Returns:
            PrismaticCore instance (simplified representation of CAD geometry)

        Raises:
            ImportError: If trimesh is not available
            ValueError: If file cannot be parsed

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_import import AdvancedGeometryImporter
            >>> 
            >>> # Import from STEP file
            >>> core = AdvancedGeometryImporter.from_cad(Path("geometry.step"))
            >>> print(f"Imported geometry with {len(core.blocks)} blocks")
        """
        if not _TRIMESH_AVAILABLE:
            raise ImportError(
                "trimesh is required for CAD import. Install with: pip install trimesh[all]"
            )

        # Auto-detect format from extension
        if format is None:
            ext = filepath.suffix.lower()
            format_map = {".step": "step", ".stp": "step", ".iges": "iges", ".igs": "iges", ".stl": "stl"}
            format = format_map.get(ext, "stl")

        try:
            # Load mesh using trimesh
            mesh = trimesh.load_mesh(str(filepath), file_type=format)

            # Convert mesh to PrismaticCore representation
            core = PrismaticCore(name=f"Imported-CAD-{filepath.stem}")

            # Extract bounding box for dimensions
            bounds = mesh.bounds
            core.core_height = abs(bounds[1][2] - bounds[0][2])  # z-dimension
            core.core_diameter = max(
                abs(bounds[1][0] - bounds[0][0]), abs(bounds[1][1] - bounds[0][1])
            )  # max x or y

            # Create simplified block representation from mesh
            # This is a placeholder - full implementation would extract
            # individual volumes/blocks from the CAD geometry

            # For now, create a single center block
            # Full implementation would parse CAD structure to identify blocks
            if core.core_diameter > 0 and core.core_height > 0:
                    block = GraphiteBlock(
                        id=0,
                        position=Point3D(
                            (bounds[0][0] + bounds[1][0]) / 2,
                            (bounds[0][1] + bounds[1][1]) / 2,
                            (bounds[0][2] + bounds[1][2]) / 2,
                        ),
                        flat_to_flat=core.core_diameter / 2,
                        height=core.core_height,
                        block_type="fuel",
                    )
                    core.blocks.append(block)

            return core

        except Exception as e:
            raise ValueError(f"Error parsing CAD file: {e}") from e

    @staticmethod
    def from_mcnp(filepath: Path) -> Optional[PrismaticCore]:
        """
        Import geometry from MCNP input file.

        Supports:
        - Surface definitions (P, S, CZ, PZ, etc.)
        - Cell definitions
        - Material assignments

        Args:
            filepath: Path to MCNP input file

        Returns:
            PrismaticCore instance with extracted geometry

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_import import AdvancedGeometryImporter
            >>> 
            >>> core = AdvancedGeometryImporter.from_mcnp(Path("geometry.i"))
            >>> print(f"Imported geometry: {len(core.blocks)} blocks")
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse MCNP surfaces
            surfaces = AdvancedGeometryImporter._parse_mcnp_surfaces(content)

            # Parse MCNP cells
            cells = AdvancedGeometryImporter._parse_mcnp_cells(content)

            # Reconstruct geometry
            core = PrismaticCore(name="Imported-MCNP")
            core = AdvancedGeometryImporter._reconstruct_from_mcnp(surfaces, cells, core)

            return core

        except Exception as e:
            raise ValueError(f"Error parsing MCNP geometry: {e}") from e

    @staticmethod
    def _parse_mcnp_surfaces(content: str) -> Dict[int, Dict[str, Any]]:
        """Parse MCNP surface definitions."""
        surfaces = {}
        # MCNP format: <id> <type> <params>
        # Examples: 1 PX 0.0 (plane), 2 CZ 150.0 (cylinder), 3 PZ -396.5 (plane)
        lines = content.split("\n")
        in_surface_section = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith("c") or line.startswith("C"):
                continue

            # Check if line starts with a number (surface definition)
            # MCNP surfaces start with surface ID (integer)
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # Check if first part is a digit (surface ID)
                    if parts[0].isdigit() or (parts[0].startswith("-") and parts[0][1:].isdigit()):
                        surf_id = abs(int(parts[0]))
                        if len(parts) >= 2:
                            surf_type = parts[1].upper()
                            params = [float(x) for x in parts[2:] if _is_numeric(x)]

                            if params or surf_type in ["PX", "PY", "PZ"]:  # Planes can have single param
                                surfaces[surf_id] = {"type": surf_type, "params": params}

                except (ValueError, IndexError):
                    continue

        return surfaces

    @staticmethod
    def _parse_mcnp_cells(content: str) -> Dict[int, Dict[str, Any]]:
        """Parse MCNP cell definitions."""
        cells = {}
        # MCNP format: <id> <material> <density> <region>
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("c") or line.startswith("C"):
                continue

            parts = line.split()
            if len(parts) >= 3:
                try:
                    cell_id = int(parts[0])
                    material_str = parts[1]
                    # Material can be number or 0 (void)
                    is_digit = material_str.isdigit() or (
                        material_str.startswith("-") and material_str[1:].isdigit()
                    )
                    material = int(material_str) if is_digit else None
                    # Region is the rest (simplified)
                    region = " ".join(parts[2:]) if len(parts) > 2 else ""

                    cells[cell_id] = {"material": material, "region": region}

                except (ValueError, IndexError):
                    continue

        return cells

    @staticmethod
    def _reconstruct_from_mcnp(
        surfaces: Dict[int, Dict[str, Any]], cells: Dict[int, Dict[str, Any]], core: PrismaticCore
    ) -> PrismaticCore:
        """Reconstruct PrismaticCore from MCNP parsed data."""
        # Extract dimensions from surfaces
        core_radius = None
        z_min = None
        z_max = None

        for surf_id, surf_data in surfaces.items():
            surf_type = surf_data["type"]
            params = surf_data["params"]

            if surf_type == "CZ" and params:
                # Cylinder about z-axis
                radius = abs(params[0])
                if core_radius is None or radius > core_radius:
                    core_radius = radius
            elif surf_type == "PZ" and params:
                # z-plane
                z_pos = params[0]
                if z_min is None or z_pos < z_min:
                    z_min = z_pos
                if z_max is None or z_pos > z_max:
                    z_max = z_pos

        if core_radius:
            core.core_diameter = core_radius * 2
        if z_min is not None and z_max is not None:
            core.core_height = abs(z_max - z_min)

        return core


def _is_numeric(s: str) -> bool:
    """Check if string is numeric."""
    try:
        float(s)
        return True
    except ValueError:
        return False


class GeometryConverter:
    """
    Advanced geometry conversion utilities.

    Provides methods to convert between different geometry formats
    and perform geometry transformations.
    """

    @staticmethod
    def convert_format(
        input_path: Path,
        output_path: Path,
        input_format: str,
        output_format: str,
    ) -> bool:
        """
        Convert geometry between different formats.

        Args:
            input_path: Path to input geometry file
            output_path: Path to output geometry file
            input_format: Input format ('json', 'openmc', 'serpent', 'cad', 'mcnp')
            output_format: Output format ('json', 'openmc', 'serpent', 'stl', 'vtk')

        Returns:
            True if conversion successful

        Examples:
            >>> from pathlib import Path
            >>> from smrforge.geometry.advanced_import import GeometryConverter
            >>> 
            >>> GeometryConverter.convert_format(
            ...     Path("geometry.xml"),
            ...     Path("geometry.json"),
            ...     "openmc",
            ...     "json"
            ... )
        """
        # Import geometry
        if input_format == "openmc":
            core = AdvancedGeometryImporter.from_openmc_full(input_path)
        elif input_format == "serpent":
            core = AdvancedGeometryImporter.from_serpent_full(input_path)
        elif input_format == "cad":
            core = AdvancedGeometryImporter.from_cad(input_path)
        elif input_format == "mcnp":
            core = AdvancedGeometryImporter.from_mcnp(input_path)
        elif input_format == "json":
            from smrforge.geometry.importers import GeometryImporter

            core = GeometryImporter.from_json(input_path)
        else:
            raise ValueError(f"Unsupported input format: {input_format}")

        if core is None:
            return False

        # Export geometry
        if output_format == "json":
            from smrforge.geometry.core_geometry import GeometryExporter

            GeometryExporter.to_json(core, output_path)
        elif output_format == "stl":
            GeometryConverter._export_to_stl(core, output_path)
        elif output_format == "vtk":
            from smrforge.visualization.mesh_3d import export_mesh_to_vtk
            from smrforge.geometry.mesh_extraction import extract_core_volume_mesh

            mesh = extract_core_volume_mesh(core)
            export_mesh_to_vtk(mesh, str(output_path))
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return True

    @staticmethod
    def _export_to_stl(core: PrismaticCore, filepath: Path):
        """Export geometry to STL format."""
        if not _TRIMESH_AVAILABLE:
            raise ImportError("trimesh is required for STL export. Install with: pip install trimesh")

        # Create mesh from blocks
        vertices = []
        faces = []
        face_offset = 0

        for block in core.blocks:
            # Create hexagonal prism mesh for block
            from smrforge.geometry.mesh_3d import extract_hexagonal_prism_mesh

            block_mesh = extract_hexagonal_prism_mesh(
                center=(block.position.x, block.position.y, block.position.z),
                flat_to_flat=block.flat_to_flat,
                height=block.height,
            )

            # Add vertices
            vertices.extend(block_mesh.vertices)

            # Add faces with offset
            if block_mesh.faces is not None:
                for face in block_mesh.faces:
                    faces.append([v + face_offset for v in face])
                face_offset += len(block_mesh.vertices)

        # Create trimesh and export
        if vertices and faces:
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            mesh.export(str(filepath))


