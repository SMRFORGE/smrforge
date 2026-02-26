"""
Converters workflow example: Serpent, OpenMC, and MCNP export.

Demonstrates:
- Exporting a reactor to Serpent, OpenMC, and MCNP formats
- Using the pre_export hook for custom pre-processing
- Loading a preset reactor and exporting to each format

Usage:
    python examples/converters_workflow_example.py [--output-dir OUTPUT_DIR]
"""

import argparse
import sys
from pathlib import Path

# Add project root for dev runs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smrforge.convenience import create_reactor
from smrforge.io.converters import MCNPConverter, OpenMCConverter, SerpentConverter
from smrforge.workflows.plugin_registry import clear_hooks, register_hook

try:
    from rich.console import Console
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


def main() -> None:
    """Run converters workflow example."""
    parser = argparse.ArgumentParser(description="Converters workflow example")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("converters_output"),
        help="Output directory for exported files",
    )
    args = parser.parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Optional: register pre_export hook to log exports
    def log_pre_export(ctx):
        fmt = ctx.get("format", "?")
        path = ctx.get("output_file", "?")
        print(f"  pre_export: exporting to {fmt} -> {path}")

    try:
        register_hook("pre_export", log_pre_export)

        # Create reactor from preset
        reactor = create_reactor("valar-10")
        print("Created reactor: valar-10")

        # Export to Serpent
        serp_path = out_dir / "reactor.serp"
        SerpentConverter.export_reactor(reactor, serp_path)
        print(f"Exported Serpent: {serp_path}")

        # Export to OpenMC
        openmc_path = out_dir / "openmc"
        OpenMCConverter.export_reactor(reactor, openmc_path, particles=1000, batches=20)
        print(f"Exported OpenMC: {openmc_path}")

        # Export to MCNP
        mcnp_path = out_dir / "reactor.mcnp"
        MCNPConverter.export_reactor(reactor, mcnp_path)
        print(f"Exported MCNP: {mcnp_path}")

        # Rich table summary (with plain fallback)
        if _RICH_AVAILABLE:
            table = Table(title=f"Export Summary: {out_dir}")
            table.add_column("Format", style="cyan")
            table.add_column("Output", style="green")
            table.add_column("Status", justify="center")
            table.add_row("Serpent", str(serp_path), "OK")
            table.add_row("OpenMC", str(openmc_path), "OK")
            table.add_row("MCNP", str(mcnp_path), "OK")
            Console().print(table)
        print(f"\nAll exports written to {out_dir}")
    finally:
        clear_hooks("pre_export")


if __name__ == "__main__":
    main()
