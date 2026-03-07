#!/usr/bin/env python3
"""
Generate preprocessed Zarr nuclear data library from ENDF files.

Parses ENDF cross-sections for common SMR nuclides and stores them in Zarr format
for fast offline loading. Use for air-gapped deployments or to avoid runtime parsing.

Usage:
    python scripts/generate_preprocessed_library.py --endf-dir ~/ENDF-B-VIII.1 --output preprocessed-common.zarr
    python scripts/generate_preprocessed_library.py --endf-dir $SMRFORGE_ENDF_DIR --output preprocessed.zarr --zip

Output:
    - Directory: preprocessed-common.zarr/ (Zarr LocalStore)
    - Optional: preprocessed-common.zarr.zip for transfer

Use with download_preprocessed_library(offline_path="path/to/preprocessed-common.zarr")
or set NuclearDataCache(cache_dir=Path("path/to/preprocessed-common.zarr")).
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smrforge.core.constants import parse_nuclide_string
from smrforge.core.reactor_core import NuclearDataCache, Nuclide
from smrforge.data_downloader import COMMON_SMR_NUCLIDES

REACTIONS = ["fission", "capture", "total"]
TEMPERATURES_K = [293.6, 600.0, 900.0]  # Room, hot, very hot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate preprocessed Zarr library from ENDF data"
    )
    parser.add_argument(
        "--endf-dir",
        type=Path,
        required=True,
        help="Path to ENDF-B-VIII.1 (or similar) directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("preprocessed-common.zarr"),
        help="Output Zarr directory (default: preprocessed-common.zarr)",
    )
    parser.add_argument(
        "--nuclides",
        nargs="+",
        default=None,
        help="Nuclide list (default: COMMON_SMR_NUCLIDES from data_downloader)",
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Create .zarr.zip archive for transfer",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    endf_path = args.endf_dir.expanduser().resolve()
    if not endf_path.is_dir():
        print(f"Error: ENDF directory not found: {endf_path}")
        sys.exit(1)

    output_path = args.output.expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    nuclide_names = args.nuclides or COMMON_SMR_NUCLIDES
    nuclides = []
    for name in nuclide_names:
        try:
            Z, A, m = parse_nuclide_string(name)
            nuclides.append(Nuclide(Z=Z, A=A, m=m))
        except ValueError:
            if args.verbose:
                print(f"Skipping invalid nuclide: {name}")
            continue

    print(f"Generating preprocessed library from {endf_path}")
    print(f"Output: {output_path}")
    print(
        f"Nuclides: {len(nuclides)} | Reactions: {REACTIONS} | Temperatures: {TEMPERATURES_K}"
    )

    # Create cache with output as cache_dir so Zarr is written there
    cache = NuclearDataCache(
        cache_dir=output_path,
        local_endf_dir=endf_path,
    )

    total = len(nuclides) * len(REACTIONS) * len(TEMPERATURES_K)
    done = 0
    errors = 0

    for nuclide in nuclides:
        for reaction in REACTIONS:
            for temp in TEMPERATURES_K:
                try:
                    cache.get_cross_section(nuclide, reaction, temperature=temp)
                    done += 1
                    if args.verbose:
                        print(f"  {nuclide.name}/{reaction} @ {temp}K")
                except Exception as e:
                    errors += 1
                    if args.verbose:
                        print(f"  Skip {nuclide.name}/{reaction} @ {temp}K: {e}")

    print(f"\nProcessed: {done}/{total} ({errors} skipped)")

    if args.zip:
        zip_path = output_path.with_suffix(output_path.suffix + ".zip")
        print(f"Creating archive: {zip_path}")
        shutil.make_archive(
            str(zip_path.with_suffix("")), "zip", output_path.parent, output_path.name
        )
        print(f"Done. Transfer {zip_path} and extract for offline use.")

    print("\nUsage:")
    print(f"  download_preprocessed_library(offline_path={repr(str(output_path))})")
    print(
        f"  Or: NuclearDataCache(cache_dir=Path({repr(str(output_path))}), local_endf_dir=None)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
