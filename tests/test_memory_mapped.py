"""
Unit tests for memory-mapped array utilities.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from smrforge.utils.memory_mapped import MemoryMappedArray


class TestMemoryMappedArray:
    """Tests for MemoryMappedArray class."""

    def test_memory_mapped_array_creation(self):
        """Test creating memory-mapped array."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(100, 10),
                dtype=np.float64,
                mode='w+',
                create=True
            )
            
            assert arr.shape == (100, 10)
            assert arr.dtype == np.float64
            assert arr.path == temp_path
            
            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_read_write(self):
        """Test reading and writing to memory-mapped array."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='w+',
                create=True
            )
            
            # Write value
            arr[0, 0] = 42.0
            
            # Read value
            assert arr[0, 0] == 42.0
            
            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_slicing(self):
        """Test array slicing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        arr = None
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='w+',
                create=True
            )
            
            # Write to slice
            arr[0:5, 0:3] = 1.0
            
            # Read slice
            slice_data = arr[0:5, 0:3]
            assert np.all(slice_data == 1.0)
            
            arr.close()
            arr = None  # Mark as closed
        finally:
            if arr is not None:
                try:
                    arr.close()
                except:
                    pass
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except PermissionError:
                    # File may still be in use, skip cleanup
                    pass

    def test_memory_mapped_array_property(self):
        """Test array property access."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='w+',
                create=True
            )
            
            assert isinstance(arr.array, np.memmap)
            assert arr.array.shape == (10, 5)
            
            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_closed_access(self):
        """Test accessing closed array raises error."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='w+',
                create=True
            )
            
            arr.close()
            
            with pytest.raises(RuntimeError, match="closed"):
                _ = arr.array
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_context_manager(self):
        """Test using memory-mapped array as context manager."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            with MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='w+',
                create=True
            ) as arr:
                arr[0, 0] = 42.0
                assert arr[0, 0] == 42.0
            
            # Array should be closed after context exit
            # (reopening to verify data persisted)
            arr2 = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode='r'
            )
            assert arr2[0, 0] == 42.0
            arr2.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_different_dtype(self):
        """Test memory-mapped array with different dtype."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as f:
            temp_path = Path(f.name)
        
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float32,
                mode='w+',
                create=True
            )
            
            assert arr.dtype == np.float32
            assert arr.array.dtype == np.float32
            
            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()
