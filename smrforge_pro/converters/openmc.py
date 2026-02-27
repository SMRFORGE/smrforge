"""
Pro OpenMC converter — full geometry + materials XML, round-trip, validate_export.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class OpenMCConverter:
    """Pro OpenMC converter. Delegates to Community implementation (full)."""

    @staticmethod
    def export_reactor(reactor: Any, output_dir: Path) -> None:
        """Export reactor to OpenMC format (geometry.xml, materials.xml, settings.xml)."""
        from smrforge.io.openmc_export import export_reactor_to_openmc

        export_reactor_to_openmc(reactor, Path(output_dir))

    @staticmethod
    def import_reactor(
        geometry_file: Path,
        materials_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Import reactor from OpenMC format."""
        from smrforge.io.openmc_import import import_reactor_from_openmc

        return import_reactor_from_openmc(
            Path(geometry_file),
            Path(materials_file) if materials_file else None,
        )
