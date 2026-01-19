"""
Unit tests for error message utilities.
"""

import pytest

from smrforge.utils.error_messages import (
    format_cross_section_error,
    format_geometry_error,
    format_solver_error,
    format_validation_error,
    suggest_correction,
)


class TestFormatValidationError:
    """Tests for format_validation_error function."""

    def test_format_validation_error_negative_power(self):
        """Test formatting error for negative power."""
        msg = format_validation_error("power_mw", -10.0, "negative")
        assert "Invalid power_mw" in msg
        assert "Power must be > 0" in msg
        assert "Did you mean 10.0?" in msg

    def test_format_validation_error_negative_temperature(self):
        """Test formatting error for negative temperature."""
        msg = format_validation_error("temperature", -100.0, "negative")
        assert "Invalid temperature" in msg
        assert "Temperature must be positive" in msg
        assert "Did you mean 100.0 K?" in msg

    def test_format_validation_error_negative_enrichment(self):
        """Test formatting error for negative enrichment."""
        msg = format_validation_error("enrichment", -0.05, "negative")
        assert "Invalid enrichment" in msg
        assert "Enrichment must be 0-1" in msg

    def test_format_validation_error_out_of_range_enrichment_high(self):
        """Test formatting error for enrichment > 1."""
        msg = format_validation_error("enrichment", 19.5, "out_of_range")
        assert "Invalid enrichment" in msg
        assert "Enrichment must be 0-1" in msg
        assert "Did you mean 0.195?" in msg

    def test_format_validation_error_out_of_range_enrichment_low(self):
        """Test formatting error for enrichment < 0."""
        msg = format_validation_error("enrichment", -0.1, "out_of_range")
        assert "Invalid enrichment" in msg
        assert "Enrichment must be >= 0" in msg

    def test_format_validation_error_temperature_order(self):
        """Test formatting error for temperature order."""
        msg = format_validation_error("inlet_temperature", 800.0, "temperature_order")
        assert "Invalid inlet_temperature" in msg
        assert "Inlet temperature must be less than outlet temperature" in msg

    def test_format_validation_error_missing_required(self):
        """Test formatting error for missing required field."""
        msg = format_validation_error("power", None, "missing_required")
        assert "Missing required field: power" in msg

    def test_format_validation_error_with_suggestions(self):
        """Test formatting error with custom suggestions."""
        suggestions = ["Check units", "Verify input"]
        msg = format_validation_error("test_field", 42, "unknown", suggestions)
        assert "Invalid test_field" in msg
        assert "Suggestions:" in msg
        assert "Check units" in msg

    def test_format_validation_error_base_message(self):
        """Test base error message format."""
        msg = format_validation_error("test_field", 42, "unknown")
        assert "Invalid test_field: 42" in msg


class TestSuggestCorrection:
    """Tests for suggest_correction function."""

    def test_suggest_correction_enrichment_percentage(self):
        """Test suggesting correction for enrichment as percentage."""
        suggestion = suggest_correction(19.5, "enrichment")
        assert suggestion is not None
        assert "Did you mean 0.195?" in suggestion
        assert "fraction, not percent" in suggestion

    def test_suggest_correction_enrichment_negative(self):
        """Test suggesting correction for negative enrichment."""
        suggestion = suggest_correction(-0.05, "enrichment")
        assert suggestion is not None
        assert "Did you mean 0.05?" in suggestion

    def test_suggest_correction_enrichment_valid(self):
        """Test that valid enrichment returns None."""
        suggestion = suggest_correction(0.195, "enrichment")
        assert suggestion is None

    def test_suggest_correction_power_small(self):
        """Test suggesting correction for very small power (might be in W)."""
        suggestion = suggest_correction(1e-7, "power_mw")
        assert suggestion is not None
        assert "Did you mean" in suggestion
        assert "MW" in suggestion

    def test_suggest_correction_temperature_celsius(self):
        """Test suggesting correction for temperature that might be Celsius."""
        suggestion = suggest_correction(500.0, "temperature")
        assert suggestion is not None
        assert "Did you mean 773.15 K?" in suggestion
        assert "Kelvin, not Celsius" in suggestion

    def test_suggest_correction_temperature_negative(self):
        """Test suggesting correction for negative temperature."""
        suggestion = suggest_correction(-50.0, "temperature")
        assert suggestion is not None
        assert "Did you mean 50.0 K?" in suggestion

    def test_suggest_correction_no_suggestion(self):
        """Test that values with no common mistakes return None."""
        suggestion = suggest_correction(1000.0, "power_mw")
        assert suggestion is None


class TestFormatCrossSectionError:
    """Tests for format_cross_section_error function."""

    def test_format_cross_section_error(self):
        """Test formatting cross-section error."""
        msg = format_cross_section_error(0.6, 0.5, 0, 0)
        assert "Invalid cross sections for material 0, group 0" in msg
        assert "σ_a (0.600000) > σ_t (0.500000)" in msg
        assert "Absorption cross section cannot exceed total cross section" in msg


class TestFormatSolverError:
    """Tests for format_solver_error function."""

    def test_format_solver_error_basic(self):
        """Test basic solver error formatting."""
        msg = format_solver_error("Test error", "diffusion")
        assert "Diffusion solver error: Test error" in msg

    def test_format_solver_error_convergence(self):
        """Test solver error with convergence issues."""
        msg = format_solver_error("convergence failed", "diffusion")
        # Check that message contains "converge" (which is in "converged")
        assert "converge" in msg.lower()
        assert "Suggestions:" in msg
        assert "Increase max_iterations" in msg or "max_iterations" in msg.lower()

    def test_format_solver_error_nan(self):
        """Test solver error with NaN/Inf."""
        msg = format_solver_error("NaN detected", "monte_carlo")
        assert "NaN" in msg or "nan" in msg.lower()
        assert "Suggestions:" in msg
        assert "Check for negative cross sections" in msg

    def test_format_solver_error_with_custom_suggestions(self):
        """Test solver error with custom suggestions."""
        suggestions = ["Custom suggestion"]
        msg = format_solver_error("Test error", "diffusion", suggestions)
        assert "Custom suggestion" in msg


class TestFormatGeometryError:
    """Tests for format_geometry_error function."""

    def test_format_geometry_error_basic(self):
        """Test basic geometry error formatting."""
        msg = format_geometry_error("Test error", "prismatic")
        assert "Prismatic geometry error: Test error" in msg

    def test_format_geometry_error_mesh(self):
        """Test geometry error with mesh issues."""
        msg = format_geometry_error("Mesh error", "pebble_bed")
        assert "mesh" in msg.lower()
        assert "Suggestions:" in msg
        assert "Call geometry.build_mesh()" in msg

    def test_format_geometry_error_material(self):
        """Test geometry error with material issues."""
        msg = format_geometry_error("Material error", "prismatic")
        assert "material" in msg.lower()
        assert "Suggestions:" in msg
        assert "Check material_map is valid" in msg
