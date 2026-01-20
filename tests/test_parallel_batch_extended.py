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
        mock_executor_instance.submit.side_effect = lambda func, item: futures_list[items.index(item)]
        
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)
        
        with patch('smrforge.utils.parallel_batch.ProcessPoolExecutor', mock_executor):
            with patch.dict('sys.modules', {'rich.progress': None}):
                # Force ImportError for rich
                import importlib
                import smrforge.utils.parallel_batch
                importlib.reload(smrforge.utils.parallel_batch)
                
                # Now test
                result = batch_process(items, double, parallel=True, use_threads=False, show_progress=False)
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
        
        with patch('smrforge.utils.parallel_batch.ThreadPoolExecutor', mock_executor):
            with patch.dict('sys.modules', {'rich.progress': None}):
                # Force ImportError for rich
                import importlib
                import smrforge.utils.parallel_batch
                importlib.reload(smrforge.utils.parallel_batch)
                # Re-import to get reloaded version
                from smrforge.utils.parallel_batch import batch_process
                
                result = batch_process(items, double, parallel=True, use_threads=True, show_progress=True)
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
        
        futures_map = {1: mock_future_good, 2: mock_future_error, 3: mock_future_another}
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = lambda func, item: futures_map[item]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__ = MagicMock(return_value=None)
        
        with patch('smrforge.utils.parallel_batch.ThreadPoolExecutor', mock_executor):
            with patch.dict('sys.modules', {'rich.progress': None}):
                import importlib
                import smrforge.utils.parallel_batch
                importlib.reload(smrforge.utils.parallel_batch)
                from smrforge.utils.parallel_batch import batch_process
                
                result = batch_process(items, failing_func, parallel=True, use_threads=True)
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
        
        with patch('smrforge.utils.parallel_batch.ThreadPoolExecutor', mock_executor):
            with patch.dict('sys.modules', {'rich.progress': None}):
                import importlib
                import smrforge.utils.parallel_batch
                importlib.reload(smrforge.utils.parallel_batch)
                from smrforge.utils.parallel_batch import batch_process
                
                result = batch_process(items, failing_func, parallel=True, use_threads=True)
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
        with patch('smrforge.utils.parallel_batch.batch_process') as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, parallel=True)
            assert result == [1.05, 1.10]
            mock_batch.assert_called_once()
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs['parallel'] is True
            assert call_kwargs['show_progress'] is True
    
    def test_batch_solve_keff_parallel_false(self):
        """Test batch_solve_keff with parallel=False."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]
        
        with patch('smrforge.utils.parallel_batch.batch_process') as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, parallel=False)
            assert result == [1.05, 1.10]
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs['parallel'] is False
    
    def test_batch_solve_keff_custom_max_workers(self):
        """Test batch_solve_keff with custom max_workers."""
        reactors = [MockReactor(1.05), MockReactor(1.10)]
        
        with patch('smrforge.utils.parallel_batch.batch_process') as mock_batch:
            mock_batch.return_value = [1.05, 1.10]
            result = batch_solve_keff(reactors, max_workers=4)
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs['max_workers'] == 4
    
    def test_batch_solve_keff_show_progress_false(self):
        """Test batch_solve_keff with show_progress=False."""
        reactors = [MockReactor(1.05)]
        
        with patch('smrforge.utils.parallel_batch.batch_process') as mock_batch:
            mock_batch.return_value = [1.05]
            result = batch_solve_keff(reactors, show_progress=False)
            call_kwargs = mock_batch.call_args[1]
            assert call_kwargs['show_progress'] is False
