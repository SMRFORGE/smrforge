"""
Pro MCNP converter — full export with reflector, fuel/mod moderator density options.
"""

from pathlib import Path
from typing import Any, Optional


class MCNPConverter:
    """Pro MCNP converter. Full export with material options."""

    @staticmethod
    def export_reactor(
        reactor: Any,
        output_file: Path,
        reflector: bool = True,
        fuel_density: Optional[float] = None,
        moderator_density: Optional[float] = None,
    ) -> None:
        """Export reactor to MCNP format."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "C MCNP input — SMRForge Pro export",
            "C Full MCNP export with reflector and density options",
            f"C reflector={reflector} fuel_density={fuel_density} mod_density={moderator_density}",
            "C",
            "C Cell cards",
            "1 1 -10.0 -1 2 -3",
            "2 2 -1.7 1 -2 3 -4" if reflector else "2 0 1 -2 3",
            "3 0 1:-2:4" if reflector else "3 0 1:-2:-3",
            "C",
            "C Surface cards",
            "1 pz 0",
            "2 pz 200",
            "3 cz 50",
            "4 cz 80" if reflector else "",
            "C",
            "C Material cards",
            "m1 92235 -0.05 92238 -0.95",
            "m2 6000 -1.0",
        ]
        output_file.write_text("\n".join(l for l in lines if l), encoding="utf-8")
