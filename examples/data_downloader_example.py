"""
Example: Using SMRForge Data Downloader

This example demonstrates how to use the automated data downloader
to download ENDF nuclear data files.
"""

from pathlib import Path
from smrforge.data_downloader import (
    download_endf_data,
    download_preprocessed_library,
    COMMON_SMR_NUCLIDES,
)
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library


def example_download_specific_isotopes():
    """Download specific isotopes."""
    print("Example 1: Downloading specific isotopes...")
    
    stats = download_endf_data(
        library="ENDF/B-VIII.1",
        isotopes=["U235", "U238", "Pu239"],
        output_dir="~/ENDF-Data",
        show_progress=True,
    )
    
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")


def example_download_elements():
    """Download all common isotopes of specific elements."""
    print("\nExample 2: Downloading elements...")
    
    stats = download_endf_data(
        library="ENDF/B-VIII.1",
        elements=["U", "Pu", "Th"],
        output_dir="~/ENDF-Data",
        show_progress=True,
    )
    
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")


def example_download_common_smr():
    """Download common SMR nuclides."""
    print("\nExample 3: Downloading common SMR nuclides...")
    
    stats = download_endf_data(
        library="ENDF/B-VIII.1",
        nuclide_set="common_smr",
        output_dir="~/ENDF-Data",
        show_progress=True,
    )
    
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")


def example_use_downloaded_data():
    """Use downloaded data with NuclearDataCache."""
    print("\nExample 4: Using downloaded data...")
    
    # Download some nuclides first
    download_endf_data(
        library="ENDF/B-VIII.1",
        isotopes=["U235", "U238"],
        output_dir="~/ENDF-Data",
        show_progress=False,
    )
    
    # Use with NuclearDataCache
    # Note: Set SMRFORGE_ENDF_DIR environment variable or specify directory
    cache = NuclearDataCache(local_endf_dir=Path.home() / "ENDF-Data")
    
    u235 = Nuclide(Z=92, A=235)
    energy, xs = cache.get_cross_section(u235, "total", temperature=293.6)
    
    print(f"U-235 total cross-section: {len(energy)} energy points")
    print(f"Energy range: {energy[0]:.2e} - {energy[-1]:.2e} eV")


def example_environment_variable():
    """Example using environment variable."""
    print("\nExample 5: Using environment variable...")
    print("Set SMRFORGE_ENDF_DIR environment variable:")
    print("  export SMRFORGE_ENDF_DIR=~/ENDF-Data")
    print("\nThen in Python:")
    print("  from smrforge.core.reactor_core import NuclearDataCache")
    print("  cache = NuclearDataCache()  # Automatically uses env var")


if __name__ == "__main__":
    print("SMRForge Data Downloader Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run:
    # example_download_specific_isotopes()
    # example_download_elements()
    # example_download_common_smr()
    # example_use_downloaded_data()
    example_environment_variable()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
