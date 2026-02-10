"""
OpenMC import implementation for SMRForge.

Imports geometry and materials from OpenMC XML files into SMRForge
PrismaticCore format. Uses advanced_import for geometry parsing.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logging import get_logger

logger = get_logger("smrforge.io.openmc_import")


def import_reactor_from_openmc(
    geometry_file: Path,
    materials_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Import reactor from OpenMC format.

    Args:
        geometry_file: Path to geometry.xml
        materials_file: Optional path to materials.xml (parsed for metadata)

    Returns:
        Dictionary with 'core', 'source', 'format', and optionally 'materials'.

    Raises:
        FileNotFoundError: If geometry_file does not exist
        ValueError: If geometry cannot be parsed
    """
    geometry_file = Path(geometry_file)
    if not geometry_file.exists():
        raise FileNotFoundError(f"Geometry file not found: {geometry_file}")

    from ..geometry.advanced_import import AdvancedGeometryImporter

    core = AdvancedGeometryImporter._from_openmc_xml_csg(geometry_file)

    if core is None:
        raise ValueError(f"Could not parse OpenMC geometry from {geometry_file}")

    result: Dict[str, Any] = {
        "core": core,
        "source": str(geometry_file),
        "format": "openmc",
    }

    if materials_file and Path(materials_file).exists():
        result["materials"] = _parse_materials_xml(Path(materials_file))

    return result


def _parse_materials_xml(path: Path) -> Dict[int, Dict[str, Any]]:
    """Parse materials.xml into a dict of material_id -> {name, composition, temperature}."""
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        return {}

    materials: Dict[int, Dict[str, Any]] = {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for mat_elem in root.findall("material"):
            mat_id = int(mat_elem.get("id", 0))
            name = mat_elem.get("name", "")
            temp = float(mat_elem.get("temperature", 300.0))
            comp: Dict[str, float] = {}
            for nuc_elem in mat_elem.findall("nuclide"):
                nuc_name = nuc_elem.get("name", "")
                if nuc_name:
                    ao = nuc_elem.get("ao")
                    wo = nuc_elem.get("wo")
                    val = float(ao or wo or "0")
                    comp[nuc_name] = val
            materials[mat_id] = {"name": name, "composition": comp, "temperature": temp}
    except Exception as e:
        logger.warning("Could not parse materials.xml: %s", e)

    return materials
