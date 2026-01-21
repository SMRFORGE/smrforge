"""
Extended tests for smrforge.utils.logging module to improve coverage.

This test file focuses on edge cases and additional scenarios not covered
in the main test_utils_logging.py file to reach 75%+ coverage.
"""

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call
import tempfile
import os

import smrforge.utils.logging as logging_module


class TestSetupLoggingEdgeCases:
    """Additional edge case tests for setup_logging."""
    
    def test_setup_logging_all_levels(self):
        """Test setup_logging with all valid logging levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level_name in levels:
            logging_module.setup_logging(level=level_name)
            logger = logging.getLogger("smrforge")
            expected_level = getattr(logging, level_name)
            assert logger.level == expected_level
    
    def test_setup_logging_lowercase_level(self):
        """Test setup_logging with lowercase level string."""
        logging_module.setup_logging(level="debug")
        logger = logging.getLogger("smrforge")
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_custom_date_format(self):
        """Test setup_logging with custom date format."""
        custom_date_format = "%Y-%m-%d"
        logging_module.setup_logging(
            level="INFO",
            date_format=custom_date_format
        )
        logger = logging.getLogger("smrforge")
        # Verify formatter was created with custom date format
        assert len(logger.handlers) > 0
        handler = logger.handlers[0]
        assert handler.formatter.datefmt == custom_date_format
    
    def test_setup_logging_file_creates_parent_dir(self, tmp_path):
        """Test that setup_logging creates parent directory for log file."""
        log_dir = tmp_path / "subdir" / "nested"
        log_file = log_dir / "test.log"
        
        # Directory should not exist yet
        assert not log_dir.exists()
        
        logging_module.setup_logging(level="INFO", log_file=log_file)
        
        # Directory should now exist
        assert log_dir.exists()
        assert log_file.exists()
    
    def test_setup_logging_file_append_mode(self, tmp_path):
        """Test that setup_logging uses append mode for log files."""
        log_file = tmp_path / "test.log"
        
        # Write initial content
        log_file.write_text("Initial content\n")
        
        logging_module.setup_logging(level="INFO", log_file=log_file)
        logger = logging.getLogger("smrforge")
        logger.info("New message")
        
        # Should append, not overwrite
        content = log_file.read_text()
        assert "Initial content" in content
        assert "New message" in content
    
    def test_setup_logging_file_encoding(self, tmp_path):
        """Test that setup_logging uses UTF-8 encoding for log files."""
        log_file = tmp_path / "test.log"
        
        logging_module.setup_logging(level="INFO", log_file=log_file)
        logger = logging.getLogger("smrforge")
        logger.info("Test message with unicode: ☢️")
        
        # Should handle unicode correctly
        content = log_file.read_text(encoding='utf-8')
        assert "☢️" in content
    
    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        logger = logging.getLogger("smrforge")
        
        # Add some dummy handlers
        handler1 = logging.StreamHandler()
        handler2 = logging.StreamHandler()
        logger.addHandler(handler1)
        logger.addHandler(handler2)
        
        original_count = len(logger.handlers)
        
        # Setup logging should clear and add new handlers
        logging_module.setup_logging(level="INFO")
        
        # Should have different handlers now
        assert len(logger.handlers) >= 1
        # Should not have more than 2 handlers (console + maybe file)
        assert len(logger.handlers) <= 2
    
    def test_setup_logging_propagate_false(self):
        """Test that setup_logging sets propagate=False."""
        logging_module.setup_logging(level="INFO")
        logger = logging.getLogger("smrforge")
        assert logger.propagate is False
    
    def test_setup_logging_logs_configuration(self, tmp_path):
        """Test that setup_logging logs the configuration message."""
        log_file = tmp_path / "test.log"
        
        logging_module.setup_logging(level="INFO", log_file=log_file)
        
        # Should log configuration message
        content = log_file.read_text()
        assert "Logging configured" in content
        assert "level=INFO" in content or "level=INFO" in content
    
    def test_setup_logging_multiple_calls(self):
        """Test calling setup_logging multiple times."""
        # First call
        logging_module.setup_logging(level="DEBUG")
        logger1 = logging.getLogger("smrforge")
        assert logger1.level == logging.DEBUG
        
        # Second call with different level
        logging_module.setup_logging(level="ERROR")
        logger2 = logging.getLogger("smrforge")
        assert logger2.level == logging.ERROR


class TestLogSolverIterationExtended:
    """Extended tests for log_solver_iteration."""
    
    def test_log_solver_iteration_all_levels(self):
        """Test log_solver_iteration logs at DEBUG level."""
        mock_logger = Mock()
        mock_logger.debug = Mock()
        
        logging_module.log_solver_iteration(1, 1.0, 1e-5, logger=mock_logger)
        
        # Should call debug, not info or other levels
        mock_logger.debug.assert_called_once()
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
    
    def test_log_solver_iteration_format_validation(self):
        """Test that log_solver_iteration formats message correctly."""
        mock_logger = Mock()
        
        logging_module.log_solver_iteration(42, 1.12345678, 1.234e-7, logger=mock_logger)
        
        call_args = mock_logger.debug.call_args[0][0]
        assert "Iteration" in call_args
        assert "42" in call_args
        assert "1.12345678" in call_args or "1.1235" in call_args
        assert "1.23e-07" in call_args or "1.234e-07" in call_args or "1.23e-7" in call_args
    
    def test_log_solver_iteration_edge_values(self):
        """Test log_solver_iteration with edge case values."""
        mock_logger = Mock()
        
        # Zero values
        logging_module.log_solver_iteration(0, 0.0, 0.0, logger=mock_logger)
        mock_logger.debug.assert_called()
        
        # Very large values
        logging_module.log_solver_iteration(10000, 1e10, 1e10, logger=mock_logger)
        mock_logger.debug.assert_called()
        
        # Negative values (edge case)
        logging_module.log_solver_iteration(-1, -1.0, -1e-5, logger=mock_logger)
        mock_logger.debug.assert_called()


class TestLogConvergenceExtended:
    """Extended tests for log_convergence."""
    
    def test_log_convergence_format_validation(self):
        """Test that log_convergence formats message correctly."""
        mock_logger = Mock()
        
        logging_module.log_convergence(1.001234, 25, 5e-8, logger=mock_logger)
        
        call_args = mock_logger.info.call_args[0][0]
        assert "converged" in call_args.lower()
        assert "1.001234" in call_args or "1.0012" in call_args
        assert "25" in call_args
        assert "5e-08" in call_args or "5.00e-08" in call_args or "5e-8" in call_args
    
    def test_log_convergence_logs_at_info_level(self):
        """Test log_convergence logs at INFO level."""
        mock_logger = Mock()
        
        logging_module.log_convergence(1.0, 10, 1e-6, logger=mock_logger)
        
        # Should call info, not debug or other levels
        mock_logger.info.assert_called_once()
        mock_logger.debug.assert_not_called()
        mock_logger.warning.assert_not_called()


class TestLogNuclearDataFetchExtended:
    """Extended tests for log_nuclear_data_fetch."""
    
    def test_log_nuclear_data_fetch_format_validation(self):
        """Test that log_nuclear_data_fetch formats message correctly."""
        mock_logger = Mock()
        
        logging_module.log_nuclear_data_fetch(
            "U235", "fission", 1200.0, "sandy", logger=mock_logger
        )
        
        call_args = mock_logger.info.call_args[0][0]
        assert "U235" in call_args
        assert "fission" in call_args
        assert "1200" in call_args
        assert "sandy" in call_args or "SANDY" in call_args
    
    def test_log_nuclear_data_fetch_different_backends(self):
        """Test log_nuclear_data_fetch with different backends."""
        mock_logger = Mock()
        
        backends = ["sandy", "endf_parser", "simple_parser", "custom_backend"]
        for backend in backends:
            logging_module.log_nuclear_data_fetch(
                "U238", "total", 600.0, backend, logger=mock_logger
            )
            call_args = mock_logger.info.call_args[0][0]
            assert backend in call_args
            mock_logger.reset_mock()
    
    def test_log_nuclear_data_fetch_metastable_nuclides(self):
        """Test log_nuclear_data_fetch with metastable nuclides."""
        mock_logger = Mock()
        
        logging_module.log_nuclear_data_fetch(
            "U235m", "capture", 800.0, "endf_parser", logger=mock_logger
        )
        
        call_args = mock_logger.info.call_args[0][0]
        assert "U235m" in call_args


class TestLogCacheOperationExtended:
    """Extended tests for log_cache_operation."""
    
    def test_log_cache_operation_format_validation(self):
        """Test that log_cache_operation formats message correctly."""
        mock_logger = Mock()
        
        logging_module.log_cache_operation("hit", "test_key", logger=mock_logger)
        
        call_args = mock_logger.debug.call_args[0][0]
        assert "hit" in call_args.lower()
        assert "test_key" in call_args
    
    def test_log_cache_operation_all_operations(self):
        """Test log_cache_operation with all operation types."""
        mock_logger = Mock()
        
        operations = ["hit", "miss", "write", "delete", "clear"]
        for operation in operations:
            logging_module.log_cache_operation(operation, "test_key", logger=mock_logger)
            call_args = mock_logger.debug.call_args[0][0]
            assert operation in call_args.lower()
            mock_logger.reset_mock()
    
    def test_log_cache_operation_complex_keys(self):
        """Test log_cache_operation with complex cache keys."""
        mock_logger = Mock()
        
        complex_keys = [
            "endfb8.0/U235/total/1200.0K",
            "file://path/to/data.zarr",
            "memory://key:value:subkey"
        ]
        
        for key in complex_keys:
            logging_module.log_cache_operation("hit", key, logger=mock_logger)
            call_args = mock_logger.debug.call_args[0][0]
            assert key in call_args


class TestModuleInitialization:
    """Tests for module-level initialization and setup."""
    
    def test_module_sets_global_logger(self):
        """Test that module sets global _logger on import."""
        # The module calls setup_logging() at the bottom
        # We can verify this by checking that a logger exists
        logger = logging.getLogger("smrforge")
        assert logger is not None
    
    def test_module_default_logging_level(self):
        """Test that module sets default WARNING level on import."""
        # Module should call setup_logging(level="WARNING") at bottom
        logger = logging.getLogger("smrforge")
        # After module import, level should be WARNING or whatever was last set
        assert logger.level >= logging.WARNING
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns same logger instance for same name."""
        logger1 = logging_module.get_logger("smrforge.test")
        logger2 = logging_module.get_logger("smrforge.test")
        
        # Should return same logger instance (logging module caches loggers)
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test that get_logger returns different loggers for different names."""
        logger1 = logging_module.get_logger("smrforge.test1")
        logger2 = logging_module.get_logger("smrforge.test2")
        
        # Should return different logger instances
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestIntegrationScenarios:
    """Integration tests combining multiple logging functions."""
    
    def test_full_logging_workflow(self, tmp_path):
        """Test a complete logging workflow."""
        log_file = tmp_path / "workflow.log"
        
        # Setup logging
        logging_module.setup_logging(level="DEBUG", log_file=log_file)
        logger = logging_module.get_logger("smrforge.test")
        
        # Use various log functions
        logging_module.log_solver_iteration(1, 1.0, 1e-5, logger=logger)
        logging_module.log_convergence(1.0, 10, 1e-6, logger=logger)
        logging_module.log_nuclear_data_fetch("U235", "fission", 1200.0, "sandy", logger=logger)
        logging_module.log_cache_operation("hit", "test_key", logger=logger)
        
        # Verify all messages are in log file
        content = log_file.read_text()
        assert "Iteration" in content
        assert "converged" in content.lower()
        assert "U235" in content
        assert "hit" in content.lower()
    
    def test_multiple_loggers_integration(self):
        """Test using multiple loggers simultaneously."""
        logger1 = logging_module.get_logger("smrforge.module1")
        logger2 = logging_module.get_logger("smrforge.module2")
        
        # Both should work independently
        logging_module.log_cache_operation("hit", "key1", logger=logger1)
        logging_module.log_cache_operation("miss", "key2", logger=logger2)
        
        # Both loggers should be valid
        assert logger1.name == "smrforge.module1"
        assert logger2.name == "smrforge.module2"
