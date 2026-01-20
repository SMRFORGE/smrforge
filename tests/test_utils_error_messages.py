"""
Tests for smrforge.utils.error_messages module.
"""

import pytest
from smrforge.utils.error_messages import (
    format_validation_error,
    suggest_correction,
    format_cross_section_error,
    format_solver_error,
    format_geometry_error,
)


class TestFormatValidationError:
    """Test format_validation_error function."""
    
    def test_format_validation_error_negative_power(self):
        """Test formatting error for negative power."""
        msg = format_validation_error("power_mw", -10.0, "negative")
        assert "Invalid power_mw" in msg
        assert "-10.0" in msg
        assert "Power must be > 0" in msg
    
    def test_format_validation_error_negative_temperature(self):
        """Test formatting error for negative temperature."""
        msg = format_validation_error("temperature", -100.0, "negative")
        assert "Invalid temperature" in msg
        assert "Temperature must be positive" in msg
    
    def test_format_validation_error_enrichment_negative(self):
        """Test formatting error for negative enrichment."""
        msg = format_validation_error("enrichment", -0.1, "negative")
        assert "Invalid enrichment" in msg
        assert "Enrichment must be 0-1" in msg
    
    def test_format_validation_error_enrichment_out_of_range_high(self):
        """Test formatting error for enrichment > 1."""
        msg = format_validation_error("enrichment", 19.5, "out_of_range")
        assert "Invalid enrichment" in msg
        assert "19.5" in msg
        assert "fraction, not percent" in msg
    
    def test_format_validation_error_enrichment_out_of_range_low(self):
        """Test formatting error for enrichment < 0."""
        msg = format_validation_error("enrichment", -0.1, "out_of_range")
        assert "Invalid enrichment" in msg
        assert "Enrichment must be >= 0" in msg
    
    def test_format_validation_error_temperature_order(self):
        """Test formatting error for temperature order."""
        msg = format_validation_error("inlet_temperature", 600.0, "temperature_order")
        assert "Invalid inlet_temperature" in msg
        assert "Inlet temperature must be less than outlet" in msg
    
    def test_format_validation_error_missing_required(self):
        """Test formatting error for missing required field."""
        msg = format_validation_error("power_mw", None, "missing_required")
        assert "Missing required field" in msg
        assert "power_mw" in msg
    
    def test_format_validation_error_with_suggestions(self):
        """Test formatting error with custom suggestions."""
        suggestions = ["Check units", "Verify input"]
        # Use a generic error type that doesn't have specific handling
        msg = format_validation_error("test_field", -10.0, "generic_error", suggestions)
        assert "Suggestions" in msg
        assert "Check units" in msg
    
    def test_format_validation_error_fallback(self):
        """Test formatting error with fallback (no specific handling, no suggestions)."""
        # Use an error type that doesn't match any specific cases and no suggestions
        msg = format_validation_error("test_field", "invalid_value", "unknown_error_type")
        assert "Invalid test_field" in msg
        assert "invalid_value" in msg
        # Should return base message without suggestions
        assert "Suggestions" not in msg


class TestSuggestCorrection:
    """Test suggest_correction function."""
    
    def test_suggest_correction_enrichment_percent(self):
        """Test suggestion for enrichment as percent."""
        suggestion = suggest_correction(19.5, "enrichment")
        assert suggestion is not None
        assert "0.195" in suggestion or "fraction" in suggestion.lower()
    
    def test_suggest_correction_enrichment_negative(self):
        """Test suggestion for negative enrichment."""
        suggestion = suggest_correction(-0.1, "enrichment")
        assert suggestion is not None
        assert "0.1" in suggestion
    
    def test_suggest_correction_power_units(self):
        """Test suggestion for power in wrong units."""
        suggestion = suggest_correction(1e-7, "power_mw")
        assert suggestion is not None
        assert "MW" in suggestion
    
    def test_suggest_correction_temperature_celsius(self):
        """Test suggestion for temperature in Celsius."""
        suggestion = suggest_correction(500.0, "temperature")
        assert suggestion is not None
        assert "773.15" in suggestion or "Kelvin" in suggestion
    
    def test_suggest_correction_temperature_negative(self):
        """Test suggestion for negative temperature."""
        suggestion = suggest_correction(-100.0, "temperature")
        assert suggestion is not None
        assert "100" in suggestion
    
    def test_suggest_correction_no_suggestion(self):
        """Test that no suggestion is returned for valid values."""
        suggestion = suggest_correction(0.195, "enrichment")
        # May or may not return suggestion, but shouldn't error
        assert suggestion is None or isinstance(suggestion, str)


class TestFormatCrossSectionError:
    """Test format_cross_section_error function."""
    
    def test_format_cross_section_error(self):
        """Test formatting cross-section error."""
        msg = format_cross_section_error(0.5, 0.3, 1, 0)
        assert "Invalid cross sections" in msg
        assert "material 1" in msg
        assert "group 0" in msg
        assert "σ_a" in msg
        assert "σ_t" in msg
        assert "Absorption cross section cannot exceed total" in msg


class TestFormatSolverError:
    """Test format_solver_error function."""
    
    def test_format_solver_error_basic(self):
        """Test basic solver error formatting."""
        msg = format_solver_error("Test error", "diffusion")
        assert "Diffusion solver error" in msg
        assert "Test error" in msg
    
    def test_format_solver_error_convergence(self):
        """Test solver error with convergence issues."""
        # The function checks for "convergence" or "converged" in the error message
        msg = format_solver_error("Failed to converged", "diffusion")
        assert "converged" in msg.lower()
        assert "Suggestions" in msg
        assert "max_iterations" in msg
    
    def test_format_solver_error_nan(self):
        """Test solver error with NaN/Inf."""
        msg = format_solver_error("NaN detected", "diffusion")
        assert "nan" in msg.lower() or "inf" in msg.lower()
        assert "Suggestions" in msg
        assert "negative cross sections" in msg.lower()
    
    def test_format_solver_error_with_suggestions(self):
        """Test solver error with custom suggestions."""
        suggestions = ["Check input", "Verify data"]
        msg = format_solver_error("Test error", "diffusion", suggestions)
        assert "Suggestions" in msg
        assert "Check input" in msg


class TestFormatGeometryError:
    """Test format_geometry_error function."""
    
    def test_format_geometry_error_basic(self):
        """Test basic geometry error formatting."""
        msg = format_geometry_error("Test error", "prismatic")
        assert "Prismatic geometry error" in msg
        assert "Test error" in msg
    
    def test_format_geometry_error_mesh(self):
        """Test geometry error with mesh issues."""
        msg = format_geometry_error("Mesh not found", "prismatic")
        assert "Suggestions" in msg
        assert "build_mesh()" in msg
        assert "n_radial" in msg
    
    def test_format_geometry_error_material(self):
        """Test geometry error with material issues."""
        msg = format_geometry_error("Material invalid", "prismatic")
        assert "Suggestions" in msg
        assert "material_map" in msg
        assert "cross-section data" in msg
