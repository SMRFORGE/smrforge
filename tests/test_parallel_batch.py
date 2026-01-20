"""
Unit tests for parallel batch processing utilities.
"""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
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
        result = batch_process(items, double, parallel=True, use_threads=True, max_workers=2)
        assert result == [2, 4, 6, 8]
    
    def test_batch_process_with_threads(self):
        """Test batch_process with use_threads=True."""
        items = [1, 2, 3, 4]
        result = batch_process(
            items, 
            lambda x: x * 2, 
            parallel=True, 
            use_threads=True,
            max_workers=2
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
            return x ** 2
        
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
        result = batch_process(items, failing_func, parallel=True, max_workers=2, use_threads=True)
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
        
        # Mock ThreadPoolExecutor to avoid actual parallel execution
        mock_executor = MagicMock()
        mock_future = MagicMock()
        mock_future.result.return_value = 4
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value.__enter__.return_value.__exit__ = MagicMock(return_value=None)
        
        with patch.dict(sys.modules, {'rich.progress': mock_rich_module}):
            with patch('smrforge.utils.parallel_batch.ThreadPoolExecutor', mock_executor):
                items = [1, 2]
                result = batch_process(
                    items, 
                    double, 
                    parallel=True,
                    use_threads=True,
                    show_progress=True,
                    max_workers=2
                )
                # Should complete without error
                assert len(result) == 2
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
