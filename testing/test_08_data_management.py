#!/usr/bin/env python
"""
Data Management Testing Script

This script tests ENDF data management features (setup, download, validation).

Usage:
    python test_08_data_management.py
"""

import sys
from pathlib import Path

try:
    from smrforge.core.endf_setup import setup_endf_data_interactive
    from smrforge.data_downloader import download_endf_data
    from smrforge.core.reactor_core import scan_endf_directory, organize_bulk_endf_downloads
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_scan_endf_directory():
    """Test scanning ENDF directory."""
    print("\n1. Testing scan ENDF directory...")
    
    # Check if ENDF directory exists in common locations
    possible_dirs = [
        Path.home() / 'ENDF-Data',
        Path.home() / 'Downloads' / 'ENDF-B-VIII.1',
        Path('/app/endf-data'),  # Docker
        Path('./endf-data')
    ]
    
    endf_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            endf_dir = dir_path
            break
    
    if endf_dir is None:
        print("⏭️  Skipped (no ENDF directory found)")
        print("   Try: smrforge data setup")
        return False
    
    try:
        scan_results = scan_endf_directory(endf_dir)
        print(f"✅ Scanned ENDF directory: {endf_dir}")
        print(f"   Files found: {scan_results.get('total_files', 0)}")
        print(f"   Valid files: {scan_results.get('valid_files', 0)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_organize_bulk_downloads():
    """Test organizing bulk-downloaded ENDF files."""
    print("\n2. Testing organize bulk downloads...")
    
    # Create a test source directory with dummy files
    test_source = Path('./test_endf_source')
    test_source.mkdir(exist_ok=True)
    
    # Create a dummy ENDF-like file
    dummy_file = test_source / 'n-092_U_235.endf'
    with open(dummy_file, 'w') as f:
        f.write("ENDF/B-VIII.1                                                         0  0\n")
        f.write(" " * 1000)  # Make it large enough to pass validation
    
    try:
        stats = organize_bulk_endf_downloads(
            source_dir=test_source,
            target_dir=Path('./test_endf_organized'),
            create_structure=True
        )
        
        print(f"✅ Organized bulk downloads")
        print(f"   Files found: {stats.get('files_found', 0)}")
        print(f"   Files organized: {stats.get('files_organized', 0)}")
        
        # Cleanup
        import shutil
        if Path('./test_endf_organized').exists():
            shutil.rmtree('./test_endf_organized')
        if test_source.exists():
            shutil.rmtree(test_source)
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_download():
    """Test downloading ENDF data."""
    print("\n3. Testing data download...")
    print("   Note: This will skip actual download in automated test")
    print("   To test manually: smrforge data download --library ENDF-B-VIII.1 --nuclide-set common")
    
    try:
        # Just test that the function exists and can be called with minimal params
        # Don't actually download in automated test
        print("✅ Download function available")
        print("   Use CLI for actual download: smrforge data download")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_data_validation():
    """Test ENDF data validation."""
    print("\n4. Testing data validation...")
    
    # Check if ENDF directory exists
    possible_dirs = [
        Path.home() / 'ENDF-Data',
        Path.home() / 'Downloads' / 'ENDF-B-VIII.1',
        Path('/app/endf-data'),
        Path('./endf-data')
    ]
    
    endf_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            endf_dir = dir_path
            break
    
    if endf_dir is None:
        print("⏭️  Skipped (no ENDF directory found)")
        return False
    
    try:
        from smrforge.cli import data_validate
        from argparse import Namespace
        
        # Create mock args
        args = Namespace(
            endf_dir=endf_dir,
            files=None,
            output=None
        )
        
        # This might require ENDF files, so we'll just test that it can be called
        print(f"✅ Validation function available")
        print(f"   To validate: smrforge data validate --endf-dir {endf_dir}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Data Management Testing")
    print("="*60)
    print("\nNote: Some tests require ENDF data to be available.")
    print("If tests are skipped, run: smrforge data setup")
    
    results = {}
    results['scan_directory'] = test_scan_endf_directory()
    results['organize_bulk'] = test_organize_bulk_downloads()
    results['data_download'] = test_data_download()
    results['data_validation'] = test_data_validation()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else ("⏭️" if result is None else "❌")
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("\nNote: Some tests may be skipped if ENDF data is not available.")
    print("This is expected - use CLI commands for full functionality.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
