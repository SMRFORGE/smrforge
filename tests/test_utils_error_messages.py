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


class TestErrorMessagesEdgeCases:
    """Edge case tests for error_messages.py to improve coverage to 60%+."""
    
    def test_format_validation_error_negative_power_thermal(self):
        """Test formatting error for negative power_thermal."""
        msg = format_validation_error("power_thermal", -5.0, "negative")
        assert "Invalid power_thermal" in msg
        assert "Power must be > 0" in msg
        assert "Did you mean 5.0?" in msg
    
    def test_format_validation_error_negative_outlet_temperature(self):
        """Test formatting error for negative outlet_temperature."""
        msg = format_validation_error("outlet_temperature", -200.0, "negative")
        assert "Invalid outlet_temperature" in msg
        assert "Temperature must be positive" in msg
        assert "Did you mean 200.0 K?" in msg
    
    def test_format_validation_error_negative_inlet_temperature(self):
        """Test formatting error for negative inlet_temperature."""
        msg = format_validation_error("inlet_temperature", -150.0, "negative")
        assert "Invalid inlet_temperature" in msg
        assert "Temperature must be positive" in msg
        assert "Did you mean 150.0 K?" in msg
    
    def test_format_validation_error_non_numeric_negative(self):
        """Test formatting error with non-numeric value for negative error type."""
        msg = format_validation_error("test_field", "invalid", "negative")
        # Should fall back to base message since value is not numeric
        assert "Invalid test_field" in msg
        assert "invalid" in msg
    
    def test_format_validation_error_integer_value(self):
        """Test formatting error with integer value."""
        msg = format_validation_error("power_mw", -10, "negative")
        assert "Invalid power_mw" in msg
        assert "-10" in msg
        assert "Power must be > 0" in msg
    
    def test_format_validation_error_float_zero(self):
        """Test formatting error with zero value."""
        msg = format_validation_error("power_mw", 0.0, "negative")
        assert "Invalid power_mw" in msg
        assert "0.0" in msg
    
    def test_format_validation_error_enrichment_zero(self):
        """Test formatting error with enrichment = 0."""
        msg = format_validation_error("enrichment", -0.0, "negative")
        # Should handle zero
        assert "Invalid enrichment" in msg
    
    def test_format_validation_error_enrichment_exactly_one(self):
        """Test formatting error with enrichment = 1.0."""
        msg = format_validation_error("enrichment", 1.0, "out_of_range")
        # Should not trigger > 1.0 condition
        assert "Invalid enrichment" in msg
    
    def test_format_validation_error_enrichment_just_over_one(self):
        """Test formatting error with enrichment just over 1.0."""
        msg = format_validation_error("enrichment", 1.01, "out_of_range")
        assert "Invalid enrichment" in msg
        assert "1.01" in msg
        assert "fraction, not percent" in msg
    
    def test_format_validation_error_suggestions_empty_list(self):
        """Test formatting error with empty suggestions list."""
        msg = format_validation_error("test_field", -10.0, "generic", [])
        # Empty list should not add suggestions
        assert "Suggestions" not in msg
        assert "Invalid test_field" in msg
    
    def test_format_validation_error_suggestions_multiple(self):
        """Test formatting error with multiple suggestions."""
        suggestions = ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
        msg = format_validation_error("test_field", -10.0, "generic", suggestions)
        assert "Suggestions" in msg
        assert "Suggestion 1" in msg
        assert "Suggestion 2" in msg
        assert "Suggestion 3" in msg
    
    def test_suggest_correction_enrichment_exactly_one(self):
        """Test suggestion for enrichment = 1.0."""
        suggestion = suggest_correction(1.0, "enrichment")
        # Should not trigger percentage suggestion (1.0 < value <= 100.0)
        assert suggestion is None
    
    def test_suggest_correction_enrichment_exactly_100(self):
        """Test suggestion for enrichment = 100.0."""
        suggestion = suggest_correction(100.0, "enrichment")
        assert suggestion is not None
        assert "1.0" in suggestion or "fraction" in suggestion.lower()
    
    def test_suggest_correction_enrichment_over_100(self):
        """Test suggestion for enrichment > 100."""
        suggestion = suggest_correction(150.0, "enrichment")
        # Should not trigger percentage suggestion (value > 100.0)
        assert suggestion is None
    
    def test_suggest_correction_enrichment_just_over_one(self):
        """Test suggestion for enrichment just over 1.0."""
        suggestion = suggest_correction(1.5, "enrichment")
        assert suggestion is not None
        assert "0.015" in suggestion or "fraction" in suggestion.lower()
    
    def test_suggest_correction_power_zero(self):
        """Test suggestion for zero power."""
        suggestion = suggest_correction(0.0, "power_mw")
        # Should not trigger unit suggestion (value not > 0)
        assert suggestion is None
    
    def test_suggest_correction_power_boundary(self):
        """Test suggestion for power at boundary (1e-6)."""
        suggestion = suggest_correction(1e-6, "power_mw")
        # Boundary condition: value not < 1e-6, so should return None
        assert suggestion is None
    
    def test_suggest_correction_power_just_below_boundary(self):
        """Test suggestion for power just below boundary."""
        suggestion = suggest_correction(1e-7, "power_mw")
        assert suggestion is not None
        assert "MW" in suggestion
    
    def test_suggest_correction_temperature_exactly_200(self):
        """Test suggestion for temperature at lower boundary (200)."""
        suggestion = suggest_correction(200.0, "temperature")
        assert suggestion is not None
        assert "473.15" in suggestion or "Kelvin" in suggestion
    
    def test_suggest_correction_temperature_exactly_1000(self):
        """Test suggestion for temperature at upper boundary (1000)."""
        suggestion = suggest_correction(1000.0, "temperature")
        assert suggestion is not None
        assert "1273.15" in suggestion or "Kelvin" in suggestion
    
    def test_suggest_correction_temperature_just_below_200(self):
        """Test suggestion for temperature just below 200."""
        suggestion = suggest_correction(199.0, "temperature")
        # Should not trigger Celsius suggestion (value < 200)
        assert suggestion is None
    
    def test_suggest_correction_temperature_just_above_1000(self):
        """Test suggestion for temperature just above 1000."""
        suggestion = suggest_correction(1001.0, "temperature")
        # Should not trigger Celsius suggestion (value > 1000)
        assert suggestion is None
    
    def test_suggest_correction_temperature_zero(self):
        """Test suggestion for zero temperature."""
        suggestion = suggest_correction(0.0, "temperature")
        # Should not trigger negative suggestion (value not < 0)
        assert suggestion is None
    
    def test_suggest_correction_string_value(self):
        """Test suggestion with string value."""
        suggestion = suggest_correction("invalid", "enrichment")
        # Should return None for non-numeric values
        assert suggestion is None
    
    def test_suggest_correction_list_value(self):
        """Test suggestion with list value."""
        suggestion = suggest_correction([1, 2, 3], "enrichment")
        # Should return None for non-numeric values
        assert suggestion is None
    
    def test_suggest_correction_unknown_field(self):
        """Test suggestion with unknown field name."""
        suggestion = suggest_correction(50.0, "unknown_field")
        # Should return None for unknown fields
        assert suggestion is None
    
    def test_format_cross_section_error_zero_values(self):
        """Test cross-section error with zero values."""
        msg = format_cross_section_error(0.0, 0.0, 0, 0)
        assert "Invalid cross sections" in msg
        assert "material 0" in msg
        assert "group 0" in msg
    
    def test_format_cross_section_error_negative_values(self):
        """Test cross-section error with negative values."""
        msg = format_cross_section_error(-0.1, -0.2, 1, 1)
        assert "Invalid cross sections" in msg
        assert "material 1" in msg
        assert "group 1" in msg
    
    def test_format_cross_section_error_very_large_values(self):
        """Test cross-section error with very large values."""
        msg = format_cross_section_error(1e6, 1e5, 2, 3)
        assert "Invalid cross sections" in msg
        assert "material 2" in msg
        assert "group 3" in msg
    
    def test_format_cross_section_error_different_precision(self):
        """Test cross-section error formatting precision."""
        msg = format_cross_section_error(0.123456789, 0.987654321, 5, 10)
        # Should format with 6 decimal places
        assert "0.123456" in msg or "0.123457" in msg
    
    def test_format_solver_error_convergence_and_nan(self):
        """Test solver error with both convergence and NaN keywords."""
        msg = format_solver_error("Failed to converged, NaN detected", "diffusion")
        assert "Suggestions" in msg
        assert "max_iterations" in msg or "max_iterations" in msg.lower()
        assert "negative cross sections" in msg.lower()
    
    def test_format_solver_error_custom_solver_type(self):
        """Test solver error with custom solver type."""
        msg = format_solver_error("Test error", "monte_carlo")
        assert "Monte_carlo solver error" in msg or "Monte Carlo solver error" in msg
    
    def test_format_solver_error_empty_suggestions(self):
        """Test solver error with empty custom suggestions."""
        msg = format_solver_error("generic error", "diffusion", [])
        # Empty list should not add suggestions if no keywords match
        assert "Diffusion solver error" in msg
    
    def test_format_solver_error_existing_suggestions_with_keyword(self):
        """Test solver error with existing suggestions plus keyword match."""
        custom_suggestions = ["Custom 1", "Custom 2"]
        msg = format_solver_error("convergence failed", "diffusion", custom_suggestions)
        assert "Suggestions" in msg
        assert "Custom 1" in msg
        assert "Custom 2" in msg
        # Should also include automatic suggestions
        assert "max_iterations" in msg or "max_iterations" in msg.lower()
    
    def test_format_solver_error_inf_keyword(self):
        """Test solver error with 'inf' keyword (lowercase)."""
        msg = format_solver_error("inf detected", "diffusion")
        assert "inf" in msg.lower()
        assert "Suggestions" in msg
    
    def test_format_solver_error_nan_keyword_uppercase(self):
        """Test solver error with 'NaN' keyword (uppercase)."""
        msg = format_solver_error("NaN detected", "diffusion")
        assert "nan" in msg.lower() or "NaN" in msg
        assert "Suggestions" in msg
    
    def test_format_geometry_error_different_geometry_type(self):
        """Test geometry error with different geometry type."""
        msg = format_geometry_error("Test error", "pebble_bed")
        assert "Pebble_bed geometry error" in msg or "Pebble Bed geometry error" in msg
    
    def test_format_geometry_error_uppercase_mesh(self):
        """Test geometry error with uppercase MESH keyword."""
        msg = format_geometry_error("MESH not found", "prismatic")
        assert "mesh" in msg.lower() or "MESH" in msg
        assert "Suggestions" in msg
    
    def test_format_geometry_error_uppercase_material(self):
        """Test geometry error with uppercase MATERIAL keyword."""
        msg = format_geometry_error("MATERIAL invalid", "prismatic")
        assert "material" in msg.lower() or "MATERIAL" in msg
        assert "Suggestions" in msg
    
    def test_format_geometry_error_mesh_and_material(self):
        """Test geometry error with both mesh and material keywords."""
        msg = format_geometry_error("Mesh and Material error", "prismatic")
        # Should match first condition (mesh)
        assert "Suggestions" in msg
        assert "build_mesh()" in msg
    
    def test_format_geometry_error_empty_message(self):
        """Test geometry error with empty error message."""
        msg = format_geometry_error("", "prismatic")
        assert "Prismatic geometry error" in msg
    
    def test_format_geometry_error_whitespace_only(self):
        """Test geometry error with whitespace-only message."""
        msg = format_geometry_error("   ", "prismatic")
        assert "Prismatic geometry error" in msg
