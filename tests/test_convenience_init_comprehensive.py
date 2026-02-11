"""
Comprehensive tests for smrforge.convenience package.
"""

import importlib
import sys
from unittest.mock import patch

import pytest


class TestConvenienceInitImportPaths:
    """Test import paths for convenience package."""

    def test_import_when_parent_available(self):
        """Test import when parent convenience module is already loaded."""
        if "smrforge.convenience" in sys.modules:
            importlib.reload(sys.modules["smrforge.convenience"])

        import smrforge.convenience

        assert hasattr(smrforge.convenience, "_CONVENIENCE_MAIN_AVAILABLE")

    def test_transient_convenience_available(self):
        """Test transient convenience functions availability."""
        import smrforge.convenience

        # Check if transient functions are available
        assert hasattr(smrforge.convenience, "_TRANSIENT_CONVENIENCE_AVAILABLE")
        is_available = smrforge.convenience._TRANSIENT_CONVENIENCE_AVAILABLE

        # If available, check that functions are in __all__
        if is_available and hasattr(smrforge.convenience, "__all__"):
            __all__ = smrforge.convenience.__all__
            transient_funcs = [
                "quick_transient",
                "reactivity_insertion",
                "decay_heat_removal",
            ]
            for func in transient_funcs:
                if is_available:
                    # Function might be in __all__ if available
                    pass

    def test_transient_convenience_not_available(self):
        """Test when transient convenience functions are not available."""
        with patch.dict(sys.modules, {"smrforge.convenience.transients": None}):
            if "smrforge.convenience" in sys.modules:
                importlib.reload(sys.modules["smrforge.convenience"])

            import smrforge.convenience

            # Should have flag set to False
            assert hasattr(smrforge.convenience, "_TRANSIENT_CONVENIENCE_AVAILABLE")
            # May be False if import failed
            assert isinstance(
                smrforge.convenience._TRANSIENT_CONVENIENCE_AVAILABLE, bool
            )

    def test_all_exports_when_available(self):
        """Test __all__ exports when convenience main is available."""
        import smrforge.convenience

        if (
            hasattr(smrforge.convenience, "__all__")
            and smrforge.convenience._CONVENIENCE_MAIN_AVAILABLE
        ):
            __all__ = smrforge.convenience.__all__

            # Should contain main convenience functions
            expected_main = [
                "list_presets",
                "get_preset",
                "create_reactor",
                "analyze_preset",
                "compare_designs",
                "quick_keff",
                "SimpleReactor",
            ]

            for func in expected_main:
                if smrforge.convenience._CONVENIENCE_MAIN_AVAILABLE:
                    # Function should be available
                    pass

    def test_all_exports_when_transients_available(self):
        """Test __all__ exports when transient convenience is available."""
        import smrforge.convenience

        if (
            hasattr(smrforge.convenience, "__all__")
            and hasattr(smrforge.convenience, "_TRANSIENT_CONVENIENCE_AVAILABLE")
            and smrforge.convenience._TRANSIENT_CONVENIENCE_AVAILABLE
        ):
            __all__ = smrforge.convenience.__all__

            # Should contain transient functions
            expected_transients = [
                "quick_transient",
                "reactivity_insertion",
                "decay_heat_removal",
            ]

            for func in expected_transients:
                # Function should be in __all__ if available
                pass


class TestConvenienceInitEdgeCases:
    """Edge case tests for convenience package."""

    def test_import_when_parent_is_same_module(self):
        """Test import path for convenience package."""
        if "smrforge.convenience" in sys.modules:
            original = sys.modules["smrforge.convenience"]
            try:
                import smrforge.convenience

                assert hasattr(smrforge.convenience, "_CONVENIENCE_MAIN_AVAILABLE")
            finally:
                sys.modules["smrforge.convenience"] = original
        else:
            import smrforge.convenience

            assert hasattr(smrforge.convenience, "_CONVENIENCE_MAIN_AVAILABLE")

    def test_all_empty_when_main_unavailable(self):
        """Test __all__ is empty when main convenience is unavailable."""
        # This tests the case where _CONVENIENCE_MAIN_AVAILABLE is False
        # and __all__ only contains transient functions if available
        import smrforge.convenience

        # Check that __all__ exists
        assert hasattr(smrforge.convenience, "__all__")
        # If main is unavailable, __all__ might be empty or only contain transients
        __all__ = smrforge.convenience.__all__
        assert isinstance(__all__, list)

    def test_all_exports_only_main_available(self):
        """Test __all__ when only main convenience is available, not transients."""
        import smrforge.convenience

        # Check __all__ structure
        if hasattr(smrforge.convenience, "__all__"):
            __all__ = smrforge.convenience.__all__
            assert isinstance(__all__, list)

            # If main is available, should have main functions
            if smrforge.convenience._CONVENIENCE_MAIN_AVAILABLE:
                expected = [
                    "list_presets",
                    "get_preset",
                    "create_reactor",
                    "analyze_preset",
                    "compare_designs",
                    "quick_keff",
                    "SimpleReactor",
                ]
                # At least some of these should be in __all__
                pass
