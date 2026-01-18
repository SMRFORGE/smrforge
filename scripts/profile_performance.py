#!/usr/bin/env python
"""
Performance profiling script for SMRForge.

Generates profiling reports for key operations to identify bottlenecks.

Usage:
    python scripts/profile_performance.py [--function FUNCTION] [--output OUTPUT]
"""

import cProfile
import pstats
import io
import sys
import argparse
from pathlib import Path
from typing import Optional

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from smrforge.geometry.prismatic_core import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion, CrossSectionData


def profile_keff_calculation(output_file: Optional[Path] = None):
    """Profile k-eff calculation."""
    print("Profiling k-eff calculation...")
    
    # Create geometry
    geometry = PrismaticCore(name="ProfileCore")
    geometry.core_height = 200.0
    geometry.core_diameter = 100.0
    geometry.generate_mesh(n_radial=10, n_axial=5)
    
    # Create cross-section data
    xs_data = CrossSectionData(
        n_groups=4,
        n_materials=2,
        sigma_t=np.ones((2, 4)),
        sigma_s=np.ones((2, 4, 4)) * 0.5,
        sigma_f=np.array([[0.0, 0.0, 0.1, 0.2], [0.0, 0.0, 0.0, 0.0]]),
        nu_sigma_f=np.array([[0.0, 0.0, 0.25, 0.4], [0.0, 0.0, 0.0, 0.0]]),
        chi=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]),
        D=np.ones((2, 4)),
    )
    
    solver = MultiGroupDiffusion(geometry, xs_data)
    
    # Profile
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = solver.solve_eigenvalue()
    
    profiler.disable()
    
    # Generate report
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    report = s.getvalue()
    
    if output_file:
        output_file.write_text(report)
        print(f"✅ Profile report saved to {output_file}")
    else:
        print("\n" + "="*70)
        print("Performance Profile Report")
        print("="*70)
        print(report)
    
    print(f"\nK-eff result: {result['k_eff']:.6f}")
    
    return report


def profile_mesh_generation(output_file: Optional[Path] = None):
    """Profile mesh generation."""
    print("Profiling mesh generation...")
    
    geometry = PrismaticCore(name="ProfileGeometry")
    geometry.core_height = 200.0
    geometry.core_diameter = 100.0
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    geometry.generate_mesh(n_radial=10, n_axial=5)
    
    profiler.disable()
    
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    report = s.getvalue()
    
    if output_file:
        output_file.write_text(report)
        print(f"✅ Profile report saved to {output_file}")
    else:
        print("\n" + "="*70)
        print("Mesh Generation Profile Report")
        print("="*70)
        print(report)
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile SMRForge performance")
    parser.add_argument(
        "--function",
        choices=["keff", "mesh"],
        default="keff",
        help="Function to profile (default: keff)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for profile report (default: print to stdout)"
    )
    
    args = parser.parse_args()
    
    if args.function == "keff":
        profile_keff_calculation(args.output)
    elif args.function == "mesh":
        profile_mesh_generation(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
