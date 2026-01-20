"""
Unit tests for optimization utilities.
"""

import numpy as np
import pytest

from smrforge.utils.optimization_utils import (
    batch_vectorized_operations,
    ensure_contiguous,
    smart_array_copy,
    vectorized_cross_section_lookup,
    vectorized_normalize,
    zero_copy_slice,
)


class TestEnsureContiguous:
    """Tests for ensure_contiguous function."""

    def test_ensure_contiguous_already_contiguous(self):
        """Test with already contiguous array."""
        arr = np.array([1, 2, 3, 4, 5])
        result = ensure_contiguous(arr)
        
        assert np.array_equal(result, arr)
        assert result is arr  # Should be same object (view)

    def test_ensure_contiguous_non_contiguous(self):
        """Test with non-contiguous array."""
        arr = np.array([1, 2, 3, 4, 5])
        strided = arr[::2]  # Non-contiguous
        
        result = ensure_contiguous(strided)
        
        assert np.array_equal(result, np.array([1, 3, 5]))
        assert result.flags['C_CONTIGUOUS']

    def test_ensure_contiguous_force_copy(self):
        """Test with force_copy=True."""
        arr = np.array([1, 2, 3])
        result = ensure_contiguous(arr, force_copy=True)
        
        assert np.array_equal(result, arr)
        # Should be contiguous
        assert result.flags['C_CONTIGUOUS']


class TestVectorizedCrossSectionLookup:
    """Tests for vectorized_cross_section_lookup function."""

    def test_vectorized_cross_section_lookup(self):
        """Test vectorized cross-section lookup."""
        material_ids = np.array([0, 1, 0, 1])
        energy_groups = np.array([0, 1, 2, 0])
        xs_table = np.array([[0.5, 0.8, 1.0], [0.4, 0.7, 0.9]])
        
        result = vectorized_cross_section_lookup(material_ids, energy_groups, xs_table)
        
        expected = np.array([0.5, 0.7, 1.0, 0.4])
        assert np.array_equal(result, expected)

    def test_vectorized_cross_section_lookup_single(self):
        """Test with single lookup."""
        material_ids = np.array([0])
        energy_groups = np.array([1])
        xs_table = np.array([[0.5, 0.8, 1.0], [0.4, 0.7, 0.9]])
        
        result = vectorized_cross_section_lookup(material_ids, energy_groups, xs_table)
        
        assert result[0] == 0.8


class TestVectorizedNormalize:
    """Tests for vectorized_normalize function."""

    def test_vectorized_normalize_whole_array(self):
        """Test normalizing whole array."""
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        result = vectorized_normalize(arr, axis=None)
        
        # Normalizes by max value, so max becomes norm_value (1.0)
        assert np.isclose(result.max(), 1.0)
        assert np.all(result >= 0)

    def test_vectorized_normalize_along_axis(self):
        """Test normalizing along axis."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = vectorized_normalize(arr, axis=1)
        
        # Normalizes by max value per row, so max in each row becomes 1.0
        assert np.allclose(result.max(axis=1), 1.0)

    def test_vectorized_normalize_inplace(self):
        """Test in-place normalization."""
        arr = np.array([1.0, 2.0, 3.0])
        result = vectorized_normalize(arr, inplace=True)
        
        assert result is arr
        # Normalizes by max value, so max becomes 1.0
        assert np.isclose(result.max(), 1.0)

    def test_vectorized_normalize_custom_norm_value(self):
        """Test normalization with custom norm value."""
        arr = np.array([1.0, 2.0, 3.0])
        result = vectorized_normalize(arr, norm_value=10.0)
        
        # Normalizes by max value, so max becomes norm_value (10.0)
        assert np.isclose(result.max(), 10.0)

    def test_vectorized_normalize_zero_array(self):
        """Test normalization with zero array (should handle gracefully)."""
        arr = np.array([0.0, 0.0, 0.0])
        result = vectorized_normalize(arr)
        
        # Should not crash, result should be finite
        assert np.all(np.isfinite(result))


class TestBatchVectorizedOperations:
    """Tests for batch_vectorized_operations function."""

    def test_batch_vectorized_operations_sum(self):
        """Test batch sum operation."""
        arrays = [np.array([1, 2, 3]), np.array([4, 5, 6])]
        result = batch_vectorized_operations(arrays, operation="sum")
        
        expected = np.array([5, 7, 9])
        assert np.array_equal(result, expected)

    def test_batch_vectorized_operations_mean(self):
        """Test batch mean operation."""
        arrays = [np.array([1, 2, 3]), np.array([4, 5, 6])]
        result = batch_vectorized_operations(arrays, operation="mean")
        
        expected = np.array([2.5, 3.5, 4.5])
        assert np.array_equal(result, expected)

    def test_batch_vectorized_operations_max(self):
        """Test batch max operation."""
        arrays = [np.array([1, 5, 3]), np.array([4, 2, 6])]
        result = batch_vectorized_operations(arrays, operation="max")
        
        expected = np.array([4, 5, 6])
        assert np.array_equal(result, expected)

    def test_batch_vectorized_operations_min(self):
        """Test batch min operation."""
        arrays = [np.array([1, 5, 3]), np.array([4, 2, 6])]
        result = batch_vectorized_operations(arrays, operation="min")
        
        expected = np.array([1, 2, 3])
        assert np.array_equal(result, expected)

    def test_batch_vectorized_operations_empty(self):
        """Test with empty array list."""
        with pytest.raises(ValueError, match="Empty array list"):
            batch_vectorized_operations([], operation="sum")

    def test_batch_vectorized_operations_unknown(self):
        """Test with unknown operation."""
        arrays = [np.array([1, 2, 3])]
        with pytest.raises(ValueError, match="Unknown operation"):
            batch_vectorized_operations(arrays, operation="unknown")


class TestZeroCopySlice:
    """Tests for zero_copy_slice function."""

    def test_zero_copy_slice_basic(self):
        """Test basic slicing."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, 1, 4)
        
        expected = np.array([2, 3, 4])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_with_step(self):
        """Test slicing with step."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, 0, 5, 2)
        
        expected = np.array([1, 3, 5])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_no_args(self):
        """Test slicing with no arguments (full array)."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr)
        
        assert np.array_equal(result, arr)


class TestSmartArrayCopy:
    """Tests for smart_array_copy function."""

    def test_smart_array_copy_no_target(self):
        """Test copying with no target."""
        source = np.array([1, 2, 3])
        result = smart_array_copy(source)
        
        assert np.array_equal(result, source)
        assert result is not source  # Should be a copy

    def test_smart_array_copy_compatible_target(self):
        """Test copying with compatible target (reuse memory)."""
        source = np.array([1, 2, 3])
        target = np.zeros(3, dtype=int)
        result = smart_array_copy(source, target)
        
        assert np.array_equal(result, source)
        assert result is target  # Should reuse target

    def test_smart_array_copy_incompatible_target(self):
        """Test copying with incompatible target."""
        source = np.array([1, 2, 3])
        target = np.zeros(5, dtype=int)  # Wrong shape
        result = smart_array_copy(source, target)
        
        assert np.array_equal(result, source)
        assert result is not target  # Should create new array

    def test_smart_array_copy_force_copy(self):
        """Test copying with force_copy=True."""
        source = np.array([1, 2, 3])
        target = np.zeros(3, dtype=int)
        result = smart_array_copy(source, target, force_copy=True)
        
        assert np.array_equal(result, source)
        assert result is not target  # Should create new array

    def test_smart_array_copy_dtype_mismatch(self):
        """Test copying with dtype mismatch."""
        source = np.array([1, 2, 3], dtype=int)
        target = np.zeros(3, dtype=float)  # Different dtype
        result = smart_array_copy(source, target)
        
        assert np.array_equal(result, source)
        assert result is not target  # Should create new array
    
    def test_smart_array_copy_non_contiguous_target(self):
        """Test copying with non-contiguous target (should create new array)."""
        source = np.array([1, 2, 3])
        target = np.zeros(6, dtype=int)[::2]  # Non-contiguous (shape (3,))
        result = smart_array_copy(source, target)
        
        assert np.array_equal(result, source)
        assert result is not target  # Should create new array (target not C-contiguous)
