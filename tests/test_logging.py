"""
Tests for logging utility module.
"""

import logging
import tempfile
from pathlib import Path

import pytest

from smrforge.utils.logging import (
    get_logger,
    log_cache_operation,
    log_convergence,
    log_nuclear_data_fetch,
    log_solver_iteration,
    setup_logging,
)


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_with_name(self):
        """Test get_logger with specific name."""
        logger = get_logger("smrforge.test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge.test"

    def test_get_logger_with_none(self):
        """Test get_logger with None name (defaults to 'smrforge')."""
        logger = get_logger(None)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge"

    def test_get_logger_default(self):
        """Test get_logger with no arguments."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "smrforge"


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        setup_logging()
        logger = logging.getLogger("smrforge")
        assert logger.level == logging.INFO

    def test_setup_logging_with_level(self):
        """Test setup_logging with custom level."""
        setup_logging(level="DEBUG")
        logger = logging.getLogger("smrforge")
        assert logger.level == logging.DEBUG

        setup_logging(level="WARNING")
        logger = logging.getLogger("smrforge")
        assert logger.level == logging.WARNING

    def test_setup_logging_with_log_file(self, tmp_path):
        """Test setup_logging with log file."""
        log_file = tmp_path / "test.log"
        setup_logging(level="INFO", log_file=log_file)

        # Log a message
        logger = logging.getLogger("smrforge")
        logger.info("Test message")

        # Verify file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_with_custom_format(self):
        """Test setup_logging with custom format string."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(level="INFO", format_string=custom_format)
        logger = logging.getLogger("smrforge")

        # Format should be set (we can't easily verify exact format,
        # but we can verify logger still works)
        logger.info("Test")
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_with_date_format(self):
        """Test setup_logging with custom date format."""
        setup_logging(level="INFO", date_format="%Y/%m/%d")
        logger = logging.getLogger("smrforge")
        logger.info("Test")
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates log file directory if needed."""
        log_file = tmp_path / "subdir" / "test.log"
        setup_logging(level="INFO", log_file=log_file)

        # Directory should be created
        assert log_file.parent.exists()
        assert log_file.parent.is_dir()


class TestLogSolverIteration:
    """Test log_solver_iteration function."""

    def test_log_solver_iteration_with_logger(self):
        """Test log_solver_iteration with provided logger."""
        logger = logging.getLogger("test_solver")
        log_solver_iteration(iteration=10, k_eff=1.001234, residual=1e-6, logger=logger)
        # Function should execute without error

    def test_log_solver_iteration_without_logger(self):
        """Test log_solver_iteration without logger (uses default)."""
        log_solver_iteration(iteration=10, k_eff=1.001234, residual=1e-6, logger=None)
        # Function should execute without error

    def test_log_solver_iteration_no_logger_param(self):
        """Test log_solver_iteration without logger parameter."""
        log_solver_iteration(iteration=5, k_eff=1.0, residual=1e-5)
        # Function should execute without error


class TestLogConvergence:
    """Test log_convergence function."""

    def test_log_convergence_with_logger(self):
        """Test log_convergence with provided logger."""
        logger = logging.getLogger("test_convergence")
        log_convergence(k_eff=1.001234, iterations=25, residual=5e-8, logger=logger)
        # Function should execute without error

    def test_log_convergence_without_logger(self):
        """Test log_convergence without logger (uses default)."""
        log_convergence(k_eff=1.001234, iterations=25, residual=5e-8, logger=None)
        # Function should execute without error

    def test_log_convergence_no_logger_param(self):
        """Test log_convergence without logger parameter."""
        log_convergence(k_eff=1.0, iterations=10, residual=1e-6)
        # Function should execute without error


class TestLogNuclearDataFetch:
    """Test log_nuclear_data_fetch function."""

    def test_log_nuclear_data_fetch_with_logger(self):
        """Test log_nuclear_data_fetch with provided logger."""
        logger = logging.getLogger("test_nuclear")
        log_nuclear_data_fetch(
            nuclide="U235",
            reaction="fission",
            temperature=1200.0,
            backend="sandy",
            logger=logger,
        )
        # Function should execute without error

    def test_log_nuclear_data_fetch_without_logger(self):
        """Test log_nuclear_data_fetch without logger (uses default)."""
        log_nuclear_data_fetch(
            nuclide="U235",
            reaction="fission",
            temperature=1200.0,
            backend="sandy",
            logger=None,
        )
        # Function should execute without error

    def test_log_nuclear_data_fetch_no_logger_param(self):
        """Test log_nuclear_data_fetch without logger parameter."""
        log_nuclear_data_fetch(
            nuclide="U238", reaction="capture", temperature=900.0, backend="endf_parser"
        )
        # Function should execute without error


class TestLogCacheOperation:
    """Test log_cache_operation function."""

    def test_log_cache_operation_with_logger(self):
        """Test log_cache_operation with provided logger."""
        logger = logging.getLogger("test_cache")
        log_cache_operation("hit", "endfb8.0/U235/total/1200.0K", logger=logger)
        # Function should execute without error

    def test_log_cache_operation_without_logger(self):
        """Test log_cache_operation without logger (uses default)."""
        log_cache_operation("hit", "endfb8.0/U235/total/1200.0K", logger=None)
        # Function should execute without error

    def test_log_cache_operation_no_logger_param(self):
        """Test log_cache_operation without logger parameter."""
        log_cache_operation("miss", "endfb8.0/U238/capture/900.0K")
        # Function should execute without error

    def test_log_cache_operation_write(self):
        """Test log_cache_operation for write operation."""
        log_cache_operation("write", "test/key/path")
        # Function should execute without error
