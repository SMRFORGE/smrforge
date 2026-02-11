"""
Unit tests for optimization utilities.
"""

import gc

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


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Ensure proper cleanup after each test to prevent resource leaks."""
    yield
    # Force aggressive garbage collection to free memory
    # Multiple calls help ensure all cycles are collected
    gc.collect()
    gc.collect()  # Second pass for cyclic references
    # Clear any cached NumPy operations if possible
    try:
        import numpy as np

        # Force NumPy to release any cached memory
        np.seterr(all="ignore")  # Reset error handling
    except Exception:
        pass


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
        assert result.flags["C_CONTIGUOUS"]

    def test_ensure_contiguous_force_copy(self):
        """Test with force_copy=True."""
        arr = np.array([1, 2, 3])
        result = ensure_contiguous(arr, force_copy=True)

        assert np.array_equal(result, arr)
        # Should be contiguous
        assert result.flags["C_CONTIGUOUS"]


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

    def test_vectorized_normalize_empty_array(self):
        """Test normalization with empty array (size 0)."""
        arr = np.array([])
        result = vectorized_normalize(arr)

        assert result.size == 0
        assert result is not arr  # copy when not inplace
        assert result.dtype == arr.dtype

    def test_vectorized_normalize_empty_array_inplace(self):
        """Test in-place normalization with empty array."""
        arr = np.array([])
        result = vectorized_normalize(arr, inplace=True)

        assert result.size == 0
        assert result is arr


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

    def test_smart_array_copy_target_same_shape_different_dtype(self):
        """Test copying with same shape but different dtype."""
        source = np.array([1, 2, 3], dtype=int)
        target = np.zeros(3, dtype=float)
        result = smart_array_copy(source, target)

        assert np.array_equal(result, source)
        assert result is not target  # Different dtype, should create new

    def test_smart_array_copy_target_same_shape_same_dtype_contiguous(self):
        """Test copying with compatible target that is C-contiguous."""
        source = np.array([1, 2, 3], dtype=int)
        target = np.zeros(3, dtype=int)  # Same shape and dtype, C-contiguous
        result = smart_array_copy(source, target)

        assert np.array_equal(result, source)
        assert result is target  # Should reuse target


class TestOptimizationUtilsEdgeCases:
    """Edge case tests for optimization utilities."""

    def test_vectorized_normalize_axis_zero(self):
        """Test normalization with axis=0."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = vectorized_normalize(arr, axis=0)

        # Normalizes by max value per column
        assert np.allclose(result.max(axis=0), 1.0)

    def test_vectorized_normalize_very_small_values(self):
        """Test normalization with very small values."""
        arr = np.array([1e-20, 2e-20, 3e-20])
        result = vectorized_normalize(arr)

        # Should handle small values without overflow
        assert np.all(np.isfinite(result))
        assert np.isclose(result.max(), 1.0)

    def test_vectorized_normalize_custom_norm_value_inplace(self):
        """Test in-place normalization with custom norm value."""
        arr = np.array([1.0, 2.0, 3.0])
        result = vectorized_normalize(arr, norm_value=5.0, inplace=True)

        assert result is arr
        assert np.isclose(result.max(), 5.0)

    def test_batch_vectorized_operations_single_array(self):
        """Test batch operations with single array."""
        arrays = [np.array([1, 2, 3])]
        result = batch_vectorized_operations(arrays, operation="sum")

        assert np.array_equal(result, np.array([1, 2, 3]))

    def test_batch_vectorized_operations_multiple_arrays(self):
        """Test batch operations with many arrays."""
        arrays = [np.array([i, i + 1, i + 2]) for i in range(5)]
        result = batch_vectorized_operations(arrays, operation="sum")

        expected = np.array([0 + 1 + 2 + 3 + 4, 1 + 2 + 3 + 4 + 5, 2 + 3 + 4 + 5 + 6])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_negative_indices(self):
        """Test slicing with negative indices."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, -4, -1)

        expected = np.array([2, 3, 4])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_only_start(self):
        """Test slicing with only start index."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, start=2)

        expected = np.array([3, 4, 5])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_only_stop(self):
        """Test slicing with only stop index."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, stop=3)

        expected = np.array([1, 2, 3])
        assert np.array_equal(result, expected)

    def test_ensure_contiguous_fortran_order(self):
        """Test ensure_contiguous with Fortran-ordered array."""
        arr = np.array([[1, 2, 3], [4, 5, 6]], order="F")
        result = ensure_contiguous(arr)

        assert result.flags["C_CONTIGUOUS"]
        assert np.array_equal(result, arr)

    def test_vectorized_cross_section_lookup_empty(self):
        """Test vectorized cross-section lookup with empty arrays."""
        material_ids = np.array([], dtype=int)
        energy_groups = np.array([], dtype=int)
        xs_table = np.array([[0.5, 0.8], [0.4, 0.7]])

        result = vectorized_cross_section_lookup(material_ids, energy_groups, xs_table)

        assert len(result) == 0


class TestOptimizationUtilsAdditionalEdgeCases:
    """Additional edge case tests for optimization_utils.py to improve coverage to 60%+."""

    def test_vectorized_normalize_negative_values(self):
        """Test normalization with negative values."""
        arr = np.array([-1.0, -2.0, -3.0])
        result = vectorized_normalize(arr)

        # Should normalize by max (absolute), max should become norm_value
        assert np.all(np.isfinite(result))

    def test_vectorized_normalize_mixed_signs(self):
        """Test normalization with mixed positive and negative values."""
        arr = np.array([-5.0, 0.0, 5.0])
        result = vectorized_normalize(arr)

        assert np.all(np.isfinite(result))
        assert np.isclose(result.max(), 1.0)

    def test_vectorized_normalize_nan_handling(self):
        """Test normalization with NaN values (should propagate)."""
        arr = np.array([1.0, np.nan, 3.0])
        result = vectorized_normalize(arr)

        # NaN should propagate through normalization
        assert np.isnan(result[1])

    def test_vectorized_normalize_inf_handling(self):
        """Test normalization with Inf values."""
        arr = np.array([1.0, np.inf, 3.0])
        result = vectorized_normalize(arr)

        # Inf as max yields inf/inf -> nan; finite elements become 0
        assert np.isnan(result[1]) or np.isinf(result[1])
        assert np.all(np.isfinite(result[[0, 2]]))

    def test_vectorized_normalize_axis_negative(self):
        """Test normalization with negative axis."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = vectorized_normalize(arr, axis=-1)  # Last axis

        # Should normalize along last axis (columns)
        assert np.allclose(result.max(axis=-1), 1.0)

    def test_vectorized_normalize_keepdims(self):
        """Test normalization with keepdims behavior (implicit via axis)."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = vectorized_normalize(arr, axis=1)

        # Should normalize along axis 1 (each row)
        assert result.shape == (2, 2)
        assert np.allclose(result.max(axis=1), 1.0)

    def test_batch_vectorized_operations_different_shapes_error(self):
        """Test batch operations with arrays of different shapes."""
        arrays = [np.array([1, 2, 3]), np.array([4, 5])]  # Different shapes

        # Should raise ValueError when trying to stack
        with pytest.raises(ValueError):
            batch_vectorized_operations(arrays, operation="sum")

    def test_batch_vectorized_operations_single_element(self):
        """Test batch operations with single-element arrays."""
        arrays = [np.array([1]), np.array([2])]
        result = batch_vectorized_operations(arrays, operation="sum")

        assert np.array_equal(result, np.array([3]))

    def test_batch_vectorized_operations_2d_arrays(self):
        """Test batch operations with 2D arrays."""
        arrays = [np.array([[1, 2], [3, 4]]), np.array([[5, 6], [7, 8]])]
        result = batch_vectorized_operations(arrays, operation="sum")

        expected = np.array([[6, 8], [10, 12]])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_all_none(self):
        """Test zero_copy_slice with all None arguments."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, None, None, None)

        assert np.array_equal(result, arr)

    def test_zero_copy_slice_start_none(self):
        """Test zero_copy_slice with start=None."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, None, 3, None)

        expected = np.array([1, 2, 3])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_stop_none(self):
        """Test zero_copy_slice with stop=None."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, 2, None, None)

        expected = np.array([3, 4, 5])
        assert np.array_equal(result, expected)

    def test_zero_copy_slice_step_none(self):
        """Test zero_copy_slice with step=None."""
        arr = np.array([1, 2, 3, 4, 5])
        result = zero_copy_slice(arr, 1, 4, None)

        expected = np.array([2, 3, 4])
        assert np.array_equal(result, expected)

    def test_smart_array_copy_target_wrong_dtype_but_compatible(self):
        """Test smart_array_copy with target having wrong dtype but compatible shape."""
        source = np.array([1, 2, 3], dtype=int)
        target = np.zeros(3, dtype=float)  # Different dtype, same shape

        result = smart_array_copy(source, target)

        # Should create new array because dtype doesn't match
        assert result is not target
        assert np.array_equal(result, source)

    def test_smart_array_copy_target_fortran_order(self):
        """Test smart_array_copy with Fortran-ordered target (2D so actually F-contig)."""
        source = np.array([[1, 2], [3, 4], [5, 6]])
        target = np.zeros((3, 2), dtype=int, order="F")

        result = smart_array_copy(source, target)

        # Fortran-ordered 2D is not C-contiguous; implementation creates new array
        assert result is not target
        assert np.array_equal(result, source)
