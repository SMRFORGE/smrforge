"""
Tests for simplified transient analysis convenience API.
"""

import numpy as np
import pytest


class TestQuickTransient:
    """Test quick_transient convenience function."""

    def test_quick_transient_reactivity_insertion(self):
        """Test reactivity insertion transient."""
        from smrforge.convenience.transients import quick_transient

        result = quick_transient(
            power=1e6,  # 1 MWth
            temperature=1200.0,  # K
            reactivity_insertion=0.001,  # 1 m$
            transient_type="reactivity_insertion",
            duration=100.0,  # 100 seconds
        )

        assert "time" in result
        assert "power" in result
        assert "T_fuel" in result
        assert "T_moderator" in result

        assert len(result["time"]) > 0
        assert len(result["power"]) == len(result["time"])
        assert np.all(result["power"] >= 0)  # Power must be non-negative

    def test_quick_transient_reactivity_step(self):
        """Test reactivity step transient."""
        from smrforge.convenience.transients import quick_transient

        result = quick_transient(
            power=1e6,
            temperature=1200.0,
            reactivity_insertion=0.002,  # 2 m$
            transient_type="reactivity_step",
            duration=100.0,
        )

        assert "time" in result
        assert "power" in result

    def test_quick_transient_decay_heat(self):
        """Test decay heat removal transient."""
        from smrforge.convenience.transients import quick_transient

        result = quick_transient(
            power=1e6,
            temperature=1200.0,
            transient_type="decay_heat",
            duration=3600.0,  # 1 hour
        )

        assert "time" in result
        assert "power" in result

        # Power should decrease over time (decay heat)
        if len(result["power"]) > 10:
            assert result["power"][-1] < result["power"][0]

    def test_quick_transient_invalid_type(self):
        """Test that invalid transient type raises error."""
        from smrforge.convenience.transients import quick_transient

        with pytest.raises(ValueError):
            quick_transient(
                power=1e6,
                temperature=1200.0,
                transient_type="invalid_type",
                duration=100.0,
            )

    def test_quick_transient_invalid_inputs(self):
        """Test that invalid inputs raise errors."""
        from smrforge.convenience.transients import quick_transient

        with pytest.raises(ValueError):
            quick_transient(
                power=-1e6,  # Invalid: negative power
                temperature=1200.0,
                duration=100.0,
            )

        with pytest.raises(ValueError):
            quick_transient(
                power=1e6,
                temperature=-100.0,  # Invalid: negative temperature
                duration=100.0,
            )

        with pytest.raises(ValueError):
            quick_transient(
                power=1e6,
                temperature=1200.0,
                duration=-10.0,  # Invalid: negative duration
            )

    def test_quick_transient_long_term_optimization(self):
        """Test long-term transient with optimizations."""
        from smrforge.convenience.transients import quick_transient

        # 72-hour transient (should auto-enable optimizations)
        result = quick_transient(
            power=1e6,
            temperature=1200.0,
            transient_type="decay_heat",
            duration=72 * 3600,  # 72 hours
            long_term_optimization=True,
        )

        assert "time" in result
        assert len(result["time"]) > 0
        assert result["time"][-1] >= 72 * 3600 - 3600.0  # Should reach near end


class TestReactivityInsertion:
    """Test reactivity_insertion convenience wrapper."""

    def test_reactivity_insertion(self):
        """Test reactivity insertion wrapper."""
        from smrforge.convenience.transients import reactivity_insertion

        result = reactivity_insertion(
            power=1e6,
            temperature=1200.0,
            reactivity=0.002,  # 2 m$
            duration=100.0,
        )

        assert "time" in result
        assert "power" in result
        assert len(result["time"]) > 0


class TestDecayHeatRemoval:
    """Test decay_heat_removal convenience wrapper."""

    def test_decay_heat_removal(self):
        """Test decay heat removal wrapper."""
        from smrforge.convenience.transients import decay_heat_removal

        result = decay_heat_removal(
            power=1e6,
            temperature=1200.0,
            duration=3600.0,  # 1 hour
        )

        assert "time" in result
        assert "power" in result

    def test_decay_heat_removal_long_term(self):
        """Test long-term decay heat removal."""
        from smrforge.convenience.transients import decay_heat_removal

        # 72-hour transient (should auto-enable optimizations)
        result = decay_heat_removal(
            power=1e6,
            temperature=1200.0,
            duration=72 * 3600,  # 72 hours
        )

        assert "time" in result
        assert result["time"][-1] >= 72 * 3600 - 3600.0


class TestImports:
    """Test that convenience functions can be imported."""

    def test_import_quick_transient(self):
        """Test importing quick_transient."""
        from smrforge.convenience.transients import quick_transient

        assert callable(quick_transient)

    def test_import_from_convenience(self):
        """Test importing from convenience module."""
        try:
            from smrforge.convenience import quick_transient

            assert callable(quick_transient)
        except ImportError:
            # May not be exported at top level
            pass

    def test_import_from_top_level(self):
        """Test importing from top-level smrforge."""
        try:
            from smrforge import quick_transient

            assert callable(quick_transient)
        except ImportError:
            # May not be exported at top level
            pass
