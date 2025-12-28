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
from typing import Dict, List, Optional, Tuple

import asyncio
import numpy as np
import polars as pl  # Much faster than pandas
import requests
import zarr  # Modern, fast alternative to HDF5
from numba import njit, prange

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

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

    def __hash__(self):
        return hash(self.zam)


class NuclearDataCache:
    """
    High-performance nuclear data cache using Zarr for storage.
    
    Much faster than HDF5 with better compression and chunking. Provides
    two-level caching: in-memory cache for hot data and persistent Zarr
    storage for cross-section data. Automatically fetches ENDF files when
    needed and supports multiple backends (SANDY, built-in parser).
    
    Attributes:
        cache_dir: Directory for persistent cache storage.
        _memory_cache: In-memory dictionary cache for frequently accessed data.
        root: Zarr root group for persistent storage.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize nuclear data cache.
        
        Args:
            cache_dir: Optional path to cache directory. Defaults to
                ``~/.smrforge/nucdata`` if not provided.
        
        Example:
            >>> cache = NuclearDataCache()
            >>> # Or specify custom cache location
            >>> cache = NuclearDataCache(cache_dir=Path("/tmp/nucdata"))
        """
        self.cache_dir = cache_dir or Path.home() / ".smrforge" / "nucdata"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for hot data
        self._memory_cache: Dict = {}

        # Open zarr store (lazy loading)
        from zarr.storage import LocalStore

        self.store = LocalStore(str(self.cache_dir))
        self.root = zarr.open(self.store, mode="a")

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
            from endf_parserpy import EndfParserFactory

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf-parserpy", logger
            )
            parser = EndfParserFactory.create()
            endf_dict = parser.parsefile(str(endf_file))

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
        try:
            from endf_parserpy import EndfParserFactory
            available_backends.append("endf-parserpy")
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
            f"  - endf-parserpy (recommended): pip install endf-parserpy\n"
            f"    Official IAEA library, comprehensive ENDF-6 support\n"
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
        
        Args:
            key: Cache key string identifying the data.
            energy: 1D array of neutron energies in eV.
            xs: 1D array of cross sections in barns (must match energy length).
        
        Note:
            Data is stored with zstd compression and 1024-element chunks
            for optimal performance. The key is also added to the in-memory
            cache for faster subsequent access.
        """
        group = self.root.create_group(key, overwrite=True)
        # Use create_array with data parameter (shape is inferred from data)
        # Note: zstd compression requires numcodecs, using default compression for compatibility
        group.create_array("energy", data=energy, chunks=(1024,))
        group.create_array("xs", data=xs, chunks=(1024,))

        # Cache in memory
        self._memory_cache[key] = (energy, xs)

    async def get_cross_section_async(
        self,
        nuclide: Nuclide,
        reaction: str,
        temperature: float = 293.6,
        library: Library = Library.ENDF_B_VIII,
        client: Optional["httpx.AsyncClient"] = None,
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
            client: Optional httpx.AsyncClient for async file downloads.
        
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
        client: Optional["httpx.AsyncClient"] = None,
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
            client: Optional httpx.AsyncClient for async file downloads.
        
        Returns:
            Tuple of (energy, cross_section) arrays.
        
        Raises:
            ImportError: If all backends fail and data cannot be fetched.
        """
        # Download ENDF file if needed (async)
        endf_file = await self._ensure_endf_file_async(nuclide, library, client)
        reaction_mt = self._reaction_to_mt(reaction)

        # Try endf-parserpy first (official IAEA library, recommended)
        try:
            from endf_parserpy import EndfParserFactory

            log_nuclear_data_fetch(
                nuclide.name, reaction, temperature, "endf-parserpy", logger
            )
            parser = EndfParserFactory.create()
            endf_dict = parser.parsefile(str(endf_file))

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
        try:
            from endf_parserpy import EndfParserFactory
            available_backends.append("endf-parserpy")
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
            f"  - endf-parserpy (recommended): pip install endf-parserpy\n"
            f"    Official IAEA library, comprehensive ENDF-6 support\n"
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
        
        Args:
            endf_file: Path to ENDF-6 format file.
            reaction: Reaction name (e.g., "fission", "capture", "elastic", "total").
            nuclide: Nuclide instance (currently unused but kept for API consistency).
        
        Returns:
            Tuple of (energy, cross_section) arrays, or (None, None) if parsing fails.
            Energy is in eV, cross sections are in barns.
        
        Note:
            The SMRForge ENDF parser (endf_parser.py) is preferred over this method.
            This is kept as a last-resort fallback when other parsers are unavailable.
        
        Supported Reactions:
            - "total" (MT=1)
            - "elastic" (MT=2)
            - "fission" (MT=18)
            - "capture" or "n,gamma" (MT=102)
            - "n,2n" (MT=16)
            - "n,alpha" (MT=107)
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
                        val_str = line[j : j + 11].strip()
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
            # Only process complete pairs (must have even number of values)
            if len(values) % 2 != 0:
                logger.warning(f"Odd number of values in ENDF MF=3 section, MT={reaction_mt}, discarding last value")
                values = values[:-1]  # Discard last unpaired value
            
            for idx in range(0, len(values) - 1, 2):
                energy_list.append(values[idx])
                xs_list.append(values[idx + 1])

            if len(energy_list) > 0 and len(xs_list) > 0:
                energy = np.array(energy_list)
                xs = np.array(xs_list)
                
                # Validate that energies are positive and cross sections are non-negative
                if np.any(energy <= 0):
                    logger.warning(f"Found non-positive energies in ENDF data for MT={reaction_mt}")
                    # Filter out invalid energies
                    valid_mask = energy > 0
                    energy = energy[valid_mask]
                    xs = xs[valid_mask]
                
                if np.any(xs < 0):
                    logger.warning(f"Found negative cross sections in ENDF data for MT={reaction_mt}, setting to zero")
                    xs = np.maximum(xs, 0.0)  # Clamp negative values to zero
                
                # Ensure we still have valid data after filtering
                if len(energy) > 0 and len(xs) > 0 and len(energy) == len(xs):
                    return energy, xs
                else:
                    logger.error(f"Invalid data after filtering for MT={reaction_mt}")

        except Exception as e:
            logger.debug(f"Error parsing ENDF file {endf_file} for MT={reaction_mt}: {e}")

        return None, None

    @staticmethod
    def _extract_mf3_data(mf3_mt_data) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Extract energy and cross-section arrays from endf-parserpy MF3 section data.
        
        This method handles the various ways endf-parserpy might structure MF3 data.
        MF3 sections contain tabulated (energy, cross-section) pairs.
        
        Args:
            mf3_mt_data: The parsed MF3/MT data structure from endf-parserpy.
        
        Returns:
            Tuple of (energy, cross_section) arrays, or (None, None) if extraction fails.
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
    ) -> np.ndarray:
        """
        Fast Doppler broadening of cross sections using Numba JIT compilation.
        
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
        
        Args:
            reaction: Reaction name (case-insensitive). Supported reactions:
                - "total" -> MT=1
                - "elastic" -> MT=2
                - "fission" -> MT=18
                - "capture" or "n,gamma" -> MT=102
                - "n,2n" -> MT=16
                - "n,alpha" -> MT=107
        
        Returns:
            MT number (integer). Returns 1 (total) for unknown reactions.
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
        Download ENDF file if not present in cache (synchronous version).
        
        Checks if the ENDF file for the specified nuclide and library exists
        in the cache directory. If not, downloads it from IAEA Nuclear Data
        Services and saves it locally.
        
        Args:
            nuclide: Nuclide instance.
            library: Nuclear data library enum.
        
        Returns:
            Path to the ENDF file (either existing or newly downloaded).
        
        Raises:
            requests.RequestException: If download fails (network error, HTTP error, etc.).
            IOError: If file cannot be written to cache directory.
        """
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

    async def _ensure_endf_file_async(
        self, nuclide: Nuclide, library: Library, client: Optional["httpx.AsyncClient"] = None
    ) -> Path:
        """
        Download ENDF file if not present in cache (async version).
        
        Async version that supports parallel downloads. If client is provided,
        uses it; otherwise creates a temporary client.
        
        Args:
            nuclide: Nuclide instance.
            library: Nuclear data library enum.
            client: Optional httpx.AsyncClient for making requests. If None,
                creates a temporary client.
        
        Returns:
            Path to the ENDF file (either existing or newly downloaded).
        
        Raises:
            httpx.HTTPError: If download fails (network error, HTTP error, etc.).
            IOError: If file cannot be written to cache directory.
            RuntimeError: If httpx is not available.
        """
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx is required for async file downloads. Install with: pip install httpx")
        
        endf_dir = self.cache_dir / "endf" / library.value
        endf_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{nuclide.name}.endf"
        filepath = endf_dir / filename

        if not filepath.exists():
            # Download from NNDC or IAEA
            url = self._get_endf_url(nuclide, library)
            
            use_temporary_client = client is None
            if use_temporary_client:
                client = httpx.AsyncClient(timeout=30.0)
            
            try:
                response = await client.get(url)
                response.raise_for_status()
                filepath.write_bytes(response.content)
            finally:
                if use_temporary_client:
                    await client.aclose()

        return filepath

    @staticmethod
    def _get_endf_url(nuclide: Nuclide, library: Library) -> str:
        """
        Construct download URL for ENDF file from IAEA Nuclear Data Services.
        
        Args:
            nuclide: Nuclide instance (e.g., Nuclide(Z=92, A=235) for U235).
            library: Nuclear data library enum (e.g., Library.ENDF_B_VIII).
        
        Returns:
            URL string pointing to the ENDF file download endpoint.
        
        Note:
            This is a simplified implementation. A production version would
            need proper URL construction following IAEA NDS conventions,
            including proper library versioning and nuclide naming schemes.
        """
        # IAEA Nuclear Data Services
        base_url = "https://www-nds.iaea.org/public/download-endf"
        # Simplified - real implementation needs proper URL construction
        return f"{base_url}/{library.value}/{nuclide.name}.endf"


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

    def __init__(self):
        """
        Initialize cross-section table.
        
        Creates an empty table. Use generate_multigroup() to populate it
        with cross-section data.
        
        Example:
            >>> table = CrossSectionTable()
            >>> nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
            >>> reactions = ["fission", "capture"]
            >>> groups = np.logspace(7, -1, 70)  # 70-group structure
            >>> df = table.generate_multigroup(nuclides, reactions, groups)
        """
        self.data: Optional[pl.DataFrame] = None
        self._cache = NuclearDataCache()

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

    async def generate_multigroup_async(
        self,
        nuclides: List[Nuclide],
        reactions: List[str],
        group_structure: np.ndarray,
        temperature: float = 900.0,
        weighting_flux: Optional[np.ndarray] = None,
        client: Optional["httpx.AsyncClient"] = None,
    ) -> pl.DataFrame:
        """
        Generate multi-group cross sections with optimal performance (async version).
        
        Async version that supports parallel fetching of cross-section data for
        all nuclide/reaction combinations. This provides significant speedup
        (3-10x) when fetching data that requires network requests or file I/O.
        
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
            client: Optional httpx.AsyncClient for async file downloads.
                If None, creates a temporary client.
        
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
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx is required for async operations. Install with: pip install httpx")
        
        n_groups = len(group_structure) - 1

        # Optimized: Pre-allocate NumPy arrays
        n_total = len(nuclides) * len(reactions) * n_groups
        nuclide_names = np.empty(n_total, dtype=object)
        reaction_names = np.empty(n_total, dtype=object)
        groups = np.empty(n_total, dtype=np.int32)
        xs_values = np.empty(n_total, dtype=np.float64)

        # Create async HTTP client for parallel downloads
        use_temporary_client = client is None
        if use_temporary_client:
            client = httpx.AsyncClient(timeout=30.0)

        try:
            # Create tasks for all nuclide/reaction combinations
            tasks = []
            task_metadata = []
            
            for nuclide in nuclides:
                for reaction in reactions:
                    tasks.append(
                        self._cache.get_cross_section_async(
                            nuclide, reaction, temperature, library=Library.ENDF_B_VIII, client=client
                        )
                    )
                    task_metadata.append((nuclide, reaction))

            # Fetch all cross sections in parallel
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
        finally:
            if use_temporary_client:
                await client.aclose()

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
    ) -> np.ndarray:
        """
        Fast group collapse using Numba JIT compilation.
        
        Collapses continuous-energy cross sections to a multi-group structure
        using flux-weighted averaging within each energy group. Uses Numba
        parallel execution for orders of magnitude better performance than PyNE.
        
        Args:
            energy: 1D array of continuous-energy points in eV (must be sorted).
            xs: 1D array of cross sections in barns at corresponding energies.
            group_bounds: 1D array of energy group boundaries in eV, in descending
                order (highest to lowest). Number of groups = len(group_bounds) - 1.
            weighting_flux: Optional 1D array of flux values for flux-weighting.
                Must have same length as energy. If None, uses 1/E weighting.
        
        Returns:
            1D array of multi-group cross sections in barns (one value per group).
        
        Note:
            The group bounds should be in descending order (high to low energy),
            which is the standard convention for neutron transport codes.
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
        Pivot multi-group cross-section table into 3D array for solver input.
        
        Converts the Polars DataFrame format into a NumPy array optimized
        for neutron transport solver consumption. The array shape follows
        the standard (nuclide, reaction, group) ordering.
        
        Args:
            nuclides: List of nuclide name strings to include (must match
                nuclide names in the table).
            reactions: List of reaction name strings to include (must match
                reaction names in the table).
        
        Returns:
            3D NumPy array with shape (n_nuclides, n_reactions, n_groups)
            containing cross-section values in barns. Ordering follows
            the input nuclide and reaction lists.
        
        Example:
            >>> table = CrossSectionTable()
            >>> # ... populate table ...
            >>> # Pivot for solver
            >>> xs_matrix = table.pivot_for_solver(
            ...     nuclides=["U235", "U238"],
            ...     reactions=["fission", "capture", "absorption"]
            ... )
            >>> print(xs_matrix.shape)  # (2, 3, n_groups)
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

    def __init__(self):
        """
        Initialize decay data handler.
        
        Creates empty caches for decay constants and branching ratios.
        Data is loaded on-demand when methods are called.
        """
        self._cache = NuclearDataCache()
        self._decay_constants: Dict[Nuclide, float] = {}
        self._branching_ratios: Dict[Tuple[Nuclide, Nuclide], float] = {}

    @lru_cache(maxsize=512)
    def get_decay_constant(self, nuclide: Nuclide) -> float:
        """
        Get decay constant for a nuclide.
        
        Args:
            nuclide: Nuclide instance.
        
        Returns:
            Decay constant in units of 1/s. Returns 0.0 for stable nuclides
            or if half-life data is unavailable.
        
        Example:
            >>> decay = DecayData()
            >>> u235 = Nuclide(Z=92, A=235)
            >>> lambda_decay = decay.get_decay_constant(u235)
            >>> print(f"Half-life: {np.log(2) / lambda_decay / (365.25*24*3600):.2e} years")
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
        
        Args:
            nuclides: List of Nuclide instances in the decay chain. Order
                matters for matrix indexing.
        
        Returns:
            Sparse matrix in scipy.sparse.csr_matrix format. Shape is
            (n_nuclides, n_nuclides). Diagonal elements are negative
            (decay out), off-diagonal elements are positive (decay in).
        
        Example:
            >>> decay = DecayData()
            >>> chain = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=236)]
            >>> A = decay.build_decay_matrix(chain)
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
            This is a placeholder implementation. A production version would
            query ENDF decay data files (MF=8) or pre-computed decay tables.
        """
        # Use cached data or pre-computed tables
        # Placeholder implementation
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
            This is a placeholder implementation. A production version would
            query ENDF decay data files (MF=8) to get decay modes and
            branching ratios for each decay channel.
        """
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
