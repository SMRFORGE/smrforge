"""
Memory-mapped file utilities for large datasets.

This module provides utilities for using memory-mapped arrays for large
cross-section and flux data, enabling datasets larger than RAM.

Phase 3 optimization - enables larger problems.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.utils.memory_mapped")


class MemoryMappedArray:
    """
    Wrapper for memory-mapped NumPy arrays.
    
    Provides convenient interface for memory-mapped arrays with automatic
    cleanup and shape validation.
    
    Example:
        >>> from smrforge.utils.memory_mapped import MemoryMappedArray
        >>> 
        >>> # Create memory-mapped array for large cross-section data
        >>> xs_data = MemoryMappedArray(
        ...     path='xs_data.dat',
        ...     shape=(1000, 100),
        ...     dtype=np.float64,
        ...     mode='w+'  # Create new file
        ... )
        >>> 
        >>> # Use like normal NumPy array
        >>> xs_data[0, 0] = 1.5
        >>> value = xs_data[0, 0]
        >>> 
        >>> # Cleanup
        >>> xs_data.close()
    """
    
    def __init__(
        self,
        path: str,
        shape: Tuple[int, ...],
        dtype: np.dtype = np.float64,
        mode: str = "r",
        create: bool = False,
    ):
        """
        Initialize memory-mapped array.
        
        Args:
            path: Path to memory-mapped file
            shape: Array shape
            dtype: Data type
            mode: Access mode ('r' = read, 'w+' = read/write, 'c' = copy-on-write)
            create: Whether to create file if it doesn't exist
        """
        self.path = Path(path)
        self.shape = shape
        self.dtype = dtype
        self.mode = mode
        self._array: Optional[np.memmap] = None
        
        # Create file if needed
        if create and not self.path.exists():
            logger.info(f"Creating memory-mapped file: {self.path}")
            # Create file with zeros
            arr = np.memmap(str(self.path), dtype=dtype, mode='w+', shape=shape)
            arr[:] = 0.0
            del arr
        
        # Open memory-mapped array
        self._array = np.memmap(str(self.path), dtype=dtype, mode=mode, shape=shape)
        
        logger.debug(
            f"Memory-mapped array opened: {self.path} "
            f"({shape}, {dtype}, mode='{mode}')"
        )
    
    @property
    def array(self) -> np.memmap:
        """Get the underlying memory-mapped array."""
        if self._array is None:
            raise RuntimeError("Memory-mapped array is closed")
        return self._array
    
    def __getitem__(self, key):
        """Array indexing."""
        return self.array[key]
    
    def __setitem__(self, key, value):
        """
        Array assignment.
        
        Args:
            key: Array index or slice
            value: Value to assign
        
        Raises:
            ValueError: If array is opened in read-only mode.
        """
        if self.mode == 'r':
            raise ValueError("Cannot write to read-only memory-mapped array")
        self.array[key] = value
    
    def __array__(self):
        """Convert to NumPy array (for compatibility)."""
        return np.array(self.array)
    
    def close(self):
        """Close memory-mapped array."""
        if self._array is not None:
            del self._array
            self._array = None
            logger.debug(f"Memory-mapped array closed: {self.path}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


def create_memory_mapped_cross_sections(
    path: str,
    n_materials: int,
    n_groups: int,
    dtype: np.dtype = np.float64,
) -> Tuple[MemoryMappedArray, MemoryMappedArray, MemoryMappedArray]:
    """
    Create memory-mapped arrays for cross-section data.
    
    Creates three memory-mapped files:
    - sigma_t.dat - Total cross sections [n_materials, n_groups]
    - sigma_s.dat - Scattering cross sections [n_materials, n_groups, n_groups]
    - sigma_f.dat - Fission cross sections [n_materials, n_groups]
    
    Args:
        path: Base path for files (e.g., 'xs_data' -> 'xs_data_sigma_t.dat')
        n_materials: Number of materials
        n_groups: Number of energy groups
        dtype: Data type
    
    Returns:
        Tuple of (sigma_t, sigma_s, sigma_f) memory-mapped arrays
    """
    base_path = Path(path)
    
    # Create directory if needed
    base_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create memory-mapped arrays
    sigma_t = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_t.dat")),
        shape=(n_materials, n_groups),
        dtype=dtype,
        mode='w+',
        create=True,
    )
    
    sigma_s = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_s.dat")),
        shape=(n_materials, n_groups, n_groups),
        dtype=dtype,
        mode='w+',
        create=True,
    )
    
    sigma_f = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_f.dat")),
        shape=(n_materials, n_groups),
        dtype=dtype,
        mode='w+',
        create=True,
    )
    
    logger.info(
        f"Created memory-mapped cross-section files: "
        f"{n_materials} materials, {n_groups} groups"
    )
    
    return sigma_t, sigma_s, sigma_f


def load_memory_mapped_cross_sections(
    path: str,
    n_materials: int,
    n_groups: int,
    dtype: np.dtype = np.float64,
    mode: str = "r",
) -> Tuple[MemoryMappedArray, MemoryMappedArray, MemoryMappedArray]:
    """
    Load existing memory-mapped cross-section files.
    
    Args:
        path: Base path for files (e.g., 'xs_data' -> 'xs_data_sigma_t.dat')
        n_materials: Number of materials
        n_groups: Number of energy groups
        dtype: NumPy dtype for arrays (default: float64)
        mode: Access mode ('r' for read-only, 'r+' for read-write)
    
    Returns:
        Tuple of (sigma_t, sigma_s, sigma_f) MemoryMappedArray objects
    
    Raises:
        FileNotFoundError: If cross-section files don't exist.
        OSError: If files cannot be opened.
        ValueError: If mode is invalid or dimensions are invalid (<= 0).
    
    Example:
        >>> from smrforge.utils.memory_mapped import load_memory_mapped_cross_sections
        >>> 
        >>> # Load existing memory-mapped arrays
        >>> sigma_t, sigma_s, sigma_f = load_memory_mapped_cross_sections(
        ...     path="xs_data",
        ...     n_materials=3,
        ...     n_groups=4,
        ...     mode='r'  # Read-only
        ... )
        >>> 
        >>> # Read data
        >>> xs_value = sigma_t[0, 0]  # Material 0, group 0
        >>> 
        >>> # Close when done
        >>> sigma_t.close()
        >>> sigma_s.close()
        >>> sigma_f.close()
    """
    base_path = Path(path)
    
    # Load memory-mapped arrays
    sigma_t = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_t.dat")),
        shape=(n_materials, n_groups),
        dtype=dtype,
        mode=mode,
    )
    
    sigma_s = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_s.dat")),
        shape=(n_materials, n_groups, n_groups),
        dtype=dtype,
        mode=mode,
    )
    
    sigma_f = MemoryMappedArray(
        path=str(base_path.with_name(base_path.name + "_sigma_f.dat")),
        shape=(n_materials, n_groups),
        dtype=dtype,
        mode=mode,
    )
    
    logger.info(
        f"Loaded memory-mapped cross-section files: "
        f"{n_materials} materials, {n_groups} groups"
    )
    
    return sigma_t, sigma_s, sigma_f
