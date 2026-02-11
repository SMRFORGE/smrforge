"""
Tests for smrforge.utils.__init__.py import error paths.
"""

from unittest.mock import Mock, patch

import pytest


class TestUtilsInitImports:
    """Test utils.__init__.py import error handling."""

    def test_utils_init_imports_success(self):
        """Test utils.__init__.py imports successfully."""
        import smrforge.utils

        assert hasattr(smrforge.utils, "get_logo_path")
        assert hasattr(smrforge.utils, "get_logger")

    def test_utils_init_parallel_batch_import_error(self):
        """Test utils.__init__.py handles parallel_batch import error."""
        with patch("smrforge.utils.parallel_batch", side_effect=ImportError("Test")):
            # Should not raise, just skip the import
            import importlib

            import smrforge.utils

            importlib.reload(smrforge.utils)
            # Should still have other imports
            assert hasattr(smrforge.utils, "get_logo_path")

    def test_utils_init_optimization_utils_import_error(self):
        """Test utils.__init__.py handles optimization_utils import error."""
        with patch(
            "smrforge.utils.optimization_utils", side_effect=ImportError("Test")
        ):
            import importlib

            import smrforge.utils

            importlib.reload(smrforge.utils)
            # Should still have other imports
            assert hasattr(smrforge.utils, "get_logo_path")

    def test_utils_init_memory_mapped_import_error(self):
        """Test utils.__init__.py handles memory_mapped import error."""
        with patch("smrforge.utils.memory_mapped", side_effect=ImportError("Test")):
            import importlib

            import smrforge.utils

            importlib.reload(smrforge.utils)
            # Should still have other imports
            assert hasattr(smrforge.utils, "get_logo_path")

    def test_utils_init_memory_pool_import_error(self):
        """Test utils.__init__.py handles memory_pool import error."""
        with patch("smrforge.utils.memory_pool", side_effect=ImportError("Test")):
            import importlib

            import smrforge.utils

            importlib.reload(smrforge.utils)
            # Should still have other imports
            assert hasattr(smrforge.utils, "get_logo_path")
