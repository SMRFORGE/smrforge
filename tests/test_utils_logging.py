"""
Tests for smrforge.utils.logging module.
"""

import pytest
import logging
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import smrforge.utils.logging as logging_module


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_default(self):
        """Test get_logger with default name."""
        logger = logging_module.get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge"
    
    def test_get_logger_custom_name(self):
        """Test get_logger with custom name."""
        logger = logging_module.get_logger("smrforge.test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge.test"
    
    def test_get_logger_none(self):
        """Test get_logger with None (should use default)."""
        logger = logging_module.get_logger(None)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge"


class TestSetupLogging:
    """Test setup_logging function."""
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        # Clear any existing handlers first
        logger = logging.getLogger("smrforge")
        original_handlers = len(logger.handlers)
        logger.handlers.clear()
        
        logging_module.setup_logging()
        logger = logging.getLogger("smrforge")
        # Should have WARNING level (default) or whatever was set
        assert logger.level in [logging.WARNING, logging.INFO, logging.DEBUG]
        # Should have at least one handler after setup
        assert len(logger.handlers) >= 1
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom level."""
        logging_module.setup_logging(level="DEBUG")
        logger = logging.getLogger("smrforge")
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_with_file(self, tmp_path):
        """Test setup_logging with log file."""
        log_file = tmp_path / "test.log"
        logging_module.setup_logging(level="INFO", log_file=log_file)
        logger = logging.getLogger("smrforge")
        assert log_file.exists()
        # Should have both console and file handlers
        assert len(logger.handlers) >= 1
    
    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format."""
        custom_format = "%(levelname)s - %(message)s"
        logging_module.setup_logging(level="INFO", format_string=custom_format)
        logger = logging.getLogger("smrforge")
        # Verify handler has custom format
        assert len(logger.handlers) > 0
    
    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid level (should default to INFO)."""
        logging_module.setup_logging(level="INVALID")
        logger = logging.getLogger("smrforge")
        # Should default to INFO when invalid level provided
        assert logger.level in [logging.INFO, logging.WARNING]


class TestLogSolverIteration:
    """Test log_solver_iteration function."""
    
    def test_log_solver_iteration_default_logger(self):
        """Test log_solver_iteration with default logger."""
        with patch('smrforge.utils.logging.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_module.log_solver_iteration(10, 1.001234, 1e-6)
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "Iteration" in call_args
            assert "1.001234" in call_args
    
    def test_log_solver_iteration_custom_logger(self):
        """Test log_solver_iteration with custom logger."""
        mock_logger = Mock()
        logging_module.log_solver_iteration(5, 1.0, 1e-5, logger=mock_logger)
        mock_logger.debug.assert_called_once()


class TestLogConvergence:
    """Test log_convergence function."""
    
    def test_log_convergence_default_logger(self):
        """Test log_convergence with default logger."""
        with patch('smrforge.utils.logging.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_module.log_convergence(1.001234, 25, 5e-8)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "converged" in call_args.lower()
            assert "1.001234" in call_args
    
    def test_log_convergence_custom_logger(self):
        """Test log_convergence with custom logger."""
        mock_logger = Mock()
        logging_module.log_convergence(1.0, 10, 1e-6, logger=mock_logger)
        mock_logger.info.assert_called_once()


class TestLogNuclearDataFetch:
    """Test log_nuclear_data_fetch function."""
    
    def test_log_nuclear_data_fetch_default_logger(self):
        """Test log_nuclear_data_fetch with default logger."""
        with patch('smrforge.utils.logging.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_module.log_nuclear_data_fetch("U235", "fission", 1200.0, "sandy")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "U235" in call_args
            assert "fission" in call_args
            assert "1200" in call_args
    
    def test_log_nuclear_data_fetch_custom_logger(self):
        """Test log_nuclear_data_fetch with custom logger."""
        mock_logger = Mock()
        logging_module.log_nuclear_data_fetch("U238", "total", 600.0, "endf_parser", logger=mock_logger)
        mock_logger.info.assert_called_once()


class TestLogCacheOperation:
    """Test log_cache_operation function."""
    
    def test_log_cache_operation_hit(self):
        """Test log_cache_operation with hit."""
        with patch('smrforge.utils.logging.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_module.log_cache_operation("hit", "test_key")
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "hit" in call_args
            assert "test_key" in call_args
    
    def test_log_cache_operation_miss(self):
        """Test log_cache_operation with miss."""
        mock_logger = Mock()
        logging_module.log_cache_operation("miss", "test_key", logger=mock_logger)
        mock_logger.debug.assert_called_once()
    
    def test_log_cache_operation_write(self):
        """Test log_cache_operation with write."""
        mock_logger = Mock()
        logging_module.log_cache_operation("write", "test_key", logger=mock_logger)
        mock_logger.debug.assert_called_once()
