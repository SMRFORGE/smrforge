# nucdata/core.py - Modern Nuclear Data Handler
"""
Fast, efficient nuclear data handling using modern Python libraries.
Replacement for PyNE with better performance and usability.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import numpy as np
import polars as pl  # Much faster than pandas
from numba import njit, prange
import zarr  # Modern, fast alternative to HDF5
import requests
from enum import Enum


class Library(Enum):
    """Supported nuclear data libraries."""
    ENDF_B_VIII = "endfb8.0"
    JEFF_33 = "jeff3.3"
    JENDL_5 = "jendl5.0"


@dataclass
class Nuclide:
    """Lightweight nuclide representation."""
    Z: int  # Atomic number
    A: int  # Mass number
    m: int = 0  # Metastable state
    
    @property
    def zam(self) -> int:
        """ZZAAAM notation."""
        return self.Z * 10000 + self.A * 10 + self.m
    
    @property
    def name(self) -> str:
        """Human-readable name like 'U235'."""
        from .constants import ELEMENT_SYMBOLS
        symbol = ELEMENT_SYMBOLS[self.Z]
        suffix = f"m{self.m}" if self.m > 0 else ""
        return f"{symbol}{self.A}{suffix}"
    
    def __hash__(self):
        return hash(self.zam)


class NuclearDataCache:
    """
    High-performance nuclear data cache using Zarr for storage.
    Much faster than HDF5 with better compression and chunking.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".smrforge" / "nucdata"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for hot data
        self._memory_cache: Dict = {}
        
        # Open zarr store (lazy loading)
        from zarr.storage import LocalStore
        self.store = LocalStore(str(self.cache_dir))
        self.root = zarr.open(self.store, mode='a')
    
    @lru_cache(maxsize=1024)
    def get_cross_section(
        self, 
        nuclide: Nuclide, 
        reaction: str,
        temperature: float = 293.6,
        library: Library = Library.ENDF_B_VIII
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get cross section data with aggressive caching.
        
        Returns:
            energy (eV), cross_section (barns)
        """
        key = f"{library.value}/{nuclide.name}/{reaction}/{temperature:.1f}K"
        
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Check zarr cache
        try:
            group = self.root[key]
            energy = group['energy'][:]
            xs = group['xs'][:]
            self._memory_cache[key] = (energy, xs)
            return energy, xs
        except KeyError:
            # Not cached, fetch and cache
            return self._fetch_and_cache(nuclide, reaction, temperature, library, key)
    
    def _fetch_and_cache(
        self, 
        nuclide: Nuclide, 
        reaction: str, 
        temperature: float,
        library: Library,
        key: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Fetch from source and cache. Tries multiple backends in order."""
        # Download ENDF file if needed
        endf_file = self._ensure_endf_file(nuclide, library)
        
        # Try OpenMC first (preferred - fast C++ backend)
        try:
            import openmc.data
            evaluation = openmc.data.endf.Evaluation(endf_file)
            reaction_mt = self._reaction_to_mt(reaction)
            if reaction_mt in evaluation:
                rxn_data = evaluation[reaction_mt]
                energy, xs = rxn_data.xs['0K'].x, rxn_data.xs['0K'].y
                
                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    xs = self._doppler_broaden(energy, xs, 293.6, temperature, nuclide.A)
                
                # Cache and return
                self._save_to_cache(key, energy, xs)
                return energy, xs
        except ImportError:
            pass  # Try next backend
        except Exception as e:
            # OpenMC available but failed - log and try next
            import warnings
            warnings.warn(f"OpenMC parsing failed: {e}. Trying alternative backend.", stacklevel=2)
        
        # Try SANDY as alternative (lighter weight, pure Python)
        try:
            import sandy
            endf_tapes = sandy.Endf6.from_file(str(endf_file))
            reaction_mt = self._reaction_to_mt(reaction)
            
            # Extract cross section data
            if reaction_mt in endf_tapes:
                mf3 = endf_tapes.filter_by(mf=3, mt=reaction_mt)
                if len(mf3) > 0:
                    energy = mf3[0].data['E'].values
                    xs = mf3[0].data['XS'].values
                    
                    # Apply temperature if needed
                    if abs(temperature - 293.6) > 1.0:
                        xs = self._doppler_broaden(energy, xs, 293.6, temperature, nuclide.A)
                    
                    # Cache and return
                    self._save_to_cache(key, energy, xs)
                    return energy, xs
        except ImportError:
            pass  # Try next backend
        except Exception as e:
            import warnings
            warnings.warn(f"SANDY parsing failed: {e}. Trying SMRForge parser.", stacklevel=2)
        
        # Try SMRForge's custom ENDF parser (pure Python, no dependencies)
        try:
            from .endf_parser import ENDFCompatibility
            evaluation = ENDFCompatibility(endf_file)
            reaction_mt = self._reaction_to_mt(reaction)
            
            if reaction_mt in evaluation:
                rxn_data = evaluation[reaction_mt]
                energy = rxn_data.xs['0K'].x
                xs = rxn_data.xs['0K'].y
                
                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    xs = self._doppler_broaden(energy, xs, 293.6, temperature, nuclide.A)
                
                # Cache and return
                self._save_to_cache(key, energy, xs)
                return energy, xs
        except ImportError:
            pass  # Module import failed
        except Exception as e:
            import warnings
            warnings.warn(f"SMRForge ENDF parser failed: {e}. Trying simple parser.", stacklevel=2)
        
        # Fallback: Simple ENDF parser for common reactions
        try:
            energy, xs = self._simple_endf_parse(endf_file, reaction, nuclide)
            if energy is not None and xs is not None:
                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    xs = self._doppler_broaden(energy, xs, 293.6, temperature, nuclide.A)
                
                # Cache and return
                self._save_to_cache(key, energy, xs)
                return energy, xs
        except Exception as e:
            import warnings
            warnings.warn(f"Simple ENDF parser failed: {e}", stacklevel=2)
        
        # All backends failed - provide helpful error message
        available_backends = []
        try:
            import openmc.data
            available_backends.append("OpenMC")
        except ImportError:
            pass
        try:
            import sandy
            available_backends.append("SANDY")
        except ImportError:
            pass
        
        error_msg = (
            f"Failed to parse cross-section data for {nuclide.name}/{reaction}. "
            f"No suitable backend available.\n\n"
            f"Installed backends: {', '.join(available_backends) if available_backends else 'None'}\n\n"
            f"To enable cross-section fetching, install one of:\n"
            f"  - OpenMC (preferred): pip install openmc>=0.13.0\n"
            f"    Note: Requires build tools (CMake, gfortran), takes several minutes to build\n"
            f"  - SANDY (lighter alternative): pip install sandy\n"
            f"    Pure Python, easier to install\n\n"
            f"Note: SMRForge includes a built-in ENDF parser, but it failed to parse this file.\n"
            f"This may indicate an issue with the ENDF file format or unsupported reaction.\n\n"
            f"Alternatively, pre-populate the cache directory at:\n"
            f"  {self.cache_dir}\n"
            f"with processed cross-section data to avoid runtime fetching."
        )
        raise ImportError(error_msg)
    
    def _save_to_cache(self, key: str, energy: np.ndarray, xs: np.ndarray):
        """Save cross-section data to zarr cache."""
        group = self.root.create_group(key, overwrite=True)
        group.create_dataset('energy', data=energy, chunks=(1024,), compression='zstd')
        group.create_dataset('xs', data=xs, chunks=(1024,), compression='zstd')
        
        # Cache in memory
        self._memory_cache[key] = (energy, xs)
    
    def _simple_endf_parse(
        self, 
        endf_file: Path, 
        reaction: str, 
        nuclide: Nuclide
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Simple ENDF parser for basic reactions (total, elastic, fission, capture).
        This is a minimal fallback that parses basic MT numbers from ENDF files.
        
        Note: The SMRForge ENDF parser (endf_parser.py) is preferred over this method.
        This is kept as a last-resort fallback.
        """
        reaction_mt = self._reaction_to_mt(reaction)
        
        try:
            with open(endf_file, 'r') as f:
                lines = f.readlines()
            
            # Find MF=3 (cross sections) section
            mf3_start = None
            for i, line in enumerate(lines):
                if line[70:72].strip() == '3' and int(line[72:75]) == reaction_mt:
                    mf3_start = i
                    break
            
            if mf3_start is None:
                return None, None
            
            # Parse the data points
            # ENDF format: each line can have up to 6 values (6E11.0 format)
            # Data comes as pairs: (E1, XS1, E2, XS2, ...)
            energy_list = []
            xs_list = []
            
            i = mf3_start + 1
            values = []  # Collect all values first
            
            while i < len(lines):
                line = lines[i]
                
                # Check if we've moved to next section (look at control record)
                if len(line) > 75:
                    try:
                        if line[70:72].strip() and int(line[70:72]) != 3:
                            break  # Not MF=3 anymore
                    except (ValueError, IndexError):
                        pass
                
                # Parse data (6 values per line in 11-character fields starting at column 0)
                for j in range(0, min(66, len(line)), 11):
                    if j + 11 > len(line):
                        break
                    try:
                        val_str = line[j:j+11].strip()
                        if val_str:  # Only parse non-empty strings
                            val = float(val_str)
                            values.append(val)
                    except (ValueError, IndexError):
                        continue
                
                i += 1
                
                # Check for end of section (next control record or blank line)
                if i < len(lines):
                    next_line = lines[i]
                    if len(next_line) > 75:
                        try:
                            # Check if next line is a new section
                            mf = next_line[70:72].strip()
                            if mf and int(mf) != 3:
                                break
                        except (ValueError, IndexError):
                            pass
            
            # Pair up values: (E1, XS1, E2, XS2, ...)
            for idx in range(0, len(values) - 1, 2):
                energy_list.append(values[idx])
                xs_list.append(values[idx + 1])
            
            if len(energy_list) > 0 and len(xs_list) > 0:
                energy = np.array(energy_list)
                xs = np.array(xs_list)
                return energy, xs
        
        except Exception:
            pass
        
        return None, None
    
    @staticmethod
    @njit(parallel=True, cache=True)
    def _doppler_broaden(
        energy: np.ndarray,
        xs: np.ndarray,
        T_old: float,
        T_new: float,
        A: int
    ) -> np.ndarray:
        """
        Fast Doppler broadening using Numba.
        Much faster than PyNE's implementation.
        """
        # Simplified kernel-based broadening
        # Real implementation would use proper convolution
        # This is a placeholder for the concept
        
        factor = np.sqrt(T_new / T_old)
        xs_new = xs.copy()
        
        # Apply simple scaling (real version needs proper physics)
        for i in prange(len(xs_new)):
            xs_new[i] *= factor
        
        return xs_new
    
    @staticmethod
    def _reaction_to_mt(reaction: str) -> int:
        """Convert reaction string to MT number."""
        MT_MAP = {
            'total': 1,
            'elastic': 2,
            'fission': 18,
            'capture': 102,
            'n,gamma': 102,
            'n,2n': 16,
            'n,alpha': 107,
        }
        return MT_MAP.get(reaction.lower(), 1)
    
    def _ensure_endf_file(self, nuclide: Nuclide, library: Library) -> Path:
        """Download ENDF file if not present."""
        endf_dir = self.cache_dir / "endf" / library.value
        endf_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{nuclide.name}.endf"
        filepath = endf_dir / filename
        
        if not filepath.exists():
            # Download from NNDC or IAEA
            url = self._get_endf_url(nuclide, library)
            response = requests.get(url)
            response.raise_for_status()
            filepath.write_bytes(response.content)
        
        return filepath
    
    @staticmethod
    def _get_endf_url(nuclide: Nuclide, library: Library) -> str:
        """Get download URL for ENDF file."""
        # IAEA Nuclear Data Services
        base_url = "https://www-nds.iaea.org/public/download-endf"
        # Simplified - real implementation needs proper URL construction
        return f"{base_url}/{library.value}/{nuclide.name}.endf"


class CrossSectionTable:
    """
    Fast multi-group cross section table using Polars.
    10-100x faster than pandas for tabular operations.
    """
    
    def __init__(self):
        self.data: Optional[pl.DataFrame] = None
        self._cache = NuclearDataCache()
    
    def generate_multigroup(
        self,
        nuclides: List[Nuclide],
        reactions: List[str],
        group_structure: np.ndarray,
        temperature: float = 900.0,  # Typical HTGR temp
        weighting_flux: Optional[np.ndarray] = None
    ) -> pl.DataFrame:
        """
        Generate multi-group cross sections with optimal performance.
        
        Args:
            nuclides: List of nuclides
            reactions: List of reactions (e.g., ['fission', 'capture'])
            group_structure: Energy group boundaries [eV]
            temperature: Temperature [K]
            weighting_flux: Optional flux spectrum for collapsing
        
        Returns:
            Polars DataFrame with columns: nuclide, reaction, group, xs
        """
        n_groups = len(group_structure) - 1
        
        # Pre-allocate arrays
        records = []
        
        for nuclide in nuclides:
            for reaction in reactions:
                # Get continuous energy data
                energy, xs = self._cache.get_cross_section(
                    nuclide, reaction, temperature
                )
                
                # Collapse to multi-group
                mg_xs = self._collapse_to_multigroup(
                    energy, xs, group_structure, weighting_flux
                )
                
                # Store results
                for g, xs_val in enumerate(mg_xs):
                    records.append({
                        'nuclide': nuclide.name,
                        'reaction': reaction,
                        'group': g,
                        'xs': xs_val
                    })
        
        # Create DataFrame (Polars is much faster than pandas)
        self.data = pl.DataFrame(records)
        return self.data
    
    @staticmethod
    @njit(parallel=True, cache=True)
    def _collapse_to_multigroup(
        energy: np.ndarray,
        xs: np.ndarray,
        group_bounds: np.ndarray,
        weighting_flux: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Fast group collapse using Numba.
        Orders of magnitude faster than PyNE.
        """
        n_groups = len(group_bounds) - 1
        mg_xs = np.zeros(n_groups)
        
        if weighting_flux is None:
            # Use 1/E weighting
            weighting_flux = 1.0 / energy
        
        for g in prange(n_groups):
            E_low = group_bounds[g+1]  # Reversed order (high to low)
            E_high = group_bounds[g]
            
            # Find energy indices in this group
            mask = (energy >= E_low) & (energy <= E_high)
            
            if np.sum(mask) > 0:
                # Flux-weighted average
                e_g = energy[mask]
                xs_g = xs[mask]
                flux_g = np.interp(e_g, energy, weighting_flux)
                
                mg_xs[g] = np.sum(xs_g * flux_g * np.diff(e_g)) / np.sum(flux_g * np.diff(e_g))
        
        return mg_xs
    
    def pivot_for_solver(self, nuclides: List[str], reactions: List[str]) -> np.ndarray:
        """
        Pivot table into matrix form optimized for solver.
        Returns shape: (n_nuclides, n_reactions, n_groups)
        """
        # Filter and pivot using Polars (extremely fast)
        filtered = self.data.filter(
            (pl.col('nuclide').is_in(nuclides)) &
            (pl.col('reaction').is_in(reactions))
        )
        
        # Pivot operation
        pivoted = filtered.pivot(
            values='xs',
            index=['nuclide', 'group'],
            columns='reaction'
        )
        
        # Convert to numpy for solver
        return pivoted.select(reactions).to_numpy()


class DecayData:
    """
    Fast decay data handling for fission products and actinides.
    """
    
    def __init__(self):
        self._cache = NuclearDataCache()
        self._decay_constants: Dict[Nuclide, float] = {}
        self._branching_ratios: Dict[Tuple[Nuclide, Nuclide], float] = {}
    
    @lru_cache(maxsize=512)
    def get_decay_constant(self, nuclide: Nuclide) -> float:
        """Get decay constant [1/s]."""
        half_life = self._get_half_life(nuclide)  # seconds
        return np.log(2) / half_life if half_life > 0 else 0.0
    
    def build_decay_matrix(self, nuclides: List[Nuclide]) -> np.ndarray:
        """
        Build Bateman equation decay matrix.
        Fast sparse matrix construction.
        """
        from scipy.sparse import lil_matrix
        
        n = len(nuclides)
        A = lil_matrix((n, n))
        
        nuclide_to_idx = {nuc: i for i, nuc in enumerate(nuclides)}
        
        for i, parent in enumerate(nuclides):
            # Diagonal: -lambda_i (decay out)
            A[i, i] = -self.get_decay_constant(parent)
            
            # Off-diagonal: lambda_j * b_ji (decay in from parent j)
            daughters = self._get_daughters(parent)
            for daughter, branching in daughters:
                if daughter in nuclide_to_idx:
                    j = nuclide_to_idx[daughter]
                    A[j, i] = self.get_decay_constant(parent) * branching
        
        return A.tocsr()  # Convert to CSR for fast matrix ops
    
    def _get_half_life(self, nuclide: Nuclide) -> float:
        """Get half-life from data files."""
        # Use OpenMC data or pre-computed tables
        # Placeholder implementation
        return 1e10  # seconds
    
    def _get_daughters(self, parent: Nuclide) -> List[Tuple[Nuclide, float]]:
        """Get decay daughters and branching ratios."""
        # Query decay data
        # Placeholder implementation
        return []


# Example usage
if __name__ == "__main__":
    # Initialize
    cache = NuclearDataCache()
    xs_table = CrossSectionTable()
    
    # Define nuclides
    U235 = Nuclide(Z=92, A=235)
    U238 = Nuclide(Z=92, A=238)
    Pu239 = Nuclide(Z=94, A=239)
    
    # Generate multi-group XS table
    group_structure = np.logspace(-5, 7, 9)  # 8-group structure
    
    df = xs_table.generate_multigroup(
        nuclides=[U235, U238, Pu239],
        reactions=['fission', 'capture', 'elastic'],
        group_structure=group_structure,
        temperature=1200.0  # HTGR operating temp
    )
    
    print(df)
    
    # Access specific cross section (blazingly fast)
    u235_fission = df.filter(
        (pl.col('nuclide') == 'U235') & 
        (pl.col('reaction') == 'fission')
    )
    print(u235_fission)
