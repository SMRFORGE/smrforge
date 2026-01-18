#!/usr/bin/env python
"""
Generate requirements-lock.txt with pinned dependency versions.

This script generates a requirements-lock.txt file with exact version pins
for all dependencies. This ensures reproducible builds.

Usage:
    python scripts/generate_requirements_lock.py
"""

import subprocess
import sys
from pathlib import Path


def get_installed_versions():
    """Get installed package versions using pip freeze."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().split("\n")


def parse_requirements_file(requirements_file):
    """Parse requirements file and return package names."""
    packages = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Extract package name (before ==, >=, etc.)
            package = line.split()[0].split('=')[0].split('<')[0].split('>')[0]
            packages.append(package.lower())
    return packages


def filter_relevant_packages(installed_packages, required_packages):
    """Filter installed packages to only include required ones."""
    relevant = []
    required_set = {pkg.lower().replace('_', '-').replace('.', '-') for pkg in required_packages}
    
    for package_line in installed_packages:
        package_name = package_line.split('==')[0].split('@')[0].lower()
        # Check if this package or its variants are in required
        for req_pkg in required_set:
            if package_name == req_pkg or package_name.replace('-', '_') == req_pkg.replace('-', '_'):
                relevant.append(package_line)
                break
    
    return relevant


def main():
    """Generate requirements-lock.txt from installed packages."""
    project_root = Path(__file__).parent.parent
    
    # Read requirements files
    requirements_file = project_root / "requirements.txt"
    requirements_dev_file = project_root / "requirements-dev.txt"
    
    if not requirements_file.exists():
        print(f"Error: {requirements_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Get required packages
    required_packages = parse_requirements_file(requirements_file)
    if requirements_dev_file.exists():
        required_packages.extend(parse_requirements_file(requirements_dev_file))
    
    # Get installed packages
    print("Collecting installed package versions...")
    installed_packages = get_installed_versions()
    
    # Filter to relevant packages
    relevant_packages = filter_relevant_packages(installed_packages, required_packages)
    
    # Sort alphabetically (case-insensitive)
    relevant_packages.sort(key=str.lower)
    
    # Write requirements-lock.txt
    lock_file = project_root / "requirements-lock.txt"
    with open(lock_file, 'w') as f:
        f.write("# Locked dependency versions for reproducible builds\n")
        f.write("# Generated automatically by scripts/generate_requirements_lock.py\n")
        f.write("# Do not edit manually - regenerate with: python scripts/generate_requirements_lock.py\n")
        f.write("\n")
        
        for package in relevant_packages:
            f.write(f"{package}\n")
    
    print(f"✅ Generated {lock_file}")
    print(f"   Locked {len(relevant_packages)} packages")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
