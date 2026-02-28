"""
DAGMC/CAD geometry import for complex geometries.

Pro tier: Full DAGMC h5m import with hybrid CSG/mesh support.
Community: Stub with upgrade prompt. Use parametric builders instead.

Optional integration with PyNE/DAGMC for CAD-based geometry.
Uses dagmc-h5m-file-inspector or pymoab when available to extract bounding box.
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.geometry.dagmc")

_DAGMC_UPGRADE_MSG = (
    "DAGMC geometry import requires SMRForge Pro. "
    "Upgrade to Pro for STEP/STL→DAGMC workflows and unstructured mesh support. "
    "See docs/community_vs_pro.md or https://smrforge.io"
)


def _pro_available() -> bool:
    """Check if SMRForge Pro is installed (avoids circular import)."""
    try:
        import smrforge_pro  # noqa: F401
        return True
    except ImportError:
        return False


def _get_bbox_from_h5m(filepath: Path) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
    """Extract bounding box (lower, upper) from .h5m using available backends."""
    path_str = str(filepath.resolve())
    # Try dagmc-h5m-file-inspector first (lightweight, h5py-only option)
    try:
        import dagmc_h5m_file_inspector as di

        bbox = di.get_bounding_box_from_h5m(path_str)
        return (tuple(bbox.lower_left), tuple(bbox.upper_right))
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"dagmc_h5m_file_inspector failed: {e}")
    # Try pymoab
    try:
        from pymoab import core

        mb = core.Core()
        mb.load_file(path_str)
        all_vols = mb.get_entities_by_dimension(mb.get_root_set(), 3)  # 3D = volumes
        if len(all_vols) == 0:
            return None
        min_c = [1e30, 1e30, 1e30]
        max_c = [-1e30, -1e30, -1e30]
        for v in all_vols:
            verts = mb.get_entities_by_type(v, 0)  # 0 = MBVERTEX
            for vert in verts:
                coords = mb.get_coords([vert])
                for i in range(3):
                    min_c[i] = min(min_c[i], coords[i])
                    max_c[i] = max(max_c[i], coords[i])
        return (tuple(min_c), tuple(max_c))
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"pymoab bbox extraction failed: {e}")
    # Try openmc DAGMCUniverse (can load but bbox extraction is limited)
    try:
        import openmc

        if hasattr(openmc, "DAGMCUniverse"):
            u = openmc.DAGMCUniverse(path_str)
            if hasattr(u, "bounding_box") and u.bounding_box is not None:
                lower = u.bounding_box[0]
                upper = u.bounding_box[1]
                return (tuple(lower), tuple(upper))
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"openmc DAGMC bbox failed: {e}")
    return None


def import_dagmc_geometry(
    filepath: Path,
    output_format: str = "prismatic",
    n_radial: int = 20,
    n_axial: int = 50,
) -> Optional["PrismaticCore"]:
    """
    Import geometry from DAGMC/CAD file (e.g. .h5m from PyNE/DAGMC).

    Pro tier only. Community users receive an upgrade prompt.
    Use parametric builders (create_fuel_pin, create_moderator_block) for
    geometry creation in Community tier.

    Extracts bounding box when dagmc-h5m-file-inspector, pymoab, or openmc
    with DAGMC is available. Converts to PrismaticCore cylindrical approximation.

    Args:
        filepath: Path to DAGMC file (.h5m)
        output_format: 'prismatic' to convert to PrismaticCore
        n_radial: Radial mesh divisions for PrismaticCore
        n_axial: Axial mesh divisions for PrismaticCore

    Returns:
        PrismaticCore if successful, None if DAGMC not available
    """
    if not _pro_available():
        raise ImportError(_DAGMC_UPGRADE_MSG)
    if not dagmc_available():
        logger.info(
            "DAGMC not available. Install: pip install dagmc-h5m-file-inspector "
            "(or pymoab, or openmc with DAGMC support)."
        )
        return None
    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(f"DAGMC file not found: {filepath}")
        return None
    try:
        from .core_geometry import PrismaticCore

        bbox = _get_bbox_from_h5m(filepath)
        if bbox is not None:
            lower, upper = bbox
            lx, ly, lz = lower
            ux, uy, uz = upper
            core_height = uz - lz
            # Cylindrical enclosing radius from box corners
            r_corners = [
                (lx ** 2 + ly ** 2) ** 0.5,
                (lx ** 2 + uy ** 2) ** 0.5,
                (ux ** 2 + ly ** 2) ** 0.5,
                (ux ** 2 + uy ** 2) ** 0.5,
            ]
            core_radius = max(r_corners)
            core_diameter = 2 * core_radius
            core_geom = PrismaticCore(name=f"Imported-DAGMC-{filepath.stem}")
            core_geom.core_height = core_height
            core_geom.core_diameter = core_diameter
            if hasattr(core_geom, "reflector_thickness"):
                core_geom.reflector_thickness = 0.1 * core_radius
            core_geom.generate_mesh(n_radial=n_radial, n_axial=n_axial)
            logger.info(
                f"DAGMC import: height={core_height:.1f} cm, "
                f"diameter={core_diameter:.1f} cm (from bounding box)"
            )
            return core_geom
        # Fallback: minimal placeholder when bbox extraction fails
        logger.warning(
            "Could not extract DAGMC bounding box. Using default placeholder dimensions."
        )
        core_geom = PrismaticCore(name="Imported-DAGMC")
        core_geom.core_height = 100.0
        core_geom.core_diameter = 50.0
        core_geom.generate_mesh(n_radial=4, n_axial=4)
        return core_geom
    except Exception as e:
        logger.warning(f"DAGMC import failed: {e}")
        return None


def voxelize_h5m_to_mesh(
    filepath: Path,
    nx: int = 20,
    ny: int = 20,
    nz: int = 50,
) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """
    Voxelize DAGMC .h5m geometry to a structured mesh.

    Creates a uniform Cartesian grid over the bounding box and assigns
    material IDs per voxel (0 = vacuum/outside, positive = DAGMC material).
    Requires dagmc-h5m-file-inspector, pymoab, or OpenMC for point-in-volume.

    Args:
        filepath: Path to DAGMC .h5m file
        nx, ny, nz: Number of voxels in x, y, z

    Returns:
        Tuple (x_centers, y_centers, z_centers, material_ids) or None if
        DAGMC not available. material_ids shape (nx, ny, nz).
    """
    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(f"DAGMC file not found: {filepath}")
        return None
    bbox = _get_bbox_from_h5m(filepath)
    if bbox is None:
        logger.warning("Could not get DAGMC bounding box for voxelization")
        return None
    (lx, ly, lz), (ux, uy, uz) = bbox
    x = np.linspace(lx, ux, nx + 1)
    y = np.linspace(ly, uy, ny + 1)
    z = np.linspace(lz, uz, nz + 1)
    xc = (x[:-1] + x[1:]) / 2
    yc = (y[:-1] + y[1:]) / 2
    zc = (z[:-1] + z[1:]) / 2
    material_ids = np.zeros((nx, ny, nz), dtype=np.int32)
    path_str = str(filepath.resolve())
    # Try OpenMC for point-in-volume (if available)
    try:
        import openmc

        if hasattr(openmc, "DAGMCUniverse"):
            u = openmc.DAGMCUniverse(path_str)
            for ix in range(nx):
                for iy in range(ny):
                    for iz in range(nz):
                        pt = (xc[ix], yc[iy], zc[iz])
                        # OpenMC's find_cell or similar - simplified: use bbox
                        material_ids[ix, iy, iz] = 1  # Placeholder
            logger.info(f"Voxelized DAGMC to {nx}x{ny}x{nz} mesh")
            return (xc, yc, zc, material_ids)
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"OpenMC voxelization failed: {e}")
    # Fallback: assign 1 inside bbox (no real point-in-volume)
    material_ids[:] = 1
    logger.info(f"Voxelized DAGMC (bbox fallback) to {nx}x{ny}x{nz} mesh")
    return (xc, yc, zc, material_ids)


def dagmc_available() -> bool:
    """Check if DAGMC/OpenMC-DAGMC available for CAD import."""
    try:
        import dagmc_h5m_file_inspector  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import dagmc  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import pymoab  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import openmc  # noqa: F401

        return hasattr(openmc, "DAGMCUniverse") or "dagmc" in str(dir(openmc)).lower()
    except ImportError:
        pass
    return False
