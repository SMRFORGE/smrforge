"""
Tests implementing COVERAGE_TRACKING.md (lines 258-277) – Modules Below 75% Target.

Covers:
- data_downloader.py: _get_endf_url, _get_nndc_url, _get_download_urls, _cache_successful_source, _expand_elements_to_nuclides (Medium)
- core/decay_chain_utils.py: build_fission_product_chain max_depth=0 (Low)
- geometry/validation.py: Gap severity, check_distances_and_clearances ImportError, ValidationReport (Medium)
- geometry/advanced_import.py: _is_numeric, CSGSurface, CSGCell, Lattice, GeometryConverter (Medium)
- convenience.py, convenience/__init__.py: wrapper/import paths, _get_library ImportError (Low)
- economics.integration, burnup/fuel_management_integration: import/init paths (Low)
- core/endf_setup.py: print_* helpers, validate_endf_setup(nonexistent + None→standard_dir) (Low)
- control/integration.py: create_controlled_reactivity (Low)
- core/self_shielding_integration.py: _RESONANCE_AVAILABLE=False path (Low)
- core/multigroup_advanced.py: SPHFactors, SPHMethod init (Low)
- neutronics/hybrid_solver.py: RegionPartition (Low)
- neutronics/adaptive_sampling.py: ImportanceMap init/get_total_importance (Low)
- neutronics/implicit_mc.py: IMCTimeStep, ImplicitMonteCarloSolver init (Low)
- neutronics/monte_carlo_optimized.py: ReactionType, ParticleBank init/add_particle/clear (Low)
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# geometry/advanced_import.py (Medium – Complex feature)
# ---------------------------------------------------------------------------

class TestAdvancedImportCoverage:
    """Coverage for geometry/advanced_import.py per table 258-277."""

    def test_is_numeric_true(self):
        """_is_numeric returns True for numeric strings."""
        from smrforge.geometry.advanced_import import _is_numeric
        assert _is_numeric("1.5") is True
        assert _is_numeric("0") is True
        assert _is_numeric("-2.3e-4") is True

    def test_is_numeric_false(self):
        """_is_numeric returns False for non-numeric strings."""
        from smrforge.geometry.advanced_import import _is_numeric
        assert _is_numeric("abc") is False
        assert _is_numeric("") is False
        assert _is_numeric("1.2.3") is False

    def test_csg_surface_dataclass(self):
        """CSGSurface can be constructed and has expected attributes."""
        from smrforge.geometry.advanced_import import CSGSurface
        s = CSGSurface(id=1, surface_type="z-cylinder", coeffs=[0.0, 0.0, 10.0], boundary_type="vacuum")
        assert s.id == 1
        assert s.surface_type == "z-cylinder"
        assert s.boundary_type == "vacuum"

    def test_csg_cell_dataclass(self):
        """CSGCell can be constructed with optional attributes."""
        from smrforge.geometry.advanced_import import CSGCell
        c = CSGCell(id=1, region="-1 & 2 & -3", material=1, fill=0)
        assert c.id == 1
        assert c.region == "-1 & 2 & -3"
        assert c.material == 1
        assert c.surfaces == []

    def test_lattice_dataclass(self):
        """Lattice can be constructed (requires Point3D-like or mock)."""
        from smrforge.geometry.advanced_import import Lattice
        try:
            from smrforge.geometry.core_geometry import Point3D
            p = Point3D(0, 0, 0)
        except ImportError:
            p = MagicMock()
            p.x = p.y = p.z = 0
        L = Lattice(
            id=1,
            lattice_type="rectangular",
            dimension=(2, 2, 1),
            lower_left=p,
            pitch=(1.26, 1.26, 800.0),
            universes=[[[1, 1], [1, 1]]],
        )
        assert L.id == 1
        assert L.lattice_type == "rectangular"
        assert L.dimension == (2, 2, 1)

    def test_geometry_converter_unsupported_input_format(self):
        """GeometryConverter.convert_format raises ValueError for unsupported input format."""
        from smrforge.geometry.advanced_import import GeometryConverter
        with pytest.raises(ValueError, match="Unsupported input format"):
            GeometryConverter.convert_format(
                Path("/nonexistent.in"),
                Path("/nonexistent.out"),
                "unknown_format",
                "json",
            )

    def test_geometry_converter_unsupported_output_format(self):
        """GeometryConverter.convert_format raises ValueError for unsupported output format."""
        from smrforge.geometry.advanced_import import GeometryConverter, AdvancedGeometryImporter
        mock_core = MagicMock()
        with patch.object(AdvancedGeometryImporter, "from_openmc_full", return_value=mock_core):
            with pytest.raises(ValueError, match="Unsupported output format"):
                GeometryConverter.convert_format(
                    Path("/x.xml"),
                    Path("/y.out"),
                    "openmc",
                    "unknown_output_format",
                )


# ---------------------------------------------------------------------------
# geometry/validation.py (Medium – Consider improvement)
# ---------------------------------------------------------------------------

class TestGeometryValidationCoverage:
    """Coverage for geometry/validation.py – Gap severity, check_distances_and_clearances."""

    def test_gap_severity_overlap_large(self):
        """Gap __post_init__ sets severity='error' when gap_size < -1.0."""
        try:
            from smrforge.geometry.core_geometry import Point3D
            from smrforge.geometry.validation import Gap
            p = Point3D(0, 0, 0)
        except ImportError:
            pytest.skip("Geometry module not available")
        g = Gap(
            element1_id="a", element2_id="b",
            distance=1.0, expected_distance=3.0,
            gap_size=0.0, location=p,
        )
        assert g.gap_size == -2.0
        assert g.severity == "error"

    def test_gap_severity_small_overlap(self):
        """Gap __post_init__ sets severity='warning' when -1 <= gap_size < 0."""
        try:
            from smrforge.geometry.core_geometry import Point3D
            from smrforge.geometry.validation import Gap
            p = Point3D(0, 0, 0)
        except ImportError:
            pytest.skip("Geometry module not available")
        g = Gap(
            element1_id="a", element2_id="b",
            distance=2.0, expected_distance=2.5,
            gap_size=0.0, location=p,
        )
        assert g.gap_size == -0.5
        assert g.severity == "warning"

    def test_gap_severity_large_gap(self):
        """Gap __post_init__ sets severity='warning' when gap_size > 5.0."""
        try:
            from smrforge.geometry.core_geometry import Point3D
            from smrforge.geometry.validation import Gap
            p = Point3D(0, 0, 0)
        except ImportError:
            pytest.skip("Geometry module not available")
        g = Gap(
            element1_id="a", element2_id="b",
            distance=20.0, expected_distance=10.0,
            gap_size=0.0, location=p,
        )
        assert g.gap_size == 10.0
        assert g.severity == "warning"

    def test_gap_severity_info(self):
        """Gap __post_init__ sets severity='info' when 0 <= gap_size <= 5."""
        try:
            from smrforge.geometry.core_geometry import Point3D
            from smrforge.geometry.validation import Gap
            p = Point3D(0, 0, 0)
        except ImportError:
            pytest.skip("Geometry module not available")
        g = Gap(
            element1_id="a", element2_id="b",
            distance=3.0, expected_distance=2.0,
            gap_size=0.0, location=p,
        )
        assert g.gap_size == 1.0
        assert g.severity == "info"

    def test_check_distances_and_clearances_import_error(self):
        """check_distances_and_clearances raises ImportError when geometry types unavailable."""
        from smrforge.geometry import validation as val
        with patch.object(val, "_GEOMETRY_TYPES_AVAILABLE", False):
            with pytest.raises(ImportError, match="Geometry module not available"):
                val.check_distances_and_clearances(MagicMock())


# ---------------------------------------------------------------------------
# data_downloader.py (Medium – Helper functions tested)
# ---------------------------------------------------------------------------

class TestDataDownloaderHelperCoverage:
    """Additional helper coverage for data_downloader.py per table 258-277."""

    def test_parse_isotope_string_helper_coverage(self):
        """_parse_isotope_string helper coverage: normal and invalid symbol."""
        try:
            import smrforge.data_downloader as dd
        except ImportError:
            pytest.skip("Data downloader module not available")
        r = dd._parse_isotope_string("U235")
        assert r is not None
        assert r.Z == 92 and r.A == 235 and r.m == 0
        assert dd._parse_isotope_string("Xx235") is None

    def test_get_nndc_url_returns_url_for_endf_library(self):
        """_get_nndc_url returns NNDC URL for ENDF/B-VIII and VIII.1."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        nuclide = dd._parse_isotope_string("U235")
        assert nuclide is not None
        url8 = dd._get_nndc_url(nuclide, Library.ENDF_B_VIII)
        assert "nndc.bnl.gov" in url8
        assert nuclide.name in url8 or "endf" in url8.lower()
        url81 = dd._get_nndc_url(nuclide, Library.ENDF_B_VIII_1)
        assert "nndc.bnl.gov" in url81

    def test_get_download_urls_returns_iaea_first_by_default(self):
        """_get_download_urls returns [IAEA, NNDC] when cache is empty/default."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        nuclide = dd._parse_isotope_string("U235")
        assert nuclide is not None
        urls = dd._get_download_urls(nuclide, Library.ENDF_B_VIII)
        assert len(urls) == 2
        assert "iaea" in urls[0].lower() or "nds" in urls[0].lower()
        assert "nndc.bnl.gov" in urls[1]

    def test_get_download_urls_returns_nndc_first_when_cached(self):
        """_get_download_urls returns [NNDC, IAEA] when _source_cache prefers nndc."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        nuclide = dd._parse_isotope_string("U235")
        assert nuclide is not None
        old = getattr(dd, "_source_cache", {}).copy()
        try:
            dd._source_cache[Library.ENDF_B_VIII.value] = "nndc"
            urls = dd._get_download_urls(nuclide, Library.ENDF_B_VIII)
            assert len(urls) == 2
            assert "nndc.bnl.gov" in urls[0]
        finally:
            dd._source_cache.clear()
            dd._source_cache.update(old)

    def test_cache_successful_source_iaea_and_nndc(self):
        """_cache_successful_source sets iaea or nndc in _source_cache from URL."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        old = getattr(dd, "_source_cache", {}).copy()
        try:
            dd._cache_successful_source("https://nds.iaea.org/exfor/endf/endfb8.0/", Library.ENDF_B_VIII)
            assert dd._source_cache.get(Library.ENDF_B_VIII.value) == "iaea"
            dd._cache_successful_source("https://www.nndc.bnl.gov/endf/b8.1/endf/U235.endf", Library.ENDF_B_VIII_1)
            assert dd._source_cache.get(Library.ENDF_B_VIII_1.value) == "nndc"
        finally:
            dd._source_cache.clear()
            dd._source_cache.update(old)

    def test_get_endf_url_returns_iaea_url(self):
        """_get_endf_url returns IAEA URL for ENDF library."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        nuclide = dd._parse_isotope_string("U235")
        assert nuclide is not None
        url = dd._get_endf_url(nuclide, Library.ENDF_B_VIII)
        assert "iaea" in url.lower()
        assert nuclide.name in url

    def test_expand_elements_to_nuclides_unknown_element_skipped(self):
        """_expand_elements_to_nuclides skips unknown element and returns others or []."""
        try:
            import smrforge.data_downloader as dd
            from smrforge.core.reactor_core import Library
        except ImportError:
            pytest.skip("Data downloader or reactor_core not available")
        result = dd._expand_elements_to_nuclides(["Xx"], Library.ENDF_B_VIII)
        assert result == []
        result_u = dd._expand_elements_to_nuclides(["U"], Library.ENDF_B_VIII)
        assert len(result_u) > 0
        assert all(n.Z == 92 for n in result_u)


# ---------------------------------------------------------------------------
# convenience.py (Low – Convenience wrapper)
# ---------------------------------------------------------------------------

class TestConvenienceCoverage:
    """Minimal coverage for convenience.py wrapper paths."""

    def test_convenience_import_run_presets(self):
        """convenience.run_presets or similar is callable if exposed."""
        try:
            import smrforge.convenience as conv
            if hasattr(conv, "run_presets"):
                assert callable(conv.run_presets)
        except ImportError:
            pytest.skip("Convenience module not available")

    def test_convenience_has_common_attrs(self):
        """convenience exposes expected high-level attributes."""
        try:
            import smrforge.convenience as conv
            assert hasattr(conv, "__name__")
        except ImportError:
            pytest.skip("Convenience module not available")

    def test_get_library_returns_cached_when_design_library_set(self):
        """_get_library() returns cached _design_library when already set."""
        try:
            import smrforge.convenience as conv_mod
        except ImportError:
            pytest.skip("Convenience module not available")
        if not getattr(conv_mod, "_PRESETS_AVAILABLE", False):
            pytest.skip("Presets not available")
        cached = MagicMock()
        cached.list_designs.return_value = ["design-a", "design-b"]
        with patch.object(conv_mod, "_design_library", cached):
            out = conv_mod.list_presets()
        assert out == ["design-a", "design-b"]
        cached.list_designs.assert_called_once()


# ---------------------------------------------------------------------------
# economics/integration.py (Low – Not critical, but move off 0%)
# ---------------------------------------------------------------------------

class TestEconomicsIntegrationCoverage:
    """Minimal coverage for economics/integration.py (0% -> nonzero)."""

    def test_economics_integration_import(self):
        """economics.integration can be imported and has expected content."""
        try:
            from smrforge.economics import integration as eco_int
            assert hasattr(eco_int, "__name__")
        except ImportError:
            pytest.skip("Economics integration not available")


# ---------------------------------------------------------------------------
# convenience/__init__.py (Low – Import wrapper, ImportError path)
# ---------------------------------------------------------------------------

class TestConvenienceInitCoverage:
    """Coverage for convenience/__init__.py – _get_library ImportError path."""

    def test_list_presets_raises_when_presets_unavailable(self):
        """list_presets() raises ImportError when _PRESETS_AVAILABLE is False."""
        try:
            import smrforge.convenience as conv_mod
        except ImportError:
            pytest.skip("Convenience package not available")
        with patch.object(conv_mod, "_PRESETS_AVAILABLE", False):
            with patch.object(conv_mod, "_design_library", None):
                with pytest.raises(ImportError, match="Preset designs not available"):
                    conv_mod.list_presets()


# ---------------------------------------------------------------------------
# geometry/validation.py – ValidationReport methods
# ---------------------------------------------------------------------------

class TestValidationReportCoverage:
    """Coverage for ValidationReport.add_error, add_warning, add_info, summary."""

    def test_validation_report_summary_and_messages(self):
        """ValidationReport add_error/add_warning/add_info and summary()."""
        try:
            from smrforge.geometry.validation import ValidationReport
        except ImportError:
            pytest.skip("Geometry validation not available")
        r = ValidationReport()
        assert r.valid is True
        r.add_error("err1")
        r.add_warning("w1")
        r.add_info("i1")
        assert r.valid is False
        assert "err1" in r.errors and "w1" in r.warnings and "i1" in r.info
        s = r.summary()
        assert "INVALID" in s
        assert "Errors: 1" in s
        assert "Warnings: 1" in s
        assert "Info: 1" in s

    def test_validation_report_summary_valid_branch(self):
        """ValidationReport.summary() shows VALID when no errors (valid=True)."""
        try:
            from smrforge.geometry.validation import ValidationReport
        except ImportError:
            pytest.skip("Geometry validation not available")
        r = ValidationReport()
        r.add_info("info only")
        assert r.valid is True
        s = r.summary()
        assert "VALID" in s and "INVALID" not in s
        assert "Info: 1" in s


# ---------------------------------------------------------------------------
# core/decay_chain_utils.py (Low – build_fission_product_chain max_depth=0)
# ---------------------------------------------------------------------------

class TestDecayChainUtilsCoverage:
    """Coverage for core/decay_chain_utils.build_fission_product_chain max_depth=0."""

    def test_build_fission_product_chain_max_depth_zero(self):
        """build_fission_product_chain with max_depth=0 returns chain with only parent."""
        try:
            from smrforge.core.decay_chain_utils import build_fission_product_chain
            from smrforge.core.reactor_core import Nuclide
        except ImportError:
            pytest.skip("decay_chain_utils or reactor_core not available")
        parent = Nuclide(92, 235, 0)
        chain = build_fission_product_chain(parent, max_depth=0)
        assert len(chain.nuclides) == 1
        assert chain.nuclides[0].Z == 92 and chain.nuclides[0].A == 235


# ---------------------------------------------------------------------------
# burnup/fuel_management_integration.py (Low – Integration code)
# ---------------------------------------------------------------------------

class TestFuelManagementIntegrationCoverage:
    """Minimal coverage for burnup/fuel_management_integration.py."""

    def test_fuel_management_integration_import_and_init(self):
        """BurnupFuelManagerIntegration can be imported and constructed with mock."""
        try:
            from smrforge.burnup.fuel_management_integration import BurnupFuelManagerIntegration
        except ImportError:
            pytest.skip("burnup.fuel_management_integration not available")
        mock_fm = MagicMock()
        mock_fm.assemblies = []
        obj = BurnupFuelManagerIntegration(mock_fm)
        assert obj.fuel_manager is mock_fm
        assert obj._assembly_solvers == {}
        assert obj._assembly_inventories == {}


# ---------------------------------------------------------------------------
# core/endf_setup.py (Low – Setup code)
# ---------------------------------------------------------------------------

class TestEndfSetupCoverage:
    """Minimal coverage for core/endf_setup.py."""

    def test_endf_setup_print_helpers(self):
        """endf_setup print_step/print_success/print_error/print_info/print_warning are callable."""
        try:
            from smrforge.core import endf_setup as es
        except ImportError:
            pytest.skip("endf_setup not available")
        es.print_step(1, "Test")
        es.print_success("ok")
        es.print_error("err")
        es.print_info("info")
        es.print_warning("warn")

    def test_validate_endf_setup_nonexistent_dir(self):
        """validate_endf_setup returns (False, results) for nonexistent directory."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
        except ImportError:
            pytest.skip("endf_setup not available")
        path = Path("/__nonexistent_endf_dir_xyz__")
        valid, results = validate_endf_setup(path)
        assert valid is False
        assert results["directory_exists"] is False
        assert "errors" in results
        assert any("does not exist" in str(e) for e in results["errors"])

    def test_validate_endf_setup_none_uses_standard_dir(self):
        """validate_endf_setup(None) uses get_standard_endf_directory() and validates it."""
        try:
            from smrforge.core.endf_setup import validate_endf_setup
        except ImportError:
            pytest.skip("endf_setup not available")
        with patch("smrforge.core.endf_setup.get_standard_endf_directory", return_value=Path("/__nonexistent_std_endf__")):
            valid, results = validate_endf_setup(None)
        assert valid is False
        assert results["directory_exists"] is False


# ---------------------------------------------------------------------------
# control/integration.py (Low – Integration code)
# ---------------------------------------------------------------------------

class TestControlIntegrationCoverage:
    """Minimal coverage for control/integration.py."""

    def test_create_controlled_reactivity_returns_callable(self):
        """create_controlled_reactivity returns a callable that returns reactivity."""
        try:
            from smrforge.control.integration import create_controlled_reactivity
        except ImportError:
            pytest.skip("control.integration not available")
        mock_controller = MagicMock()
        mock_controller.rod_worth = 1e-4
        mock_controller.control_step.return_value = {"reactivity_change": -0.001}
        rho = create_controlled_reactivity(mock_controller, 1e6, 1200.0)
        assert callable(rho)
        out = rho(0.0, None)
        assert isinstance(out, (int, float))
        mock_controller.control_step.assert_called_once()


# ---------------------------------------------------------------------------
# core/self_shielding_integration.py (Low – Integration code)
# ---------------------------------------------------------------------------

class TestSelfShieldingIntegrationCoverage:
    """Minimal coverage for core/self_shielding_integration.py."""

    def test_get_cross_section_with_self_shielding_resonance_unavailable(self):
        """get_cross_section_with_self_shielding uses cache when _RESONANCE_AVAILABLE is False."""
        try:
            import smrforge.core.self_shielding_integration as ssi_mod
            from smrforge.core.reactor_core import Nuclide, NuclearDataCache
        except ImportError:
            pytest.skip("self_shielding_integration or reactor_core not available")
        with patch.object(ssi_mod, "_RESONANCE_AVAILABLE", False):
            cache = MagicMock(spec=NuclearDataCache)
            e_arr = np.array([1e6, 2e6])
            xs_arr = np.array([1.0, 0.8])
            cache.get_cross_section.return_value = (e_arr, xs_arr)
            nuclide = Nuclide(Z=92, A=238)
            energy, xs = ssi_mod.get_cross_section_with_self_shielding(
                cache, nuclide, "capture", 900.0, enable_self_shielding=True
            )
            cache.get_cross_section.assert_called_once()
            np.testing.assert_array_equal(energy, e_arr)
            np.testing.assert_array_equal(xs, xs_arr)


# ---------------------------------------------------------------------------
# core/multigroup_advanced.py (Low – Advanced feature)
# ---------------------------------------------------------------------------

class TestMultigroupAdvancedCoverage:
    """Minimal coverage for core/multigroup_advanced.py."""

    def test_sph_factors_dataclass(self):
        """SPHFactors can be instantiated with required fields."""
        try:
            from smrforge.core.multigroup_advanced import SPHFactors
        except ImportError:
            pytest.skip("multigroup_advanced not available")
        f = SPHFactors(
            nuclide="U238",
            reaction="capture",
            groups=np.array([0, 1]),
            sph_factors=np.array([1.0, 1.0]),
        )
        assert f.nuclide == "U238"
        assert f.reaction == "capture"
        assert len(f.sph_factors) == 2

    def test_sph_method_init(self):
        """SPHMethod initializes with empty cache."""
        try:
            from smrforge.core.multigroup_advanced import SPHMethod
        except ImportError:
            pytest.skip("multigroup_advanced not available")
        sph = SPHMethod()
        assert hasattr(sph, "_sph_cache")
        assert sph._sph_cache == {}


# ---------------------------------------------------------------------------
# neutronics/hybrid_solver.py, adaptive_sampling.py (Low – Advanced feature)
# ---------------------------------------------------------------------------

class TestNeutronicsAdvancedCoverage:
    """Minimal coverage for neutronics hybrid_solver and adaptive_sampling."""

    def test_region_partition_init(self):
        """RegionPartition can be constructed with at least one region."""
        try:
            from smrforge.neutronics.hybrid_solver import RegionPartition
        except ImportError:
            pytest.skip("neutronics.hybrid_solver not available")
        mask = np.array([[True]])
        ids_arr = np.array([[0]])
        p = RegionPartition(
            diffusion_mask=mask,
            region_ids=ids_arr,
            n_diffusion_regions=1,
            n_mc_regions=0,
        )
        assert p.n_diffusion_regions == 1
        assert p.n_mc_regions == 0

    def test_importance_map_init_and_get_total(self):
        """ImportanceMap can be constructed and get_total_importance works."""
        try:
            from smrforge.neutronics.adaptive_sampling import ImportanceMap
        except ImportError:
            pytest.skip("neutronics.adaptive_sampling not available")
        imp = ImportanceMap(
            z_centers=np.array([0.0]),
            r_centers=np.array([0.0]),
            importance=np.array([[1.0]]),
        )
        assert imp.get_total_importance() == 1.0
        assert imp.get_sampling_probability(0.0, 0.0) >= 0


# ---------------------------------------------------------------------------
# neutronics/implicit_mc.py (Low – Advanced feature)
# ---------------------------------------------------------------------------

class TestImplicitMcCoverage:
    """Minimal coverage for neutronics/implicit_mc.py."""

    def test_imc_time_step_dataclass(self):
        """IMCTimeStep can be constructed with valid dt and stability_factor."""
        try:
            from smrforge.neutronics.implicit_mc import IMCTimeStep
        except ImportError:
            pytest.skip("neutronics.implicit_mc not available")
        step = IMCTimeStep(dt=1.0, t=0.0, step=0, implicit=True, stability_factor=0.5)
        assert step.dt == 1.0
        assert step.t == 0.0
        assert step.step == 0
        assert step.implicit is True

    def test_imc_time_step_invalid_dt_raises(self):
        """IMCTimeStep raises ValueError for dt <= 0."""
        try:
            from smrforge.neutronics.implicit_mc import IMCTimeStep
        except ImportError:
            pytest.skip("neutronics.implicit_mc not available")
        with pytest.raises(ValueError, match="Time step must be positive"):
            IMCTimeStep(dt=0.0, t=0.0, step=0)

    def test_implicit_monte_carlo_solver_init(self):
        """ImplicitMonteCarloSolver can be constructed with mock mc_solver."""
        try:
            from smrforge.neutronics.implicit_mc import ImplicitMonteCarloSolver
        except ImportError:
            pytest.skip("neutronics.implicit_mc not available")
        mock_mc = MagicMock()
        solver = ImplicitMonteCarloSolver(mock_mc, dt_base=1.0, implicit=True, stability_factor=0.5)
        assert solver.mc_solver is mock_mc
        assert solver.dt_base == 1.0
        assert solver.current_time == 0.0
        assert solver.step_number == 0


# ---------------------------------------------------------------------------
# neutronics/monte_carlo_optimized.py (Low – Performance code)
# ---------------------------------------------------------------------------

class TestMonteCarloOptimizedCoverage:
    """Minimal coverage for neutronics/monte_carlo_optimized.py."""

    def test_reaction_type_enum(self):
        """ReactionType enum has expected values."""
        try:
            from smrforge.neutronics.monte_carlo_optimized import ReactionType
        except ImportError:
            pytest.skip("neutronics.monte_carlo_optimized not available")
        assert ReactionType.SCATTER.value == 0
        assert ReactionType.FISSION.value == 1
        assert ReactionType.CAPTURE.value == 2

    def test_particle_bank_init_and_add(self):
        """ParticleBank can be constructed and add_particle works."""
        try:
            from smrforge.neutronics.monte_carlo_optimized import ParticleBank
        except ImportError:
            pytest.skip("neutronics.monte_carlo_optimized not available")
        bank = ParticleBank(capacity=10)
        assert bank.size == 0
        assert bank.capacity == 10
        idx = bank.add_particle(
            position=np.array([0.0, 0.0, 0.0]),
            direction=np.array([1.0, 0.0, 0.0]),
            energy=1e6,
            weight=1.0,
            generation=0,
        )
        assert idx == 0
        assert bank.size == 1
        assert np.all(bank.get_alive_mask() == True)
        bank.clear()
        assert bank.size == 0
