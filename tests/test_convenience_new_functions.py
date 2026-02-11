"""Tests for new convenience and help functions."""

from pathlib import Path

import pytest


class TestListReactorTypes:
    def test_returns_non_empty_list(self):
        from smrforge import list_reactor_types

        result = list_reactor_types()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_prismatic(self):
        from smrforge import list_reactor_types

        result = list_reactor_types()
        assert "prismatic" in result


class TestListFuelTypes:
    def test_returns_non_empty_list(self):
        from smrforge import list_fuel_types

        result = list_fuel_types()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_uco(self):
        from smrforge import list_fuel_types

        result = list_fuel_types()
        assert "UCO" in result


class TestQuickSweep:
    def test_sweep_with_reactor_json_path(self):
        from smrforge import quick_sweep

        reactor_path = (
            Path(__file__).resolve().parents[1] / "examples" / "inputs" / "reactor.json"
        )
        if not reactor_path.exists():
            pytest.skip("examples/inputs/reactor.json not found")

        out = quick_sweep(
            reactor_path,
            {"enrichment": [0.15, 0.19]},
            analysis="keff",
        )
        assert "results" in out
        assert "failed_cases" in out
        assert "summary_stats" in out
        assert isinstance(out["results"], list)
        assert len(out["results"]) >= 1
        for r in out["results"]:
            assert "parameters" in r
            assert "k_eff" in r

    def test_sweep_with_preset_when_available(self):
        from smrforge.convenience import _PRESETS_AVAILABLE
        from smrforge import quick_sweep

        if not _PRESETS_AVAILABLE:
            pytest.skip("Presets not available")

        out = quick_sweep("valar-10", {"enrichment": [0.19]}, analysis="keff")
        assert "results" in out
        assert len(out["results"]) >= 1


class TestQuickEconomics:
    def test_economics_with_reactor_json_path(self):
        from smrforge import quick_economics

        reactor_path = (
            Path(__file__).resolve().parents[1] / "examples" / "inputs" / "reactor.json"
        )
        if not reactor_path.exists():
            pytest.skip("examples/inputs/reactor.json not found")

        result = quick_economics(reactor_path)
        assert isinstance(result, dict)
        assert "lcoe" in result or "capital_costs" in result

    def test_economics_with_preset_when_available(self):
        from smrforge.convenience import _PRESETS_AVAILABLE
        from smrforge import quick_economics

        if not _PRESETS_AVAILABLE:
            pytest.skip("Presets not available")

        result = quick_economics("valar-10")
        assert isinstance(result, dict)
        assert "lcoe" in result or "capital_costs" in result


class TestListConstraintSets:
    def test_returns_regulatory_and_safety(self):
        from smrforge import list_constraint_sets

        result = list_constraint_sets()
        assert "regulatory_limits" in result
        assert "safety_margins" in result

    def test_get_constraint_set(self):
        from smrforge import get_constraint_set

        cs = get_constraint_set("regulatory_limits")
        assert cs.name == "regulatory_limits"
        assert "max_power_density" in cs.constraints


class TestGetExamplePath:
    def test_reactor_example(self):
        from smrforge import get_example_path

        p = get_example_path("reactor")
        assert p.exists()
        assert p.name == "reactor.json"

    def test_unknown_raises(self):
        from smrforge import get_example_path

        with pytest.raises(ValueError, match="Unknown example"):
            get_example_path("nonexistent")


class TestListExamples:
    def test_returns_non_empty(self):
        from smrforge import list_examples

        result = list_examples()
        assert isinstance(result, list)
        assert "basic_neutronics" in result or len(result) > 0


class TestListNuclides:
    def test_returns_common_nuclides(self):
        from smrforge import list_nuclides

        result = list_nuclides()
        assert "U235" in result
        assert "U238" in result


class TestListSweepableParams:
    def test_contains_enrichment(self):
        from smrforge import list_sweepable_params

        result = list_sweepable_params()
        assert "enrichment" in result


class TestGetDefaultOutputDir:
    def test_returns_path(self):
        from smrforge import get_default_output_dir

        p = get_default_output_dir()
        assert p == Path("output")


class TestSystemInfo:
    def test_returns_dict_with_version(self):
        from smrforge import system_info

        info = system_info()
        assert "version" in info
        assert "convenience" in info


class TestHelpTopics:
    def test_returns_list(self):
        from smrforge import help_topics

        topics = help_topics()
        assert "geometry" in topics
        assert "convenience" in topics


class TestQuickOptimize:
    def test_optimize_with_preset(self):
        from smrforge.convenience import _PRESETS_AVAILABLE
        from smrforge import quick_optimize

        if not _PRESETS_AVAILABLE:
            pytest.skip("Presets not available")

        out = quick_optimize("valar-10", {"enrichment": (0.19, 0.20)}, max_iter=2)
        assert "optimal_point" in out
        assert "success" in out


class TestQuickUq:
    def test_uq_with_preset(self):
        from smrforge.convenience import _PRESETS_AVAILABLE
        from smrforge import quick_uq

        if not _PRESETS_AVAILABLE:
            pytest.skip("Presets not available")

        out = quick_uq(
            "valar-10",
            [
                {
                    "name": "enrichment",
                    "nominal": 0.195,
                    "distribution": "normal",
                    "uncertainty": 0.01,
                }
            ],
            n_samples=3,
        )
        assert "mean" in out
        assert "output_names" in out


class TestGetDefaultEndfDir:
    def test_returns_path(self):
        from smrforge import get_default_endf_dir

        p = get_default_endf_dir()
        assert isinstance(p, Path)
        assert "ENDF" in str(p) or "endf" in str(p).lower()


class TestListEndfLibraries:
    def test_returns_libraries(self):
        from smrforge import list_endf_libraries

        result = list_endf_libraries()
        assert "ENDF/B-VIII.1" in result
        assert "ENDF/B-VIII.0" in result


class TestListGeometryTypes:
    def test_returns_core_types(self):
        from smrforge import list_geometry_types

        result = list_geometry_types()
        assert "PrismaticCore" in result
        assert "PebbleBedCore" in result


class TestListAnalysisTypes:
    def test_returns_analysis_types(self):
        from smrforge import list_analysis_types

        result = list_analysis_types()
        assert "keff" in result
        assert "burnup" in result


class TestListSurrogates:
    def test_returns_list(self):
        from smrforge import list_surrogates

        result = list_surrogates()
        assert isinstance(result, list)


class TestQuickDownloadEndf:
    def test_quick_download_endf_mocked(self):
        """Test quick_download_endf with mocked download (no network)."""
        from unittest.mock import MagicMock, patch

        from smrforge import quick_download_endf

        mock_stats = {
            "downloaded": 0,
            "skipped": 5,
            "failed": 0,
            "total": 5,
            "output_dir": "/tmp",
        }
        with patch(
            "smrforge.data_downloader.download_endf_data", return_value=mock_stats
        ):
            stats = quick_download_endf(show_progress=False)
            assert stats["total"] == 5
            assert "output_dir" in stats
