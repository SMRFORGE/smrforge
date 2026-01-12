"""
Automated ENDF data downloader for SMRForge.

Provides programmatic download of ENDF nuclear data files from NNDC and IAEA,
with support for selective downloads, progress indicators, and resume capability.

Example:
    >>> from smrforge.data_downloader import download_endf_data
    >>> 
    >>> # Download full library
    >>> download_endf_data(
    ...     library="ENDF/B-VIII.1",
    ...     output_dir="~/ENDF-Data"
    ... )
    >>> 
    >>> # Download specific elements
    >>> download_endf_data(
    ...     library="ENDF/B-VIII.1",
    ...     elements=["U", "Pu", "Th"],
    ...     output_dir="~/ENDF-Data"
    ... )
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Tuple
import os
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .core.reactor_core import (
    Library,
    Nuclide,
    NuclearDataCache,
    get_standard_endf_directory,
    organize_bulk_endf_downloads,
)
from .core.constants import ELEMENT_SYMBOLS, SYMBOL_TO_Z
from .utils.logging import get_logger

logger = get_logger("smrforge.data_downloader")


# URL source cache: remembers which source works best for each library
_source_cache: Dict[str, str] = {}  # library.value -> "iaea" or "nndc"


# Common SMR nuclides for pre-selected sets
COMMON_SMR_NUCLIDES = [
    "H1", "H2", "O16", "O17", "O18",  # Water/moderator
    "C12", "C13",  # Graphite
    "U235", "U238", "U236", "U237",  # Uranium
    "Pu239", "Pu240", "Pu241", "Pu242", "Pu238",  # Plutonium
    "Th232", "Th233",  # Thorium
    "Np237", "Am241", "Am243",  # Minor actinides
    "Zr90", "Zr91", "Zr92", "Zr94", "Zr96",  # Zirconium
    "Fe54", "Fe56", "Fe57", "Fe58",  # Iron
    "Cr50", "Cr52", "Cr53", "Cr54",  # Chromium
    "Ni58", "Ni60", "Ni61", "Ni62", "Ni64",  # Nickel
]


def _get_endf_url(nuclide: Nuclide, library: Library) -> str:
    """
    Generate download URL for ENDF file from IAEA Nuclear Data Services.
    
    Args:
        nuclide: Nuclide instance.
        library: Nuclear data library enum.
    
    Returns:
        URL string for downloading the ENDF file.
    """
    # IAEA Nuclear Data Services URLs
    base_urls = {
        Library.ENDF_B_VIII: "https://www-nds.iaea.org/exfor/endf/endfb8.0",
        Library.ENDF_B_VIII_1: "https://www-nds.iaea.org/exfor/endf/endfb8.1",
        Library.JEFF_33: "https://www-nds.iaea.org/exfor/endf/jeff3.3",
        Library.JENDL_5: "https://www-nds.iaea.org/exfor/endf/jendl5.0",
    }
    
    base_url = base_urls.get(library, base_urls[Library.ENDF_B_VIII_1])
    
    # Generate filename in standard format: n-ZZZ_Element_AAA.endf
    z_str = f"{nuclide.Z:03d}"
    symbol = ELEMENT_SYMBOLS[nuclide.Z]
    a_str = f"{nuclide.A:03d}"
    meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
    filename = f"n-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"
    
    return f"{base_url}/{filename}"


def _get_nndc_url(nuclide: Nuclide, library: Library) -> str:
    """
    Generate download URL for ENDF file from NNDC (alternative source).
    
    Args:
        nuclide: Nuclide instance.
        library: Nuclear data library enum.
    
    Returns:
        URL string for downloading the ENDF file.
    """
    # NNDC URLs
    base_urls = {
        Library.ENDF_B_VIII: "https://www.nndc.bnl.gov/endf/b8.0/endf",
        Library.ENDF_B_VIII_1: "https://www.nndc.bnl.gov/endf/b8.1/endf",
    }
    
    base_url = base_urls.get(library)
    if not base_url:
        # Fallback to IAEA for non-ENDF libraries
        return _get_endf_url(nuclide, library)
    
    # NNDC uses simpler naming: U235.endf
    filename = f"{nuclide.name}.endf"
    
    return f"{base_url}/{filename}"


def _get_download_urls(nuclide: Nuclide, library: Library) -> List[str]:
    """
    Get download URLs with source caching (preferred source first).
    
    Args:
        nuclide: Nuclide instance.
        library: Nuclear data library enum.
    
    Returns:
        List of URLs, with preferred source first based on cache.
    """
    iaea_url = _get_endf_url(nuclide, library)
    nndc_url = _get_nndc_url(nuclide, library)
    
    # Check cache for preferred source
    preferred_source = _source_cache.get(library.value)
    
    if preferred_source == "nndc":
        return [nndc_url, iaea_url]
    else:
        # Default to IAEA first (or if cache says "iaea")
        return [iaea_url, nndc_url]


def _cache_successful_source(url: str, library: Library):
    """
    Cache which source was successful for future downloads.
    
    Args:
        url: URL that succeeded.
        library: Library enum.
    """
    if "iaea.org" in url:
        _source_cache[library.value] = "iaea"
    elif "nndc.bnl.gov" in url:
        _source_cache[library.value] = "nndc"


def _parse_isotope_string(iso_str: str) -> Optional[Nuclide]:
    """
    Parse isotope string (e.g., "U235", "Pu239m1") to Nuclide.
    
    Args:
        iso_str: Isotope string.
    
    Returns:
        Nuclide instance if parsing succeeds, None otherwise.
    """
    iso_str = iso_str.strip()
    
    # Handle metastable states (e.g., "U239m1", "Am242m")
    if 'm' in iso_str.lower():
        parts = iso_str.lower().split('m')
        base = parts[0]
        m_str = parts[1] if len(parts) > 1 else "1"
        m = int(m_str) if m_str.isdigit() else 1
    else:
        base = iso_str
        m = 0
    
    # Extract element symbol and mass number
    # Pattern: ElementSymbol + MassNumber (e.g., "U235", "Pu239")
    import re
    match = re.match(r"^([A-Z][a-z]?)(\d+)$", base)
    if not match:
        return None
    
    symbol, a_str = match.groups()
    if symbol not in SYMBOL_TO_Z:
        return None
    
    Z = SYMBOL_TO_Z[symbol]
    A = int(a_str)
    
    return Nuclide(Z=Z, A=A, m=m)


def _expand_elements_to_nuclides(elements: List[str], library: Library) -> List[Nuclide]:
    """
    Expand element symbols to all available nuclides for that element.
    
    Note: This is a simplified version. In practice, you'd need to query
    the data source for available nuclides, or use a predefined list.
    
    Args:
        elements: List of element symbols (e.g., ["U", "Pu"]).
        library: Nuclear data library.
    
    Returns:
        List of Nuclide instances for common isotopes of those elements.
    """
    nuclides = []
    
    # Common isotopes for each element (simplified - would need full list)
    common_isotopes = {
        "U": [235, 238, 236, 237, 234, 233],
        "Pu": [239, 240, 241, 242, 238, 244],
        "Th": [232, 233, 230, 231],
        "H": [1, 2],
        "O": [16, 17, 18],
        "C": [12, 13],
        "Zr": [90, 91, 92, 94, 96],
        "Fe": [54, 56, 57, 58],
        "Cr": [50, 52, 53, 54],
        "Ni": [58, 60, 61, 62, 64],
    }
    
    for element in elements:
        if element not in SYMBOL_TO_Z:
            logger.warning(f"Unknown element symbol: {element}")
            continue
        
        Z = SYMBOL_TO_Z[element]
        isotopes = common_isotopes.get(element, [])
        
        for A in isotopes:
            nuclides.append(Nuclide(Z=Z, A=A, m=0))
    
    return nuclides


def download_file(
    url: str,
    output_path: Path,
    resume: bool = True,
    show_progress: bool = True,
    max_retries: int = 3,
    timeout: int = 30,
    session: Optional[requests.Session] = None,
) -> bool:
    """
    Download a file from URL with resume capability and progress indicator.
    
    Args:
        url: URL to download from.
        output_path: Path to save the file.
        resume: If True, resume interrupted downloads.
        show_progress: If True, show progress bar.
        max_retries: Maximum number of retry attempts.
        timeout: Request timeout in seconds.
    
    Returns:
        True if download succeeded, False otherwise.
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError(
            "requests library is required for downloads. "
            "Install with: pip install requests"
        )
    
    # Use provided session or create new one
    if session is None:
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    
    # Check if file exists and resume
    headers = {}
    if resume and output_path.exists():
        headers["Range"] = f"bytes={output_path.stat().st_size}-"
    
    try:
        response = session.get(url, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Handle partial content (resume)
        mode = "ab" if resume and output_path.exists() else "wb"
        
        total_size = int(response.headers.get("content-length", 0))
        if resume and output_path.exists():
            existing_size = output_path.stat().st_size
            total_size += existing_size
        
        with open(output_path, mode) as f:
            if show_progress and TQDM_AVAILABLE:
                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=output_path.name,
                    initial=output_path.stat().st_size if resume and output_path.exists() else 0,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def download_endf_data(
    library: Union[str, Library] = "ENDF/B-VIII.1",
    output_dir: Optional[Union[str, Path]] = None,
    elements: Optional[List[str]] = None,
    isotopes: Optional[List[str]] = None,
    nuclides: Optional[List[Nuclide]] = None,
    nuclide_set: Optional[str] = None,
    resume: bool = True,
    show_progress: bool = True,
    validate: bool = True,
    organize: bool = True,
    max_workers: int = 5,
) -> Dict[str, any]:
    """
    Download ENDF nuclear data files from NNDC/IAEA.
    
    Args:
        library: Library version (e.g., "ENDF/B-VIII.1") or Library enum.
        output_dir: Output directory. Defaults to standard ENDF directory.
        elements: List of element symbols to download (e.g., ["U", "Pu"]).
        isotopes: List of isotope strings (e.g., ["U235", "Pu239"]).
        nuclides: List of Nuclide instances.
        nuclide_set: Pre-defined set name (e.g., "common_smr").
        resume: If True, resume interrupted downloads.
        show_progress: If True, show progress indicators.
        validate: If True, validate downloaded files.
        organize: If True, organize files into standard structure.
        max_workers: Maximum concurrent downloads (default: 5). Uses parallel downloads when > 1.
    
    Returns:
        Dictionary with download statistics:
        - "downloaded": Number of files downloaded
        - "skipped": Number of files skipped (already exist)
        - "failed": Number of failed downloads
        - "total": Total number of files attempted
        - "output_dir": Path to output directory
    
    Example:
        >>> from smrforge.data_downloader import download_endf_data
        >>> 
        >>> # Download full library
        >>> stats = download_endf_data(
        ...     library="ENDF/B-VIII.1",
        ...     output_dir="~/ENDF-Data"
        ... )
        >>> 
        >>> # Download specific elements
        >>> stats = download_endf_data(
        ...     library="ENDF/B-VIII.1",
        ...     elements=["U", "Pu", "Th"],
        ...     output_dir="~/ENDF-Data"
        ... )
        >>> 
        >>> # Download common SMR nuclides
        >>> stats = download_endf_data(
        ...     library="ENDF/B-VIII.1",
        ...     nuclide_set="common_smr",
        ...     output_dir="~/ENDF-Data"
        ... )
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError(
            "requests library is required for downloads. "
            "Install with: pip install requests"
        )
    
    # Convert library string to enum
    if isinstance(library, str):
        library_map = {
            "ENDF/B-VIII.0": Library.ENDF_B_VIII,
            "ENDF/B-VIII.1": Library.ENDF_B_VIII_1,
            "JEFF-3.3": Library.JEFF_33,
            "JENDL-5.0": Library.JENDL_5,
        }
        library = library_map.get(library, Library.ENDF_B_VIII_1)
    
    # Determine output directory
    if output_dir is None:
        output_dir = get_standard_endf_directory()
    else:
        output_dir = Path(output_dir).expanduser().resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temporary download directory
    download_dir = output_dir / "downloads" / library.value
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine nuclides to download
    nuclide_list: List[Nuclide] = []
    
    if nuclide_set == "common_smr":
        nuclide_list = [_parse_isotope_string(iso) for iso in COMMON_SMR_NUCLIDES]
        nuclide_list = [n for n in nuclide_list if n is not None]
    elif nuclides:
        nuclide_list = nuclides
    elif isotopes:
        nuclide_list = [_parse_isotope_string(iso) for iso in isotopes]
        nuclide_list = [n for n in nuclide_list if n is not None]
    elif elements:
        nuclide_list = _expand_elements_to_nuclides(elements, library)
    else:
        # Full library - would need to query available nuclides
        # For now, use common SMR set as default
        logger.warning(
            "Full library download not yet implemented. "
            "Using common_smr set instead. "
            "Specify elements, isotopes, or nuclide_set for selective downloads."
        )
        nuclide_list = [_parse_isotope_string(iso) for iso in COMMON_SMR_NUCLIDES]
        nuclide_list = [n for n in nuclide_list if n is not None]
    
    if not nuclide_list:
        raise ValueError("No nuclides specified for download")
    
    logger.info(f"Downloading {len(nuclide_list)} nuclides from {library.value}")
    
    # Download files
    stats = {
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "total": len(nuclide_list),
        "output_dir": str(output_dir),
    }
    
    for nuclide in nuclide_list:
        # Generate filename using the same method as NuclearDataCache
        z_str = f"{nuclide.Z:03d}"
        symbol = ELEMENT_SYMBOLS[nuclide.Z]
        a_str = f"{nuclide.A:03d}"
        meta_suffix = f"m{nuclide.m}" if nuclide.m > 0 else ""
        filename = f"n-{z_str}_{symbol}_{a_str}{meta_suffix}.endf"
        filepath = download_dir / filename
        
        # Skip if already exists and resume is enabled
        if resume and filepath.exists():
            if validate:
                # Quick validation check
                if NuclearDataCache._validate_endf_file(filepath):
                    continue  # Skip, will count later
                else:
                    # Invalid file, re-download
                    filepath.unlink()
            else:
                continue  # Skip, will count later
        
        # Get URLs with caching (preferred source first)
        urls = _get_download_urls(nuclide, library)
        download_tasks.append((nuclide, filepath, urls))
    
    # Count skipped files
    skipped_count = len(nuclide_list) - len(download_tasks)
    
    # Initialize stats
    stats = {
        "downloaded": 0,
        "skipped": skipped_count,
        "failed": 0,
        "total": len(nuclide_list),
        "output_dir": str(output_dir),
    }
    
    # Create shared session with connection pooling for parallel downloads
    if download_tasks and max_workers > 1:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers * 2,
            max_retries=retry_strategy,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    else:
        session = None
    
    # Download files in parallel or sequentially
    if max_workers > 1 and len(download_tasks) > 1:
        # Parallel download
        _download_parallel(
            download_tasks,
            stats,
            session=session,
            resume=resume,
            show_progress=show_progress,
            validate=validate,
            library=library,
            max_workers=max_workers,
        )
    else:
        # Sequential download (original behavior)
        for nuclide, filepath, urls in download_tasks:
            success = False
            for url in urls:
                if download_file(
                    url, filepath, resume=resume, show_progress=show_progress, session=session
                ):
                    # Validate if requested
                    if validate:
                        if NuclearDataCache._validate_endf_file(filepath):
                            success = True
                            # Cache successful source
                            _cache_successful_source(url, library)
                            break
                        else:
                            # Invalid file, try next URL
                            filepath.unlink()
                            continue
                    else:
                        success = True
                        _cache_successful_source(url, library)
                        break
            
            if success:
                stats["downloaded"] += 1
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to download {nuclide.name}")
    
    # Organize files if requested
    if organize and stats["downloaded"] > 0:
        logger.info("Organizing downloaded files...")
        library_version = "VIII.1" if library == Library.ENDF_B_VIII_1 else "VIII.0"
        organize_stats = organize_bulk_endf_downloads(
            source_dir=download_dir,
            target_dir=output_dir,
            library_version=library_version,
            create_structure=True,
        )
        stats["organized"] = organize_stats.get("files_organized", 0)
    
    logger.info(
        f"Download complete: {stats['downloaded']} downloaded, "
        f"{stats['skipped']} skipped, {stats['failed']} failed"
    )
    
    return stats


def _download_parallel(
    download_tasks: List[Tuple[Nuclide, Path, List[str]]],
    stats: Dict[str, int],
    session: Optional[requests.Session],
    resume: bool,
    show_progress: bool,
    validate: bool,
    library: Library,
    max_workers: int,
):
    """
    Download files in parallel using ThreadPoolExecutor.
    
    Args:
        download_tasks: List of (nuclide, filepath, urls) tuples.
        stats: Statistics dictionary to update.
        session: Shared requests session.
        resume: Whether to resume interrupted downloads.
        show_progress: Whether to show progress.
        validate: Whether to validate files.
        library: Library enum.
        max_workers: Maximum number of parallel workers.
    """
    def download_single_file(task: Tuple[Nuclide, Path, List[str]]) -> Tuple[Nuclide, bool, Optional[str]]:
        """Download a single file and return (nuclide, success, successful_url)."""
        nuclide, filepath, urls = task
        for url in urls:
            if download_file(
                url, filepath, resume=resume, show_progress=False, session=session
            ):
                # Validate if requested
                if validate:
                    if NuclearDataCache._validate_endf_file(filepath):
                        return (nuclide, True, url)
                    else:
                        # Invalid file, try next URL
                        filepath.unlink()
                        continue
                else:
                    return (nuclide, True, url)
        return (nuclide, False, None)
    
    # Create progress bar if requested
    if show_progress and TQDM_AVAILABLE:
        pbar = tqdm(total=len(download_tasks), desc="Downloading ENDF files", unit="file")
    else:
        pbar = None
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single_file, task): task for task in download_tasks}
        
        for future in as_completed(futures):
            nuclide, success, successful_url = future.result()
            
            if pbar:
                pbar.set_description(f"Downloading {nuclide.name}")
                pbar.update(1)
            
            if success:
                stats["downloaded"] += 1
                if successful_url:
                    _cache_successful_source(successful_url, library)
                if pbar:
                    pbar.set_postfix({
                        "Downloaded": stats["downloaded"],
                        "Failed": stats["failed"]
                    })
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to download {nuclide.name}")
                if pbar:
                    pbar.set_postfix({
                        "Downloaded": stats["downloaded"],
                        "Failed": stats["failed"]
                    })
    
    if pbar:
        pbar.close()


def download_preprocessed_library(
    library: Union[str, Library] = "ENDF/B-VIII.1",
    nuclides: Union[str, List[Nuclide]] = "common_smr",
    output_dir: Optional[Union[str, Path]] = None,
    show_progress: bool = True,
) -> Dict[str, any]:
    """
    Download pre-processed Zarr library (placeholder for Phase 2).
    
    This function will be implemented in Phase 2 to download pre-processed
    libraries from GitHub Releases or Zenodo.
    
    Args:
        library: Library version.
        nuclides: Nuclide set name or list of Nuclides.
        output_dir: Output directory.
        show_progress: If True, show progress indicators.
    
    Returns:
        Dictionary with download statistics.
    """
    logger.warning(
        "Pre-processed library download not yet implemented. "
        "This feature will be available in Phase 2. "
        "Use download_endf_data() to download raw ENDF files instead."
    )
    
    # For now, fall back to raw ENDF download
    if isinstance(nuclides, str):
        return download_endf_data(
            library=library,
            output_dir=output_dir,
            nuclide_set=nuclides,
            show_progress=show_progress,
        )
    else:
        return download_endf_data(
            library=library,
            output_dir=output_dir,
            nuclides=nuclides,
            show_progress=show_progress,
        )
