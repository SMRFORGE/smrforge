"""
OpenMC export implementation for SMRForge.

Exports SMRForge reactor geometry and materials to OpenMC XML format
(geometry.xml, materials.xml, settings.xml). Supports PrismaticCore and
PebbleBedCore with homogenized cylindrical geometry for runnable models.

OpenMC format reference: https://docs.openmc.org/en/stable/io_formats/
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ..geometry.core_geometry import (
    MaterialRegion,
    PebbleBedCore,
    PrismaticCore,
)
from ..utils.logging import get_logger

logger = get_logger("smrforge.io.openmc_export")

# Material ID assignment
MAT_FUEL = 1
MAT_GRAPHITE = 2
MAT_COOLANT = 3
MAT_VOID = 0


def _normalize_nuclide(name: str) -> str:
    """Convert SMRForge nuclide names to OpenMC format (e.g. C -> C0, He -> He4)."""
    _mapping = {
        "C": "C0",
        "He": "He4",
        "H": "H1",
        "O": "O16",
        "N": "N14",
        "Si": "Si28",
        "Al": "Al27",
        "Fe": "Fe56",
    }
    return _mapping.get(name, name)


def _collect_materials(
    core: Union[PrismaticCore, PebbleBedCore],
) -> Tuple[Dict[int, MaterialRegion], Dict[str, int]]:
    """
    Collect unique material regions from core and assign IDs.
    Returns (material_id -> MaterialRegion, nuclide_name -> OpenMC format).
    """
    seen: Dict[str, MaterialRegion] = {}
    mat_id = MAT_FUEL

    if isinstance(core, PrismaticCore):
        for block in core.blocks:
            for ch in block.fuel_channels:
                mr = ch.material_region
                if mr and mr.material_id not in seen:
                    seen[mr.material_id] = mr
                    mat_id += 1
            if (
                block.moderator_material
                and block.moderator_material.material_id not in seen
            ):
                seen[block.moderator_material.material_id] = block.moderator_material
                mat_id += 1
    elif isinstance(core, PebbleBedCore):
        for pebble in core.pebbles:
            mr = pebble.material_region
            if mr and mr.material_id not in seen:
                seen[mr.material_id] = mr
                mat_id += 1

    # Build ID mapping: first fuel-like, then graphite
    materials: Dict[int, MaterialRegion] = {}
    idx = 1
    for mid, mr in seen.items():
        materials[idx] = mr
        idx += 1

    return materials, {}


def _write_materials_xml(
    materials: Dict[int, MaterialRegion],
    output_path: Path,
) -> None:
    """Write materials.xml with nuclide compositions in atom/b-cm (sum units)."""
    lines = ['<?xml version="1.0"?>', "<materials>"]
    for mat_id, mr in materials.items():
        comp = mr.composition or {}
        if not comp:
            comp = {"U235": 4.5e-5, "U238": 2.2e-4, "C0": 0.08}
        temp = getattr(mr, "temperature", 900.0)
        lines.append(
            f'  <material id="{mat_id}" name="{mr.material_id}" temperature="{temp:.1f}">'
        )
        lines.append('    <density value="sum" units="atom/b-cm" />')
        for nuc, dens in comp.items():
            onuc = _normalize_nuclide(nuc)
            lines.append(f'    <nuclide name="{onuc}" ao="{dens:.6e}" />')
        lines.append("  </material>")
    lines.append("</materials>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_geometry_xml_prismatic(
    core: PrismaticCore,
    materials: Dict[int, MaterialRegion],
    output_path: Path,
) -> None:
    """Write geometry.xml for PrismaticCore (homogenized cylindrical model)."""
    r_core = core.core_diameter / 2 if core.core_diameter else 50.0
    r_outer = r_core + (core.reflector_thickness or 30.0)
    z_lo = 0.0
    z_hi = core.core_height if core.core_height else 200.0

    # Surfaces: 1=z_lo, 2=z_hi, 3=core cylinder, 4=outer cylinder
    # Cells: 1=fuel (inside 3), 2=reflector (between 3 and 4), 0=outside
    mat_ids = list(materials.keys())
    mat_fuel = mat_ids[0] if mat_ids else MAT_FUEL
    mat_refl = mat_ids[1] if len(mat_ids) > 1 else MAT_GRAPHITE

    lines = [
        '<?xml version="1.0"?>',
        "<geometry>",
        "  <!-- Homogenized cylindrical core from SMRForge PrismaticCore -->",
        f'  <surface id="1" type="z-plane" coeffs="{z_lo}" boundary="vacuum" />',
        f'  <surface id="2" type="z-plane" coeffs="{z_hi}" boundary="vacuum" />',
        f'  <surface id="3" type="z-cylinder" coeffs="0 0 {r_core}" boundary="transmission" />',
        f'  <surface id="4" type="z-cylinder" coeffs="0 0 {r_outer}" boundary="vacuum" />',
        f'  <cell id="1" material="{mat_fuel}" region="-1 2 -3" />',
        f'  <cell id="2" material="{mat_refl}" region="-1 2 3 -4" />',
        f'  <cell id="3" material="void" region="1 | -2 | 4" />',
        "</geometry>",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_geometry_xml_pebble(
    core: PebbleBedCore,
    materials: Dict[int, MaterialRegion],
    output_path: Path,
) -> None:
    """Write geometry.xml for PebbleBedCore (homogenized cylindrical model)."""
    r_core = core.core_diameter / 2 if core.core_diameter else 150.0
    z_lo = 0.0
    z_hi = core.core_height if core.core_height else 1100.0
    mat_ids = list(materials.keys())
    mat_fuel = mat_ids[0] if mat_ids else MAT_FUEL

    lines = [
        '<?xml version="1.0"?>',
        "<geometry>",
        "  <!-- Homogenized pebble bed from SMRForge PebbleBedCore -->",
        f'  <surface id="1" type="z-plane" coeffs="{z_lo}" boundary="vacuum" />',
        f'  <surface id="2" type="z-plane" coeffs="{z_hi}" boundary="vacuum" />',
        f'  <surface id="3" type="z-cylinder" coeffs="0 0 {r_core}" boundary="vacuum" />',
        f'  <cell id="1" material="{mat_fuel}" region="-1 2 -3" />',
        f'  <cell id="2" material="void" region="1 | -2 | 3" />',
        "</geometry>",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_settings_xml(
    output_path: Path,
    particles: int = 1000,
    batches: int = 20,
    x_min: float = -50,
    x_max: float = 50,
    y_min: float = -50,
    y_max: float = 50,
    z_min: float = 0,
    z_max: float = 200,
) -> None:
    """Write settings.xml for eigenvalue run."""
    params = f"{x_min} {y_min} {z_min} {x_max} {y_max} {z_max}"
    lines = [
        '<?xml version="1.0"?>',
        "<settings>",
        "  <run_mode>eigenvalue</run_mode>",
        f"  <particles>{particles}</particles>",
        f"  <batches>{batches}</batches>",
        "  <inactive>5</inactive>",
        "  <source>",
        '    <space type="box">',
        f"      <parameters>{params}</parameters>",
        "    </space>",
        "  </source>",
        "</settings>",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _get_core_from_reactor(reactor: Any) -> Union[PrismaticCore, PebbleBedCore]:
    """Extract core geometry from reactor object."""
    if isinstance(reactor, (PrismaticCore, PebbleBedCore)):
        return reactor
    core = getattr(reactor, "core", None)
    if core is None and hasattr(reactor, "_get_core"):
        core = reactor._get_core()
    if core is None and hasattr(reactor, "_core"):
        core = reactor._core
    if core is None:
        raise ValueError(
            "Reactor has no core geometry. Call build_core() or provide a core directly."
        )
    return core


def export_reactor_to_openmc(
    reactor: Any,
    output_dir: Union[str, Path],
    particles: int = 1000,
    batches: int = 20,
) -> Path:
    """
    Export SMRForge reactor to OpenMC XML input files.

    Args:
        reactor: Reactor instance (SimpleReactor, preset, or PrismaticCore/PebbleBedCore)
        output_dir: Output directory for geometry.xml, materials.xml, settings.xml
        particles: Neutrons per generation (default 1000 for quick tests)
        batches: Number of batches (default 20)

    Returns:
        Path to output directory

    Raises:
        ValueError: If reactor has no core geometry
        OSError: If output directory cannot be created

    Example:
        >>> from smrforge import create_reactor
        >>> from smrforge.io.openmc_export import export_reactor_to_openmc
        >>> reactor = create_reactor("valar-10")
        >>> if hasattr(reactor, 'build_core'):
        ...     reactor.build_core()
        >>> path = export_reactor_to_openmc(reactor, "openmc_run")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    core = _get_core_from_reactor(reactor)
    materials, _ = _collect_materials(core)

    if not materials:
        # Create default fuel and graphite for empty core
        materials = {
            1: MaterialRegion(
                material_id="fuel",
                composition={"U235": 4.5e-5, "U238": 2.2e-4, "C0": 0.08},
                temperature=900.0,
                density=1.74,
            ),
            2: MaterialRegion(
                material_id="graphite",
                composition={"C0": 0.08},
                temperature=700.0,
                density=1.7,
            ),
        }
        logger.warning("No materials found in core; using default fuel and graphite")

    _write_materials_xml(materials, output_dir / "materials.xml")

    if isinstance(core, PrismaticCore):
        _write_geometry_xml_prismatic(core, materials, output_dir / "geometry.xml")
    elif isinstance(core, PebbleBedCore):
        _write_geometry_xml_pebble(core, materials, output_dir / "geometry.xml")
    else:
        raise TypeError(f"Unsupported core type: {type(core)}")

    r_core = (
        core.core_diameter / 2
        if hasattr(core, "core_diameter") and core.core_diameter
        else 50.0
    )
    z_hi = (
        core.core_height if hasattr(core, "core_height") and core.core_height else 200.0
    )
    _write_settings_xml(
        output_dir / "settings.xml",
        particles=particles,
        batches=batches,
        x_min=-r_core - 10,
        x_max=r_core + 10,
        y_min=-r_core - 10,
        y_max=r_core + 10,
        z_min=0,
        z_max=z_hi,
    )

    logger.info("OpenMC export complete: %s", output_dir)
    return output_dir
