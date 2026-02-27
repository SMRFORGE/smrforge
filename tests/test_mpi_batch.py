"""
Tests for MPI batch processing utilities.
"""

import pytest


class TestMPIBatch:
    """Tests for mpi_batch module."""

    def test_mpi_available_returns_bool(self):
        """mpi_available returns a boolean."""
        from smrforge.utils.mpi_batch import mpi_available

        assert isinstance(mpi_available(), bool)

    def test_mpi_batch_process_serial_fallback(self):
        """mpi_batch_process works in serial (use_mpi=False)."""
        from smrforge.utils.mpi_batch import mpi_batch_process

        def double(x):
            return x * 2

        items = [1, 2, 3, 4, 5]
        result = mpi_batch_process(items, double, use_mpi=False)
        assert result == [2, 4, 6, 8, 10]
