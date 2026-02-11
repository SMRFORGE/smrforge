"""
Extended tests for parallel_batch.py to improve coverage.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from smrforge.utils.parallel_batch import (
    ReactorLike,
    batch_process,
    batch_solve_keff,
)

# Mark all tests in this file to run serially to avoid resource contention
pytestmark = pytest.mark.parallel_batch


class MockReactor:
    """Mock reactor for testing."""

    def __init__(self, k_eff: float):
        self.k_eff = k_eff

    def solve_keff(self) -> float:
        """Return k-eff value."""
        return self.k_eff


class TestBatchProcessExtended:
    """Extended tests for batch_process function."""

    def test_batch_process_with_processes_no_rich(self):
        """Test batch_process with ProcessPoolExecutor when Rich is not available."""

        def double(x):
            return x * 2

        items = [1, 2, 3]
        # Mock ProcessPoolExecutor to avoid actual multiprocessing
        mock_executor = MagicMock()
        mock_future1 = MagicMock()
        mock_future1.result.return_value = 2
        mock_future2 = MagicMock()
        mock_future2.result.return_value = 4
        mock_future3 = MagicMock()
        mock_future3.result.return_value = 6

        futures_list = [mock_future1, mock_future2, mock_future3]
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_list[
            items.index(item)
        ]

        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ProcessPoolExecutor", mock_executor):
            with patch.dict("sys.modules", {"rich.progress": None}):
                # Force ImportError for rich
                import importlib

                import smrforge.utils.parallel_batch

                importlib.reload(smrforge.utils.parallel_batch)

                # Now test
                result = batch_process(
                    items, double, parallel=True, use_threads=False, show_progress=False
                )
                assert len(result) == 3

    def test_batch_process_rich_unavailable(self):
        """Test batch_process when Rich is not available but show_progress=True."""

        def double(x):
            return x * 2

        items = [1, 2]

        # Mock ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_future = MagicMock()
        mock_future.result.return_value = 4
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.return_value = mock_future
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch.dict("sys.modules", {"rich.progress": None}):
                # Force ImportError for rich
                import importlib

                import smrforge.utils.parallel_batch

                importlib.reload(smrforge.utils.parallel_batch)
                # Re-import to get reloaded version
                from smrforge.utils.parallel_batch import batch_process

                result = batch_process(
                    items, double, parallel=True, use_threads=True, show_progress=True
                )
                # Should complete without Rich
                assert len(result) == 2

    def test_batch_process_error_stored_in_results(self):
        """Test that errors are stored in results list."""

        def failing_func(x):
            if x == 2:
                raise ValueError("Test error")
            return x * 2

        items = [1, 2, 3]

        # Mock ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_future_good = MagicMock()
        mock_future_good.result.return_value = 2
        mock_future_error = MagicMock()
        mock_future_error.result.side_effect = ValueError("Test error")
        mock_future_another = MagicMock()
        mock_future_another.result.return_value = 6

        futures_map = {
            1: mock_future_good,
            2: mock_future_error,
            3: mock_future_another,
        }

        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_map[item]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch.dict("sys.modules", {"rich.progress": None}):
                import importlib

                import smrforge.utils.parallel_batch

                importlib.reload(smrforge.utils.parallel_batch)
                from smrforge.utils.parallel_batch import batch_process

                result = batch_process(
                    items, failing_func, parallel=True, use_threads=True
                )
                assert len(result) == 3
                assert result[0] == 2  # Success
                assert isinstance(result[1], ValueError)  # Error stored
                assert result[2] == 6  # Success

    def test_batch_process_multiple_errors(self):
        """Test batch_process with multiple errors."""

        def failing_func(x):
            if x in [2, 4]:
                raise ValueError(f"Error for {x}")
            return x * 2

        items = [1, 2, 3, 4]

        # Mock ThreadPoolExecutor with multiple errors
        mock_executor = MagicMock()
        futures_map = {}
        for item in items:
            mock_future = MagicMock()
            if item in [2, 4]:
                mock_future.result.side_effect = ValueError(f"Error for {item}")
            else:
                mock_future.result.return_value = item * 2
            futures_map[item] = mock_future

        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_map[item]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch.dict("sys.modules", {"rich.progress": None}):
                import importlib

                import smrforge.utils.parallel_batch

                importlib.reload(smrforge.utils.parallel_batch)
                from smrforge.utils.parallel_batch import batch_process

                result = batch_process(
                    items, failing_func, parallel=True, use_threads=True
                )
                assert len(result) == 4
                assert result[0] == 2  # Success
                assert isinstance(result[1], ValueError)  # Error
                assert result[2] == 6  # Success
                assert isinstance(result[3], ValueError)  # Error


class TestBatchSolveKeffExtended:
    """Extended tests for batch_solve_keff function."""

    def test_batch_solve_keff_parallel_true(self):
        """Test batch_solve_keff with parallel=True."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]

        # Mock batch_process to avoid actual parallel execution
        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, parallel=True)
            assert result == [1.05, 1.10]
            mock_batch.assert_called_once()
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs["parallel"] is True
            assert call_kwargs["show_progress"] is True

    def test_batch_solve_keff_parallel_false(self):
        """Test batch_solve_keff with parallel=False."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]

        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, parallel=False)
            assert result == [1.05, 1.10]
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs["parallel"] is False

    def test_batch_solve_keff_custom_max_workers(self):
        """Test batch_solve_keff with custom max_workers."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]

        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, max_workers=4)
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs["max_workers"] == 4

    def test_batch_solve_keff_show_progress_false(self):
        """Test batch_solve_keff with show_progress=False."""
        reactors = [MockReactor(1.05)]

        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05]
            result = batch_solve_keff(reactors, show_progress=False)
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs["show_progress"] is False


class TestParallelBatchAdditionalEdgeCases:
    """Additional edge case tests for parallel_batch.py to improve coverage to 60%+."""

    def test_batch_process_rich_available_with_progress(self):
        """Test batch_process when Rich is available and show_progress=True."""

        def double(x):
            return x * 2

        items = [1, 2, 3]

        # Mock Rich progress classes
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress_instance = MagicMock()
        mock_progress_instance.add_task.return_value = mock_task
        mock_progress_instance.update = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        mock_rich_module = MagicMock()
        mock_rich_module.Progress = mock_progress
        mock_rich_module.BarColumn = MagicMock()
        mock_rich_module.TextColumn = MagicMock()
        mock_rich_module.SpinnerColumn = MagicMock()

        # Mock ThreadPoolExecutor
        mock_executor = MagicMock()
        mock_future1 = MagicMock()
        mock_future1.result.return_value = 2
        mock_future2 = MagicMock()
        mock_future2.result.return_value = 4
        mock_future3 = MagicMock()
        mock_future3.result.return_value = 6

        futures_list = [mock_future1, mock_future2, mock_future3]
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_list[
            items.index(item)
        ]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch.dict("sys.modules", {"rich.progress": mock_rich_module}):
            with patch(
                "smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor
            ):
                # Mock as_completed to return futures in order
                from concurrent.futures import Future

                with patch(
                    "smrforge.utils.parallel_batch.as_completed",
                    return_value=futures_list,
                ):
                    result = batch_process(
                        items,
                        double,
                        parallel=True,
                        use_threads=True,
                        show_progress=True,
                        max_workers=2,
                    )
                    assert result == [2, 4, 6]
                    mock_progress.assert_called_once()

    def test_batch_process_rich_available_no_progress(self):
        """Test batch_process when Rich is available but show_progress=False."""

        def double(x):
            return x * 2

        items = [1, 2, 3]

        # Mock ThreadPoolExecutor (Rich path not taken when show_progress=False)
        mock_executor = MagicMock()
        mock_future1 = MagicMock()
        mock_future1.result.return_value = 2
        mock_future2 = MagicMock()
        mock_future2.result.return_value = 4
        mock_future3 = MagicMock()
        mock_future3.result.return_value = 6

        futures_list = [mock_future1, mock_future2, mock_future3]
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_list[
            items.index(item)
        ]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch(
                "smrforge.utils.parallel_batch.as_completed", return_value=futures_list
            ):
                result = batch_process(
                    items,
                    double,
                    parallel=True,
                    use_threads=True,
                    show_progress=False,
                    max_workers=2,
                )
                assert result == [2, 4, 6]

    def test_batch_process_error_logging_path(self):
        """Test batch_process error logging path when errors occur."""

        def failing_func(x):
            if x == 2:
                raise ValueError(f"Error for {x}")
            return x * 2

        items = [1, 2, 3]

        # Mock ThreadPoolExecutor with error
        mock_executor = MagicMock()
        mock_future_good = MagicMock()
        mock_future_good.result.return_value = 2
        mock_future_error = MagicMock()
        mock_future_error.result.side_effect = ValueError("Error for 2")
        mock_future_another = MagicMock()
        mock_future_another.result.return_value = 6

        futures_list = [mock_future_good, mock_future_error, mock_future_another]
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_list[
            items.index(item)
        ]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch(
                "smrforge.utils.parallel_batch.as_completed", return_value=futures_list
            ):
                with patch("smrforge.utils.parallel_batch.logger") as mock_logger:
                    result = batch_process(
                        items, failing_func, parallel=True, use_threads=True
                    )
                    assert len(result) == 3
                    # Error should be logged
                    assert mock_logger.error.called
                    # Warning about errors should be logged
                    assert mock_logger.warning.called

    def test_batch_process_max_workers_equals_items(self):
        """Test batch_process when max_workers equals number of items."""

        def double(x):
            return x * 2

        items = [1, 2, 3, 4]

        # Should work correctly
        result = batch_process(
            items,
            double,
            parallel=True,
            use_threads=True,
            max_workers=4,  # Equal to len(items)
        )
        assert result == [2, 4, 6, 8]

    def test_batch_process_max_workers_greater_than_items(self):
        """Test batch_process when max_workers > number of items (should be limited)."""

        def double(x):
            return x * 2

        items = [1, 2]  # Only 2 items

        # max_workers=10 should be limited to 2
        result = batch_process(
            items,
            double,
            parallel=True,
            use_threads=True,
            max_workers=10,  # Greater than len(items)
        )
        assert result == [2, 4]

    def test_batch_process_duplicate_items(self):
        """Test batch_process with duplicate items (edge case for item_to_index)."""

        def square(x):
            return x**2

        items = [1, 2, 1, 2]  # Duplicates

        result = batch_process(
            items, square, parallel=True, use_threads=True, max_workers=2
        )
        # Should process all items, duplicates get last processed value
        assert len(result) == 4
        assert all(isinstance(r, (int, ValueError)) for r in result)

    def test_batch_process_non_picklable_items_threads(self):
        """Test batch_process with non-picklable items using threads (should work)."""

        def get_len(obj):
            return len(obj)

        # Lists are picklable, but test thread execution path
        items = [[1, 2], [3, 4], [5]]

        result = batch_process(
            items, get_len, parallel=True, use_threads=True, max_workers=2
        )
        assert result == [2, 2, 1]

    def test_batch_process_zero_max_workers(self):
        """Test batch_process with max_workers=0 (should use cpu_count or 1)."""

        def double(x):
            return x * 2

        items = [1, 2, 3]

        # max_workers=0 should be handled (likely falls back to cpu_count)
        # Use threads to avoid pickling issues
        result = batch_process(
            items, double, parallel=True, use_threads=True, max_workers=0
        )
        assert result == [2, 4, 6]

    def test_batch_solve_keff_parallel_with_progress(self):
        """Test batch_solve_keff with parallel=True and show_progress=True."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]

        # Mock batch_process
        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, parallel=True, show_progress=True)
            assert result == [1.05, 1.10]
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs["show_progress"] is True

    def test_batch_solve_keff_default_parameters(self):
        """Test batch_solve_keff with default parameters."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]

        with patch("smrforge.utils.parallel_batch.batch_process") as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors)
            assert result == [1.05, 1.10]
            call_kwargs = mock_batch.call_args[1]
            # Defaults should be: parallel=True, show_progress=True
            assert call_kwargs["parallel"] is True
            assert call_kwargs["show_progress"] is True

    def test_batch_process_progress_with_multiple_errors(self):
        """Test batch_process progress path with multiple errors."""

        def failing_func(x):
            if x in [2, 4]:
                raise ValueError(f"Error for {x}")
            return x * 2

        items = [1, 2, 3, 4]

        # Mock Rich progress
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress_instance = MagicMock()
        mock_progress_instance.add_task.return_value = mock_task
        mock_progress_instance.update = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        mock_rich_module = MagicMock()
        mock_rich_module.Progress = mock_progress
        mock_rich_module.BarColumn = MagicMock()
        mock_rich_module.TextColumn = MagicMock()
        mock_rich_module.SpinnerColumn = MagicMock()

        # Mock executor with errors
        mock_executor = MagicMock()
        futures_map = {}
        for item in items:
            mock_future = MagicMock()
            if item in [2, 4]:
                mock_future.result.side_effect = ValueError(f"Error for {item}")
            else:
                mock_future.result.return_value = item * 2
            futures_map[item] = mock_future

        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_map[item]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch.dict("sys.modules", {"rich.progress": mock_rich_module}):
            with patch(
                "smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor
            ):
                with patch(
                    "smrforge.utils.parallel_batch.as_completed",
                    return_value=list(futures_map.values()),
                ):
                    with patch("smrforge.utils.parallel_batch.logger") as mock_logger:
                        result = batch_process(
                            items,
                            failing_func,
                            parallel=True,
                            use_threads=True,
                            show_progress=True,
                            max_workers=2,
                        )
                        assert len(result) == 4
                        # Should log errors
                        assert mock_logger.error.called
                        # Should log warning about errors
                        assert mock_logger.warning.called

    def test_batch_process_as_completed_exception_path(self):
        """Test batch_process when as_completed raises (covers exception path)."""

        def double(x):
            return x * 2

        items = [1, 2, 3]
        mock_future = MagicMock()
        mock_future.result.return_value = 2
        mock_future.done.return_value = True

        def as_completed_raiser(*args, **kwargs):
            yield mock_future
            raise RuntimeError("as_completed failed")

        mock_executor = MagicMock()
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda f, item: mock_future
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch(
                "smrforge.utils.parallel_batch.as_completed",
                side_effect=as_completed_raiser,
            ):
                with patch.dict("sys.modules", {"rich.progress": None}):
                    with patch("smrforge.utils.parallel_batch.logger") as mock_logger:
                        result = batch_process(
                            items,
                            double,
                            parallel=True,
                            use_threads=True,
                            show_progress=False,
                            max_workers=2,
                        )
                        assert mock_logger.warning.called
                        warn_msg = " ".join(
                            str(c) for c in mock_logger.warning.call_args_list
                        )
                        assert (
                            "as_completed" in warn_msg
                            or "cancelling" in warn_msg.lower()
                        )

    def test_batch_process_incomplete_futures_warning_path(self):
        """Test batch_process when as_completed yields fewer than len(items) (completed_count < len)."""

        def double(x):
            return x * 2

        items = [1, 2, 3]
        mock_f1 = MagicMock()
        mock_f1.result.return_value = 2
        mock_f1.done.return_value = True

        def as_completed_one_then_stop(*args, **kwargs):
            yield mock_f1
            return

        mock_executor = MagicMock()
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda f, item: mock_f1
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)

        with patch("smrforge.utils.parallel_batch.ThreadPoolExecutor", mock_executor):
            with patch(
                "smrforge.utils.parallel_batch.as_completed",
                side_effect=as_completed_one_then_stop,
            ):
                with patch.dict("sys.modules", {"rich.progress": None}):
                    with patch("smrforge.utils.parallel_batch.logger") as mock_logger:
                        result = batch_process(
                            items,
                            double,
                            parallel=True,
                            use_threads=True,
                            show_progress=False,
                            max_workers=2,
                        )
                        assert mock_logger.warning.called
                        calls_str = " ".join(
                            str(c) for c in mock_logger.warning.call_args_list
                        )
                        assert "Only" in calls_str and "futures completed" in calls_str
