"""
Pro OpenMC converter - delegates to Community implementation with optional enhancements.

Pro tier: Full export/import; tally visualization available in Pro docs.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union


class OpenMCConverter:
    """
    OpenMC format converter (Pro).

    Full export/import delegates to smrforge.io. Pro adds tally visualization.
    """

    @staticmethod
    def export_reactor(
        reactor: Any,
        output_dir: Union[str, Path],
        particles: int = 1000,
        batches: int = 20,
    ) -> Path:
        """
        Export reactor to OpenMC XML format.

        Args:
            reactor: Reactor instance (SimpleReactor, preset, or PrismaticCore/PebbleBedCore)
            output_dir: Output directory for geometry.xml, materials.xml, settings.xml
            particles: Neutrons per generation (default 1000)
            batches: Number of batches (default 20)

        Returns:
            Path to output directory
        """
        from smrforge.io.openmc_export import export_reactor_to_openmc

        return export_reactor_to_openmc(
            reactor,
            Path(output_dir),
            particles=particles,
            batches=batches,
        )

    @staticmethod
    def import_reactor(
        geometry_file: Path,
        materials_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Import reactor from OpenMC format.

        Args:
            geometry_file: Path to geometry.xml
            materials_file: Optional path to materials.xml

        Returns:
            Dictionary with 'core', 'source', 'format', 'materials' (if provided)
        """
        from smrforge.io.openmc_import import import_reactor_from_openmc

        return import_reactor_from_openmc(
            Path(geometry_file),
            Path(materials_file) if materials_file else None,
        )
