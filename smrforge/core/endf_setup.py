"""
ENDF File Setup Wizard

Interactive guide to help users set up ENDF nuclear data files manually.
Provides step-by-step instructions and validation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .reactor_core import (
    NuclearDataCache,
    get_standard_endf_directory,
    organize_bulk_endf_downloads,
    scan_endf_directory,
)


def print_step(step_num: int, title: str):
    """Print a formatted step header."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print("=" * 60)


def print_success(message: str):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"⚠ {message}")


def setup_endf_data_interactive() -> Optional[Path]:
    """
    Interactive wizard to guide users through ENDF data setup.

    Returns:
        Path to configured ENDF directory if successful, None if cancelled.
    """
    print("\n" + "=" * 60)
    print("SMRForge ENDF Data Setup Wizard")
    print("=" * 60)
    print("\nThis wizard will help you set up ENDF nuclear data files.")
    print("ENDF files are required for cross-section calculations.")
    print("\nYou have two options:")
    print("  1. Use existing ENDF files (if you already have them)")
    print("  2. Get instructions for downloading ENDF files")

    # Step 1: Choose option
    print_step(1, "Choose Setup Option")
    while True:
        choice = input("\nEnter your choice (1 or 2, or 'q' to quit): ").strip()
        if choice.lower() == "q":
            print("\nSetup cancelled.")
            return None
        if choice in ["1", "2"]:
            break
        print_error("Invalid choice. Please enter 1 or 2.")

    if choice == "1":
        return setup_existing_files()
    else:
        return setup_download_instructions()


def setup_existing_files() -> Optional[Path]:
    """Guide user through setting up existing ENDF files."""
    print_step(2, "Locate Your ENDF Files")
    print("\nPlease provide the path to your ENDF files directory.")
    print("This can be:")
    print("  - A directory with ENDF files in any structure")
    print("  - A directory with subdirectories containing ENDF files")
    print("  - The standard ENDF-B-VIII.1 download directory")

    standard_dir = get_standard_endf_directory()
    print(f"\nStandard location: {standard_dir}")

    while True:
        path_input = input(
            "\nEnter path to your ENDF directory (or 'q' to quit): "
        ).strip()
        if path_input.lower() == "q":
            return None

        if not path_input:
            print_error("Path cannot be empty.")
            continue

        try:
            endf_dir = Path(path_input).expanduser().resolve()
            if not endf_dir.exists():
                print_error(f"Directory does not exist: {endf_dir}")
                print_info("Please check the path and try again.")
                continue

            break
        except Exception as e:
            print_error(f"Invalid path: {e}")
            continue

    # Step 3: Scan and validate
    print_step(3, "Scanning and Validating ENDF Files")
    print(f"\nScanning {endf_dir}...")

    try:
        results = scan_endf_directory(endf_dir)

        print(f"\nScan Results:")
        print(f"  Total files found: {results['total_files']}")
        print(f"  Valid ENDF files: {results['valid_files']}")
        print(f"  Directory structure: {results['directory_structure']}")
        print(
            f"  Library versions: {', '.join(results['library_versions']) if results['library_versions'] else 'None detected'}"
        )

        if results["valid_files"] == 0:
            print_error("\nNo valid ENDF files found in this directory!")
            print_info("Please check that:")
            print("  - The directory contains .endf files")
            print("  - Files are valid ENDF format")
            print("  - Files are not corrupted")

            retry = (
                input("\nWould you like to try a different directory? (y/n): ")
                .strip()
                .lower()
            )
            if retry == "y":
                return setup_existing_files()
            return None

        # Show sample nuclides
        if results["nuclides"]:
            print(f"\nSample nuclides found: {', '.join(results['nuclides'][:10])}")
            if len(results["nuclides"]) > 10:
                print(f"  ... and {len(results['nuclides']) - 10} more")

    except Exception as e:
        print_error(f"Error scanning directory: {e}")
        return None

    # Step 4: Organize (optional)
    print_step(4, "Organize Files (Optional)")
    print("\nWould you like to organize your ENDF files into the standard structure?")
    print("This will:")
    print("  - Copy files to a standard directory structure")
    print("  - Validate all files")
    print("  - Create an organized index for fast access")
    print(f"\nStandard location: {standard_dir}")

    organize = input("\nOrganize files? (y/n): ").strip().lower()

    if organize == "y":
        library_version = "VIII.1"
        if results["library_versions"]:
            print(
                f"\nDetected library versions: {', '.join(results['library_versions'])}"
            )
            version_input = input(
                f"Enter library version (default: {library_version}): "
            ).strip()
            if version_input:
                library_version = version_input

        print(f"\nOrganizing files to {standard_dir}...")
        try:
            stats = organize_bulk_endf_downloads(
                source_dir=endf_dir,
                target_dir=standard_dir,
                library_version=library_version,
                create_structure=True,
            )

            print(f"\nOrganization Results:")
            print(f"  Files organized: {stats['files_organized']}")
            print(f"  Files skipped: {stats['files_skipped']}")
            print(f"  Unique nuclides: {stats['nuclides_indexed']}")

            if stats["files_organized"] > 0:
                print_success(f"Files successfully organized to {standard_dir}")
                endf_dir = standard_dir
            else:
                print_warning("No files were organized. Using original directory.")

        except Exception as e:
            print_error(f"Error organizing files: {e}")
            print_warning("Continuing with original directory structure.")

    # Step 5: Final validation
    print_step(5, "Final Validation")
    print(f"\nValidating setup with directory: {endf_dir}")

    try:
        cache = NuclearDataCache(local_endf_dir=endf_dir)

        # Test with a common nuclide
        from .reactor_core import Library, Nuclide

        test_nuclides = [
            Nuclide(92, 235),  # U-235
            Nuclide(92, 238),  # U-238
            Nuclide(8, 16),  # O-16
        ]

        found_count = 0
        for nuclide in test_nuclides:
            local_file = cache._find_local_endf_file(nuclide, Library.ENDF_B_VIII_1)
            if local_file is None:
                local_file = cache._find_local_endf_file(nuclide, Library.ENDF_B_VIII)
            if local_file:
                found_count += 1
                print_success(f"Found {nuclide.name}")
            else:
                print_warning(f"Not found: {nuclide.name} (may not be needed)")

        print(
            f"\nValidation complete: {found_count}/{len(test_nuclides)} test nuclides found"
        )

    except Exception as e:
        print_error(f"Validation error: {e}")
        return None

    # Step 6: Success
    print_step(6, "Setup Complete!")
    print(f"\n✓ ENDF data directory configured: {endf_dir}")
    print(f"\nTo use this directory in your code:")
    print(f"  from pathlib import Path")
    print(f"  from smrforge.core.reactor_core import NuclearDataCache")
    print(f"  ")
    print(f"  cache = NuclearDataCache(")
    print(f'      local_endf_dir=Path(r"{endf_dir}")')
    print(f"  )")

    return endf_dir


def setup_download_instructions() -> Optional[Path]:
    """Provide instructions for downloading ENDF files."""
    print_step(2, "Download Instructions")

    print("\nTo download ENDF files manually:")
    print("\n1. Visit one of these websites:")
    print("   - NNDC (National Nuclear Data Center):")
    print("     https://www.nndc.bnl.gov/endf/")
    print("   - IAEA Nuclear Data Services:")
    print("     https://www-nds.iaea.org/")

    print("\n2. Download ENDF/B-VIII.1 (recommended) or ENDF/B-VIII.0")
    print("   - Look for 'ENDF/B-VIII.1' or 'ENDF/B-VIII.0' downloads")
    print("   - Download the complete library (all nuclides)")

    print("\n3. Extract the files to a directory")
    print("   - The files can be in any structure")
    print("   - Common structure: ENDF-B-VIII.1/neutrons-version.VIII.1/")

    print("\n4. Run this setup wizard again")
    print("   - Choose option 1 (Use existing ENDF files)")
    print("   - Point to the extracted directory")

    standard_dir = get_standard_endf_directory()
    print(f"\nRecommended: Extract to {standard_dir}")
    print("  This is the standard location SMRForge looks for ENDF files")

    input("\nPress Enter to continue...")

    # Ask if they want to set up now
    print("\nHave you downloaded the ENDF files?")
    choice = input("Enter 'y' to set up now, or 'n' to exit: ").strip().lower()

    if choice == "y":
        return setup_existing_files()
    else:
        print("\nYou can run this setup wizard again later with:")
        print("  from smrforge.core.endf_setup import setup_endf_data_interactive")
        print("  setup_endf_data_interactive()")
        return None


def validate_endf_setup(endf_dir: Optional[Path] = None) -> Tuple[bool, Dict]:
    """
    Validate ENDF data setup and return status.

    Args:
        endf_dir: Optional ENDF directory to validate. If None, checks standard location.

    Returns:
        Tuple of (is_valid, validation_results):
        - is_valid: True if setup is valid
        - validation_results: Dictionary with validation details
    """
    if endf_dir is None:
        endf_dir = get_standard_endf_directory()

    endf_dir = Path(endf_dir)

    results = {
        "directory_exists": False,
        "has_files": False,
        "valid_files": 0,
        "nuclides": [],
        "library_versions": [],
        "directory_structure": "unknown",
        "errors": [],
        "warnings": [],
    }

    if not endf_dir.exists():
        results["errors"].append(f"Directory does not exist: {endf_dir}")
        return False, results

    results["directory_exists"] = True

    try:
        scan_results = scan_endf_directory(endf_dir)
        results.update(scan_results)
        results["has_files"] = scan_results["valid_files"] > 0

        if scan_results["valid_files"] == 0:
            results["errors"].append("No valid ENDF files found")
            return False, results

        # Test cache access
        try:
            cache = NuclearDataCache(local_endf_dir=endf_dir)
            from .reactor_core import Library, Nuclide

            # Test a few common nuclides
            test_nuclides = [Nuclide(92, 235), Nuclide(92, 238), Nuclide(8, 16)]
            found = 0
            for nuclide in test_nuclides:
                if cache._find_local_endf_file(
                    nuclide, Library.ENDF_B_VIII_1
                ) or cache._find_local_endf_file(nuclide, Library.ENDF_B_VIII):
                    found += 1

            if found == 0:
                results["warnings"].append(
                    "No test nuclides found (may still be valid)"
                )

        except Exception as e:
            results["warnings"].append(f"Cache test failed: {e}")

        return True, results

    except Exception as e:
        results["errors"].append(f"Scan failed: {e}")
        return False, results


if __name__ == "__main__":
    """Run setup wizard if executed directly."""
    result = setup_endf_data_interactive()
    if result:
        print(f"\n✓ Setup complete! ENDF directory: {result}")
        sys.exit(0)
    else:
        print("\n✗ Setup incomplete or cancelled.")
        sys.exit(1)
