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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(100, 10),
                dtype=np.float64,
                mode="w+",
                create=True,
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        arr = None
        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
            )

            assert isinstance(arr.array, np.memmap)
            assert arr.array.shape == (10, 5)

            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_closed_access(self):
        """Test accessing closed array raises error."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
            )

            arr.close()

            with pytest.raises(RuntimeError, match="closed"):
                _ = arr.array
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_context_manager(self):
        """Test using memory-mapped array as context manager."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            with MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
            ) as arr:
                arr[0, 0] = 42.0
                assert arr[0, 0] == 42.0

            # Array should be closed after context exit
            # (reopening to verify data persisted)
            arr2 = MemoryMappedArray(
                path=str(temp_path), shape=(10, 5), dtype=np.float64, mode="r"
            )
            assert arr2[0, 0] == 42.0
            arr2.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_different_dtype(self):
        """Test memory-mapped array with different dtype."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float32,
                mode="w+",
                create=True,
            )

            assert arr.dtype == np.float32
            assert arr.array.dtype == np.float32

            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_read_only_mode(self):
        """Test that read-only mode prevents writing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            # Create array first
            arr_write = MemoryMappedArray(
                path=str(temp_path),
                shape=(10, 5),
                dtype=np.float64,
                mode="w+",
                create=True,
            )
            arr_write[0, 0] = 42.0
            arr_write.close()

            # Open in read-only mode
            arr_read = MemoryMappedArray(
                path=str(temp_path), shape=(10, 5), dtype=np.float64, mode="r"
            )

            # Should be able to read
            assert arr_read[0, 0] == 42.0

            # Should not be able to write
            with pytest.raises(ValueError, match="read-only"):
                arr_read[0, 0] = 100.0

            arr_read.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_memory_mapped_array_array_conversion(self):
        """Test __array__ method for NumPy compatibility."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dat") as f:
            temp_path = Path(f.name)

        try:
            arr = MemoryMappedArray(
                path=str(temp_path),
                shape=(5, 3),
                dtype=np.float64,
                mode="w+",
                create=True,
            )

            arr[0, 0] = 1.5
            arr[1, 1] = 2.5

            # Convert to NumPy array
            np_arr = np.array(arr)

            assert isinstance(np_arr, np.ndarray)
            assert np_arr.shape == (5, 3)
            assert np_arr[0, 0] == 1.5
            assert np_arr[1, 1] == 2.5

            arr.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestCreateMemoryMappedCrossSections:
    """Tests for create_memory_mapped_cross_sections function."""

    def test_create_memory_mapped_cross_sections(self, tmp_path):
        """Test creating memory-mapped cross-section arrays."""
        from smrforge.utils.memory_mapped import create_memory_mapped_cross_sections

        base_path = tmp_path / "xs_data"

        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4, dtype=np.float64
        )

        try:
            # Check that files were created
            assert (base_path.parent / f"{base_path.name}_sigma_t.dat").exists()
            assert (base_path.parent / f"{base_path.name}_sigma_s.dat").exists()
            assert (base_path.parent / f"{base_path.name}_sigma_f.dat").exists()

            # Check shapes
            assert sigma_t.shape == (2, 4)
            assert sigma_s.shape == (2, 4, 4)
            assert sigma_f.shape == (2, 4)

            # Check that arrays are writable
            sigma_t[0, 0] = 1.0
            sigma_s[0, 0, 0] = 2.0
            sigma_f[0, 0] = 3.0

            assert sigma_t[0, 0] == 1.0
            assert sigma_s[0, 0, 0] == 2.0
            assert sigma_f[0, 0] == 3.0
        finally:
            sigma_t.close()
            sigma_s.close()
            sigma_f.close()

    def test_create_memory_mapped_cross_sections_custom_dtype(self, tmp_path):
        """Test creating cross-section arrays with custom dtype."""
        from smrforge.utils.memory_mapped import create_memory_mapped_cross_sections

        base_path = tmp_path / "xs_data"

        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=3, n_groups=2, dtype=np.float32
        )

        try:
            assert sigma_t.dtype == np.float32
            assert sigma_s.dtype == np.float32
            assert sigma_f.dtype == np.float32
        finally:
            sigma_t.close()
            sigma_s.close()
            sigma_f.close()

    def test_create_memory_mapped_cross_sections_directory_creation(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        from smrforge.utils.memory_mapped import create_memory_mapped_cross_sections

        base_path = tmp_path / "new_dir" / "xs_data"

        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4
        )

        try:
            # Directory should be created
            assert base_path.parent.exists()
            assert base_path.parent.is_dir()
        finally:
            sigma_t.close()
            sigma_s.close()
            sigma_f.close()


class TestLoadMemoryMappedCrossSections:
    """Tests for load_memory_mapped_cross_sections function."""

    def test_load_memory_mapped_cross_sections(self, tmp_path):
        """Test loading existing memory-mapped cross-section arrays."""
        from smrforge.utils.memory_mapped import (
            create_memory_mapped_cross_sections,
            load_memory_mapped_cross_sections,
        )

        base_path = tmp_path / "xs_data"

        # Create arrays first
        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4
        )

        # Write some data
        sigma_t[0, 0] = 10.0
        sigma_s[0, 0, 0] = 20.0
        sigma_f[0, 0] = 30.0

        sigma_t.close()
        sigma_s.close()
        sigma_f.close()

        # Load arrays
        sigma_t_loaded, sigma_s_loaded, sigma_f_loaded = (
            load_memory_mapped_cross_sections(
                path=str(base_path), n_materials=2, n_groups=4, mode="r"
            )
        )

        try:
            # Check that data was loaded correctly
            assert sigma_t_loaded[0, 0] == 10.0
            assert sigma_s_loaded[0, 0, 0] == 20.0
            assert sigma_f_loaded[0, 0] == 30.0

            # Check shapes
            assert sigma_t_loaded.shape == (2, 4)
            assert sigma_s_loaded.shape == (2, 4, 4)
            assert sigma_f_loaded.shape == (2, 4)
        finally:
            sigma_t_loaded.close()
            sigma_s_loaded.close()
            sigma_f_loaded.close()

    def test_load_memory_mapped_cross_sections_read_write_mode(self, tmp_path):
        """Test loading arrays in read-write mode."""
        from smrforge.utils.memory_mapped import (
            create_memory_mapped_cross_sections,
            load_memory_mapped_cross_sections,
        )

        base_path = tmp_path / "xs_data"

        # Create arrays
        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4
        )
        sigma_t[0, 0] = 5.0
        sigma_t.close()
        sigma_s.close()
        sigma_f.close()

        # Load in read-write mode
        sigma_t_loaded, _, _ = load_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4, mode="r+"
        )

        try:
            # Should be able to read
            assert sigma_t_loaded[0, 0] == 5.0

            # Should be able to write
            sigma_t_loaded[0, 0] = 15.0
            assert sigma_t_loaded[0, 0] == 15.0
        finally:
            sigma_t_loaded.close()

    def test_load_memory_mapped_cross_sections_file_not_found(self, tmp_path):
        """Test that loading non-existent files raises FileNotFoundError."""
        from smrforge.utils.memory_mapped import load_memory_mapped_cross_sections

        base_path = tmp_path / "nonexistent_xs_data"

        with pytest.raises(FileNotFoundError):
            load_memory_mapped_cross_sections(
                path=str(base_path), n_materials=2, n_groups=4
            )

    def test_load_memory_mapped_cross_sections_custom_dtype(self, tmp_path):
        """Test loading arrays with custom dtype."""
        from smrforge.utils.memory_mapped import (
            create_memory_mapped_cross_sections,
            load_memory_mapped_cross_sections,
        )

        base_path = tmp_path / "xs_data"

        # Create with float32
        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4, dtype=np.float32
        )
        sigma_t.close()
        sigma_s.close()
        sigma_f.close()

        # Load with float32
        sigma_t_loaded, sigma_s_loaded, sigma_f_loaded = (
            load_memory_mapped_cross_sections(
                path=str(base_path), n_materials=2, n_groups=4, dtype=np.float32
            )
        )

        try:
            assert sigma_t_loaded.dtype == np.float32
            assert sigma_s_loaded.dtype == np.float32
            assert sigma_f_loaded.dtype == np.float32
        finally:
            sigma_t_loaded.close()
            sigma_s_loaded.close()
            sigma_f_loaded.close()


class TestMemoryMappedArrayEdgeCases:
    """Edge case tests for MemoryMappedArray."""

    def test_memory_mapped_array_mode_c(self, tmp_path):
        """Test memory-mapped array with copy-on-write mode."""
        base_path = tmp_path / "test_data"

        # Create array first
        arr_write = MemoryMappedArray(
            path=str(base_path), shape=(10, 5), dtype=np.float64, mode="w+", create=True
        )
        arr_write[0, 0] = 42.0
        arr_write.close()

        # Open in copy-on-write mode
        arr_cow = MemoryMappedArray(
            path=str(base_path),
            shape=(10, 5),
            dtype=np.float64,
            mode="c",  # Copy-on-write
        )

        try:
            # Should be able to read
            assert arr_cow[0, 0] == 42.0

            # Writing in copy-on-write mode should work (creates copy)
            arr_cow[0, 0] = 100.0
            assert arr_cow[0, 0] == 100.0

            # Original file should still have original value
            arr_orig = MemoryMappedArray(
                path=str(base_path), shape=(10, 5), dtype=np.float64, mode="r"
            )
            assert arr_orig[0, 0] == 42.0
            arr_orig.close()
        finally:
            arr_cow.close()

    def test_memory_mapped_array_create_false_existing_file(self, tmp_path):
        """Test that create=False works with existing file."""
        base_path = tmp_path / "existing_data"

        # Create file first
        arr1 = MemoryMappedArray(
            path=str(base_path), shape=(10, 5), dtype=np.float64, mode="w+", create=True
        )
        arr1[0, 0] = 50.0
        arr1.close()

        # Open without create=True (should work since file exists)
        arr2 = MemoryMappedArray(
            path=str(base_path), shape=(10, 5), dtype=np.float64, mode="r", create=False
        )

        try:
            assert arr2[0, 0] == 50.0
        finally:
            arr2.close()

    def test_memory_mapped_array_del_cleanup(self, tmp_path):
        """Test that __del__ properly cleans up."""
        base_path = tmp_path / "del_test"

        arr = MemoryMappedArray(
            path=str(base_path), shape=(5, 3), dtype=np.float64, mode="w+", create=True
        )
        arr[0, 0] = 1.0

        # Delete should close the array
        del arr

        # File should still exist and be readable
        arr2 = MemoryMappedArray(
            path=str(base_path), shape=(5, 3), dtype=np.float64, mode="r"
        )
        try:
            assert arr2[0, 0] == 1.0
        finally:
            arr2.close()

    def test_memory_mapped_array_double_close(self, tmp_path):
        """Test that closing twice doesn't raise error."""
        base_path = tmp_path / "double_close"

        arr = MemoryMappedArray(
            path=str(base_path), shape=(5, 3), dtype=np.float64, mode="w+", create=True
        )

        arr.close()
        # Closing again should not raise error
        arr.close()

    def test_memory_mapped_array_getitem_slice(self, tmp_path):
        """Test __getitem__ with various slice patterns."""
        base_path = tmp_path / "slice_test"

        arr = MemoryMappedArray(
            path=str(base_path),
            shape=(10, 10),
            dtype=np.float64,
            mode="w+",
            create=True,
        )

        try:
            # Fill with values
            for i in range(10):
                for j in range(10):
                    arr[i, j] = i * 10 + j

            # Test various slice patterns
            assert arr[0, 0] == 0.0
            assert arr[5, 5] == 55.0
            assert arr[9, 9] == 99.0

            # Test row slice
            row = arr[5, :]
            assert len(row) == 10
            assert row[0] == 50.0

            # Test column slice
            col = arr[:, 5]
            assert len(col) == 10
            assert col[0] == 5.0

            # Test 2D slice
            block = arr[2:5, 2:5]
            assert block.shape == (3, 3)
            assert block[0, 0] == 22.0
        finally:
            arr.close()

    def test_memory_mapped_array_setitem_slice(self, tmp_path):
        """Test __setitem__ with various slice patterns."""
        base_path = tmp_path / "setitem_slice"

        arr = MemoryMappedArray(
            path=str(base_path),
            shape=(10, 10),
            dtype=np.float64,
            mode="w+",
            create=True,
        )

        try:
            # Set entire row
            arr[5, :] = 42.0
            assert np.all(arr[5, :] == 42.0)

            # Set entire column
            arr[:, 3] = 99.0
            assert np.all(arr[:, 3] == 99.0)

            # Set 2D block
            arr[2:5, 2:5] = 77.0
            assert np.all(arr[2:5, 2:5] == 77.0)

            # Set single value
            arr[0, 0] = 1.5
            assert arr[0, 0] == 1.5
        finally:
            arr.close()

    def test_create_memory_mapped_cross_sections_nested_path(self, tmp_path):
        """Test creating cross-sections with nested directory path."""
        from smrforge.utils.memory_mapped import create_memory_mapped_cross_sections

        base_path = tmp_path / "nested" / "dir" / "xs_data"

        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=3
        )

        try:
            # Directory should be created
            assert base_path.parent.exists()
            assert base_path.parent.is_dir()

            # Files should exist
            assert (base_path.parent / f"{base_path.name}_sigma_t.dat").exists()
        finally:
            sigma_t.close()
            sigma_s.close()
            sigma_f.close()

    def test_load_memory_mapped_cross_sections_mode_r_plus(self, tmp_path):
        """Test loading cross-sections in r+ mode."""
        from smrforge.utils.memory_mapped import (
            create_memory_mapped_cross_sections,
            load_memory_mapped_cross_sections,
        )

        base_path = tmp_path / "xs_data"

        # Create arrays
        sigma_t, _, _ = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4
        )
        sigma_t[0, 0] = 10.0
        sigma_t.close()

        # Load in r+ mode
        sigma_t_loaded, _, _ = load_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=4, mode="r+"
        )

        try:
            # Should be able to read
            assert sigma_t_loaded[0, 0] == 10.0

            # Should be able to write
            sigma_t_loaded[0, 0] = 20.0
            assert sigma_t_loaded[0, 0] == 20.0
        finally:
            sigma_t_loaded.close()


class TestMemoryMappedEdgeCases:
    """Edge case tests for memory_mapped.py to improve coverage to 60%+."""

    def test_memory_mapped_array_read_only_write_error(self, tmp_path):
        """Test that writing to read-only array raises ValueError."""
        temp_file = tmp_path / "test.dat"

        # Create file in write mode first
        arr_write = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        )
        arr_write[0] = 5.0
        arr_write.close()

        # Open in read-only mode
        arr_read = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="r"
        )

        try:
            # Should raise ValueError when trying to write
            with pytest.raises(ValueError, match="read-only"):
                arr_read[0] = 10.0
        finally:
            arr_read.close()

    def test_memory_mapped_array_close_multiple_times(self, tmp_path):
        """Test closing array multiple times is safe."""
        temp_file = tmp_path / "test.dat"

        arr = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        )

        # Close multiple times should be safe
        arr.close()
        arr.close()
        arr.close()

        # Accessing array after close should raise RuntimeError
        with pytest.raises(RuntimeError, match="closed"):
            _ = arr.array

    def test_memory_mapped_array_property_after_close(self, tmp_path):
        """Test accessing array property after close raises RuntimeError."""
        temp_file = tmp_path / "test.dat"

        arr = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        )
        arr.close()

        with pytest.raises(RuntimeError, match="closed"):
            _ = arr.array

    def test_memory_mapped_array_context_manager(self, tmp_path):
        """Test using array as context manager."""
        temp_file = tmp_path / "test.dat"

        with MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        ) as arr:
            arr[0] = 42.0
            assert arr[0] == 42.0

        # Array should be closed after context exit
        with pytest.raises(RuntimeError, match="closed"):
            _ = arr.array

    def test_memory_mapped_array_array_conversion(self, tmp_path):
        """Test __array__ method converts to NumPy array."""
        temp_file = tmp_path / "test.dat"

        arr = MemoryMappedArray(
            path=str(temp_file), shape=(5, 3), dtype=np.float64, mode="w+", create=True
        )

        try:
            arr[0, 0] = 1.5
            arr[1, 2] = 2.5

            # Convert to NumPy array
            np_arr = np.array(arr)

            assert isinstance(np_arr, np.ndarray)
            assert np_arr[0, 0] == 1.5
            assert np_arr[1, 2] == 2.5
            assert np_arr.shape == (5, 3)
        finally:
            arr.close()

    def test_memory_mapped_array_mode_c(self, tmp_path):
        """Test memory-mapped array with copy-on-write mode."""
        temp_file = tmp_path / "test.dat"

        # Create file first
        arr_write = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        )
        arr_write[:] = np.arange(10, dtype=np.float64)
        arr_write.close()

        # Open in copy-on-write mode
        arr_cow = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="c"
        )

        try:
            # Should be able to read
            assert arr_cow[0] == 0.0
            assert arr_cow[9] == 9.0
        finally:
            arr_cow.close()

    def test_memory_mapped_array_create_false_file_exists(self, tmp_path):
        """Test creating array with create=False when file exists."""
        temp_file = tmp_path / "test.dat"

        # Create file first
        arr1 = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="w+", create=True
        )
        arr1.close()

        # Open existing file with create=False
        arr2 = MemoryMappedArray(
            path=str(temp_file), shape=(10,), dtype=np.float64, mode="r", create=False
        )

        try:
            assert arr2.shape == (10,)
        finally:
            arr2.close()

    def test_create_memory_mapped_cross_sections_custom_dtype(self, tmp_path):
        """Test creating cross-sections with custom dtype."""
        from smrforge.utils.memory_mapped import create_memory_mapped_cross_sections

        base_path = tmp_path / "xs_data"

        sigma_t, sigma_s, sigma_f = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=3, dtype=np.float32
        )

        try:
            assert sigma_t.dtype == np.float32
            assert sigma_s.dtype == np.float32
            assert sigma_f.dtype == np.float32
        finally:
            sigma_t.close()
            sigma_s.close()
            sigma_f.close()

    def test_load_memory_mapped_cross_sections_custom_dtype(self, tmp_path):
        """Test loading cross-sections with custom dtype."""
        from smrforge.utils.memory_mapped import (
            create_memory_mapped_cross_sections,
            load_memory_mapped_cross_sections,
        )

        base_path = tmp_path / "xs_data"

        # Create with float64
        sigma_t, _, _ = create_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=3, dtype=np.float64
        )
        sigma_t.close()

        # Load with same dtype
        sigma_t_loaded, _, _ = load_memory_mapped_cross_sections(
            path=str(base_path), n_materials=2, n_groups=3, dtype=np.float64, mode="r"
        )

        try:
            assert sigma_t_loaded.dtype == np.float64
        finally:
            sigma_t_loaded.close()
