"""Tests for smrforge.utils.error_messages."""

import pytest

from smrforge.utils.error_messages import (
    format_cross_section_error,
    format_geometry_error,
    format_solver_error,
    format_validation_error,
    suggest_correction,
    suggest_install_pro,
)


class TestSuggestInstallPro:
    """Tests for suggest_install_pro."""

    def test_default_message(self):
        msg = suggest_install_pro()
        assert "SMRForge Pro" in msg
        assert "pip install smrforge-pro" in msg

    def test_with_feature(self):
        msg = suggest_install_pro(feature="OpenMC tally visualization")
        assert "OpenMC tally visualization" in msg
        assert "Pro" in msg

    def test_with_extra(self):
        msg = suggest_install_pro(extra="openmc")
        assert "smrforge-pro[openmc]" in msg

    def test_empty_extra(self):
        msg = suggest_install_pro(extra="")
        assert "pip install smrforge-pro" in msg
        assert "[" not in msg or "[]" in msg


class TestFormatValidationError:
    """Tests for format_validation_error."""

    def test_negative_power(self):
        msg = format_validation_error("power_mw", -100, "negative")
        assert "power_mw" in msg
        assert "-100" in msg
        assert "> 0" in msg or "positive" in msg.lower()

    def test_enrichment_out_of_range(self):
        msg = format_validation_error("enrichment", 19.5, "out_of_range")
        assert "enrichment" in msg
        assert "0-1" in msg or "fraction" in msg.lower()


class TestSuggestCorrection:
    """Tests for suggest_correction."""

    def test_enrichment_percent(self):
        s = suggest_correction(19.5, "enrichment")
        assert s is not None
        assert "0.195" in s or "fraction" in s.lower()

    def test_enrichment_valid(self):
        s = suggest_correction(0.195, "enrichment")
        assert s is None


class TestFormatCrossSectionError:
    """Tests for format_cross_section_error."""

    def test_invalid_sigma(self):
        msg = format_cross_section_error(0.5, 0.3, 1, 0)
        assert "material 1" in msg or "group 0" in msg
        assert "σ_a" in msg or "sigma" in msg.lower()


class TestFormatSolverError:
    """Tests for format_solver_error."""

    def test_convergence_adds_suggestions(self):
        msg = format_solver_error("Convergence failed", solver_type="diffusion")
        assert "convergence" in msg.lower() or "Convergence" in msg
        assert "max_iterations" in msg or "tolerance" in msg.lower()


class TestFormatGeometryError:
    """Tests for format_geometry_error."""

    def test_mesh_suggestion(self):
        msg = format_geometry_error("Invalid mesh", geometry_type="prismatic")
        assert "mesh" in msg.lower()
        assert "build_mesh" in msg or "Suggestions" in msg
