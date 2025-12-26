"""
Tests for presets/htgr.py module (HTGR reference designs).
"""

from pathlib import Path

import numpy as np
import pytest

try:
    from smrforge.presets.htgr import (
        DesignLibrary,
        GTMHR350,
        HTRPM200,
        MicroHTGR,
        ValarAtomicsReactor,
    )
    from smrforge.validation.models import ReactorSpecification
except ImportError:
    pytest.skip("Presets module not available", allow_module_level=True)


class TestValarAtomicsReactor:
    """Test ValarAtomicsReactor class."""

    def test_valar_atomics_reactor_initialization(self):
        """Test ValarAtomicsReactor initialization."""
        reactor = ValarAtomicsReactor()

        assert reactor.spec is not None
        assert isinstance(reactor.spec, ReactorSpecification)
        assert reactor.spec.name == "Valar-10"
        assert reactor.geometry_params is not None
        assert reactor.core is None  # Not built yet
        assert reactor.materials is not None

    def test_valar_atomics_reactor_build_core(self):
        """Test building core geometry."""
        reactor = ValarAtomicsReactor()

        core = reactor.build_core()

        assert core is not None
        assert reactor.core is not None
        assert core.name == "Valar-10"

    def test_valar_atomics_reactor_get_cross_sections(self):
        """Test getting cross section data."""
        reactor = ValarAtomicsReactor()

        xs_data = reactor.get_cross_sections()

        assert xs_data.n_groups == 8
        assert xs_data.n_materials == 2
        assert xs_data.sigma_t.shape == (2, 8)
        assert xs_data.sigma_a.shape == (2, 8)
        assert xs_data.sigma_f.shape == (2, 8)
        assert xs_data.nu_sigma_f.shape == (2, 8)
        assert xs_data.sigma_s.shape == (2, 8, 8)
        assert xs_data.chi.shape == (2, 8)
        assert xs_data.D.shape == (2, 8)

    def test_valar_atomics_reactor_create_scattering_matrix(self):
        """Test _create_scattering_matrix method."""
        reactor = ValarAtomicsReactor()

        sigma_s = reactor._create_scattering_matrix(n_groups=4, n_materials=2)

        assert sigma_s.shape == (2, 4, 4)
        # Check diagonal elements (self-scattering)
        assert np.all(sigma_s[:, 0, 0] > 0)

    def test_valar_atomics_reactor_to_json(self, tmp_path):
        """Test saving design to JSON."""
        reactor = ValarAtomicsReactor()
        filepath = tmp_path / "valar-10.json"

        reactor.to_json(filepath)

        assert filepath.exists()
        # Verify it's valid JSON
        import json

        with open(filepath) as f:
            data = json.load(f)
        assert "name" in data
        assert data["name"] == "Valar-10"

    def test_valar_atomics_reactor_from_json(self, tmp_path):
        """Test loading design from JSON."""
        reactor = ValarAtomicsReactor()
        filepath = tmp_path / "valar-10.json"

        # Save first
        reactor.to_json(filepath)

        # Load
        loaded_reactor = ValarAtomicsReactor.from_json(filepath)

        assert loaded_reactor.spec.name == "Valar-10"
        assert loaded_reactor.spec.power_thermal == 10e6
        assert loaded_reactor.core is None  # Not built from JSON


class TestGTMHR350:
    """Test GTMHR350 class."""

    def test_gtmhr350_initialization(self):
        """Test GTMHR350 initialization."""
        reactor = GTMHR350()

        assert reactor.spec is not None
        assert isinstance(reactor.spec, ReactorSpecification)
        assert reactor.spec.name == "GT-MHR-350"
        assert reactor.geometry_params is not None

    def test_gtmhr350_build_core(self):
        """Test building GT-MHR core."""
        reactor = GTMHR350()

        core = reactor.build_core()

        assert core is not None
        assert core.name == "GT-MHR-350"


class TestHTRPM200:
    """Test HTRPM200 class."""

    def test_htrpm200_initialization(self):
        """Test HTRPM200 initialization."""
        reactor = HTRPM200()

        assert reactor.spec is not None
        assert isinstance(reactor.spec, ReactorSpecification)
        assert reactor.spec.name == "HTR-PM-200"
        assert reactor.geometry_params is not None

    def test_htrpm200_build_core(self):
        """Test building HTR-PM pebble bed core."""
        reactor = HTRPM200()

        core = reactor.build_core()

        assert core is not None
        assert core.name == "HTR-PM-200"


class TestMicroHTGR:
    """Test MicroHTGR class."""

    def test_micro_htgr_initialization(self):
        """Test MicroHTGR initialization."""
        reactor = MicroHTGR()

        assert reactor.spec is not None
        assert isinstance(reactor.spec, ReactorSpecification)
        assert reactor.spec.name == "Micro-HTGR-1"
        assert reactor.geometry_params is not None

    def test_micro_htgr_spec_properties(self):
        """Test MicroHTGR specification properties."""
        reactor = MicroHTGR()

        # Check some key properties
        assert reactor.spec.power_thermal == 1e6  # 1 MWth
        assert reactor.spec.reactor_type.value == "prismatic"
        assert reactor.spec.enrichment == 0.195  # HALEU


class TestDesignLibrary:
    """Test DesignLibrary class."""

    def test_design_library_initialization(self):
        """Test DesignLibrary initialization."""
        library = DesignLibrary()

        assert library.designs is not None
        assert len(library.designs) > 0

    def test_design_library_list_designs(self):
        """Test list_designs method."""
        library = DesignLibrary()

        designs = library.list_designs()

        assert isinstance(designs, list)
        assert len(designs) > 0
        assert "valar-10" in designs
        assert "gt-mhr-350" in designs

    def test_design_library_get_design(self):
        """Test get_design method."""
        library = DesignLibrary()

        design = library.get_design("valar-10")

        assert isinstance(design, ReactorSpecification)
        assert design.name == "Valar-10"

    def test_design_library_get_design_invalid(self):
        """Test get_design with invalid name raises KeyError."""
        library = DesignLibrary()

        with pytest.raises(KeyError, match="not found"):
            library.get_design("nonexistent-design")

    def test_design_library_export_design(self, tmp_path):
        """Test export_design method."""
        library = DesignLibrary()
        filepath = tmp_path / "valar-export.json"

        library.export_design("valar-10", filepath)

        assert filepath.exists()
        # Verify it's valid JSON
        import json

        with open(filepath) as f:
            data = json.load(f)
        assert "name" in data

    def test_design_library_import_design(self, tmp_path):
        """Test import_design method."""
        library = DesignLibrary()
        filepath = tmp_path / "imported-design.json"

        # Export a design first
        library.export_design("valar-10", filepath)

        # Import with a new name
        imported = library.import_design(filepath, "valar-10-imported")

        assert isinstance(imported, ReactorSpecification)
        assert imported.name == "Valar-10"
        assert "valar-10-imported" in library.designs

    def test_design_library_validate_all_designs(self):
        """Test validate_all_designs method."""
        library = DesignLibrary()

        all_valid = library.validate_all_designs()

        # All designs should be valid (they're validated on construction)
        assert all_valid is True

    def test_design_library_compare_designs(self, capsys):
        """Test compare_designs method."""
        library = DesignLibrary()

        # This method prints to console, so we capture output
        library.compare_designs(["valar-10", "gt-mhr-350"])

        # Just verify it doesn't raise an exception
        # The method uses rich console which is hard to test directly
        assert True  # If we get here, it worked

    def test_design_library_compare_all_designs(self, capsys):
        """Test compare_designs with all designs."""
        library = DesignLibrary()

        all_designs = library.list_designs()
        library.compare_designs(all_designs)

        # Just verify it doesn't raise an exception
        assert True

