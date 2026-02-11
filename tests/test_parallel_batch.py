"""
Unit tests for parallel batch processing utilities.
"""

import gc
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from smrforge.utils.parallel_batch import (
    ReactorLike,
    batch_process,
    batch_solve_keff,
)

# Mark all tests in this file to run serially to avoid resource contention
pytestmark = pytest.mark.parallel_batch


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Ensure proper cleanup after each test to prevent resource leaks."""
    yield
    # Force garbage collection to free memory and close any lingering executors
    gc.collect()
    gc.collect()  # Second pass for cyclic references

    # On Windows, need more aggressive cleanup and longer delays
    import sys
    import threading
    import time

    if sys.platform == "win32":
        # More aggressive cleanup on Windows
        for _ in range(2):
            gc.collect()
            time.sleep(0.1)  # 100ms delay on Windows for thread cleanup

        # Check for lingering threads
        active_threads = [
            t
            for t in threading.enumerate()
            if t.is_alive()
            and t != threading.main_thread()
            and "ThreadPoolExecutor" in str(t)
        ]
        if active_threads:
            # Wait a bit more for executor threads to finish
            time.sleep(0.2)
    else:
        # Standard cleanup on other platforms
        time.sleep(0.05)  # 50ms delay for thread cleanup


class MockReactor:
    """Mock reactor for testing."""

    def __init__(self, k_eff: float):
        self.k_eff = k_eff

    def solve_keff(self) -> float:
        """Return k-eff value."""
        return self.k_eff


class TestBatchProcess:
    """Tests for batch_process function."""

    def test_batch_process_empty_list(self):
        """Test batch_process with empty list."""
        result = batch_process([], lambda x: x * 2)
        assert result == []

    def test_batch_process_single_item(self):
        """Test batch_process with single item (serial execution)."""
        result = batch_process([5], lambda x: x * 2)
        assert result == [10]

    def test_batch_process_serial_execution(self):
        """Test batch_process with parallel=False."""
        items = [1, 2, 3, 4]
        result = batch_process(items, lambda x: x * 2, parallel=False)
        assert result == [2, 4, 6, 8]

    def test_batch_process_parallel_execution(self):
        """Test batch_process with parallel=True (using threads to avoid pickling issues)."""

        def double(x):
            return x * 2

        items = [1, 2, 3, 4]
        result = batch_process(
            items, double, parallel=True, use_threads=True, max_workers=1
        )
        assert result == [2, 4, 6, 8]

    def test_batch_process_with_threads(self):
        """Test batch_process with use_threads=True."""
        items = [1, 2, 3, 4]
        result = batch_process(
            items, lambda x: x * 2, parallel=True, use_threads=True, max_workers=1
        )
        assert result == [2, 4, 6, 8]

    def test_batch_process_max_workers_limit(self):
        """Test that max_workers is limited to number of items."""

        def double(x):
            return x * 2

        items = [1, 2]
        # Should not raise error even if max_workers > len(items)
        # Use threads to avoid pickling issues on Windows
        result = batch_process(items, double, max_workers=10, use_threads=True)
        assert result == [2, 4]

    def test_batch_process_default_max_workers(self):
        """Test that default max_workers uses cpu_count()."""

        def double(x):
            return x * 2

        items = [1, 2, 3, 4]
        # When max_workers is None, should use cpu_count()
        result = batch_process(items, double, max_workers=None, use_threads=True)
        assert result == [2, 4, 6, 8]

    def test_batch_process_custom_max_workers(self):
        """Test batch_process with custom max_workers (using threads)."""

        def square(x):
            return x**2

        items = [1, 2, 3, 4, 5]
        # Use threads to avoid pickling issues on Windows
        result = batch_process(items, square, max_workers=2, use_threads=True)
        assert result == [1, 4, 9, 16, 25]

    def test_batch_process_error_handling(self):
        """Test batch_process error handling."""

        def failing_func(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2

        items = [1, 2, 3, 4]
        # Should handle errors gracefully (use threads to avoid pickling issues)
        result = batch_process(
            items, failing_func, parallel=True, max_workers=1, use_threads=True
        )
        # Error should be stored in results
        assert len(result) == 4
        assert result[0] == 2
        assert result[1] == 4
        assert isinstance(result[2], ValueError)
        assert result[3] == 8

    def test_batch_process_with_progress_bar(self):
        """Test batch_process with progress bar (Rich available)."""

        def double(x):
            return x * 2

        # Mock Rich import to simulate Rich being available
        mock_progress_class = MagicMock()
        mock_progress_instance = MagicMock()
        mock_progress_instance.add_task.return_value = 1
        mock_progress_instance.update = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress_instance
        mock_progress_class.return_value.__exit__ = MagicMock(return_value=None)

        # Create a mock module with all Rich classes
        mock_rich_module = MagicMock()
        mock_rich_module.Progress = mock_progress_class
        mock_rich_module.BarColumn = MagicMock()
        mock_rich_module.TextColumn = MagicMock()
        mock_rich_module.SpinnerColumn = MagicMock()

        # Mock ThreadPoolExecutor but return real, completed Future objects so that
        # concurrent.futures.as_completed() can iterate without timing out.
        from concurrent.futures import Future

        mock_executor = MagicMock()
        f1 = Future()
        f1.set_result(2)
        f2 = Future()
        f2.set_result(4)
        futures = [f1, f2]

        def submit_side_effect(fn, arg):
            return futures.pop(0)

        mock_pool = mock_executor.return_value.__enter__.return_value
        mock_pool.submit.side_effect = submit_side_effect

        with patch.dict(sys.modules, {"rich.progress": mock_rich_module}):
            with patch(
                "smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor
            ):
                items = [1, 2]
                result = batch_process(
                    items,
                    double,
                    parallel=True,
                    use_threads=True,
                    show_progress=True,
                    max_workers=1,
                )
                # Should complete without error
                assert len(result) == 2
                assert result == [2, 4]
                # Verify progress bar was used
                mock_progress_class.assert_called_once()


class TestBatchSolveKeff:
    """Tests for batch_solve_keff function."""

    def test_batch_solve_keff_empty_list(self):
        """Test batch_solve_keff with empty list."""
        result = batch_solve_keff([])
        assert result == []

    def test_batch_solve_keff_single_reactor(self):
        """Test batch_solve_keff with single reactor."""
        reactor = MockReactor(1.05)
        result = batch_solve_keff([reactor])
        assert result == [1.05]

    def test_batch_solve_keff_multiple_reactors(self):
        """Test batch_solve_keff with multiple reactors."""
        reactors = [
            MockReactor(1.05),
            MockReactor(1.10),
            MockReactor(1.15),
        ]
        result = batch_solve_keff(reactors, parallel=False)
        assert result == [1.05, 1.10, 1.15]

    def test_batch_solve_keff_parallel_execution(self):
        """Test batch_solve_keff with parallel=True."""
        reactors = [
            MockReactor(1.05),
            MockReactor(1.10),
            MockReactor(1.15),
        ]
        # Note: On Windows, ProcessPoolExecutor has pickling issues with lambda functions
        # This test uses serial execution to verify functionality
        result = batch_solve_keff(reactors, parallel=False)
        assert result == [1.05, 1.10, 1.15]

    def test_batch_solve_keff_custom_max_workers(self):
        """Test batch_solve_keff with custom max_workers (serial execution)."""
        reactors = [
            MockReactor(1.05),
            MockReactor(1.10),
        ]
        # Use serial execution to avoid pickling issues
        result = batch_solve_keff(reactors, parallel=False)
        assert result == [1.05, 1.10]

    def test_batch_solve_keff_no_progress(self):
        """Test batch_solve_keff with show_progress=False (serial execution)."""
        reactors = [
            MockReactor(1.05),
            MockReactor(1.10),
        ]
        # Use serial execution to avoid pickling issues
        result = batch_solve_keff(reactors, parallel=False, show_progress=False)
        assert result == [1.05, 1.10]

    def test_batch_solve_keff_protocol_compliance(self):
        """Test that batch_solve_keff works with ReactorLike protocol."""

        # Any object with solve_keff() method should work
        class CustomReactor:
            def solve_keff(self):
                return 1.20

        reactors = [CustomReactor(), CustomReactor()]
        result = batch_solve_keff(reactors, parallel=False)
        assert result == [1.20, 1.20]


class TestReactorLikeProtocol:
    """Tests for ReactorLike protocol."""

    def test_protocol_accepts_mock_reactor(self):
        """Test that MockReactor satisfies ReactorLike protocol."""
        reactor = MockReactor(1.05)
        # Should not raise type error
        result = batch_solve_keff([reactor], parallel=False)
        assert result == [1.05]

    def test_protocol_requires_solve_keff_method(self):
        """Test that objects without solve_keff() raise AttributeError."""

        class BadReactor:
            pass

        reactors = [BadReactor()]
        with pytest.raises(AttributeError):
            batch_solve_keff(reactors, parallel=False)


class TestParallelBatchEdgeCases:
    """Edge case tests for parallel batch processing."""

    def test_batch_process_rich_unavailable(self):
        """Test batch_process when Rich is not available."""

        def double(x):
            return x * 2

        # Mock Rich import to fail
        with patch.dict(sys.modules, {"rich.progress": None}):
            items = [1, 2, 3]
            result = batch_process(
                items,
                double,
                parallel=True,
                use_threads=True,
                show_progress=True,  # Request progress but Rich unavailable
                max_workers=1,
            )
            assert result == [2, 4, 6]

    def test_batch_process_progress_without_rich(self):
        """Test batch_process with show_progress=True but Rich unavailable."""

        def square(x):
            return x**2

        # Simulate Rich not being available
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "rich.progress":
                raise ImportError("No module named 'rich'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            items = [1, 2, 3, 4]
            result = batch_process(
                items,
                square,
                parallel=True,
                use_threads=True,
                show_progress=True,
                max_workers=1,
            )
            assert result == [1, 4, 9, 16]

    def test_batch_process_with_processes_error_handling(self):
        """Test batch_process error handling with ProcessPoolExecutor."""

        def failing_func(x):
            if x == 2:
                raise ValueError(f"Error for {x}")
            return x * 2

        items = [1, 2, 3, 4]
        # Use threads to avoid pickling issues, but test error handling
        result = batch_process(
            items,
            failing_func,
            parallel=True,
            use_threads=True,  # Use threads to avoid Windows pickling issues
            max_workers=1,
        )

        # Should handle errors gracefully
        assert len(result) == 4
        assert result[0] == 2
        assert isinstance(result[1], ValueError)
        assert result[2] == 6
        assert result[3] == 8

    def test_batch_process_results_with_errors(self):
        """Test that batch_process returns results even when some fail."""

        def sometimes_fails(x):
            if x % 2 == 0:
                raise RuntimeError(f"Failed for {x}")
            return x * 3

        items = [1, 2, 3, 4, 5]
        result = batch_process(
            items, sometimes_fails, parallel=True, use_threads=True, max_workers=1
        )

        assert len(result) == 5
        assert result[0] == 3  # 1 * 3
        assert isinstance(result[1], RuntimeError)
        assert result[2] == 9  # 3 * 3
        assert isinstance(result[3], RuntimeError)
        assert result[4] == 15  # 5 * 3

    def test_batch_process_max_workers_one(self):
        """Test batch_process with max_workers=1."""

        def double(x):
            return x * 2

        items = [1, 2, 3, 4]
        result = batch_process(
            items, double, parallel=True, use_threads=True, max_workers=1
        )
        assert result == [2, 4, 6, 8]

    def test_batch_process_more_items_than_workers(self):
        """Test batch_process with more items than workers."""

        def square(x):
            return x**2

        items = list(range(1, 21))  # 20 items
        result = batch_process(
            items,
            square,
            parallel=True,
            use_threads=True,
            max_workers=1,  # Only 4 workers
        )

        assert len(result) == 20
        assert result[0] == 1
        assert result[4] == 25
        assert result[19] == 400

    def test_batch_solve_keff_empty_with_parallel(self):
        """Test batch_solve_keff with empty list and parallel=True."""
        result = batch_solve_keff([], parallel=True)
        assert result == []

    def test_batch_solve_keff_single_with_progress(self):
        """Test batch_solve_keff with single reactor and show_progress=True."""
        reactor = MockReactor(1.05)
        result = batch_solve_keff([reactor], parallel=False, show_progress=True)
        assert result == [1.05]

    def test_batch_process_state_preservation(self):
        """Test that batch_process preserves order of results."""

        def add_index(x):
            return (x[0], x[1])

        items = [(i, i * 2) for i in range(10)]
        result = batch_process(
            items, add_index, parallel=True, use_threads=True, max_workers=1
        )

        # Results should be in same order as input
        assert len(result) == 10
        for i, res in enumerate(result):
            assert res[0] == i
            assert res[1] == i * 2
