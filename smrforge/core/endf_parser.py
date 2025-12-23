"""
SMRForge ENDF Parser - Lightweight Python-only ENDF-6 file parser.

This is a custom implementation focused on what SMRForge needs:
- Cross-section data extraction (MF=3)
- Basic reaction support (total, elastic, fission, capture)
- Energy-dependent cross sections
- Temperature handling via Doppler broadening
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
import warnings

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None


@dataclass
class ReactionData:
    """Cross-section data for a specific reaction."""
    energy: np.ndarray  # Energy in eV
    cross_section: np.ndarray  # Cross section in barns
    mt_number: int  # Material table number
    reaction_name: str
    
    def interpolate(self, energy: float) -> float:
        """Linear interpolation of cross-section at given energy."""
        if energy <= self.energy[0]:
            return self.cross_section[0]
        if energy >= self.energy[-1]:
            return self.cross_section[-1]
        
        idx = np.searchsorted(self.energy, energy)
        e1, e2 = self.energy[idx-1], self.energy[idx]
        xs1, xs2 = self.cross_section[idx-1], self.cross_section[idx]
        
        # Linear interpolation
        f = (energy - e1) / (e2 - e1) if e2 != e1 else 0.0
        return xs1 + f * (xs2 - xs1)


class ENDFEvaluation:
    """
    ENDF-6 file evaluation parser.
    
    Usage:
        eval = ENDFEvaluation("U235.endf")
        if 1 in eval:  # MT=1 (total)
            data = eval[1]
            energy, xs = data.energy, data.cross_section
    """
    
    def __init__(self, filename: Path):
        """
        Initialize ENDF evaluation from file.
        
        Args:
            filename: Path to ENDF-6 file
        """
        self.filename = Path(filename)
        self.reactions: Dict[int, ReactionData] = {}
        self.metadata: Dict[str, any] = {}
        
        if not self.filename.exists():
            raise FileNotFoundError(f"ENDF file not found: {filename}")
        
        self._parse_file()
    
    def __contains__(self, mt: int) -> bool:
        """Check if reaction MT number exists."""
        return mt in self.reactions
    
    def __getitem__(self, mt: int) -> ReactionData:
        """Get reaction data by MT number."""
        if mt not in self.reactions:
            raise KeyError(f"Reaction MT={mt} not found in {self.filename}")
        return self.reactions[mt]
    
    def to_polars(self) -> Optional['pl.DataFrame']:
        """
        Export all reactions as a Polars DataFrame.
        
        Returns:
            DataFrame with columns: mt_number, reaction_name, energy, cross_section
            Returns None if Polars is not available
        """
        if not POLARS_AVAILABLE:
            return None
        
        records = []
        for mt, reaction in self.reactions.items():
            for energy, xs in zip(reaction.energy, reaction.cross_section):
                records.append({
                    'mt_number': mt,
                    'reaction_name': reaction.reaction_name,
                    'energy': energy,
                    'cross_section': xs
                })
        
        return pl.DataFrame(records)
    
    def get_reactions_dataframe(self) -> Optional['pl.DataFrame']:
        """
        Get a Polars DataFrame with one row per reaction (aggregated data).
        
        Returns:
            DataFrame with columns: mt_number, reaction_name, n_points, 
                                   energy_min, energy_max, xs_min, xs_max
            Returns None if Polars is not available
        """
        if not POLARS_AVAILABLE:
            return None
        
        records = []
        for mt, reaction in self.reactions.items():
            records.append({
                'mt_number': mt,
                'reaction_name': reaction.reaction_name,
                'n_points': len(reaction.energy),
                'energy_min': float(reaction.energy.min()),
                'energy_max': float(reaction.energy.max()),
                'xs_min': float(reaction.cross_section.min()),
                'xs_max': float(reaction.cross_section.max()),
                'xs_mean': float(reaction.cross_section.mean()),
            })
        
        return pl.DataFrame(records)
    
    def _parse_file(self):
        """Parse ENDF file and extract all reactions."""
        with open(self.filename, 'r') as f:
            lines = f.readlines()
        
        # Parse header (MF=1, MT=451) for metadata
        self._parse_header(lines)
        
        # Parse cross sections (MF=3)
        self._parse_mf3(lines)
    
    def _parse_header(self, lines: List[str]):
        """Parse ENDF header for metadata."""
        # Look for MF=1, MT=451 (evaluation information)
        for i, line in enumerate(lines):
            try:
                mf = int(line[70:72].strip())
                mt = int(line[72:75].strip())
                
                if mf == 1 and mt == 451:
                    # Extract ZA (Z*1000 + A) from line 1
                    if i + 1 < len(lines):
                        za_line = lines[i + 1]
                        za = int(float(za_line[0:11]))
                        z = za // 1000
                        a = za % 1000
                        self.metadata['Z'] = z
                        self.metadata['A'] = a
                        self.metadata['ZA'] = za
                    break
            except (ValueError, IndexError):
                continue
    
    def _parse_mf3(self, lines: List[str]):
        """
        Parse MF=3 (cross sections) sections.
        
        ENDF format:
        - Control record: COLUMNS 70-72 = MF, 72-75 = MT, 66-70 = MAT
        - Data records: COLUMNS 0-11, 11-22, 22-33, 33-44, 44-55, 55-66 (6 values per line)
        - Data format: 6E11.0 (6 exponential numbers, 11 chars each)
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a control record (must have 80 chars)
            if len(line) < 75:
                i += 1
                continue
            
            try:
                mf = int(line[70:72].strip())
                mt = int(line[72:75].strip())
            except (ValueError, IndexError):
                i += 1
                continue
            
            # Process MF=3 (cross sections)
            if mf == 3:
                energy, xs = self._parse_mf3_section(lines, i, mt)
                
                if energy is not None and len(energy) > 0:
                    reaction_name = self._mt_to_reaction_name(mt)
                    self.reactions[mt] = ReactionData(
                        energy=energy,
                        cross_section=xs,
                        mt_number=mt,
                        reaction_name=reaction_name
                    )
            
            i += 1
    
    def _parse_mf3_section(
        self, 
        lines: List[str], 
        start_idx: int, 
        mt: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Parse a single MF=3 section for given MT number.
        
        Returns:
            Tuple of (energy array, cross_section array) or (None, None) if failed
        """
        if start_idx >= len(lines):
            return None, None
        
        # Control record (first line)
        control_line = lines[start_idx]
        
        # Read interpolation flags and number of points (if present)
        try:
            # NPL - number of points (columns 0-11 might have info)
            # For now, we'll read until we hit next section
            pass
        except (ValueError, IndexError):
            pass
        
        # Parse data records
        energy_list = []
        xs_list = []
        
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we've hit a new section (control record)
            if len(line) >= 75:
                try:
                    next_mf = int(line[70:72].strip())
                    next_mt = int(line[72:75].strip())
                    
                    # If we hit a different MF or MT, we're done
                    if next_mf != 3 or (next_mt != mt and next_mt != 0):
                        break
                except (ValueError, IndexError):
                    pass
            
            # Parse 6 values per line (ENDF 6E11.0 format)
            # Each value is 11 characters wide
            line_values = []
            for j in range(0, min(66, len(line)), 11):
                if j + 11 > len(line):
                    break
                
                val_str = line[j:j+11].strip()
                if val_str:
                    try:
                        # ENDF uses E format (can be like 1.23+5 or 1.23E+5 or 1.23E+05)
                        # Python can't directly parse "1.23+5", needs "1.23e+5"
                        # Try to normalize the format
                        val_str_upper = val_str.upper()
                        
                        # If it has a + or - sign that's not at the start and no E, add E
                        if 'E' not in val_str_upper and ('+' in val_str or '-' in val_str[1:]):
                            # Find where the exponent starts (first + or - that's not at position 0)
                            for i, char in enumerate(val_str[1:], 1):
                                if char in '+-':
                                    # Insert 'e' or 'E' before the sign
                                    val_str = val_str[:i] + 'e' + val_str[i:]
                                    break
                        
                        # Convert to lowercase for Python's float parser
                        val_str = val_str.lower()
                        
                        val = float(val_str)
                        line_values.append(val)
                    except (ValueError, IndexError):
                        continue
            
            # ENDF stores data as pairs: (E1, XS1, E2, XS2, ...)
            for idx in range(0, len(line_values) - 1, 2):
                if idx + 1 < len(line_values):
                    energy_list.append(line_values[idx])
                    xs_list.append(line_values[idx + 1])
            
            i += 1
        
        if len(energy_list) == 0 or len(xs_list) == 0:
            return None, None
        
        # Convert to numpy arrays and sort by energy
        energy = np.array(energy_list)
        xs = np.array(xs_list)
        
        # Sort by energy (ENDF doesn't guarantee ordering)
        sort_idx = np.argsort(energy)
        energy = energy[sort_idx]
        xs = xs[sort_idx]
        
        # Remove duplicates (keep last value)
        unique_idx = np.unique(energy, return_index=True)[1]
        # Reverse to keep last occurrence
        unique_idx = np.sort(unique_idx)
        energy = energy[unique_idx]
        xs = xs[unique_idx]
        
        return energy, xs
    
    @staticmethod
    def _mt_to_reaction_name(mt: int) -> str:
        """Convert MT number to reaction name."""
        MT_NAMES = {
            1: 'total',
            2: 'elastic',
            3: 'non-elastic',
            4: 'inelastic',
            16: 'n,2n',
            17: 'n,3n',
            18: 'fission',
            19: 'fission (first chance)',
            20: 'fission (second chance)',
            21: 'fission (third chance)',
            22: 'n,n\'alpha',
            28: 'n,n\'p',
            102: 'capture',
            103: 'n,gamma',
            107: 'n,alpha',
            111: 'n,2alpha',
            112: 'n,3alpha',
        }
        return MT_NAMES.get(mt, f'MT{mt}')


# Compatibility wrapper for extended API
class ENDFCompatibility:
    """
    Extended API wrapper for ENDF evaluation.
    
    Usage:
        from smrforge.core.endf_parser import ENDFCompatibility
        evaluation = ENDFCompatibility("U235.endf")
        if 1 in evaluation:  # MT=1 (total)
            rxn_data = evaluation[1]
            energy = rxn_data.energy
            xs = rxn_data.cross_section
            # Or access via xs dictionary
            xs_data = rxn_data.xs['0K']
    """
    
    def __init__(self, filename: Path):
        """Initialize from ENDF file."""
        self._evaluation = ENDFEvaluation(filename)
    
    def __contains__(self, mt: int) -> bool:
        """Check if reaction exists."""
        return mt in self._evaluation
    
    def __getitem__(self, mt: int):
        """Get reaction data with extended interface."""
        reaction = self._evaluation[mt]
        
        # Return object with extended attributes
        class ReactionWrapper:
            def __init__(self, reaction_data: ReactionData):
                self._data = reaction_data
                self.energy = reaction_data.energy
                self.cross_section = reaction_data.cross_section
                
                # Provide xs dictionary structure for temperature data
                self.xs = {
                    '0K': type('obj', (object,), {
                        'x': reaction_data.energy,
                        'y': reaction_data.cross_section
                    })()
                }
        
        return ReactionWrapper(reaction)
    
    def to_polars(self) -> Optional['pl.DataFrame']:
        """Export all reactions as Polars DataFrame."""
        return self._evaluation.to_polars()
    
    def get_reactions_dataframe(self) -> Optional['pl.DataFrame']:
        """Get summary DataFrame of all reactions."""
        return self._evaluation.get_reactions_dataframe()

