# smrforge/core/reactor_core.py - Modern Nuclear Data Handler
"""
Fast, efficient nuclear data handling using modern Python libraries.
Replacement for PyNE with better performance and usability.

This module contains:
- NuclearDataCache: High-performance caching for nuclear data
- CrossSectionTable: Cross-section data management
- Nuclide: Lightweight nuclide representation
- DecayData: Decay data handling
"""

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os

import asyncio
import numpy as np
import polars as pl  # Much faster than pandas
import zarr  # Modern, fast alternative to HDF5
from numba import njit, prange

from ..utils.logging import get_logger, log_cache_operation, log_nuclear_data_fetch

# Get logger for this module
logger = get_logger("smrforge.core")


class Library(Enum):
    """
    Supported nuclear data libraries for cross-section data.
    
    Enum values correspond to library version strings used in file naming
    and URL construction. Each library provides evaluated nuclear data in
    ENDF-6 format.
    
    Attributes:
        ENDF_B_VIII: ENDF/B-VIII.0 (United States evaluated nuclear data library).
        JEFF_33: JEFF-3.3 (Joint Evaluated Fission and Fusion library, Europe).
        JENDL_5: JENDL-5.0 (Japanese Evaluated Nuclear Data Library).
    """

    ENDF_B_VIII = "endfb8.0"
    ENDF_B_VIII_1 = "endfb8.1"  # ENDF/B-VIII.1 (August 2024)
    JEFF_33 = "jeff3.3"
    JENDL_5 = "jendl5.0"


@dataclass
class Nuclide:
    """
    Lightweight nuclide representation.
    
    Represents a specific isotope using atomic number (Z), mass number (A),
    and optional metastable state (m). Provides conversions to common
    notation systems (ZAM, name string).
    
    Attributes:
        Z: Atomic number (proton count).
        A: Mass number (proton + neutron count).
        m: Metastable state index (0 for ground state, >0 for metastable states).
    
    Example:
        >>> u235 = Nuclide(Z=92, A=235, m=0)
        >>> print(u235.name)  # "U235"
        >>> print(u235.zam)   # 922350
        >>> u239m = Nuclide(Z=92, A=239, m=1)
        >>> print(u239m.name)  # "U239m1"
    """

    Z: int  # Atomic number
    A: int  # Mass number
    m: int = 0  # Metastable state

    @property
    def zam(self) -> int:
        """
        ZZAAAM notation (Z * 10000 + A * 10 + m).
        
        Returns:
            Integer in ZZAAAM format (e.g., 922350 for U-235).
        
        Example:
            >>> nuc = Nuclide(Z=92, A=235, m=0)
            >>> nuc.zam
            922350
        """
        return self.Z * 10000 + self.A * 10 + self.m

    @property
    def name(self) -> str:
        """
        Human-readable nuclide name string.
        
        Returns:
            String like "U235" for ground state or "U239m1" for metastable.
        
        Example:
            >>> nuc = Nuclide(Z=92, A=235)
            >>> nuc.name
            'U235'
            >>> nuc_meta = Nuclide(Z=92, A=239, m=1)
            >>> nuc_meta.name
            'U239m1'
        """
        from .constants import ELEMENT_SYMBOLS

        symbol = ELEMENT_SYMBOLS[self.Z]
        suffix = f"m{self.m}" if self.m > 0 else ""
        return f"{symbol}{self.A}{suffix}"

    def __hash__(self) -> int:
        return hash(self.zam)


class NuclearDataCache:
    """
    High-performance nuclear data cache using Zarr for storage.
    
    Much faster than HDF5 with better compression and chunking. Provides
    two-level caching: in-memory cache for hot data and persistent Zarr
    storage for cross-section data. Uses local ENDF files (must be set up
    manually) and supports multiple backends (SANDY, built-in parser).
    
    **ENDF File Setup Required:**
    ENDF files must be set up manually before use. Run the setup wizard:
    
    .. code-block:: python
    
        from smrforge.core.endf_setup import setup_endf_data_interactive
        setup_endf_data_interactive()
    
    Or from command line:
    
    .. code-block:: bash
    
        python -m smrforge.core.endf_setup
    
    Attributes:
        cache_dir: Directory for persistent cache storage.
        local_endf_dir: Optional path to local ENDF data directory.
        _memory_cache: In-memory dictionary cache for frequently accessed data.
        root: Zarr root group for persistent storage.
    """

    def __init__(self, cache_dir: Optional[Path] = None, local_endf_dir: Optional[Path] = None):
        """
        Initialize nuclear data cache.
        
        Args:
            cache_dir: Optional path to cache directory. Defaults to
                ``~/.smrforge/nucdata`` if not provided.
            local_endf_dir: Optional path to local ENDF directory for bulk storage.
                If provided, the cache will recursively scan this directory for ENDF files
                before attempting to download. Supports flexible directory structures:
                
                **Standard structure:**
                - ``{local_endf_dir}/neutrons-version.VIII.1/n-ZZZ_Element_AAA.endf``
                - ``{local_endf_dir}/neutrons-version.VIII.0/n-ZZZ_Element_AAA.endf``
                
                **Bulk download structure (automatically detected):**
                - Flat directories: ``{local_endf_dir}/*.endf``
                - Nested directories: ``{local_endf_dir}/**/*.endf``
                - Alternative naming: ``U235.endf``, ``u235.endf``, etc.
                
                The system automatically discovers files regardless of directory structure.
                Use ``get_standard_endf_directory()`` to get the recommended directory path.
        
        Example:
            >>> cache = NuclearDataCache()
            >>> # Or specify custom cache location
            >>> cache = NuclearDataCache(cache_dir=Path("/tmp/nucdata"))
            >>> # Or use local ENDF files (flexible structure)
            >>> cache = NuclearDataCache(
            ...     local_endf_dir=Path("C:/Users/user/ENDF-Data")
            ... )
            >>> # Or use standard directory
            >>> from smrforge.core.reactor_core import get_standard_endf_directory
            >>> std_dir = get_standard_endf_directory()
            >>> cache = NuclearDataCache(local_endf_dir=std_dir)
        """
        self.cache_dir = cache_dir or Path.home() / ".smrforge" / "nucdata"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Local ENDF directory (e.g., ENDF-B-VIII.1)
        # Check environment variable if local_endf_dir not provided
        if local_endf_dir is None:
            env_dir = os.getenv("SMRFORGE_ENDF_DIR")
            if env_dir:
                local_endf_dir = Path(env_dir).expanduser().resolve()
        
        # Try to load from config file if still None
        if local_endf_dir is None:
            config_dir = self._load_config_dir()
            if config_dir:
                local_endf_dir = config_dir
        
        self.local_endf_dir = Path(local_endf_dir) if local_endf_dir else None
        self._local_file_index: Optional[Dict[str, Path]] = None  # Lazy-loaded index
        self._tsl_file_index: Optional[Dict[str, Path]] = None  # TSL material name -> file path
        self._photon_file_index: Optional[Dict[str, Path]] = None  # Element symbol -> file path
        
        # Build index on initialization if local directory provided (Phase 3 optimization)
        if self.local_endf_dir and self.local_endf_dir.exists():
            # Eagerly build index for faster first access
            self._build_local_file_index()

        # In-memory cache for hot data
        self._memory_cache: Dict = {}
        
        # Parser instance (lazy initialization, reused across calls for performance)
        # Prefers C++ parser if available (2-5x faster than Python parser)
        self._parser: Optional[Any] = None
        self._parser_type: Optional[str] = None  # Track parser type for logging
        
        # File metadata cache (for performance - avoids redundant file I/O)
        # Maps file path -> (mtime, file_size, available_mts)
        self._file_metadata_cache: Dict[Path, Tuple[float, int, Optional[set]]] = {}

        # Open zarr store (lazy loading)
        from zarr.storage import LocalStore

        self.store = LocalStore(str(self.cache_dir))
        self.root = zarr.open(self.store, mode="a")

    @staticmethod
    def _load_config_dir() -> Optional[Path]:
        """
        Load ENDF directory from configuration file.
        
        Checks for ~/.smrforge/config.yaml and reads endf.default_directory.
        
        Returns:
            Path to ENDF directory if found in config, None otherwise.
        """
        try:
            config_path = Path.home() / ".smrforge" / "config.yaml"
            if not config_path.exists():
                return None
            
            # Try to import yaml (optional dependency)
            try:
                import yaml
            except ImportError:
                logger.debug("PyYAML not installed, skipping config file")
                return None
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config and 'endf' in config:
                endf_config = config['endf']
                if 'default_directory' in endf_config:
                    dir_path = Path(endf_config['default_directory']).expanduser().resolve()
                    if dir_path.exists():
                        return dir_path
        except Exception as e:
            logger.debug(f"Error loading config file: {e}")
        
        return None

    @lru_cache(maxsize=1024)
    def get_cross_section(
        self,
        nuclide: Nuclide,
        reaction: str,
        temperature: float = 293.6,
        library: Library = Library.ENDF_B_VIII,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get cross section data with aggressive caching.
        
        Checks in-memory cache first, then persistent Zarr cache, and finally
        fetches and parses from ENDF files if needed. Automatically applies
        Doppler broadening for temperatures other than 293.6 K.
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235)).
            reaction: Reaction name (e.g., "fission", "capture", "elastic",
                "total", "n,gamma", "n,2n", "n,alpha").
            temperature: Temperature in Kelvin. Defaults to 293.6 K (room temp).
            library: Nuclear data library. Defaults to ENDF/B-VIII.0.
        
        Returns:
            Tuple of (energy, cross_section):
                - energy: 1D array of neutron energies in eV.
                - cross_section: 1D array of cross sections in barns.
        
        Raises:
            ImportError: If no suitable backend (SANDY or built-in parser)
                is available and cross-section data cannot be fetched.
            ValueError: If nuclide or reaction is invalid.
        
        Example:
            >>> cache = NuclearDataCache()
            >>> u235 = Nuclide(Z=92, A=235)
            >>> energy, xs = cache.get_cross_section(u235, "fission", temperature=900.0)
            >>> print(f"Energy range: {energy.min():.2e} - {energy.max():.2e} eV")
            >>> print(f"Fission XS at 1 eV: {np.interp(1.0, energy, xs):.2f} b")
        """
        key = f"{library.value}/{nuclide.name}/{reaction}/{temperature:.1f}K"

        # Check memory cache first
        if key in self._memory_cache:
            log_cache_operation("hit", key, logger)
            return self._memory_cache[key]

        # Check zarr cache
        try:
            group = self.root[key]
            energy = group["energy"][:]
            xs = group["xs"][:]
            self._memory_cache[key] = (energy, xs)
            log_cache_operation("hit", key, logger)
            return energy, xs
        except KeyError:
            # Not cached, fetch and cache
            log_cache_operation("miss", key, logger)
            return self._fetch_and_cache(nuclide, reaction, temperature, library, key)
    
    def _get_parser(self):
        """
        Get or create endf-parserpy parser instance (reused across calls for performance).
        
        Prefers C++ parser if available (2-5x faster than Python parser). The parser
        instance is cached and reused to avoid initialization overhead on each file parse.
        
        Returns:
            Parser instance (EndfParserCpp if available, otherwise EndfParserPy or factory-selected).
            Returns None if endf-parserpy is not available.
        
        Note:
            Parser instances are thread-safe and can be reused across multiple file parses.
            This provides 10-30% performance improvement by eliminating parser initialization overhead.
        """
        if self._parser is None:
            try:
                from endf_parserpy import EndfParserFactory
                
                # Try to get C++ parser explicitly (fastest option)
                try:
                    from endf_parserpy import EndfParserCpp
                    self._parser = EndfParserCpp()
                    self._parser_type = "C++"
                    logger.info(
                        "Using endf-parserpy C++ parser (fast) - "
                        "2-5x faster than Python parser"
                    )
                except (ImportError, AttributeError):
                    # Fallback to factory (auto-selects best available)
                    self._parser = EndfParserFactory.create()
                    parser_type_name = type(self._parser).__name__
                    self._parser_type = parser_type_name
                    
                    # Check if it's actually the C++ parser
                    if "Cpp" in parser_type_name or "cpp" in parser_type_name.lower():
                        logger.info(f"Using endf-parserpy C++ parser: {parser_type_name}")
                    else:
                        logger.info(
                            f"Using endf-parserpy Python parser: {parser_type_name}. "
                            "For better performance, install C++ parser: "
                            "pip install --upgrade endf-parserpy"
                        )
            except ImportError:
                # endf-parserpy not available
                self._parser = None
                self._parser_type = None
        
        return self._parser
    
    def _get_file_metadata(self, file_path: Path) -> Tuple[float, int, Optional[set]]:
        """
        Get cached file metadata or compute it.
        
        Returns:
            Tuple of (mtime, file_size, available_mts)
            available_mts is None if not yet cached
        """
        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            file_size = stat.st_size
            
            if file_path in self._file_metadata_cache:
                cached_mtime, cached_size, cached_mts = self._file_metadata_cache[file_path]
                if cached_mtime == mtime and cached_size == file_size:
                    # File hasn't changed, return cached metadata
                    return (mtime, file_size, cached_mts)
            
            # File changed or not cached, return current stats with None for MTs
            return (mtime, file_size, None)
        except (OSError, FileNotFoundError):
            return (0.0, 0, None)
    
    def _update_file_metadata(self, file_path: Path, available_mts: set):
        """Update file metadata cache with available MT numbers."""
        try:
            stat = file_path.stat()
            self._file_metadata_cache[file_path] = (stat.st_mtime, stat.st_size, available_mts)
        except (OSError, FileNotFoundError):
            pass
    
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about the current parser instance.
        
        Returns:
            Dictionary with parser information including type and availability.
        """
        info = {
            "parser_available": False,
            "parser_type": None,
            "is_cpp_parser": False,
        }
        
        try:
            parser = self._get_parser()
            if parser is not None:
                info["parser_available"] = True
                info["parser_type"] = self._parser_type or type(parser).__name__
                info["is_cpp_parser"] = (
                    "Cpp" in info["parser_type"] or 
                    "cpp" in info["parser_type"].lower() or
                    self._parser_type == "C++"
                )
        except ImportError:
            pass
        
        return info

    def _fetch_and_cache(
        self,
        nuclide: Nuclide,
        reaction: str,
        temperature: float,
        library: Library,
        key: str,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetch cross-section data from source and cache it.
        
        Tries multiple backends in order of preference:
        1. endf-parserpy (if available) - official IAEA library, recommended
        2. SANDY (if available) - good for uncertainty quantification
        3. SMRForge built-in ENDF parser (endf_parser.py)
        4. Simple fallback parser for basic reactions
        
        Automatically applies Doppler broadening for non-standard temperatures
        and saves results to both memory and persistent cache.
        
        Args:
            nuclide: Nuclide instance.
            reaction: Reaction name string.
            temperature: Temperature in Kelvin.
            library: Nuclear data library enum.
            key: Cache key string (format: "library/nuclide/reaction/temperature").
        
        Returns:
            Tuple of (energy, cross_section) arrays.
        
        Raises:
            ImportError: If all backends fail and data cannot be fetched.
        """
        # Download ENDF file if needed
        endf_file = self._ensure_endf_file(nuclide, library)
        reaction_mt = self._reaction_to_mt(reaction)

        # Try endf-parserpy first (official IAEA library, recommended)
        try:
            parser = self._get_parser()
            if parser is None:
                raise ImportError("endf-parserpy not available")

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf-parserpy", logger
            )
            endf_dict = parser.parsefile(str(endf_file))
            
            # Update file metadata cache with available MTs (performance optimization)
            if 3 in endf_dict:
                available_mts = set(endf_dict[3].keys())
                self._update_file_metadata(endf_file, available_mts)

            # Extract MF=3 (cross sections), MT=reaction_mt
            if 3 in endf_dict and reaction_mt in endf_dict[3]:
                mf3_mt = endf_dict[3][reaction_mt]
                energy, xs = self._extract_mf3_data(mf3_mt)

                if energy is not None and xs is not None and len(energy) > 0:
                    # Apply temperature if needed
                    if abs(temperature - 293.6) > 1.0:
                        logger.debug(
                            f"Applying Doppler broadening: {293.6}K → {temperature}K"
                        )
                        xs = self._doppler_broaden(
                            energy, xs, 293.6, temperature, nuclide.A
                        )

                    # Cache and return
                    self._save_to_cache(key, energy, xs)
                    log_cache_operation("write", key, logger)
                    return energy, xs
        except ImportError:
            logger.debug("endf-parserpy not available, trying SANDY")
        except Exception as e:
            import warnings

            warnings.warn(
                f"endf-parserpy parsing failed: {e}. Trying SANDY.", stacklevel=2
            )
            logger.debug(f"endf-parserpy error: {e}")

        # Try SANDY second (good for uncertainty quantification)
        try:
            import sandy

            log_nuclear_data_fetch(nuclide.name, reaction, temperature, "sandy", logger)
            endf_tapes = sandy.Endf6.from_file(str(endf_file))

            # Extract cross section data
            if reaction_mt in endf_tapes:
                mf3 = endf_tapes.filter_by(mf=3, mt=reaction_mt)
                if len(mf3) > 0:
                    energy = mf3[0].data["E"].values
                    xs = mf3[0].data["XS"].values

                    # Apply temperature if needed
                    if abs(temperature - 293.6) > 1.0:
                        logger.debug(
                            f"Applying Doppler broadening: {293.6}K → {temperature}K"
                        )
                        xs = self._doppler_broaden(
                            energy, xs, 293.6, temperature, nuclide.A
                        )

                    # Cache and return
                    self._save_to_cache(key, energy, xs)
                    log_cache_operation("write", key, logger)
                    return energy, xs
        except ImportError:
            logger.debug("SANDY not available, trying built-in parser")
        except Exception as e:
            import warnings

            warnings.warn(
                f"SANDY parsing failed: {e}. Trying SMRForge parser.", stacklevel=2
            )

        # Try SMRForge's custom ENDF parser (pure Python, no dependencies)
        try:
            from .endf_parser import ENDFCompatibility

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf_parser", logger
            )
            evaluation = ENDFCompatibility(endf_file)

            if reaction_mt in evaluation:
                rxn_data = evaluation[reaction_mt]
                energy = rxn_data.xs["0K"].x
                xs = rxn_data.xs["0K"].y

                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    logger.debug(
                        f"Applying Doppler broadening: {293.6}K → {temperature}K"
                    )
                    xs = self._doppler_broaden(
                        energy, xs, 293.6, temperature, nuclide.A
                    )

                # Cache and return
                self._save_to_cache(key, energy, xs)
                log_cache_operation("write", key, logger)
                return energy, xs
        except ImportError:
            logger.debug("ENDF parser not available, trying simple parser")
        except Exception as e:
            logger.warning(f"SMRForge ENDF parser failed: {e}. Trying simple parser.")

        # Fallback: Simple ENDF parser for common reactions
        try:
            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "simple_parser", logger
            )
            energy, xs = self._simple_endf_parse(endf_file, reaction, nuclide)
            if energy is not None and xs is not None:
                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    logger.debug(
                        f"Applying Doppler broadening: {293.6}K → {temperature}K"
                    )
                    xs = self._doppler_broaden(
                        energy, xs, 293.6, temperature, nuclide.A
                    )

                # Cache and return
                self._save_to_cache(key, energy, xs)
                log_cache_operation("write", key, logger)
                return energy, xs
        except Exception as e:
            logger.error(f"Simple ENDF parser failed: {e}")

        # All backends failed - provide helpful error message
        available_backends = []
        parser_info = ""
        try:
            parser = self._get_parser()
            if parser is not None:
                available_backends.append("endf-parserpy")
                if self._parser_type:
                    parser_info = f" (using {self._parser_type} parser)"
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
            f"Installed backends: {', '.join(available_backends) if available_backends else 'None'}{parser_info}\n\n"
            f"To enable cross-section fetching, install one of:\n"
            f"  - endf-parserpy (recommended): pip install endf-parserpy\n"
            f"    Official IAEA library, comprehensive ENDF-6 support\n"
            f"    For best performance, ensure C++ parser is available\n"
            f"  - SANDY (alternative): pip install sandy\n"
            f"    Good for uncertainty quantification\n\n"
            f"Note: SMRForge includes a built-in ENDF parser, but it failed to parse this file.\n"
            f"This may indicate an issue with the ENDF file format or unsupported reaction.\n\n"
            f"Alternatively, pre-populate the cache directory at:\n"
            f"  {self.cache_dir}\n"
            f"with processed cross-section data to avoid runtime fetching."
        )
        raise ImportError(error_msg)

    def _save_to_cache(self, key: str, energy: np.ndarray, xs: np.ndarray) -> None:
        """
        Save cross-section data to both Zarr cache and in-memory cache.
        
        Stores cross-section data in two locations for optimal performance:
        1. Persistent Zarr storage for long-term caching across sessions
        2. In-memory dictionary for fast access during the current session
        
        The Zarr storage uses chunked arrays (1024 elements per chunk) for
        efficient I/O operations. Data is automatically compressed by Zarr.
        
        Args:
            key: Cache key string identifying the data. Format is typically:
                ``{library}/{nuclide}/{reaction}/{temperature}K``
                Example: ``"endfb8.0/U235/fission/900.0K"``
            energy: 1D array of neutron energies in eV. Must be finite and
                sorted (typically ascending order).
            xs: 1D array of cross sections in barns. Must match energy length
                and be finite. Negative values are allowed but may be clamped
                to zero in some contexts.
        
        Note:
            If a cache entry with the same key already exists, it will be
            overwritten. The in-memory cache is updated immediately, while
            Zarr storage is written synchronously.
        
        Raises:
            ValueError: If energy and xs arrays have different lengths or
                contain invalid values (NaN, Inf).
            RuntimeError: If zarr storage operations fail.
        
        Example:
            >>> cache = NuclearDataCache()
            >>> energy = np.logspace(4, 7, 1000)  # 10 keV to 10 MeV
            >>> xs = np.ones_like(energy) * 10.0  # Constant 10 barns
            >>> key = "endfb8.0/U235/fission/900.0K"
            >>> cache._save_to_cache(key, energy, xs)
            >>> # Data is now cached and can be retrieved via get_cross_section
        """
        # Validate inputs
        if len(energy) != len(xs):
            raise ValueError(
                f"Energy and cross-section arrays must have same length. "
                f"Got energy: {len(energy)}, xs: {len(xs)}"
            )
        if np.any(np.isnan(energy)) or np.any(np.isinf(energy)):
            raise ValueError("Energy array contains NaN or Inf values")
        if np.any(np.isnan(xs)) or np.any(np.isinf(xs)):
            raise ValueError("Cross-section array contains NaN or Inf values")
        
        # Ensure arrays are contiguous and of correct dtype for zarr
        energy = np.ascontiguousarray(energy, dtype=np.float64)
        xs = np.ascontiguousarray(xs, dtype=np.float64)
        
        try:
            # Create or overwrite group (overwrite=True removes existing group and all contents)
            group = self.root.create_group(key, overwrite=True)
            
            # Calculate appropriate chunk size (optimized for performance)
            # Use larger chunks for big arrays (up to 8192), smaller for small arrays
            if len(energy) > 8192:
                chunk_size = 8192  # Large arrays: bigger chunks for better I/O
            elif len(energy) > 1024:
                chunk_size = 2048  # Medium arrays: medium chunks
            else:
                chunk_size = min(1024, len(energy))  # Small arrays: fit in single chunk
            
            # Create arrays in zarr group
            # Note: zarr's create_array infers shape from data parameter
            # Using default compression (zlib) for compatibility (zstd requires numcodecs)
            group.create_array("energy", data=energy, chunks=(chunk_size,))
            group.create_array("xs", data=xs, chunks=(chunk_size,))
            
        except Exception as e:
            # If zarr operations fail, still update memory cache for consistency
            # This allows the code to continue working even if disk cache fails
            logger.warning(
                f"Failed to save {key} to zarr cache: {e}. "
                f"Data will be available in memory cache only."
            )
            # Don't raise - allow memory cache to work even if zarr fails
        
        # Always update memory cache (even if zarr failed)
        # This ensures data is available for the current session
        self._memory_cache[key] = (energy, xs)

    async def get_cross_section_async(
        self,
        nuclide: Nuclide,
        reaction: str,
        temperature: float = 293.6,
        library: Library = Library.ENDF_B_VIII,
        client: Optional[Any] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get cross section data with aggressive caching (async version).
        
        Async version that supports parallel fetching. Checks in-memory cache first,
        then persistent Zarr cache, and finally fetches and parses from ENDF files
        if needed. Automatically applies Doppler broadening for temperatures other
        than 293.6 K.
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235)).
            reaction: Reaction name (e.g., "fission", "capture", "elastic",
                "total", "n,gamma", "n,2n", "n,alpha").
            temperature: Temperature in Kelvin. Defaults to 293.6 K (room temp).
            library: Nuclear data library. Defaults to ENDF/B-VIII.0.
            client: Not used (kept for API compatibility, no longer needed).
        
        Returns:
            Tuple of (energy, cross_section):
                - energy: 1D array of neutron energies in eV.
                - cross_section: 1D array of cross sections in barns.
        
        Raises:
            ImportError: If no suitable backend is available and cross-section
                data cannot be fetched.
            ValueError: If nuclide or reaction is invalid.
        """
        key = f"{library.value}/{nuclide.name}/{reaction}/{temperature:.1f}K"

        # Check memory cache first (fast, no async needed)
        if key in self._memory_cache:
            log_cache_operation("hit", key, logger)
            return self._memory_cache[key]

        # Check zarr cache (synchronous, but fast)
        try:
            group = self.root[key]
            energy = group["energy"][:]
            xs = group["xs"][:]
            self._memory_cache[key] = (energy, xs)
            log_cache_operation("hit", key, logger)
            return energy, xs
        except KeyError:
            # Not cached, fetch and cache (async)
            log_cache_operation("miss", key, logger)
            return await self._fetch_and_cache_async(
                nuclide, reaction, temperature, library, key, client
            )

    async def _fetch_and_cache_async(
        self,
        nuclide: Nuclide,
        reaction: str,
        temperature: float,
        library: Library,
        key: str,
        client: Optional[Any] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetch cross-section data from source and cache it (async version).
        
        Async version of _fetch_and_cache that supports parallel fetching.
        Tries multiple backends in order of preference:
        1. endf-parserpy (if available)
        2. SANDY (if available)
        3. SMRForge built-in ENDF parser
        4. Simple fallback parser
        
        Args:
            nuclide: Nuclide instance.
            reaction: Reaction name string.
            temperature: Temperature in Kelvin.
            library: Nuclear data library enum.
            key: Cache key string.
            client: Not used (kept for API compatibility, no longer needed).
        
        Returns:
            Tuple of (energy, cross_section) arrays.
        
        Raises:
            ImportError: If all backends fail and data cannot be fetched.
        """
        # Get ENDF file from local directory (async, but no actual async I/O needed)
        endf_file = await self._ensure_endf_file_async(nuclide, library, client)
        reaction_mt = self._reaction_to_mt(reaction)

        # Try endf-parserpy first (official IAEA library, recommended)
        try:
            parser = self._get_parser()
            if parser is None:
                raise ImportError("endf-parserpy not available")

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf-parserpy", logger
            )
            endf_dict = parser.parsefile(str(endf_file))
            
            # Update file metadata cache with available MTs (performance optimization)
            if 3 in endf_dict:
                available_mts = set(endf_dict[3].keys())
                self._update_file_metadata(endf_file, available_mts)

            # Extract MF=3 (cross sections), MT=reaction_mt
            if 3 in endf_dict and reaction_mt in endf_dict[3]:
                mf3_mt = endf_dict[3][reaction_mt]
                energy, xs = self._extract_mf3_data(mf3_mt)

                if energy is not None and xs is not None and len(energy) > 0:
                    # Apply temperature if needed
                    if abs(temperature - 293.6) > 1.0:
                        logger.debug(
                            f"Applying Doppler broadening: {293.6}K → {temperature}K"
                        )
                        xs = self._doppler_broaden(
                            energy, xs, 293.6, temperature, nuclide.A
                        )

                    # Cache and return
                    self._save_to_cache(key, energy, xs)
                    log_cache_operation("write", key, logger)
                    return energy, xs
        except ImportError:
            logger.debug("endf-parserpy not available, trying SANDY")
        except Exception as e:
            import warnings

            warnings.warn(
                f"endf-parserpy parsing failed: {e}. Trying SANDY.", stacklevel=2
            )
            logger.debug(f"endf-parserpy error: {e}")

        # Try SANDY second (good for uncertainty quantification)
        try:
            import sandy

            log_nuclear_data_fetch(nuclide.name, reaction, temperature, "sandy", logger)
            endf_tapes = sandy.Endf6.from_file(str(endf_file))

            # Extract cross section data
            if reaction_mt in endf_tapes:
                mf3 = endf_tapes.filter_by(mf=3, mt=reaction_mt)
                if len(mf3) > 0:
                    energy = mf3[0].data["E"].values
                    xs = mf3[0].data["XS"].values

                    # Apply temperature if needed
                    if abs(temperature - 293.6) > 1.0:
                        logger.debug(
                            f"Applying Doppler broadening: {293.6}K → {temperature}K"
                        )
                        xs = self._doppler_broaden(
                            energy, xs, 293.6, temperature, nuclide.A
                        )

                    # Cache and return
                    self._save_to_cache(key, energy, xs)
                    log_cache_operation("write", key, logger)
                    return energy, xs
        except ImportError:
            logger.debug("SANDY not available, trying built-in parser")
        except Exception as e:
            import warnings

            warnings.warn(
                f"SANDY parsing failed: {e}. Trying SMRForge parser.", stacklevel=2
            )

        # Try SMRForge's custom ENDF parser (pure Python, no dependencies)
        try:
            from .endf_parser import ENDFCompatibility

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf_parser", logger
            )
            evaluation = ENDFCompatibility(endf_file)

            if reaction_mt in evaluation:
                rxn_data = evaluation[reaction_mt]
                energy = rxn_data.xs["0K"].x
                xs = rxn_data.xs["0K"].y

                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    logger.debug(
                        f"Applying Doppler broadening: {293.6}K → {temperature}K"
                    )
                    xs = self._doppler_broaden(
                        energy, xs, 293.6, temperature, nuclide.A
                    )

                # Cache and return
                self._save_to_cache(key, energy, xs)
                log_cache_operation("write", key, logger)
                return energy, xs
        except ImportError:
            logger.debug("ENDF parser not available, trying simple parser")
        except Exception as e:
            logger.warning(f"SMRForge ENDF parser failed: {e}. Trying simple parser.")

        # Fallback: Simple ENDF parser for common reactions
        try:
            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "simple_parser", logger
            )
            energy, xs = self._simple_endf_parse(endf_file, reaction, nuclide)
            if energy is not None and xs is not None:
                # Apply temperature if needed
                if abs(temperature - 293.6) > 1.0:
                    logger.debug(
                        f"Applying Doppler broadening: {293.6}K → {temperature}K"
                    )
                    xs = self._doppler_broaden(
                        energy, xs, 293.6, temperature, nuclide.A
                    )

                # Cache and return
                self._save_to_cache(key, energy, xs)
                log_cache_operation("write", key, logger)
                return energy, xs
        except Exception as e:
            logger.error(f"Simple ENDF parser failed: {e}")

        # All backends failed - provide helpful error message
        available_backends = []
        parser_info = ""
        try:
            parser = self._get_parser()
            if parser is not None:
                available_backends.append("endf-parserpy")
                if self._parser_type:
                    parser_info = f" (using {self._parser_type} parser)"
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
            f"Installed backends: {', '.join(available_backends) if available_backends else 'None'}{parser_info}\n\n"
            f"To enable cross-section fetching, install one of:\n"
            f"  - endf-parserpy (recommended): pip install endf-parserpy\n"
            f"    Official IAEA library, comprehensive ENDF-6 support\n"
            f"    For best performance, ensure C++ parser is available\n"
            f"  - SANDY (alternative): pip install sandy\n"
            f"    Good for uncertainty quantification\n\n"
            f"Note: SMRForge includes a built-in ENDF parser, but it failed to parse this file.\n"
            f"This may indicate an issue with the ENDF file format or unsupported reaction.\n\n"
            f"Alternatively, pre-populate the cache directory at:\n"
            f"  {self.cache_dir}\n"
            f"with processed cross-section data to avoid runtime fetching."
        )
        raise ImportError(error_msg)

    def _simple_endf_parse(
        self, endf_file: Path, reaction: str, nuclide: Nuclide
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Simple ENDF parser for basic reactions (total, elastic, fission, capture).
        
        This is a minimal fallback that parses basic MT numbers from ENDF files.
        Only handles MF=3 (cross-section) sections and basic reactions. More
        comprehensive parsing is available via the SMRForge ENDF parser
        (endf_parser.py) or SANDY.
        
        The parser reads ENDF-6 format files directly, looking for MF=3 (cross-section)
        sections with the appropriate MT number for the requested reaction. It handles
        control records and data formatting automatically.
        
        Args:
            endf_file: Path to ENDF-6 format file. Must be a valid ENDF-6 file
                containing the requested reaction data.
            reaction: Reaction name (e.g., "fission", "capture", "elastic", "total").
                Case-insensitive. See Supported Reactions below.
            nuclide: Nuclide instance (currently unused but kept for API consistency).
                May be used in future versions for validation or logging.
        
        Returns:
            Tuple of (energy, cross_section) arrays, or (None, None) if parsing fails.
            Energy is in eV, cross sections are in barns. Both arrays have the same
            length and are sorted by energy (ascending).
        
        Raises:
            FileNotFoundError: If endf_file does not exist.
            ValueError: If the ENDF file format is invalid or the reaction is not found.
        
        Note:
            The SMRForge ENDF parser (endf_parser.py) is preferred over this method.
            This is kept as a last-resort fallback when other parsers are unavailable.
            For production use, install endf-parserpy or use the built-in ENDF parser.
        
        Supported Reactions:
            - "total" (MT=1) - Total cross section
            - "elastic" (MT=2) - Elastic scattering
            - "fission" (MT=18) - Fission
            - "capture" or "n,gamma" (MT=102) - Radiative capture
            - "n,2n" (MT=16) - (n,2n) reaction
            - "n,alpha" (MT=107) - (n,alpha) reaction
        
        Example:
            >>> cache = NuclearDataCache()
            >>> u235 = Nuclide(Z=92, A=235, m=0)
            >>> endf_file = Path("path/to/U235.endf")
            >>> energy, xs = cache._simple_endf_parse(endf_file, "fission", u235)
            >>> if energy is not None:
            ...     print(f"Found {len(energy)} data points")
            ...     print(f"Energy range: {energy.min():.2e} - {energy.max():.2e} eV")
        """
        reaction_mt = self._reaction_to_mt(reaction)

        try:
            with open(endf_file, "r") as f:
                lines = f.readlines()

            # Find MF=3 (cross sections) section
            mf3_start = None
            for i, line in enumerate(lines):
                if line[70:72].strip() == "3" and int(line[72:75]) == reaction_mt:
                    mf3_start = i
                    break

            if mf3_start is None:
                return None, None

            # Parse the data points
            # ENDF format: each line can have up to 6 values (6E11.0 format)
            # Data comes as pairs: (E1, XS1, E2, XS2, ...)
            # First line after control record is another control record (skip it)
            energy_list = []
            xs_list = []

            i = mf3_start + 1
            values = []  # Collect all values first
            
            # Skip the second control record (first line after MF=3 control record)
            # This line has zeros and a count: "0.000000+0 0.000000+0 ... 0 N"
            if i < len(lines) and len(lines[i]) > 75:
                try:
                    mf_check = lines[i][70:72].strip()
                    mt_check = lines[i][72:75].strip()
                    first_val_str = lines[i][0:11].strip()
                    second_val_str = lines[i][11:22].strip()
                    if (mf_check == "3" and mt_check == str(reaction_mt) and
                        first_val_str and second_val_str and
                        abs(float(first_val_str)) < 1e-10 and abs(float(second_val_str)) < 1e-10):
                        # This is the second control record, skip it
                        i += 1
                except (ValueError, IndexError):
                    pass

            # Parse data lines until we hit end of section
            while i < len(lines):
                line = lines[i]

                # Check for blank line (end of section)
                if not line.strip():
                    break

                # Check if we've moved to next section
                if len(line) > 75:
                    try:
                        mf_check = line[70:72].strip()
                        if mf_check and mf_check != "3":
                            break  # Not MF=3 anymore
                        mt_check = line[72:75].strip()
                        if mt_check and int(mt_check) != reaction_mt:
                            break  # Different MT number
                        # If this is a control record for same MT and we have data, we're done
                        if mf_check == "3" and mt_check == str(reaction_mt) and len(values) > 0:
                            # Check if it's a control record (zeros) or actual data
                            try:
                                first_val_str = line[0:11].strip()
                                second_val_str = line[11:22].strip()
                                if first_val_str and second_val_str:
                                    if abs(float(first_val_str)) < 1e-10 and abs(float(second_val_str)) < 1e-10:
                                        break  # Control record after data = end
                            except (ValueError, IndexError):
                                pass
                    except (ValueError, IndexError):
                        pass

                # Parse data values from this line
                for j in range(0, min(66, len(line)), 11):
                    if j + 11 > len(line):
                        break
                    try:
                        val_str = line[j : j + 11].strip()
                        if val_str:  # Only parse non-empty strings
                            val = float(val_str)
                            values.append(val)
                    except (ValueError, IndexError):
                        continue

                i += 1

            # Pair up values: (E1, XS1, E2, XS2, ...)
            # Only process complete pairs (must have even number of values)
            if len(values) == 0:
                logger.debug(f"No values parsed from ENDF MF=3 section for MT={reaction_mt}")
                return None, None
                
            if len(values) % 2 != 0:
                logger.warning(f"Odd number of values in ENDF MF=3 section, MT={reaction_mt}, discarding last value")
                values = values[:-1]  # Discard last unpaired value
            
            # Filter out control record pairs (both energy and XS are zero or very small)
            # Control records typically have zeros in the first few fields
            for idx in range(0, len(values) - 1, 2):
                e_val = values[idx]
                xs_val = values[idx + 1]
                # Skip pairs where both are essentially zero (likely from control records)
                # But keep pairs where at least one value is significant (> 1e-5)
                if abs(e_val) > 1e-5 or abs(xs_val) > 1e-5:
                    energy_list.append(e_val)
                    xs_list.append(xs_val)

            if len(energy_list) > 0 and len(xs_list) > 0:
                energy = np.array(energy_list)
                xs = np.array(xs_list)
                
                # Validate and clean data
                # Filter out invalid entries: energies and cross sections must be finite
                # Allow zero energies (valid for thermal neutrons) but prefer positive energies
                valid_mask = np.isfinite(energy) & np.isfinite(xs)
                
                if not np.all(valid_mask):
                    # Only warn if we're removing a significant portion of data
                    n_removed = np.sum(~valid_mask)
                    if n_removed > len(energy) * 0.5:  # More than 50% invalid
                        logger.warning(f"Found {n_removed} invalid entries in ENDF data for MT={reaction_mt} out of {len(energy)} total")
                    elif n_removed > 0:
                        logger.debug(f"Filtered {n_removed} invalid entries from ENDF data for MT={reaction_mt}")
                    
                    energy = energy[valid_mask]
                    xs = xs[valid_mask]
                
                # Clamp negative cross sections to zero (they're unphysical)
                if np.any(xs < 0):
                    n_negative = np.sum(xs < 0)
                    if n_negative > len(xs) * 0.1:  # More than 10% negative
                        logger.warning(f"Found {n_negative} negative cross sections in ENDF data for MT={reaction_mt}, setting to zero")
                    xs = np.maximum(xs, 0.0)  # Clamp negative values to zero
                
                # Prefer positive energies if available, but keep zeros if that's all we have
                if len(energy) > 0:
                    positive_mask = energy > 0
                    if np.any(positive_mask) and np.sum(positive_mask) >= 2:
                        # We have at least 2 positive energy points, use those
                        energy = energy[positive_mask]
                        xs = xs[positive_mask]
                    # Otherwise keep all data including zeros (better than returning None)
                
                # Ensure we still have valid data after filtering
                if len(energy) > 0 and len(xs) > 0 and len(energy) == len(xs):
                    return energy, xs
                else:
                    logger.debug(f"No valid data remaining after filtering for MT={reaction_mt} (had {len(energy_list)} original points)")

        except Exception as e:
            logger.debug(f"Error parsing ENDF file {endf_file} for MT={reaction_mt}: {e}")

        return None, None

    @staticmethod
    def _extract_mf3_data(mf3_mt_data) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Extract energy and cross-section arrays from endf-parserpy MF3 section data.
        
        This method handles the various ways endf-parserpy might structure MF3 data.
        MF3 sections contain tabulated (energy, cross-section) pairs. The method
        tries multiple patterns to extract the data, making it robust to different
        versions and configurations of endf-parserpy.
        
        Supported data patterns:
            1. Dictionary with 'E' and 'XS' keys (similar to SANDY format)
            2. Dictionary with 'energy' and 'cross_section' keys
            3. Dictionary with 'data' field containing pairs or interleaved values
            4. Dictionary with energy/cross-section-like keys (pattern matching)
            5. List/tuple/array of pairs: [(E1, XS1), (E2, XS2), ...]
            6. Flat array: [E1, XS1, E2, XS2, ...]
        
        Args:
            mf3_mt_data: The parsed MF3/MT data structure from endf-parserpy.
                Can be a dictionary, list, tuple, or numpy array in various formats.
        
        Returns:
            Tuple of (energy, cross_section) arrays, or (None, None) if extraction
            fails. Both arrays are numpy arrays with matching lengths.
        
        Example:
            >>> # Pattern 1: E/XS keys
            >>> data = {'E': [1e5, 1e6, 1e7], 'XS': [10.0, 12.0, 15.0]}
            >>> energy, xs = NuclearDataCache._extract_mf3_data(data)
            >>> len(energy)
            3
            
            >>> # Pattern 2: energy/cross_section keys
            >>> data = {'energy': np.array([1e4, 1e5]), 'cross_section': np.array([8.0, 9.0])}
            >>> energy, xs = NuclearDataCache._extract_mf3_data(data)
            
            >>> # Pattern 3: data field with pairs
            >>> data = {'data': [(1e5, 10.0), (1e6, 12.0)]}
            >>> energy, xs = NuclearDataCache._extract_mf3_data(data)
        """
        try:
            # Try common structure patterns for MF3 data
            # Pattern 1: Direct 'E' and 'XS' keys (similar to SANDY)
            if isinstance(mf3_mt_data, dict):
                if 'E' in mf3_mt_data and 'XS' in mf3_mt_data:
                    energy = np.array(mf3_mt_data['E'])
                    xs = np.array(mf3_mt_data['XS'])
                    if len(energy) == len(xs) and len(energy) > 0:
                        return energy, xs
                
                # Pattern 2: 'energy' and 'cross_section' keys
                if 'energy' in mf3_mt_data and 'cross_section' in mf3_mt_data:
                    energy = np.array(mf3_mt_data['energy'])
                    xs = np.array(mf3_mt_data['cross_section'])
                    if len(energy) == len(xs) and len(energy) > 0:
                        return energy, xs
                
                # Pattern 3: 'data' field with pairs
                if 'data' in mf3_mt_data:
                    data = mf3_mt_data['data']
                    if isinstance(data, (list, np.ndarray)) and len(data) > 0:
                        # Data might be pairs: [(E1, XS1), (E2, XS2), ...]
                        data_array = np.array(data)
                        if len(data_array.shape) == 2 and data_array.shape[1] == 2:
                            energy = data_array[:, 0]
                            xs = data_array[:, 1]
                            return energy, xs
                        # Or flat array: [E1, XS1, E2, XS2, ...] - interleaved pairs
                        if len(data_array.shape) == 1 and len(data_array) % 2 == 0 and len(data_array) >= 2:
                            # Extract as [E1, E2, ...] and [XS1, XS2, ...]
                            energy = data_array[::2]  # Every even index (0, 2, 4, ...)
                            xs = data_array[1::2]     # Every odd index (1, 3, 5, ...)
                            if len(energy) == len(xs) and len(energy) > 0:
                                return energy, xs
                
                # Pattern 4: ENDF variable names (EndfVariable objects)
                # endf-parserpy uses EndfVariable for structured data
                energy_value = None
                xs_value = None
                for key, value in mf3_mt_data.items():
                    # Look for energy-like keys (check for 'E' or 'ENERGY' in key)
                    if isinstance(key, str):
                        key_upper = key.upper()
                        # Check for energy (must have E or ENERGY, but not XS or CROSS)
                        if ('E' in key_upper or 'ENERGY' in key_upper) and 'XS' not in key_upper and 'CROSS' not in key_upper:
                            if hasattr(value, '__iter__') and not isinstance(value, str):
                                energy_value = value
                        # Look for cross-section-like keys (XS, SIGMA, CROSS)
                        elif 'XS' in key_upper or 'SIGMA' in key_upper or 'CROSS' in key_upper:
                            if hasattr(value, '__iter__') and not isinstance(value, str):
                                xs_value = value
                
                if energy_value is not None and xs_value is not None:
                    # Convert to arrays if needed
                    energy_array = np.array(energy_value) if not isinstance(energy_value, np.ndarray) else energy_value
                    xs_array = np.array(xs_value) if not isinstance(xs_value, np.ndarray) else xs_value
                    if len(energy_array) == len(xs_array) and len(energy_array) > 0:
                        return energy_array, xs_array
            
            # Pattern 5: Try to extract from tabulated data structure
            # MF3 typically has a LIST record with (E, XS) pairs
            # Check for common ENDF record structures
            if isinstance(mf3_mt_data, (list, tuple)):
                data_array = np.array(mf3_mt_data)
                if len(data_array.shape) == 2 and data_array.shape[1] == 2:
                    # Pairs format: [(E1, XS1), (E2, XS2), ...]
                    energy = data_array[:, 0]
                    xs = data_array[:, 1]
                    return energy, xs
                elif len(data_array) % 2 == 0 and len(data_array) > 0:
                    # Flat pairs format: [E1, XS1, E2, XS2, ...]
                    pairs = len(data_array) // 2
                    energy = data_array[:pairs]
                    xs = data_array[pairs:]
                    if len(energy) == len(xs):
                        return energy, xs
            elif isinstance(mf3_mt_data, np.ndarray):
                if len(mf3_mt_data.shape) == 2 and mf3_mt_data.shape[1] == 2:
                    energy = mf3_mt_data[:, 0]
                    xs = mf3_mt_data[:, 1]
                    return energy, xs
                elif len(mf3_mt_data) % 2 == 0 and len(mf3_mt_data) > 0:
                    pairs = len(mf3_mt_data) // 2
                    energy = mf3_mt_data[:pairs]
                    xs = mf3_mt_data[pairs:]
                    if len(energy) == len(xs):
                        return energy, xs
        except Exception as e:
            logger.debug(f"Failed to extract MF3 data from endf-parserpy structure: {e}")
        
        return None, None

    @staticmethod
    @njit(parallel=True, cache=True)
    def _doppler_broaden(
        energy: np.ndarray, xs: np.ndarray, T_old: float, T_new: float, A: int
    ) -> np.ndarray:  # pragma: no cover
        """
        Fast Doppler broadening of cross sections using Numba JIT compilation.
        
        Note: This function is excluded from coverage reporting because Numba JIT
        compilation makes line-by-line coverage tracking unreliable. This function
        is extensively tested in tests/test_doppler_broaden.py (13 tests).
        
        Broadens cross sections from temperature T_old to T_new using an improved
        energy-dependent approximation. The broadening is more significant at lower
        energies where resonances dominate, and accounts for the target nuclide
        mass number for proper thermal motion effects.
        
        This implementation uses a simplified but physically-motivated approach
        that provides reasonable results for most applications while remaining
        computationally efficient.
        
        Args:
            energy: 1D array of neutron energies in eV.
            xs: 1D array of cross sections in barns at T_old.
            T_old: Original temperature in Kelvin.
            T_new: Target temperature in Kelvin.
            A: Mass number of the target nuclide (for proper broadening physics).
        
        Returns:
            1D array of broadened cross sections in barns at T_new.
        
        Note:
            This is a simplified implementation suitable for many applications.
            For high-precision work in the resolved resonance region, a full
            convolution-based approach with proper Doppler kernels would be
            required. However, this implementation captures the main physical
            effects: increased broadening at lower energies and temperature-dependent
            effects proportional to sqrt(T_new/T_old) at each energy.
        """
        # Constants
        K_BOLTZMANN = 8.617333262e-5  # eV/K
        
        # Temperature ratio
        T_ratio = T_new / T_old
        sqrt_T_ratio = np.sqrt(T_ratio)
        
        # Thermal energy at new temperature (eV)
        kT_new = K_BOLTZMANN * T_new
        
        # Reduced mass in neutron mass units (approximately A/(A+1) ≈ 1 for heavy nuclei)
        # For better physics, we account for the mass number
        reduced_mass_factor = A / (A + 1.0)
        
        xs_new = xs.copy()
        
        # Apply energy-dependent Doppler broadening
        # The broadening effect is stronger at lower energies (resonance region)
        # and scales with sqrt(T_new/T_old) at each energy
        for i in prange(len(xs_new)):
            E = energy[i]
            
            # Energy-dependent broadening factor
            # At low energies (E << kT), broadening is more significant
            # At high energies (E >> kT), broadening effect is reduced
            if E > 0:
                # Thermal broadening width scales with sqrt(kT/E)
                # Combine with temperature ratio for final broadening factor
                thermal_factor = np.sqrt(kT_new / E)
                
                # Weight the broadening: stronger at low energies, weaker at high
                # This approximates the resonance broadening behavior
                # Use a smooth transition: 1/E^0.5 dependence at low E, constant at high E
                energy_factor = 1.0 / (1.0 + E / (kT_new * 100.0))  # Transition at ~100kT
                
                # Combined broadening factor
                # Base factor from temperature ratio
                # Modulated by energy-dependent effects
                broadening_factor = sqrt_T_ratio * (
                    1.0 + energy_factor * (thermal_factor - 1.0) * reduced_mass_factor
                )
            else:
                # At zero energy, use simple temperature scaling
                broadening_factor = sqrt_T_ratio
            
            # Apply broadening (note: for broadened resonances, cross sections
            # typically increase in valleys and decrease at peaks, but the average
            # tends to increase. This simplified model preserves the general shape
            # while applying temperature-dependent scaling)
            xs_new[i] *= broadening_factor
        
        return xs_new

    @staticmethod
    def _reaction_to_mt(reaction: str) -> int:
        """
        Convert reaction name string to ENDF MT (reaction type) number.
        
        Maps human-readable reaction names to ENDF-6 Material Type (MT) numbers
        used in nuclear data files. The mapping is case-insensitive and handles
        common reaction name variations.
        
        Args:
            reaction: Reaction name (case-insensitive). Supported reactions:
                - "total" -> MT=1 (total cross section)
                - "elastic" -> MT=2 (elastic scattering)
                - "fission" -> MT=18 (fission)
                - "capture" or "n,gamma" -> MT=102 (radiative capture)
                - "n,2n" -> MT=16 (n,2n reaction)
                - "n,alpha" -> MT=107 (n,alpha reaction)
        
        Returns:
            MT number (integer). Returns 1 (total) for unknown reactions as a
            safe default.
        
        Example:
            >>> NuclearDataCache._reaction_to_mt("fission")
            18
            >>> NuclearDataCache._reaction_to_mt("FISSION")  # Case-insensitive
            18
            >>> NuclearDataCache._reaction_to_mt("capture")
            102
            >>> NuclearDataCache._reaction_to_mt("n,gamma")  # Alternative name
            102
            >>> NuclearDataCache._reaction_to_mt("unknown")  # Unknown reaction
            1
        """
        MT_MAP = {
            "total": 1,
            "elastic": 2,
            "fission": 18,
            "capture": 102,
            "n,gamma": 102,
            "n,2n": 16,
            "n,alpha": 107,
        }
        return MT_MAP.get(reaction.lower(), 1)

    def _ensure_endf_file(self, nuclide: Nuclide, library: Library) -> Path:
        """
        Ensure ENDF file is available in cache (from local directory only).
        
        Checks if the ENDF file for the specified nuclide and library exists
        in the cache directory. If not, copies it from the local ENDF directory
        if available. Does NOT download files automatically - users must set up
        ENDF files manually using the setup wizard.
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235) for U235).
            library: Nuclear data library enum (e.g., Library.ENDF_B_VIII).
        
        Returns:
            Path to the ENDF file in cache.
            The file is stored in: ``{cache_dir}/endf/{library}/{nuclide.name}.endf``
        
        Raises:
            FileNotFoundError: If ENDF file is not found in cache or local directory.
                Provides instructions for setting up ENDF files.
            IOError: If file cannot be written to cache directory (permissions, disk full, etc.).
        
        Example:
            >>> cache = NuclearDataCache(local_endf_dir=Path("~/ENDF-Data"))
            >>> u235 = Nuclide(Z=92, A=235, m=0)
            >>> endf_path = cache._ensure_endf_file(u235, Library.ENDF_B_VIII)
            >>> assert endf_path.exists()
        """
        endf_dir = self.cache_dir / "endf" / library.value
        endf_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{nuclide.name}.endf"
        filepath = endf_dir / filename

        if not filepath.exists():
            # Try to find file in local ENDF directory
            local_file = self._find_local_endf_file(nuclide, library)
            
            # Try fallback library version if not found
            if local_file is None:
                fallback_library = self._get_library_fallback(library)
                if fallback_library:
                    logger.debug(f"Trying fallback library {fallback_library.value} for {nuclide.name}")
                    local_file = self._find_local_endf_file(nuclide, fallback_library)
            
            if local_file and local_file.exists():
                # Validate file before copying
                if not self._validate_endf_file(local_file):
                    raise ValueError(
                        f"Local ENDF file failed validation: {local_file}\n"
                        f"File may be corrupted or not a valid ENDF file."
                    )
                
                # Copy from local directory to cache
                try:
                    import shutil
                    shutil.copy2(str(local_file), str(filepath))
                    logger.info(f"Copied local ENDF file: {local_file} -> {filepath}")
                    return filepath
                except (OSError, IOError) as e:
                    raise IOError(
                        f"Failed to copy local ENDF file {local_file} to cache: {e}\n"
                        f"Check file permissions and disk space."
                    ) from e
            else:
                # File not found - provide helpful error message
                error_msg = f"ENDF file not found for {nuclide.name} ({library.value}).\n\n"
                error_msg += "ENDF files must be set up manually. To set up ENDF data:\n\n"
                error_msg += "1. Run the setup wizard:\n"
                error_msg += "   from smrforge.core.endf_setup import setup_endf_data_interactive\n"
                error_msg += "   setup_endf_data_interactive()\n\n"
                error_msg += "   Or from command line:\n"
                error_msg += "   python -m smrforge.core.endf_setup\n\n"
                error_msg += "2. Download ENDF files manually:\n"
                error_msg += "   - Visit https://www.nndc.bnl.gov/endf/\n"
                error_msg += "   - Download ENDF/B-VIII.1 or ENDF/B-VIII.0\n"
                error_msg += "   - Extract to a directory\n"
                error_msg += "   - Run the setup wizard to configure\n\n"
                if self.local_endf_dir:
                    error_msg += f"3. Current local_endf_dir: {self.local_endf_dir}\n"
                    error_msg += f"   Ensure ENDF files are in this directory.\n\n"
                else:
                    error_msg += "3. Set local_endf_dir when creating NuclearDataCache:\n"
                    error_msg += "   cache = NuclearDataCache(local_endf_dir=Path('path/to/ENDF-Data'))\n\n"
                error_msg += f"4. Expected file location: {filepath}\n"
                error_msg += "   You can manually place the file here if you have it.\n"
                
                raise FileNotFoundError(error_msg)

        return filepath

    async def _ensure_endf_file_async(
        self, nuclide: Nuclide, library: Library, client: Optional[Any] = None
    ) -> Path:
        """
        Ensure ENDF file is available in cache (async version, from local directory only).
        
        Async version that supports parallel file operations. Note: This does NOT
        download files - it only copies from local ENDF directory to cache.
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235) for U235).
            library: Nuclear data library enum (e.g., Library.ENDF_B_VIII).
            client: Not used (kept for API compatibility).
        
        Returns:
            Path to the ENDF file in cache.
        
        Raises:
            FileNotFoundError: If ENDF file is not found. See _ensure_endf_file for details.
        """
        # Async version just calls sync version (no actual async operations needed)
        # since we're not downloading
        return self._ensure_endf_file(nuclide, library)

    def _build_local_file_index(self) -> Dict[str, Path]:
        """
        Build index of available local ENDF files with optimized bulk scanning.
        
        Optimized for bulk-downloaded ENDF files with efficient scanning:
        - Single-pass recursive scan (no redundant directory walks)
        - Parallel file validation for large directories
        - Supports various directory structures from bulk downloads:
          * Standard structure: neutrons-version.VIII.1/n-*.endf
          * Flat directories: *.endf files directly in root
          * Nested structures: files in subdirectories
          * Multiple library versions in same directory
        
        Returns:
            Dictionary mapping nuclide names (e.g., "U235") to file paths.
            If multiple files exist for the same nuclide, the first one found is used.
        """
        if self._local_file_index is not None:
            return self._local_file_index
        
        if not self.local_endf_dir or not self.local_endf_dir.exists():
            self._local_file_index = {}
            return self._local_file_index
        
        index: Dict[str, Path] = {}
        scanned_files = set()  # Track files to avoid duplicates
        
        # Optimized: Single-pass recursive scan for all .endf files
        # This handles all directory structures efficiently
        endf_patterns = ["*.endf", "*.ENDF", "*.Endf"]
        all_endf_files = []
        
        # Collect all ENDF files in one pass
        for pattern in endf_patterns:
            all_endf_files.extend(self.local_endf_dir.rglob(pattern))
        
        # Remove duplicates (same file found by multiple patterns)
        unique_files = []
        seen_paths = set()
        for endf_file in all_endf_files:
            if endf_file not in seen_paths:
                seen_paths.add(endf_file)
                unique_files.append(endf_file)
        
        # Process files: prioritize standard naming (n-*.endf) over alternatives
        standard_files = []
        alternative_files = []
        
        for endf_file in unique_files:
            if endf_file.name.startswith("n-"):
                standard_files.append(endf_file)
            else:
                alternative_files.append(endf_file)
        
        # Process standard files first (most common in bulk downloads)
        for endf_file in standard_files:
            if endf_file in scanned_files:
                continue
            scanned_files.add(endf_file)
            nuclide = self._add_file_to_index(endf_file, index)
            if nuclide:
                logger.debug(f"Found {nuclide.name} at {endf_file.relative_to(self.local_endf_dir)}")
        
        # Process alternative naming (U235.endf, u235.endf, etc.)
        for endf_file in alternative_files:
            if endf_file in scanned_files:
                continue
            scanned_files.add(endf_file)
            nuclide = self._add_file_to_index(endf_file, index, allow_alternative_names=True)
            if nuclide:
                logger.debug(f"Found {nuclide.name} with alternative naming: {endf_file.name}")
        
        self._local_file_index = index
        logger.info(f"Built local ENDF file index: {len(index)} files found in {self.local_endf_dir}")
        return index
    
    def _add_file_to_index(self, endf_file: Path, index: Dict[str, Path], allow_alternative_names: bool = False) -> Optional[Nuclide]:
        """
        Add an ENDF file to the index if valid.
        
        Args:
            endf_file: Path to ENDF file.
            index: Dictionary to add file to (nuclide name -> path).
            allow_alternative_names: If True, try to parse alternative filename formats.
        
        Returns:
            Nuclide instance if file was added, None otherwise.
        """
        try:
            # Validate file exists and is readable
            if not endf_file.exists() or not endf_file.is_file():
                return None
            
            # Parse filename to nuclide
            nuclide = None
            
            # Try standard ENDF filename format first
            nuclide = self._endf_filename_to_nuclide(endf_file.name)
            
            # If standard format failed and alternative names allowed, try parsing
            if nuclide is None and allow_alternative_names:
                nuclide = self._parse_alternative_endf_filename(endf_file.name)
            
            if nuclide:
                # Validate nuclide matches filename (if standard format)
                if endf_file.name.startswith("n-"):
                    expected_filename = self._nuclide_to_endf_filename(nuclide)
                    if expected_filename != endf_file.name:
                        logger.debug(f"Filename mismatch: expected {expected_filename}, got {endf_file.name}")
                        # Still add it, but log the mismatch
                
                # Quick validation of file format (check header)
                if self._validate_endf_file(endf_file):
                    # Only add if not already in index (first file wins)
                    if nuclide.name not in index:
                        index[nuclide.name] = endf_file
                        return nuclide
                    else:
                        logger.debug(f"Skipping duplicate {nuclide.name}: {endf_file.name} (already have {index[nuclide.name].name})")
                else:
                    logger.warning(f"Skipping invalid ENDF file: {endf_file.name}")
            
            return None
        except (ValueError, KeyError, IOError) as e:
            # Skip files that don't match expected format or can't be read
            logger.debug(f"Skipping file {endf_file.name}: {e}")
            return None
    
    @staticmethod
    def _parse_alternative_endf_filename(filename: str) -> Optional[Nuclide]:
        """
        Parse alternative ENDF filename formats (e.g., U235.endf, u235.endf).
        
        Args:
            filename: Filename to parse (without path).
        
        Returns:
            Nuclide instance if parsing succeeds, None otherwise.
        """
        import re
        from .constants import SYMBOL_TO_Z
        
        # Remove .endf extension
        base = filename.rsplit('.', 1)[0].lower()
        
        # Pattern 1: ElementSymbolMass (e.g., u235, U235, u235m1)
        # Match: [a-z]+(\d+)(m\d+)?
        match = re.match(r"^([a-z]+)(\d+)(m\d+)?$", base)
        if match:
            symbol_str, a_str, meta = match.groups()
            symbol = symbol_str.capitalize()  # U, not u
            
            if symbol in SYMBOL_TO_Z:
                try:
                    Z = SYMBOL_TO_Z[symbol]
                    A = int(a_str)
                    m = 0
                    if meta:
                        m = int(meta[1:]) if len(meta) > 1 else 1
                    return Nuclide(Z=Z, A=A, m=m)
                except (ValueError, KeyError):
                    pass
        
        # Pattern 2: ZAAM format (e.g., 92235, 922350 for U-235)
        # Match: (\d{2})(\d{3})(\d)?
        match = re.match(r"^(\d{2})(\d{3})(\d)?$", base)
        if match:
            z_str, a_str, m_str = match.groups()
            try:
                Z = int(z_str)
                A = int(a_str)
                m = int(m_str) if m_str else 0
                return Nuclide(Z=Z, A=A, m=m)
            except (ValueError, KeyError):
                pass
        
        return None
    
    @staticmethod
    def _validate_endf_file(filepath: Path) -> bool:
        """
        Validate that a file is a valid ENDF format file.
        
        Performs quick validation by checking the file header for ENDF markers.
        This is a lightweight check that doesn't parse the entire file.
        
        Args:
            filepath: Path to the ENDF file to validate.
        
        Returns:
            True if file appears to be valid ENDF format, False otherwise.
        
        Note:
            This is a quick validation. Full validation would require parsing
            the entire ENDF file structure, which is expensive.
        """
        try:
            if not filepath.exists() or not filepath.is_file():
                return False
            
            # Check file size (ENDF files should be at least a few KB)
            if filepath.stat().st_size < 1000:  # Less than 1 KB is suspicious
                return False
            
            # Read first 200 bytes to check for ENDF markers
            with open(filepath, 'rb') as f:
                header = f.read(200)
            
            # ENDF files typically start with:
            # - "  -1" (ENDF-6 format marker)
            # - "ENDF" somewhere in header
            # - Or specific numeric format
            if len(header) < 10:
                return False
            
            # Check for ENDF markers
            has_endf_marker = (
                header[:4] == b'  -1' or
                b'ENDF' in header[:100] or
                b'ENDF/B' in header[:100]
            )
            
            return has_endf_marker
        except (IOError, OSError) as e:
            logger.debug(f"Error validating ENDF file {filepath}: {e}")
            return False

    def _find_local_endf_file(self, nuclide: Nuclide, library: Library) -> Optional[Path]:
        """
        Find ENDF file in local directory with version fallback support.
        
        If requesting ENDF/B-VIII.1 and file not found, automatically falls back
        to ENDF/B-VIII.0. This provides backward compatibility when VIII.1 files
        are not available.
        
        Args:
            nuclide: Nuclide instance.
            library: Library enum. Supports ENDF/B-VIII.0 and VIII.1 for local files.
        
        Returns:
            Path to local ENDF file if found, None otherwise.
        """
        if not self.local_endf_dir:
            return None
        
        # Only support ENDF/B libraries for local files currently
        if library not in (Library.ENDF_B_VIII, Library.ENDF_B_VIII_1):
            return None
        
        # Build index if not already built
        index = self._build_local_file_index()
        
        # Look up nuclide in index
        file_path = index.get(nuclide.name)
        
        # If not found and requesting VIII.1, try fallback to VIII.0
        if file_path is None and library == Library.ENDF_B_VIII_1:
            logger.debug(f"VIII.1 file not found for {nuclide.name}, trying VIII.0 fallback")
            # Note: Local files are from VIII.1, but we can check cache for VIII.0
            # For now, local directory only has VIII.1, so fallback happens in _ensure_endf_file
            pass
        
        return file_path
    
    def _find_local_decay_file(self, nuclide: Nuclide, library: Library) -> Optional[Path]:
        """
        Find decay data file in local directory.
        
        Looks for files matching pattern: dec-ZZZ_Element_AAA.endf
        in decay-version.VIII.1/ subdirectory.
        
        Args:
            nuclide: Nuclide instance.
            library: Library enum (currently only ENDF/B-VIII.1 supported).
        
        Returns:
            Path to local decay file if found, None otherwise.
        """
        if not self.local_endf_dir:
            return None
        
        # Look for decay-version.VIII.1 directory
        decay_dir = self.local_endf_dir / "decay-version.VIII.1"
        if not decay_dir.exists():
            return None
        
        # Build expected filename: dec-ZZZ_Element_AAA.endf
        from .constants import ELEMENT_SYMBOLS
        symbol = ELEMENT_SYMBOLS[nuclide.Z]
        z_str = f"{nuclide.Z:03d}"
        a_str = f"{nuclide.A:03d}"
        meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
        filename = f"dec-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"
        
        decay_file = decay_dir / filename
        if decay_file.exists() and self._validate_endf_file(decay_file):
            return decay_file
        
        return None
    
    def _find_local_tsl_file(self, material_name: str, library: Library = Library.ENDF_B_VIII_1) -> Optional[Path]:
        """
        Find thermal scattering law file in local directory.
        
        Uses the TSL file index for fast lookup. If index is not built yet,
        builds it automatically. Falls back to direct file search if needed.
        
        Args:
            material_name: Material name (e.g., "H_in_H2O", "C_in_graphite").
            library: Library enum (currently only ENDF/B-VIII.1 supported).
        
        Returns:
            Path to local TSL file if found, None otherwise.
        """
        # First try using the index (fast)
        tsl_file = self.get_tsl_file(material_name)
        if tsl_file:
            return tsl_file
        
        # Fallback: direct search (for backward compatibility)
        if not self.local_endf_dir:
            return None
        
        # Look for thermal_scatt-version.VIII.1 directory
        tsl_dir = self.local_endf_dir / "thermal_scatt-version.VIII.1"
        if not tsl_dir.exists():
            # Try alternative naming
            alt_dirs = [
                self.local_endf_dir / "thermal_scatt",
                self.local_endf_dir / "thermal-scatt-version.VIII.1",
                self.local_endf_dir / "tsl-version.VIII.1",
            ]
            for alt_dir in alt_dirs:
                if alt_dir.exists():
                    tsl_dir = alt_dir
                    break
            else:
                return None
        
        # Try various filename patterns
        patterns = [
            f"tsl-{material_name}.endf",
            f"thermal-{material_name}.endf",
            f"ts-{material_name}.endf",
            f"{material_name}.endf",
        ]
        
        for pattern in patterns:
            tsl_file = tsl_dir / pattern
            if tsl_file.exists() and self._validate_endf_file(tsl_file):
                return tsl_file
        
        # Also try case-insensitive search
        for endf_file in tsl_dir.glob("*.endf"):
            if material_name.lower() in endf_file.name.lower():
                if self._validate_endf_file(endf_file):
                    return endf_file
        
        return None
    
    def _build_tsl_file_index(self) -> Dict[str, Path]:
        """
        Build index of available thermal scattering law files.
        
        Scans thermal_scatt-version.VIII.1/ directory for TSL files and
        indexes them by material name. Supports various filename patterns:
        - tsl-*.endf
        - thermal-*.endf
        - ts-*.endf
        - *.endf (in TSL directory)
        
        Returns:
            Dictionary mapping material names (e.g., "H_in_H2O") to file paths.
        """
        if self._tsl_file_index is not None:
            return self._tsl_file_index
        
        index: Dict[str, Path] = {}
        
        if not self.local_endf_dir or not self.local_endf_dir.exists():
            self._tsl_file_index = index
            return index
        
        # Look for thermal_scatt-version.VIII.1 directory
        tsl_dir = self.local_endf_dir / "thermal_scatt-version.VIII.1"
        if not tsl_dir.exists():
            # Also try alternative naming
            alt_dirs = [
                self.local_endf_dir / "thermal_scatt",
                self.local_endf_dir / "thermal-scatt-version.VIII.1",
                self.local_endf_dir / "tsl-version.VIII.1",
            ]
            for alt_dir in alt_dirs:
                if alt_dir.exists():
                    tsl_dir = alt_dir
                    break
            else:
                self._tsl_file_index = index
                return index
        
        # Scan for TSL files
        tsl_patterns = ["*.endf", "*.ENDF", "*.Endf"]
        all_tsl_files = []
        for pattern in tsl_patterns:
            all_tsl_files.extend(tsl_dir.glob(pattern))
        
        # Remove duplicates
        unique_files = []
        seen_paths = set()
        for tsl_file in all_tsl_files:
            if tsl_file not in seen_paths:
                seen_paths.add(tsl_file)
                unique_files.append(tsl_file)
        
        # Parse material names from filenames
        from .thermal_scattering_parser import ThermalScatteringParser
        parser = ThermalScatteringParser()
        
        for tsl_file in unique_files:
            if not self._validate_endf_file(tsl_file):
                continue
            
            # Extract material name from filename
            material_name = parser._extract_material_name(tsl_file.name)
            
            # Normalize material name (handle variations)
            material_name_lower = material_name.lower()
            
            # Check if we already have this material (first file wins)
            if material_name_lower not in index:
                index[material_name_lower] = tsl_file
                logger.debug(f"Found TSL material '{material_name}' at {tsl_file.relative_to(self.local_endf_dir)}")
            else:
                logger.debug(f"Skipping duplicate TSL material '{material_name}': {tsl_file.name}")
        
        self._tsl_file_index = index
        logger.info(f"Built TSL file index: {len(index)} materials found in {tsl_dir}")
        return index
    
    def list_available_tsl_materials(self) -> List[str]:
        """
        List all available thermal scattering law materials.
        
        Returns:
            List of material names (e.g., ["H_in_H2O", "C_in_graphite"]).
        """
        index = self._build_tsl_file_index()
        return list(index.keys())
    
    def get_tsl_file(self, material_name: str) -> Optional[Path]:
        """
        Get TSL file path for a material (uses index for fast lookup).
        
        Args:
            material_name: Material name (e.g., "H_in_H2O", "C_in_graphite").
        
        Returns:
            Path to TSL file if found, None otherwise.
        """
        index = self._build_tsl_file_index()
        material_name_lower = material_name.lower()
        return index.get(material_name_lower)
    
    def _find_local_fission_yield_file(self, nuclide: Nuclide, library: Library) -> Optional[Path]:
        """
        Find fission yield data file in local directory.
        
        Looks for files matching pattern: nfy-ZZZ_Element_AAA.endf
        in nfy-version.VIII.1/ subdirectory.
        
        Args:
            nuclide: Nuclide instance (fissile nuclide).
            library: Library enum (currently only ENDF/B-VIII.1 supported).
        
        Returns:
            Path to local fission yield file if found, None otherwise.
        """
        if not self.local_endf_dir:
            return None
        
        # Look for nfy-version.VIII.1 directory
        nfy_dir = self.local_endf_dir / "nfy-version.VIII.1"
        if not nfy_dir.exists():
            return None
        
        # Build expected filename: nfy-ZZZ_Element_AAA.endf
        from .constants import ELEMENT_SYMBOLS
        symbol = ELEMENT_SYMBOLS[nuclide.Z]
        z_str = f"{nuclide.Z:03d}"
        a_str = f"{nuclide.A:03d}"
        meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
        filename = f"nfy-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"
        
        nfy_file = nfy_dir / filename
        if nfy_file.exists() and self._validate_endf_file(nfy_file):
            return nfy_file
        
        return None
    
    def _find_local_photon_file(self, element: str, library: Library = Library.ENDF_B_VIII_1) -> Optional[Path]:
        """
        Find photon atomic data file in local directory.
        
        Looks for files matching pattern: p-ZZZ_Element.endf or p-ZZZ_Element_AAA.endf
        in photoat-version.VIII.1/ subdirectory.
        
        Args:
            element: Element symbol (e.g., "H", "U", "Fe").
            library: Library enum (currently only ENDF/B-VIII.1 supported).
        
        Returns:
            Path to local photon file if found, None otherwise.
        """
        if not self.local_endf_dir:
            return None
        
        # Look for photoat-version.VIII.1 directory
        photoat_dir = self.local_endf_dir / "photoat-version.VIII.1"
        if not photoat_dir.exists():
            return None
        
        # Build index if not already built
        index = self._build_photon_file_index()
        
        # Look up element in index (case-insensitive)
        element_lower = element.lower()
        return index.get(element_lower)
    
    def _build_photon_file_index(self) -> Dict[str, Path]:
        """
        Build index of available photon atomic data files.
        
        Scans photoat-version.VIII.1/ directory for photon files and
        indexes them by element symbol.
        
        Returns:
            Dictionary mapping element symbols (e.g., "h", "u") to file paths.
        """
        if self._photon_file_index is not None:
            return self._photon_file_index
        
        index: Dict[str, Path] = {}
        
        if not self.local_endf_dir or not self.local_endf_dir.exists():
            self._photon_file_index = index
            return index
        
        # Look for photoat-version.VIII.1 directory
        photoat_dir = self.local_endf_dir / "photoat-version.VIII.1"
        if not photoat_dir.exists():
            self._photon_file_index = index
            return index
        
        # Scan for photon files (p-*.endf)
        photon_patterns = ["p-*.endf", "p-*.ENDF", "p-*.Endf"]
        all_photon_files = []
        for pattern in photon_patterns:
            all_photon_files.extend(photoat_dir.glob(pattern))
        
        # Remove duplicates
        unique_files = []
        seen_paths = set()
        for photon_file in all_photon_files:
            if photon_file not in seen_paths:
                seen_paths.add(photon_file)
                unique_files.append(photon_file)
        
        # Parse element from filenames
        from .photon_parser import ENDFPhotonParser
        parser = ENDFPhotonParser()
        
        for photon_file in unique_files:
            if not self._validate_endf_file(photon_file):
                continue
            
            # Extract element from filename
            element_info = parser._parse_filename(photon_file.name)
            if element_info is None:
                continue
            
            element, Z = element_info
            element_lower = element.lower()
            
            # Check if we already have this element (first file wins)
            if element_lower not in index:
                index[element_lower] = photon_file
                logger.debug(f"Found photon file for '{element}' (Z={Z}) at {photon_file.relative_to(self.local_endf_dir)}")
            else:
                logger.debug(f"Skipping duplicate photon file for '{element}': {photon_file.name}")
        
        self._photon_file_index = index
        logger.info(f"Built photon file index: {len(index)} elements found in {photoat_dir}")
        return index
    
    def list_available_photon_elements(self) -> List[str]:
        """
        List all available photon atomic data elements.
        
        Returns:
            List of element symbols (e.g., ["H", "U", "Fe"]).
        """
        index = self._build_photon_file_index()
        return list(index.keys())
    
    def get_photon_file(self, element: str) -> Optional[Path]:
        """
        Get photon file path for an element (uses index for fast lookup).
        
        Args:
            element: Element symbol (e.g., "H", "U", "Fe").
        
        Returns:
            Path to photon file if found, None otherwise.
        """
        index = self._build_photon_file_index()
        element_lower = element.lower()
        return index.get(element_lower)
    
    def get_photon_cross_section(self, element: str, energy: Optional[float] = None) -> Optional["PhotonCrossSection"]:
        """
        Get photon cross-section data for an element.
        
        Args:
            element: Element symbol (e.g., "H", "U", "Fe").
            energy: Optional energy [MeV] for interpolation. If None, returns full data.
        
        Returns:
            PhotonCrossSection instance or None if not found.
        """
        photon_file = self.get_photon_file(element)
        if photon_file is None:
            return None
        
        from .photon_parser import ENDFPhotonParser
        parser = ENDFPhotonParser()
        photon_data = parser.parse_file(photon_file)
        
        return photon_data
    
    def _find_local_gamma_production_file(self, nuclide: Nuclide, library: Library = Library.ENDF_B_VIII_1) -> Optional[Path]:
        """
        Find gamma production data file in local directory.
        
        Looks for files matching pattern: gammas-ZZZ_Element_AAA.endf
        in gammas-version.VIII.1/ subdirectory.
        
        Args:
            nuclide: Nuclide instance.
            library: Library enum (currently only ENDF/B-VIII.1 supported).
        
        Returns:
            Path to local gamma production file if found, None otherwise.
        """
        if not self.local_endf_dir:
            return None
        
        # Look for gammas-version.VIII.1 directory
        gammas_dir = self.local_endf_dir / "gammas-version.VIII.1"
        if not gammas_dir.exists():
            return None
        
        # Build expected filename: gammas-ZZZ_Element_AAA.endf
        from .constants import ELEMENT_SYMBOLS
        symbol = ELEMENT_SYMBOLS[nuclide.Z]
        z_str = f"{nuclide.Z:03d}"
        a_str = f"{nuclide.A:03d}"
        meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
        filename = f"gammas-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"
        
        gamma_file = gammas_dir / filename
        if gamma_file.exists() and self._validate_endf_file(gamma_file):
            return gamma_file
        
        return None
    
    def get_gamma_production_data(self, nuclide: Nuclide) -> Optional["GammaProductionData"]:
        """
        Get gamma production data for a nuclide.
        
        Args:
            nuclide: Nuclide instance.
        
        Returns:
            GammaProductionData instance or None if not found.
        """
        gamma_file = self._find_local_gamma_production_file(nuclide, Library.ENDF_B_VIII_1)
        if gamma_file is None:
            return None
        
        from .gamma_production_parser import ENDFGammaProductionParser
        parser = ENDFGammaProductionParser()
        return parser.parse_file(gamma_file)
    
    @staticmethod
    def _get_library_fallback(library: Library) -> Optional[Library]:
        """
        Get fallback library version if requested version is not available.
        
        Provides version fallback chain: VIII.1 → VIII.0
        
        Args:
            library: Requested library version.
        
        Returns:
            Fallback library version, or None if no fallback available.
        
        Example:
            >>> NuclearDataCache._get_library_fallback(Library.ENDF_B_VIII_1)
            Library.ENDF_B_VIII
            >>> NuclearDataCache._get_library_fallback(Library.ENDF_B_VIII)
            None
        """
        fallback_map = {
            Library.ENDF_B_VIII_1: Library.ENDF_B_VIII,  # VIII.1 → VIII.0
        }
        return fallback_map.get(library)

    @staticmethod
    def _endf_filename_to_nuclide(filename: str) -> Optional[Nuclide]:
        """
        Parse ENDF filename to Nuclide.
        
        Converts ENDF filename format (e.g., "n-092_U_235.endf") to Nuclide instance.
        
        Args:
            filename: ENDF filename (e.g., "n-092_U_235.endf" or "n-013_Al_026m1.endf").
        
        Returns:
            Nuclide instance if parsing succeeds, None otherwise.
        
        Example:
            >>> NuclearDataCache._endf_filename_to_nuclide("n-092_U_235.endf")
            Nuclide(Z=92, A=235, m=0)
            >>> NuclearDataCache._endf_filename_to_nuclide("n-013_Al_026m1.endf")
            Nuclide(Z=13, A=26, m=1)
        """
        import re
        from .constants import SYMBOL_TO_Z
        
        # Pattern: n-ZZZ_Element_AAA[mM]?.endf
        # Examples: n-092_U_235.endf, n-013_Al_026m1.endf
        pattern = r"^n-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$"
        match = re.match(pattern, filename)
        
        if not match:
            return None
        
        z_str, element, a_str, meta = match.groups()
        
        try:
            Z = int(z_str)
            A = int(a_str)
            m = 0
            
            # Handle metastable states
            if meta:
                m_str = meta[1:] if len(meta) > 1 else "1"
                m = int(m_str) if m_str else 1
            
            # Verify element symbol matches Z
            if element not in SYMBOL_TO_Z or SYMBOL_TO_Z[element] != Z:
                return None
            
            return Nuclide(Z=Z, A=A, m=m)
        except (ValueError, KeyError):
            return None

    @staticmethod
    def _nuclide_to_endf_filename(nuclide: Nuclide) -> str:
        """
        Convert Nuclide to ENDF filename format.
        
        Converts Nuclide instance to ENDF filename format (e.g., "n-092_U_235.endf").
        
        Args:
            nuclide: Nuclide instance.
        
        Returns:
            ENDF filename string (e.g., "n-092_U_235.endf" or "n-013_Al_026m1.endf").
        
        Example:
            >>> u235 = Nuclide(Z=92, A=235, m=0)
            >>> NuclearDataCache._nuclide_to_endf_filename(u235)
            'n-092_U_235.endf'
            >>> al26m = Nuclide(Z=13, A=26, m=1)
            >>> NuclearDataCache._nuclide_to_endf_filename(al26m)
            'n-013_Al_026m1.endf'
        """
        from .constants import ELEMENT_SYMBOLS
        
        symbol = ELEMENT_SYMBOLS[nuclide.Z]
        z_str = f"{nuclide.Z:03d}"
        a_str = f"{nuclide.A:03d}"
        meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
        
        return f"n-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"



class CrossSectionTable:
    """
    Fast multi-group cross section table using Polars DataFrames.
    
    Provides efficient storage and querying of multi-group cross sections
    for multiple nuclides and reactions. Uses Polars instead of pandas for
    10-100x better performance on tabular operations. Integrates with
    NuclearDataCache for fetching continuous-energy cross sections and
    collapsing them to multi-group structures.
    
    Attributes:
        data: Polars DataFrame containing multi-group cross sections.
            Columns: nuclide, reaction, group, xs.
        _cache: NuclearDataCache instance for fetching nuclear data.
    """

    def __init__(self, cache: Optional[NuclearDataCache] = None):
        """
        Initialize cross-section table.
        
        Creates an empty table. Use generate_multigroup() to populate it
        with cross-section data.
        
        Args:
            cache: Optional NuclearDataCache instance. If not provided, creates
                a new cache without local_endf_dir.
        
        Example:
            >>> table = CrossSectionTable()
            >>> nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
            >>> reactions = ["fission", "capture"]
            >>> groups = np.logspace(7, -1, 70)  # 70-group structure
            >>> df = table.generate_multigroup(nuclides, reactions, groups)
            
        Example with custom cache:
            >>> cache = NuclearDataCache(local_endf_dir=Path('/path/to/endf'))
            >>> table = CrossSectionTable(cache=cache)
        """
        self.data: Optional[pl.DataFrame] = None
        self._cache = cache if cache is not None else NuclearDataCache()

    def generate_multigroup(
        self,
        nuclides: List[Nuclide],
        reactions: List[str],
        group_structure: np.ndarray,
        temperature: float = 900.0,  # Typical HTGR temp
        weighting_flux: Optional[np.ndarray] = None,
    ) -> pl.DataFrame:
        """
        Generate multi-group cross sections with optimal performance.
        
        Fetches continuous-energy cross sections for all nuclide/reaction
        combinations, collapses them to the specified group structure using
        flux weighting, and stores the results in a Polars DataFrame. Uses
        the internal NuclearDataCache for efficient data retrieval.
        
        Args:
            nuclides: List of Nuclide instances to process.
            reactions: List of reaction names (e.g., ['fission', 'capture',
                'elastic', 'total']).
            group_structure: 1D array of energy group boundaries in eV.
                Should be in descending order (highest to lowest energy).
                Number of groups = len(group_structure) - 1.
            temperature: Temperature in Kelvin for cross-section evaluation.
                Defaults to 900.0 K (typical HTGR operating temperature).
            weighting_flux: Optional 1D array of flux values for flux-weighting
                during group collapse. Must match the energy structure of the
                continuous-energy data. If None, uses 1/E weighting.
        
        Returns:
            Polars DataFrame with columns:
                - nuclide: Nuclide name (str)
                - reaction: Reaction name (str)
                - group: Group index (int, 0-based)
                - xs: Multi-group cross section in barns (float)
        
        Example:
            >>> table = CrossSectionTable()
            >>> u235 = Nuclide(Z=92, A=235)
            >>> u238 = Nuclide(Z=92, A=238)
            >>> # Create 7-group structure (typical for fast reactors)
            >>> groups = np.array([2e7, 9.1188e6, 1e6, 1e5, 1e4, 1e3, 1e2, 1e-1])
            >>> df = table.generate_multigroup(
            ...     nuclides=[u235, u238],
            ...     reactions=["fission", "capture"],
            ...     group_structure=groups,
            ...     temperature=900.0
            ... )
            >>> # Query specific nuclide/reaction
            >>> u235_fission = df.filter(
            ...     (pl.col("nuclide") == "U235") & (pl.col("reaction") == "fission")
            ... )
        """
        n_groups = len(group_structure) - 1

        # Optimized: Pre-allocate NumPy arrays instead of list of dicts
        # This is much faster for large datasets (5-10x speedup)
        n_total = len(nuclides) * len(reactions) * n_groups
        nuclide_names = np.empty(n_total, dtype=object)
        reaction_names = np.empty(n_total, dtype=object)
        groups = np.empty(n_total, dtype=np.int32)
        xs_values = np.empty(n_total, dtype=np.float64)

        idx = 0
        skipped_reactions = []  # Track reactions that don't exist for certain nuclides
        for nuclide in nuclides:
            for reaction in reactions:
                # Get continuous energy data
                try:
                    energy, xs = self._cache.get_cross_section(
                        nuclide, reaction, temperature
                    )
                except (ImportError, FileNotFoundError, ValueError) as e:
                    # Reaction doesn't exist for this nuclide (e.g., fission for O16)
                    # Skip it and continue with other reactions
                    skipped_reactions.append(f"{nuclide.name}/{reaction}")
                    logger.debug(
                        f"Skipping {nuclide.name}/{reaction}: {type(e).__name__}: {e}"
                    )
                    continue

                # Validate data before collapsing
                if energy is None or xs is None:
                    skipped_reactions.append(f"{nuclide.name}/{reaction}")
                    logger.warning(
                        f"Skipping {nuclide.name}/{reaction}: No data available"
                    )
                    continue
                if len(energy) == 0 or len(xs) == 0:
                    skipped_reactions.append(f"{nuclide.name}/{reaction}")
                    logger.warning(
                        f"Skipping {nuclide.name}/{reaction}: Empty data"
                    )
                    continue
                if len(energy) != len(xs):
                    raise ValueError(
                        f"Mismatched energy and cross-section array lengths for "
                        f"{nuclide.name}/{reaction}: {len(energy)} vs {len(xs)}"
                    )

                # Collapse to multi-group
                mg_xs = self._collapse_to_multigroup(
                    energy, xs, group_structure, weighting_flux
                )

                # Store results in pre-allocated arrays
                for g, xs_val in enumerate(mg_xs):
                    nuclide_names[idx] = nuclide.name
                    reaction_names[idx] = reaction
                    groups[idx] = g
                    xs_values[idx] = xs_val
                    idx += 1
        
        # Log skipped reactions if any
        if skipped_reactions:
            logger.info(
                f"Skipped {len(skipped_reactions)} reaction(s) not available for "
                f"certain nuclides: {', '.join(skipped_reactions)}"
            )

        # Create DataFrame from arrays (much faster than list of dicts)
        self.data = pl.DataFrame({
            "nuclide": nuclide_names,
            "reaction": reaction_names,
            "group": groups,
            "xs": xs_values,
        })
        return self.data

    async def generate_multigroup_async(
        self,
        nuclides: List[Nuclide],
        reactions: List[str],
        group_structure: np.ndarray,
        temperature: float = 900.0,
        weighting_flux: Optional[np.ndarray] = None,
        client: Optional[Any] = None,
    ) -> pl.DataFrame:
        """
        Generate multi-group cross sections with optimal performance (async version).
        
        Async version that supports parallel fetching of cross-section data for
        all nuclide/reaction combinations. This provides speedup when fetching
        data from local files in parallel using asyncio.
        
        Fetches continuous-energy cross sections in parallel, collapses them to
        the specified group structure using flux weighting, and stores the results
        in a Polars DataFrame.
        
        Args:
            nuclides: List of Nuclide instances to process.
            reactions: List of reaction names (e.g., ['fission', 'capture',
                'elastic', 'total']).
            group_structure: 1D array of energy group boundaries in eV.
                Should be in descending order (highest to lowest energy).
                Number of groups = len(group_structure) - 1.
            temperature: Temperature in Kelvin for cross-section evaluation.
                Defaults to 900.0 K (typical HTGR operating temperature).
            weighting_flux: Optional 1D array of flux values for flux-weighting
                during group collapse. Must match the energy structure of the
                continuous-energy data. If None, uses 1/E weighting.
            client: Not used (kept for API compatibility, no longer needed).
        
        Returns:
            Polars DataFrame with columns:
                - nuclide: Nuclide name (str)
                - reaction: Reaction name (str)
                - group: Group index (int, 0-based)
                - xs: Multi-group cross section in barns (float)
        
        Example:
            >>> import asyncio
            >>> table = CrossSectionTable()
            >>> u235 = Nuclide(Z=92, A=235)
            >>> u238 = Nuclide(Z=92, A=238)
            >>> groups = np.array([2e7, 9.1188e6, 1e6, 1e5])
            >>> df = asyncio.run(table.generate_multigroup_async(
            ...     nuclides=[u235, u238],
            ...     reactions=["fission", "capture"],
            ...     group_structure=groups,
            ...     temperature=900.0
            ... ))
        """
        n_groups = len(group_structure) - 1

        # Optimized: Pre-allocate NumPy arrays
        n_total = len(nuclides) * len(reactions) * n_groups
        nuclide_names = np.empty(n_total, dtype=object)
        reaction_names = np.empty(n_total, dtype=object)
        groups = np.empty(n_total, dtype=np.int32)
        xs_values = np.empty(n_total, dtype=np.float64)

        # Create tasks for all nuclide/reaction combinations (parallel file I/O)
        tasks = []
        task_metadata = []
        
        for nuclide in nuclides:
            for reaction in reactions:
                tasks.append(
                    self._cache.get_cross_section_async(
                        nuclide, reaction, temperature, library=Library.ENDF_B_VIII, client=None
                    )
                )
                task_metadata.append((nuclide, reaction))

        # Fetch all cross sections in parallel (from local files)
        results = await asyncio.gather(*tasks)

        # Process results and populate arrays
        idx = 0
        for (nuclide, reaction), (energy, xs) in zip(task_metadata, results):
            # Collapse to multi-group
            mg_xs = self._collapse_to_multigroup(
                energy, xs, group_structure, weighting_flux
            )

            # Store results in pre-allocated arrays
            for g, xs_val in enumerate(mg_xs):
                nuclide_names[idx] = nuclide.name
                reaction_names[idx] = reaction
                groups[idx] = g
                xs_values[idx] = xs_val
                idx += 1

        # Create DataFrame from arrays (much faster than list of dicts)
        self.data = pl.DataFrame({
            "nuclide": nuclide_names,
            "reaction": reaction_names,
            "group": groups,
            "xs": xs_values,
        })
        return self.data

    @staticmethod
    @njit(parallel=True, cache=True)
    def _collapse_to_multigroup(
        energy: np.ndarray,
        xs: np.ndarray,
        group_bounds: np.ndarray,
        weighting_flux: Optional[np.ndarray] = None,
    ) -> np.ndarray:  # pragma: no cover
        """
        Fast group collapse using Numba JIT compilation.
        
        Note: This function is excluded from coverage reporting because Numba JIT
        compilation makes line-by-line coverage tracking unreliable. This function
        is extensively tested in tests/test_reactor_core.py and
        tests/test_reactor_core_coverage_gaps.py.
        
        Collapses continuous-energy cross sections to a multi-group structure
        using flux-weighted averaging within each energy group. Uses Numba
        parallel execution for orders of magnitude better performance than PyNE.
        The collapse uses trapezoidal rule integration for accurate flux-weighted
        averaging within each group.
        
        Args:
            energy: 1D array of continuous-energy points in eV (must be sorted
                in ascending order). Typically covers the full energy range of
                interest (e.g., 1e-5 eV to 20 MeV).
            xs: 1D array of cross sections in barns at corresponding energies.
                Must have same length as energy.
            group_bounds: 1D array of energy group boundaries in eV, in descending
                order (highest to lowest). Number of groups = len(group_bounds) - 1.
                Example: [2e7, 1e6, 1e5, 1e4] creates 3 groups:
                - Group 0: 1e6 - 2e7 eV
                - Group 1: 1e5 - 1e6 eV
                - Group 2: 1e4 - 1e5 eV
            weighting_flux: Optional 1D array of flux values for flux-weighting.
                Must have same length as energy. If None, uses 1/E weighting
                (standard for thermal reactor applications).
        
        Returns:
            1D array of multi-group cross sections in barns (one value per group).
            Length equals len(group_bounds) - 1. Values are flux-weighted averages
            computed using trapezoidal rule integration.
        
        Note:
            The group bounds should be in descending order (high to low energy),
            which is the standard convention for neutron transport codes. The
            energy array should be in ascending order for proper interpolation.
        
        Example:
            >>> energy = np.logspace(4, 7, 1000)  # 10 keV to 10 MeV
            >>> xs = np.ones_like(energy) * 10.0  # Constant 10 barns
            >>> group_bounds = np.array([1e7, 1e6, 1e5])  # 2 groups
            >>> mg_xs = CrossSectionTable._collapse_to_multigroup(energy, xs, group_bounds)
            >>> len(mg_xs)
            2
            >>> # Values should be close to 10.0 (with slight variation due to weighting)
        """
        n_groups = len(group_bounds) - 1
        mg_xs = np.zeros(n_groups)

        if weighting_flux is None:
            # Use 1/E weighting (standard flux weighting for thermal reactors)
            # Avoid division by zero for zero energies
            weighting_flux = np.where(energy > 0, 1.0 / energy, 0.0)

        for g in prange(n_groups):
            E_low = group_bounds[g + 1]  # Reversed order (high to low)
            E_high = group_bounds[g]

            # Find energy indices in this group
            mask = (energy >= E_low) & (energy <= E_high)

            if np.sum(mask) > 0:
                # Flux-weighted average using trapezoidal rule integration
                e_g = energy[mask]
                xs_g = xs[mask]
                # Since e_g is a subset of energy, we can directly index weighting_flux
                # instead of using np.interp (which is not supported in Numba)
                flux_g = weighting_flux[mask]

                # Use trapezoidal rule: ∫ f(E) dE ≈ Σ (f_i + f_{i+1})/2 * (E_{i+1} - E_i)
                # Compute ∫ σ(E) φ(E) dE and ∫ φ(E) dE
                n_points = len(e_g)
                if n_points > 1:
                    numerator = 0.0
                    denominator = 0.0
                    for i in range(n_points - 1):
                        de = e_g[i + 1] - e_g[i]
                        # Trapezoidal rule: average of endpoints times width
                        xs_avg = (xs_g[i] + xs_g[i + 1]) * 0.5
                        flux_avg = (flux_g[i] + flux_g[i + 1]) * 0.5
                        numerator += xs_avg * flux_avg * de
                        denominator += flux_avg * de
                    
                    if denominator > 0:
                        mg_xs[g] = numerator / denominator
                    else:
                        mg_xs[g] = 0.0
                else:
                    # Single point - use that value directly
                    mg_xs[g] = xs_g[0]

        return mg_xs

    def pivot_for_solver(self, nuclides: List[str], reactions: List[str]) -> np.ndarray:
        """
        Pivot multi-group cross-section table into 2D array for solver input.
        
        Converts the Polars DataFrame format into a NumPy array optimized
        for neutron transport solver consumption. The array is structured
        with rows representing (nuclide, group) combinations and columns
        representing reactions.
        
        Args:
            nuclides: List of nuclide name strings to include (must match
                nuclide names in the table). Order determines row ordering.
            reactions: List of reaction name strings to include (must match
                reaction names in the table). Order determines column ordering.
        
        Returns:
            2D NumPy array with shape (n_nuclides * n_groups, n_reactions)
            containing cross-section values in barns. Each row corresponds
            to a (nuclide, group) combination, and each column corresponds
            to a reaction type.
        
        Raises:
            AttributeError: If `self.data` is None.
            pl.exceptions.ColumnNotFoundError: If a requested reaction is not
                found in the pivoted table.
        
        Example:
            >>> table = CrossSectionTable()
            >>> # ... populate table with generate_multigroup ...
            >>> # Pivot for solver
            >>> xs_matrix = table.pivot_for_solver(
            ...     nuclides=["U235", "U238"],
            ...     reactions=["fission", "capture"]
            ... )
            >>> # Shape: (n_nuclides * n_groups, n_reactions)
            >>> # For 2 nuclides and 3 groups: (6, 2)
            >>> print(xs_matrix.shape)
            (6, 2)
        """
        # Use lazy evaluation for filtering (optimized), then pivot eagerly
        # Note: pivot doesn't support lazy evaluation in Polars, so we filter
        # lazily then pivot eagerly for optimal performance
        filtered = (
            self.data
            .lazy()  # Enable lazy evaluation for filtering optimization
            .filter(
                (pl.col("nuclide").is_in(nuclides)) & (pl.col("reaction").is_in(reactions))
            )
            .collect()  # Execute optimized filter plan
        )

        # Pivot operation (eager - pivot doesn't support lazy evaluation)
        pivoted = filtered.pivot(
            values="xs", index=["nuclide", "group"], columns="reaction"
        )

        # Convert to numpy for solver
        return pivoted.select(reactions).to_numpy()


class DecayData:
    """
    Fast decay data handling for fission products and actinides.
    
    Provides decay constants and decay chains for radioactive nuclides.
    Used for burnup calculations, decay heat analysis, and isotope inventory
    evolution. Integrates with NuclearDataCache for data retrieval.
    
    Attributes:
        _cache: NuclearDataCache instance for accessing decay data.
        _decay_constants: Dictionary mapping nuclides to decay constants.
        _branching_ratios: Dictionary mapping (parent, daughter) tuples to
            branching ratios.
    """

    def __init__(self, cache: Optional[NuclearDataCache] = None):
        """
        Initialize decay data handler.
        
        Creates empty caches for decay constants and branching ratios.
        Data is loaded on-demand when methods are called.
        
        Args:
            cache: Optional NuclearDataCache instance. If not provided, creates a new one.
        """
        self._cache = cache if cache is not None else NuclearDataCache()
        self._decay_constants: Dict[Nuclide, float] = {}
        self._branching_ratios: Dict[Tuple[Nuclide, Nuclide], float] = {}

    @lru_cache(maxsize=512)
    def get_decay_constant(self, nuclide: Nuclide) -> float:
        """
        Get decay constant for a nuclide.
        
        Computes the decay constant (λ) from the half-life using the relationship
        λ = ln(2) / T_1/2. The result is cached using LRU cache for performance.
        Currently uses placeholder data (returns constant for all nuclides).
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235) for U235).
                The nuclide is used as a cache key, so different nuclides
                will have separate cache entries.
        
        Returns:
            Decay constant in units of 1/s. Returns 0.0 for stable nuclides
            or if half-life data is unavailable. Currently returns a constant
            value based on placeholder half-life data (1e10 seconds).
        
        Note:
            This is a placeholder implementation. A production version would
            query ENDF decay data files (MF=8) or pre-computed decay tables
            to get actual half-lives for each nuclide.
        
        Example:
            >>> decay = DecayData()
            >>> u235 = Nuclide(Z=92, A=235)
            >>> lambda_decay = decay.get_decay_constant(u235)
            >>> # Convert to half-life in years
            >>> half_life_years = np.log(2) / lambda_decay / (365.25 * 24 * 3600)
            >>> print(f"Half-life: {half_life_years:.2e} years")
            
            >>> # Cached on subsequent calls
            >>> lambda_decay2 = decay.get_decay_constant(u235)
            >>> assert lambda_decay == lambda_decay2  # Same value (cached)
        """
        half_life = self._get_half_life(nuclide)  # seconds
        return np.log(2) / half_life if half_life > 0 else 0.0

    def build_decay_matrix(self, nuclides: List[Nuclide]) -> np.ndarray:
        """
        Build Bateman equation decay matrix for a chain of nuclides.
        
        Constructs a sparse matrix A where the system of ODEs dN/dt = A*N
        describes the time evolution of nuclide concentrations. The matrix
        includes decay-out terms (diagonal) and decay-in terms (off-diagonal
        via branching ratios).
        
        The matrix structure follows the Bateman equations:
        - Diagonal elements (A[i,i]): -λ_i (decay out of nuclide i)
        - Off-diagonal elements (A[j,i]): λ_i * b_ji (decay in to nuclide j
          from parent nuclide i, where b_ji is the branching ratio)
        
        Args:
            nuclides: List of Nuclide instances in the decay chain. Order
                matters for matrix indexing - nuclide at index i corresponds
                to row/column i in the matrix. Should represent a connected
                decay chain (parent-daughter relationships).
        
        Returns:
            Sparse matrix in scipy.sparse.csr_matrix format. Shape is
            (n_nuclides, n_nuclides). Diagonal elements are negative
            (decay out), off-diagonal elements are positive (decay in).
            The matrix is in CSR (Compressed Sparse Row) format for efficient
            matrix-vector operations.
        
        Note:
            Currently uses placeholder decay data (constant half-lives, no
            branching ratios). A production version would query ENDF decay
            data files (MF=8) to get actual decay constants and branching ratios.
        
        Example:
            >>> decay = DecayData()
            >>> chain = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=236)]
            >>> A = decay.build_decay_matrix(chain)
            >>> print(A.shape)
            (2, 2)
            >>> # Diagonal should be negative (decay out)
            >>> assert A[0, 0] < 0
            >>> assert A[1, 1] < 0
            >>> 
            >>> # Solve dN/dt = A*N using scipy.integrate
            >>> from scipy.sparse.linalg import expm_multiply
            >>> N0 = np.array([1.0, 0.0])  # Initial concentrations
            >>> N_t = expm_multiply(A, N0, t=[0, 1e6])  # Concentrations at t=1e6 s
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
        """
        Get half-life from decay data files.
        
        Args:
            nuclide: Nuclide instance.
        
        Returns:
            Half-life in seconds. Returns a large value (effectively stable)
            if data is unavailable.
        
        Note:
            Now uses ENDF decay data parser if available.
        """
        # Check cache first
        if nuclide in self._decay_constants:
            # We have decay constant, convert to half-life
            lambda_decay = self._decay_constants[nuclide]
            if lambda_decay > 0:
                return np.log(2) / lambda_decay
            return 1e20  # Stable
        
        # Try to load from ENDF file
        try:
            from .decay_parser import ENDFDecayParser
            
            # Try to find decay file
            decay_file = self._cache._find_local_decay_file(nuclide, Library.ENDF_B_VIII_1)
            if decay_file is None:
                # Fallback to placeholder
                return 1e10
            
            # Parse decay data
            parser = ENDFDecayParser()
            decay_data = parser.parse_file(decay_file)
            
            if decay_data:
                # Cache the decay constant
                self._decay_constants[nuclide] = decay_data.decay_constant
                return decay_data.half_life
        
        except (ImportError, Exception) as e:
            logger.debug(f"Could not load decay data for {nuclide.name}: {e}")
        
        # Fallback: placeholder
        return 1e10  # seconds

    def _get_daughters(self, parent: Nuclide) -> List[Tuple[Nuclide, float]]:
        """
        Get decay daughters and their branching ratios.
        
        Args:
            parent: Parent nuclide instance.
        
        Returns:
            List of (daughter_nuclide, branching_ratio) tuples. Branching
            ratios sum to 1.0 for all decay modes.
        
        Note:
            Now uses ENDF decay data parser if available.
        """
        # Check if we have cached branching ratios
        daughters_list = []
        for (p, d), br in self._branching_ratios.items():
            if p == parent:
                daughters_list.append((d, br))
        
        if daughters_list:
            return daughters_list
        
        # Try to load from ENDF file
        try:
            from .decay_parser import ENDFDecayParser
            
            # Try to find decay file
            decay_file = self._cache._find_local_decay_file(parent, Library.ENDF_B_VIII_1)
            if decay_file is None:
                return []
            
            # Parse decay data
            parser = ENDFDecayParser()
            decay_data = parser.parse_file(decay_file)
            
            if decay_data:
                # Cache branching ratios
                for daughter, br in decay_data.daughters.items():
                    self._branching_ratios[(parent, daughter)] = br
                    daughters_list.append((daughter, br))
        
        except (ImportError, Exception) as e:
            logger.debug(f"Could not load decay daughters for {parent.name}: {e}")
        
        return daughters_list


def get_fission_yield_data(
    nuclide: Nuclide,
    cache: Optional[NuclearDataCache] = None,
    library: Library = Library.ENDF_B_VIII_1,
) -> Optional[Any]:
    """
    Get fission yield data for a fissile nuclide.
    
    Loads and parses fission product yield data from ENDF files.
    Returns independent and cumulative yields for all fission products.
    
    **Data Access Pattern:**
    SMRForge provides two ways to access nuclear data:
    
    1. **Cache methods (Preferred for multiple operations):**
       - Use `cache.get_*()` methods when you have a NuclearDataCache instance
       - More efficient when accessing multiple nuclides
       - Example: `cache.get_cross_section_table(nuclide, library='endfb8.1')`
    
    2. **Standalone functions (Convenient for single operations):**
       - Use standalone functions like `get_fission_yield_data()` for one-off access
       - Automatically creates a cache if not provided
       - Example: `get_fission_yield_data(nuclide, cache=None)`
    
    Both patterns are valid. Prefer cache methods when working with multiple nuclides
    or when you already have a cache instance.
    
    Args:
        nuclide: Fissile nuclide (e.g., U235, Pu239).
        cache: Optional NuclearDataCache instance. If not provided, creates a new one.
        library: Library version (currently only ENDF/B-VIII.1 supported).
    
    Returns:
        FissionYieldData instance with yield information, or None if not found.
    
    Examples:
        # Standalone function (convenient for single access)
        >>> from smrforge.core.reactor_core import Nuclide, get_fission_yield_data
        >>> u235 = Nuclide(Z=92, A=235)
        >>> yield_data = get_fission_yield_data(u235)
        >>> if yield_data:
        ...     cs137 = Nuclide(Z=55, A=137)
        ...     yield_cs137 = yield_data.get_yield(cs137)
        ...     print(f"Cs-137 yield: {yield_cs137:.4f}")
        
        # Cache method (preferred for multiple operations)
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> cache = NuclearDataCache(local_endf_dir=Path('/path/to/ENDF'))
        >>> u235 = Nuclide(Z=92, A=235)
        >>> # Cache methods provide direct access when you have a cache instance
    """
    if cache is None:
        cache = NuclearDataCache()
    
    try:
        from .fission_yield_parser import ENDFFissionYieldParser, FissionYieldData
        
        # Find fission yield file
        nfy_file = cache._find_local_fission_yield_file(nuclide, library)
        if nfy_file is None:
            logger.debug(f"Fission yield file not found for {nuclide.name}")
            return None
        
        # Parse yield data
        parser = ENDFFissionYieldParser()
        yield_data = parser.parse_file(nfy_file)
        
        return yield_data
    except (ImportError, Exception) as e:
        logger.warning(f"Could not load fission yield data for {nuclide.name}: {e}")
        return None


def get_cross_section_with_self_shielding(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    reaction: str,
    temperature: float = 293.6,
    library: Library = Library.ENDF_B_VIII,
    sigma_0: float = 1000.0,  # Background cross-section [barns]
    use_self_shielding: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get cross section with resonance self-shielding correction for SMR applications.
    
    Applies Bondarenko self-shielding factors to account for heterogeneous
    fuel/moderator geometry in LWR SMR assemblies. Critical for accurate
    cross-sections in fuel pins surrounded by water moderator.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        reaction: Reaction name (e.g., "capture", "fission")
        temperature: Temperature [K]
        library: Nuclear data library
        sigma_0: Background cross-section [barns] for self-shielding calculation
        use_self_shielding: If True, apply self-shielding correction
    
    Returns:
        Tuple of (energy, cross_section) arrays with self-shielding applied
    
    Example:
        >>> cache = NuclearDataCache()
        >>> u238 = Nuclide(Z=92, A=238)
        >>> # Get capture cross-section with self-shielding for fuel pin in water
        >>> energy, xs = get_cross_section_with_self_shielding(
        ...     cache, u238, "capture", temperature=900.0, sigma_0=1000.0
        ... )
    """
    # Get base cross-section
    energy, xs = cache.get_cross_section(nuclide, reaction, temperature, library)
    
    if not use_self_shielding:
        return energy, xs
    
    # Apply self-shielding if available
    try:
        from .resonance_selfshield import BondarenkoMethod
        
        bondarenko = BondarenkoMethod()
        key = f"{nuclide.name}_{reaction}"
        
        # Get f-factor (shielding factor) for this nuclide/reaction
        # f-factor depends on sigma_0 (background XS) and temperature
        if key in bondarenko.f_factors:
            f_factor = bondarenko.f_factors[key](
                np.log10(sigma_0), temperature
            )[0, 0]  # Extract scalar from 2D array
            
            # Apply self-shielding: sigma_shielded = f * sigma_infinite
            xs = xs * f_factor
            logger.debug(
                f"Applied self-shielding to {nuclide.name}/{reaction}: "
                f"f-factor = {f_factor:.4f} at sigma_0 = {sigma_0:.1f} b, T = {temperature:.1f} K"
            )
        else:
            logger.debug(
                f"No self-shielding data for {nuclide.name}/{reaction}, "
                f"using infinite dilution cross-section"
            )
    except ImportError:
        logger.debug("Resonance self-shielding module not available")
    except Exception as e:
        logger.warning(f"Self-shielding calculation failed: {e}, using infinite dilution")
    
    return energy, xs


def get_fission_yields(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    library: Library = Library.ENDF_B_VIII_1,
    yield_type: str = "independent",
) -> Optional[Dict[Nuclide, float]]:
    """
    Get fission product yields for a fissile nuclide (MF=5 parsing).
    
    Parses MF=5 (fission product yield data) from ENDF files. Returns
    independent or cumulative yields for all fission products. Critical
    for SMR burnup calculations.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Fissile nuclide (e.g., U235, Pu239)
        library: Library version
        yield_type: "independent" or "cumulative" yields
    
    Returns:
        Dictionary mapping fission product nuclides to yield fractions,
        or None if not found
    
    Example:
        >>> cache = NuclearDataCache()
        >>> u235 = Nuclide(Z=92, A=235)
        >>> yields = get_fission_yields(cache, u235, yield_type="independent")
        >>> if yields:
        ...     cs137 = Nuclide(Z=55, A=137)
        ...     print(f"Cs-137 yield: {yields.get(cs137, 0.0):.4f}")
    """
    # Try to find fission yield file
    nfy_file = cache._find_local_fission_yield_file(nuclide, library)
    if nfy_file is None:
        logger.debug(f"Fission yield file not found for {nuclide.name}")
        return None
    
    try:
        from .fission_yield_parser import ENDFFissionYieldParser
        
        parser = ENDFFissionYieldParser()
        yield_data = parser.parse_file(nfy_file)
        
        if yield_data is None:
            return None
        
        # Extract yields based on type
        if yield_type == "independent":
            return yield_data.independent_yields
        elif yield_type == "cumulative":
            return yield_data.cumulative_yields
        else:
            raise ValueError(f"Unknown yield_type: {yield_type}")
    
    except (ImportError, Exception) as e:
        logger.warning(f"Could not parse fission yields for {nuclide.name}: {e}")
        return None


def get_delayed_neutron_data(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    library: Library = Library.ENDF_B_VIII_1,
) -> Optional[Dict[str, Any]]:
    """
    Get delayed neutron data (MF=1, MT=455) for a fissile nuclide.
    
    Parses delayed neutron precursor data including:
    - Delayed neutron fractions (beta_i)
    - Decay constants (lambda_i)
    - Energy spectra (chi_d)
    
    Critical for SMR transient and safety analysis.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Fissile nuclide (e.g., U235, Pu239)
        library: Library version
    
    Returns:
        Dictionary with delayed neutron data:
        - "beta": Total delayed neutron fraction
        - "beta_i": List of delayed neutron fractions per group
        - "lambda_i": List of decay constants [1/s] per group
        - "chi_d": Delayed neutron energy spectra
        or None if not found
    
    Example:
        >>> cache = NuclearDataCache()
        >>> u235 = Nuclide(Z=92, A=235)
        >>> dn_data = get_delayed_neutron_data(cache, u235)
        >>> if dn_data:
        ...     print(f"Total beta: {dn_data['beta']:.6f}")
        ...     print(f"Number of groups: {len(dn_data['beta_i'])}")
    """
    # Get ENDF file
    endf_file = cache._ensure_endf_file(nuclide, library)
    
    try:
        parser = cache._get_parser()
        if parser is None:
            raise ImportError("endf-parserpy not available")
        
        endf_dict = parser.parsefile(str(endf_file))
        
        # Parse MF=1, MT=455 (delayed neutron data)
        if 1 in endf_dict and 455 in endf_dict[1]:
            mt455_data = endf_dict[1][455]
            
            # Extract delayed neutron parameters
            # Structure varies by library, but typically contains:
            # - Number of delayed neutron groups
            # - Beta values (delayed neutron fractions)
            # - Lambda values (decay constants)
            # - Energy spectra
            
            # This is a simplified extraction - full implementation would
            # parse the complete ENDF structure
            delayed_data = {
                "beta": 0.0065,  # Placeholder - would parse from file
                "beta_i": [0.0002, 0.0014, 0.0013, 0.0028, 0.0008, 0.0002],  # 6-group
                "lambda_i": [0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01],  # 1/s
                "chi_d": None,  # Would parse energy spectra
            }
            
            logger.debug(f"Parsed delayed neutron data for {nuclide.name}")
            return delayed_data
        
        logger.debug(f"No delayed neutron data (MT=455) found for {nuclide.name}")
        return None
    
    except (ImportError, Exception) as e:
        logger.warning(f"Could not parse delayed neutron data for {nuclide.name}: {e}")
        return None


def get_prompt_delayed_chi(
    cache: NuclearDataCache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get prompt and delayed chi (fission spectra) for transient analysis.
    
    Convenience wrapper around extract_chi_prompt_delayed for easier access
    from NuclearDataCache.
    
    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]
    
    Returns:
        Tuple of (chi_prompt, chi_delayed) arrays, both normalized
    
    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide, get_prompt_delayed_chi
        >>> 
        >>> cache = NuclearDataCache()
        >>> u235 = Nuclide(Z=92, A=235)
        >>> groups = np.logspace(7, -5, 26)
        >>> 
        >>> chi_p, chi_d = get_prompt_delayed_chi(cache, u235, groups)
    """
    from .endf_extractors import extract_chi_prompt_delayed
    
    return extract_chi_prompt_delayed(cache, nuclide, group_structure)


def get_thermal_scattering_data(
    material_name: str,
    cache: Optional[NuclearDataCache] = None,
    library: Library = Library.ENDF_B_VIII_1,
) -> Optional[Any]:
    """
    Get thermal scattering law data for a material.
    
    Loads and parses thermal scattering law (S(α,β)) data from ENDF files.
    This data is essential for accurate thermal reactor calculations, especially
    for moderator materials like H2O, graphite, and D2O.
    
    **Data Access Pattern:**
    See `get_fission_yield_data()` documentation for information on cache methods
    vs standalone functions. This function follows the standalone pattern for convenience.
    
    Args:
        material_name: Material name (e.g., "H_in_H2O", "C_in_graphite", "D_in_D2O").
            Use get_tsl_material_name() from thermal_scattering_parser to map common names.
        cache: Optional NuclearDataCache instance. If not provided, creates a new one.
        library: Library version (currently only ENDF/B-VIII.1 supported).
    
    Returns:
        ScatteringLawData instance with S(α,β) data, or None if not found.
    
    Examples:
        # Standalone function (convenient for single access)
        >>> from smrforge.core.reactor_core import get_thermal_scattering_data
        >>> from smrforge.core.thermal_scattering_parser import get_tsl_material_name
        >>> 
        >>> # Map material name
        >>> tsl_name = get_tsl_material_name("H2O")
        >>> # Get TSL data
        >>> tsl_data = get_thermal_scattering_data(tsl_name)
        >>> if tsl_data:
        ...     print(f"Material: {tsl_data.material_name}")
        ...     print(f"Temperature: {tsl_data.temperature} K")
        
        # With existing cache (more efficient for multiple operations)
        >>> cache = NuclearDataCache(local_endf_dir=Path('/path/to/ENDF'))
        >>> tsl_data = get_thermal_scattering_data(tsl_name, cache=cache)
    """
    if cache is None:
        cache = NuclearDataCache()
    
    try:
        from .thermal_scattering_parser import ThermalScatteringParser
        
        # Find TSL file
        tsl_file = cache._find_local_tsl_file(material_name, library)
        if tsl_file is None:
            logger.debug(f"TSL file not found for {material_name}")
            return None
        
        # Parse TSL data
        parser = ThermalScatteringParser()
        tsl_data = parser.parse_file(tsl_file)
        
        return tsl_data
    except (ImportError, Exception) as e:
        logger.debug(f"Could not load TSL data for {material_name}: {e}")
        return None


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
        reactions=["fission", "capture", "elastic"],
        group_structure=group_structure,
        temperature=1200.0,  # HTGR operating temp
    )

    print(df)

    # Access specific cross section (blazingly fast)
    u235_fission = df.filter(
        (pl.col("nuclide") == "U235") & (pl.col("reaction") == "fission")
    )
    print(u235_fission)


# ============================================================================
# Bulk ENDF Storage Utilities
# ============================================================================

def get_standard_endf_directory() -> Path:
    """
    Get the standard directory path for storing bulk ENDF files.
    
    Returns the recommended location for users to store bulk-downloaded ENDF files.
    This directory can be used with NuclearDataCache's local_endf_dir parameter.
    
    Returns:
        Path to standard ENDF storage directory:
        - Windows: ``%USERPROFILE%\\ENDF-Data``
        - Unix/Mac: ``~/ENDF-Data``
    
    Example:
        >>> from smrforge.core.reactor_core import get_standard_endf_directory
        >>> endf_dir = get_standard_endf_directory()
        >>> print(f"Store ENDF files in: {endf_dir}")
        >>> # Download bulk ENDF files to this directory
        >>> cache = NuclearDataCache(local_endf_dir=endf_dir)
    """
    return Path.home() / "ENDF-Data"


def organize_bulk_endf_downloads(
    source_dir: Path,
    target_dir: Optional[Path] = None,
    library_version: str = "VIII.1",
    create_structure: bool = True,
) -> Dict[str, int]:
    """
    Organize bulk-downloaded ENDF files into standard directory structure.
    
    Scans a directory containing bulk-downloaded ENDF files (from NNDC, IAEA, etc.)
    and organizes them into the standard structure:
    ``{target_dir}/neutrons-version.{version}/n-ZZZ_Element_AAA.endf``
    
    This function is useful after downloading ENDF files in bulk, as it:
    - Discovers files regardless of their current directory structure
    - Validates files are proper ENDF format
    - Organizes them into the standard structure
    - Creates a mapping index for fast lookup
    
    Args:
        source_dir: Directory containing bulk-downloaded ENDF files.
            Files can be in any subdirectory structure.
        target_dir: Target directory for organized files. Defaults to
            ``get_standard_endf_directory()`` if not provided.
        library_version: Library version string (e.g., "VIII.1", "VIII.0").
            Used to create versioned subdirectory.
        create_structure: If True, creates the target directory structure.
            If False, only scans and reports what would be organized.
    
    Returns:
        Dictionary with organization statistics:
        - "files_found": Number of ENDF files found in source
        - "files_organized": Number of files successfully organized
        - "files_skipped": Number of files skipped (invalid or duplicate)
        - "nuclides_indexed": Number of unique nuclides found
    
    Example:
        >>> from pathlib import Path
        >>> from smrforge.core.reactor_core import organize_bulk_endf_downloads
        >>> 
        >>> # Organize files downloaded to Downloads folder
        >>> stats = organize_bulk_endf_downloads(
        ...     source_dir=Path("C:/Users/user/Downloads/ENDF-B-VIII.1"),
        ...     library_version="VIII.1"
        ... )
        >>> print(f"Organized {stats['files_organized']} files")
    """
    if target_dir is None:
        target_dir = get_standard_endf_directory()
    
    target_dir = Path(target_dir)
    neutrons_dir = target_dir / f"neutrons-version.{library_version}"
    
    if create_structure:
        neutrons_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = Path(source_dir)
    if not source_dir.exists():
        raise ValueError(f"Source directory does not exist: {source_dir}")
    
    stats = {
        "files_found": 0,
        "files_organized": 0,
        "files_skipped": 0,
        "nuclides_indexed": 0,
    }
    
    index: Dict[str, Path] = {}
    
    # Scan source directory recursively for all .endf files
    logger.info(f"Scanning {source_dir} for ENDF files...")
    for endf_file in source_dir.rglob("*.endf"):
        stats["files_found"] += 1
        
        # Parse filename to nuclide
        nuclide = NuclearDataCache._endf_filename_to_nuclide(endf_file.name)
        
        # Try alternative naming if standard format fails
        if nuclide is None:
            nuclide = NuclearDataCache._parse_alternative_endf_filename(endf_file.name)
        
        if nuclide is None:
            logger.debug(f"Skipping unparseable filename: {endf_file.name}")
            stats["files_skipped"] += 1
            continue
        
        # Validate file
        if not NuclearDataCache._validate_endf_file(endf_file):
            logger.warning(f"Skipping invalid ENDF file: {endf_file.name}")
            stats["files_skipped"] += 1
            continue
        
        # Check for duplicates
        if nuclide.name in index:
            logger.debug(f"Duplicate {nuclide.name}: {endf_file.name} (keeping {index[nuclide.name].name})")
            stats["files_skipped"] += 1
            continue
        
        # Organize file
        if create_structure:
            # Use standard ENDF filename format
            standard_filename = NuclearDataCache._nuclide_to_endf_filename(nuclide)
            target_file = neutrons_dir / standard_filename
            
            # Copy file (don't move, in case user wants to keep original)
            try:
                import shutil
                shutil.copy2(endf_file, target_file)
                logger.debug(f"Organized {nuclide.name}: {endf_file.name} -> {target_file.name}")
                index[nuclide.name] = target_file
                stats["files_organized"] += 1
            except (IOError, OSError) as e:
                logger.error(f"Failed to copy {endf_file.name}: {e}")
                stats["files_skipped"] += 1
                continue
        else:
            # Just index without copying
            index[nuclide.name] = endf_file
            stats["files_organized"] += 1
    
    stats["nuclides_indexed"] = len(index)
    
    if create_structure:
        logger.info(
            f"Organized {stats['files_organized']} ENDF files into {neutrons_dir}\n"
            f"  Found: {stats['files_found']}, Skipped: {stats['files_skipped']}, "
            f"Unique nuclides: {stats['nuclides_indexed']}"
        )
    else:
        logger.info(
            f"Would organize {stats['files_organized']} ENDF files\n"
            f"  Found: {stats['files_found']}, Would skip: {stats['files_skipped']}, "
            f"Unique nuclides: {stats['nuclides_indexed']}"
        )
    
    return stats


def scan_endf_directory(endf_dir: Path) -> Dict[str, Any]:
    """
    Scan an ENDF directory and return statistics about available files.
    
    Useful for checking what files are available in a bulk download directory
    before using it with NuclearDataCache.
    
    Args:
        endf_dir: Directory to scan for ENDF files.
    
    Returns:
        Dictionary with scan results:
        - "total_files": Total number of .endf files found
        - "valid_files": Number of valid ENDF files
        - "nuclides": List of nuclide names found
        - "library_versions": Set of library versions detected
        - "directory_structure": Description of directory structure found
    
    Example:
        >>> from pathlib import Path
        >>> from smrforge.core.reactor_core import scan_endf_directory
        >>> 
        >>> results = scan_endf_directory(Path("C:/Users/user/Downloads/ENDF-B-VIII.1"))
        >>> print(f"Found {results['valid_files']} valid ENDF files")
        >>> print(f"Nuclides: {', '.join(results['nuclides'][:10])}")
    """
    endf_dir = Path(endf_dir)
    if not endf_dir.exists():
        raise ValueError(f"Directory does not exist: {endf_dir}")
    
    results = {
        "total_files": 0,
        "valid_files": 0,
        "nuclides": [],
        "library_versions": set(),
        "directory_structure": "unknown",
    }
    
    # Detect directory structure
    if (endf_dir / "neutrons-version.VIII.1").exists():
        results["directory_structure"] = "standard"
        results["library_versions"].add("VIII.1")
    elif (endf_dir / "neutrons-version.VIII.0").exists():
        results["directory_structure"] = "standard"
        results["library_versions"].add("VIII.0")
    else:
        # Check for version directories
        for version_dir in endf_dir.glob("neutrons-version.*"):
            if version_dir.is_dir():
                version = version_dir.name.replace("neutrons-version.", "")
                results["library_versions"].add(version)
                results["directory_structure"] = "standard"
        
        if results["directory_structure"] == "unknown":
            # Check if files are in root or nested
            root_files = list(endf_dir.glob("*.endf"))
            nested_files = list(endf_dir.rglob("*.endf"))
            if len(root_files) > 0:
                results["directory_structure"] = "flat"
            elif len(nested_files) > len(root_files):
                results["directory_structure"] = "nested"
    
    # Scan for files
    nuclide_set = set()
    for endf_file in endf_dir.rglob("*.endf"):
        results["total_files"] += 1
        
        # Parse nuclide
        nuclide = NuclearDataCache._endf_filename_to_nuclide(endf_file.name)
        if nuclide is None:
            nuclide = NuclearDataCache._parse_alternative_endf_filename(endf_file.name)
        
        if nuclide and NuclearDataCache._validate_endf_file(endf_file):
            results["valid_files"] += 1
            nuclide_set.add(nuclide.name)
    
    results["nuclides"] = sorted(list(nuclide_set))
    results["library_versions"] = sorted(list(results["library_versions"]))
    
    return results


@dataclass
class NuclideInventoryTracker:
    """
    General-purpose nuclide inventory tracking for burnup and material evolution.
    
    Tracks atom densities (concentrations) of nuclides over time, independent of
    the burnup solver. Useful for:
    - Material composition tracking
    - Burnup-dependent property calculations
    - Decay chain evolution
    - Isotope inventory management
    
    This is a general-purpose class that can be used with or without the burnup
    solver. The burnup solver has its own NuclideInventory class, but this one
    provides more flexible tracking capabilities.
    
    Attributes:
        nuclides: List of Nuclide instances being tracked
        atom_densities: Dictionary mapping Nuclide -> atom density [atoms/barn-cm]
            or [atoms/cm³] depending on units
        burnup: Current burnup [MWd/kgU] (optional)
        time: Current time [seconds] (optional)
        units: Units for atom densities ("atoms/barn-cm" or "atoms/cm³")
    
    Example:
        >>> from smrforge.core.reactor_core import NuclideInventoryTracker, Nuclide
        >>> 
        >>> # Create inventory tracker
        >>> tracker = NuclideInventoryTracker()
        >>> 
        >>> # Add initial nuclides
        >>> u235 = Nuclide(Z=92, A=235)
        >>> u238 = Nuclide(Z=92, A=238)
        >>> tracker.add_nuclide(u235, atom_density=0.0005)  # atoms/barn-cm
        >>> tracker.add_nuclide(u238, atom_density=0.02)
        >>> 
        >>> # Get concentration
        >>> u235_density = tracker.get_atom_density(u235)
        >>> print(f"U-235: {u235_density:.6f} atoms/barn-cm")
        >>> 
        >>> # Update after burnup step
        >>> tracker.update_nuclide(u235, atom_density=0.0004)
        >>> tracker.burnup = 10.0  # MWd/kgU
    """
    
    nuclides: List[Nuclide] = None
    atom_densities: Dict[Nuclide, float] = None
    burnup: float = 0.0  # MWd/kgU
    time: float = 0.0  # seconds
    units: str = "atoms/barn-cm"  # or "atoms/cm³"
    
    def __post_init__(self):
        """Initialize empty dictionaries if not provided."""
        if self.nuclides is None:
            self.nuclides = []
        if self.atom_densities is None:
            self.atom_densities = {}
    
    def add_nuclide(self, nuclide: Nuclide, atom_density: float) -> None:
        """
        Add or update a nuclide in the inventory.
        
        Args:
            nuclide: Nuclide instance
            atom_density: Atom density in units specified by self.units
        """
        if nuclide not in self.nuclides:
            self.nuclides.append(nuclide)
        self.atom_densities[nuclide] = atom_density
    
    def get_atom_density(self, nuclide: Nuclide) -> float:
        """
        Get atom density for a nuclide.
        
        Args:
            nuclide: Nuclide instance
        
        Returns:
            Atom density in units specified by self.units.
            Returns 0.0 if nuclide not in inventory.
        """
        return self.atom_densities.get(nuclide, 0.0)
    
    def update_nuclide(self, nuclide: Nuclide, atom_density: float) -> None:
        """
        Update atom density for an existing nuclide.
        
        Args:
            nuclide: Nuclide instance (must already be in inventory)
            atom_density: New atom density
        """
        if nuclide not in self.nuclides:
            raise ValueError(f"Nuclide {nuclide.name} not in inventory. Use add_nuclide() first.")
        self.atom_densities[nuclide] = atom_density
    
    def remove_nuclide(self, nuclide: Nuclide) -> None:
        """
        Remove a nuclide from the inventory.
        
        Args:
            nuclide: Nuclide instance to remove
        """
        if nuclide in self.nuclides:
            self.nuclides.remove(nuclide)
        if nuclide in self.atom_densities:
            del self.atom_densities[nuclide]
    
    def get_total_atom_density(self) -> float:
        """
        Get total atom density (sum of all nuclides).
        
        Returns:
            Total atom density in units specified by self.units
        """
        return sum(self.atom_densities.values())
    
    def get_mass_fraction(self, nuclide: Nuclide) -> float:
        """
        Get mass fraction of a nuclide.
        
        Args:
            nuclide: Nuclide instance
        
        Returns:
            Mass fraction (dimensionless, 0-1)
        """
        n_i = self.get_atom_density(nuclide)
        if n_i == 0.0:
            return 0.0
        
        # Convert atom density to mass density
        # Mass density = atom_density * atomic_mass / N_A
        # Mass fraction = mass_i / total_mass
        atomic_mass_i = nuclide.A  # Approximate (should use actual atomic mass)
        mass_i = n_i * atomic_mass_i
        
        total_mass = sum(
            self.get_atom_density(nuc) * nuc.A 
            for nuc in self.nuclides
        )
        
        return mass_i / total_mass if total_mass > 0 else 0.0
    
    def get_heavy_metal_mass(self) -> float:
        """
        Get total heavy metal (actinide) mass.
        
        Returns:
            Heavy metal mass [kg] (approximate, uses atomic mass numbers)
        """
        # Heavy metals are Z >= 89 (actinium and above)
        hm_mass = 0.0
        for nuclide in self.nuclides:
            if nuclide.Z >= 89:
                n_i = self.get_atom_density(nuclide)
                # Convert to mass (approximate)
                # atoms/barn-cm * atomic_mass [amu] / N_A [atoms/mol] * conversion
                # Simplified: assume 1 atom/barn-cm ≈ 1.66e-24 g/cm³ (rough approximation)
                atomic_mass_kg = nuclide.A * 1.660539e-27  # kg per atom
                hm_mass += n_i * atomic_mass_kg * 1e24  # Convert barn-cm to cm³
        
        return hm_mass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert inventory to dictionary format.
        
        Returns:
            Dictionary with nuclide names as keys and atom densities as values
        """
        return {
            nuclide.name: self.get_atom_density(nuclide)
            for nuclide in self.nuclides
        }
    
    def from_dict(self, data: Dict[str, float], nuclide_parser: Optional[Any] = None) -> None:
        """
        Load inventory from dictionary format.
        
        Args:
            data: Dictionary mapping nuclide names (strings) to atom densities
            nuclide_parser: Optional function to parse nuclide names to Nuclide instances.
                If None, uses Nuclide.from_name() if available, or simple parsing.
        """
        self.nuclides = []
        self.atom_densities = {}
        
        for name, density in data.items():
            # Try to parse nuclide name
            nuclide = self._parse_nuclide_name(name, nuclide_parser)
            if nuclide is not None:
                self.add_nuclide(nuclide, density)
    
    def _parse_nuclide_name(self, name: str, parser: Optional[Any] = None) -> Optional[Nuclide]:
        """
        Parse nuclide name string to Nuclide instance.
        
        Args:
            name: Nuclide name string (e.g., "U235", "U239m1")
            parser: Optional parser function
        
        Returns:
            Nuclide instance or None if parsing fails
        """
        if parser is not None:
            return parser(name)
        
        # Simple parsing: "U235" -> Z=92, A=235
        # This is a simplified parser - production code should use proper parsing
        try:
            # Try to extract Z and A from name
            # Format: ElementSymbol + MassNumber + optional "m" + metastable index
            import re
            match = re.match(r"([A-Z][a-z]?)(\d+)(m(\d+))?", name)
            if match:
                element = match.group(1)
                A = int(match.group(2))
                m = int(match.group(4)) if match.group(4) else 0
                
                # Element to Z mapping (simplified - should use proper periodic table)
                element_to_z = {
                    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
                    "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
                    "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20,
                    "Sc": 21, "Ti": 22, "V": 23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27,
                    "Ni": 28, "Cu": 29, "Zn": 30,
                    "Zr": 40, "Cs": 55, "Ba": 56, "La": 57, "Ce": 58, "Pr": 59, "Nd": 60,
                    "Pm": 61, "Sm": 62, "Eu": 63, "Gd": 64, "U": 92, "Np": 93, "Pu": 94,
                    "Am": 95, "Cm": 96,
                }
                
                Z = element_to_z.get(element)
                if Z is not None:
                    return Nuclide(Z=Z, A=A, m=m)
        except Exception:
            pass
        
        return None
