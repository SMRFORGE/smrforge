"""
Utility functions for creating mock ENDF files for testing.

Provides comprehensive ENDF file generation that satisfies parser requirements.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np

from smrforge.core.reactor_core import Nuclide, NuclearDataCache


def create_mock_endf_file(
    nuclide: Nuclide,
    reaction: str,
    tmp_path: Path,
    energy_points: Optional[List[float]] = None,
    xs_values: Optional[List[float]] = None,
    include_mf1: bool = True,
    include_other_reactions: bool = False,
) -> Path:
    """
    Create a properly formatted mock ENDF file.
    
    Args:
        nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235))
        reaction: Reaction name (e.g., "total", "fission", "capture")
        tmp_path: Temporary directory path
        energy_points: Optional list of energy points in eV (default: [1e5, 1e6, 1e7])
        xs_values: Optional list of cross-section values in barns (default: [10.0, 12.0, 15.0])
        include_mf1: Whether to include MF=1 (evaluation info)
        include_other_reactions: Whether to include other common reactions (MT=2, 18, 102)
    
    Returns:
        Path to created ENDF file
    
    Example:
        >>> from smrforge.core.reactor_core import Nuclide
        >>> u235 = Nuclide(Z=92, A=235)
        >>> endf_file = create_mock_endf_file(u235, "total", tmp_path)
    """
    if energy_points is None:
        energy_points = [1e5, 1e6, 1e7]
    if xs_values is None:
        xs_values = [10.0, 12.0, 15.0]
    
    # Ensure same length
    n_points = min(len(energy_points), len(xs_values))
    energy_points = energy_points[:n_points]
    xs_values = xs_values[:n_points]
    
    # Get reaction MT number
    reaction_mt = NuclearDataCache._reaction_to_mt(reaction)
    
    # Format nuclide info for filename
    nuclide_name = nuclide.name
    filename = f"n-{nuclide.Z:03d}_{nuclide_name}_{nuclide.A:03d}.endf"
    endf_file = tmp_path / filename
    
    lines = []
    
    # ENDF header (MF=0, MT=0) - required
    header = (
        f" 9.{nuclide.Z:02d}{nuclide.A:03d}+4 2.345678+2          0          0          0          0  0  0     \n"
    )
    lines.append(header)
    
    # MF=1, MT=451 (evaluation info) - optional but recommended
    if include_mf1:
        mf1_mt451 = (
            f" 1.001000+3 1.000000+0          0          0          0          0  1 451     \n"
            f" 0.000000+0 0.000000+0          0          0          1          1  1 451     \n"
            f" 0.000000+0 0.000000+0          0          0          0          0  1 451     \n"
        )
        lines.append(mf1_mt451)
    
    # MF=3, MT=reaction (cross-section data) - required
    # Section header
    mf3_header = (
        f" 9.{nuclide.Z:02d}{nuclide.A:03d}+4 2.345678+2          0          0          0          0  3  {reaction_mt:3d}     \n"
    )
    lines.append(mf3_header)
    
    # Control record (LIST record with interpolation law)
    # Format: C1, C2, L1, L2, N1, N2 where N1=number of interpolation regions, N2=number of points
    mf3_control = (
        f" 0.000000+0 0.000000+0          0          0          1         {n_points:4d}  3  {reaction_mt:3d}     \n"
    )
    lines.append(mf3_control)
    
    # Interpolation law (linear interpolation, law=2)
    mf3_interp = (
        f" 0.000000+0 0.000000+0          0          0          0          0  3  {reaction_mt:3d}     \n"
    )
    lines.append(mf3_interp)
    
    # Data record - format pairs as (E, XS) with 6 values per line
    # ENDF format: 11 characters per value, 6 values per line (66 chars)
    data_pairs = list(zip(energy_points, xs_values))
    
    # Format data in ENDF-6 format (E1, XS1, E2, XS2, ...)
    for i in range(0, len(data_pairs), 3):  # 3 pairs per line (6 values)
        line_values = []
        for j in range(i, min(i + 3, len(data_pairs))):
            e, xs = data_pairs[j]
            # Format in ENDF-6 format: sign, mantissa, exponent
            e_str = f"{e:11.6e}".replace("e", "E").replace("+", "")
            xs_str = f"{xs:11.6e}".replace("e", "E").replace("+", "")
            line_values.extend([e_str, xs_str])
        
        # Pad to 6 values if needed
        while len(line_values) < 6:
            line_values.append(" 0.000000+0")
        
        # Format line: 6 values (11 chars each) + MF/MT markers
        line = "".join(f"{v:>11s}" for v in line_values[:6])
        line += f"  3  {reaction_mt:3d}     \n"
        lines.append(line)
    
    # Add other reactions if requested
    if include_other_reactions:
        other_reactions = [
            (2, "elastic", [1e5, 1e6, 1e7], [8.0, 9.0, 10.0]),
            (18, "fission", [1e5, 1e6, 1e7], [1.0, 1.5, 2.0]),
            (102, "capture", [1e5, 1e6, 1e7], [0.5, 0.6, 0.7]),
        ]
        
        for mt, _, e_vals, xs_vals in other_reactions:
            if mt == reaction_mt:
                continue  # Skip if already added
            
            # Section header
            mf3_header_other = (
                f" 9.{nuclide.Z:02d}{nuclide.A:03d}+4 2.345678+2          0          0          0          0  3  {mt:3d}     \n"
            )
            lines.append(mf3_header_other)
            
            # Control record
            mf3_control_other = (
                f" 0.000000+0 0.000000+0          0          0          1         {len(e_vals):4d}  3  {mt:3d}     \n"
            )
            lines.append(mf3_control_other)
            
            # Interpolation law
            mf3_interp_other = (
                f" 0.000000+0 0.000000+0          0          0          0          0  3  {mt:3d}     \n"
            )
            lines.append(mf3_interp_other)
            
            # Data record
            data_pairs_other = list(zip(e_vals, xs_vals))
            for i in range(0, len(data_pairs_other), 3):
                line_values = []
                for j in range(i, min(i + 3, len(data_pairs_other))):
                    e, xs = data_pairs_other[j]
                    e_str = f"{e:11.6e}".replace("e", "E").replace("+", "")
                    xs_str = f"{xs:11.6e}".replace("e", "E").replace("+", "")
                    line_values.extend([e_str, xs_str])
                
                while len(line_values) < 6:
                    line_values.append(" 0.000000+0")
                
                line = "".join(f"{v:>11s}" for v in line_values[:6])
                line += f"  3  {mt:3d}     \n"
                lines.append(line)
    
    # ENDF file terminator
    terminator = "                                                                    -1  0  0     \n"
    lines.append(terminator)
    
    # Ensure file is > 1000 bytes (validation requirement)
    content = "".join(lines)
    if len(content.encode('utf-8')) < 1000:
        padding = " " * (1000 - len(content.encode('utf-8'))) + "\n"
        content += padding
    
    endf_file.write_text(content)
    return endf_file


def create_mock_endf_file_minimal(
    nuclide: Nuclide,
    reaction: str,
    tmp_path: Path,
) -> Path:
    """
    Create a minimal but valid ENDF file (simpler version).
    
    Args:
        nuclide: Nuclide instance
        reaction: Reaction name
        tmp_path: Temporary directory path
    
    Returns:
        Path to created ENDF file
    """
    return create_mock_endf_file(
        nuclide=nuclide,
        reaction=reaction,
        tmp_path=tmp_path,
        energy_points=[1e5, 1e6, 1e7],
        xs_values=[10.0, 12.0, 15.0],
        include_mf1=True,
        include_other_reactions=False,
    )


def create_mock_endf_file_comprehensive(
    nuclide: Nuclide,
    tmp_path: Path,
) -> Path:
    """
    Create a comprehensive ENDF file with multiple reactions.
    
    Args:
        nuclide: Nuclide instance
        tmp_path: Temporary directory path
    
    Returns:
        Path to created ENDF file
    """
    return create_mock_endf_file(
        nuclide=nuclide,
        reaction="total",
        tmp_path=tmp_path,
        energy_points=[1e4, 1e5, 1e6, 1e7, 1e8],
        xs_values=[15.0, 12.0, 10.0, 8.0, 6.0],
        include_mf1=True,
        include_other_reactions=True,
    )

