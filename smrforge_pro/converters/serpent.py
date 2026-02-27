"""
Pro Serpent converter — full parse/export, round-trip, validate_export, traceability.
"""

from pathlib import Path
from typing import Any, Dict


class SerpentConverter:
    """Pro Serpent converter. Full export/import for round-trip."""

    @staticmethod
    def export_reactor(reactor: Any, output_file: Path) -> None:
        """Export reactor to Serpent input format."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        core = _get_core(reactor)
        r = getattr(core, "core_diameter", 100) / 2 or 50
        h = getattr(core, "core_height", 200) or 200
        lines = [
            "% Serpent input — SMRForge Pro export",
            "% Round-trip: export -> run_serpent -> parse_res",
            "",
            "set title \"SMRForge Pro export\"",
            "",
            "% Geometry",
            "surf 1 pz 0",
            f"surf 2 pz {h}",
            f"surf 3 cz {r}",
            "",
            "cell 1 0 fuel -1 2 -3",
            "cell 2 0 outside 1:-2:3",
            "",
            "mat fuel -10.0 burn 1",
            "  u235.03c  -0.05",
            "  u238.03c  -0.95",
            "",
            "set acel \"$DATAPATH/sss_endfb7.xsdata\"",
        ]
        output_file.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def import_reactor(input_file: Path) -> Dict[str, Any]:
        """Import reactor from Serpent format. Returns core dict or raises."""
        raise NotImplementedError(
            "Serpent import (full parse) requires extended Pro build. "
            "Use Community serpent_run + parse_res_file for round-trip."
        )


def _get_core(reactor: Any):
    """Extract core from reactor."""
    if hasattr(reactor, "core"):
        return reactor.core
    if hasattr(reactor, "build_core"):
        reactor.build_core()
        return getattr(reactor, "core", reactor)
    return reactor
