"""
Integration tests for SMRForge Pro when installed.

These tests run only when smrforge_pro is available.
Use: pytest tests/test_pro_integration.py -v
"""

import pytest

pytest.importorskip("smrforge_pro", reason="smrforge_pro not installed")


class TestProConvertersIntegration:
    """Test Pro converters when Pro is installed."""

    def test_serpent_converter_import(self):
        """Pro SerpentConverter is importable."""
        from smrforge_pro.converters.serpent import SerpentConverter

        assert SerpentConverter is not None
        assert hasattr(SerpentConverter, "export_reactor")
        assert hasattr(SerpentConverter, "import_reactor")

    def test_openmc_converter_import(self):
        """Pro OpenMCConverter is importable."""
        from smrforge_pro.converters.openmc import OpenMCConverter

        assert OpenMCConverter is not None
        assert hasattr(OpenMCConverter, "export_reactor")
        assert hasattr(OpenMCConverter, "import_reactor")

    def test_serpent_export_creates_file(self, tmp_path):
        """Pro Serpent export creates a file when reactor has core."""
        pytest.importorskip("smrforge")
        from smrforge.geometry import PrismaticCore
        from smrforge_pro.converters.serpent import SerpentConverter

        # Minimal reactor-like object with core
        core = PrismaticCore()
        core.core_diameter = 100.0
        core.core_height = 200.0

        class MiniReactor:
            name = "test"
            core = core

        reactor = MiniReactor()
        out = tmp_path / "reactor.serp"
        SerpentConverter.export_reactor(reactor, out)
        assert out.exists()
        content = out.read_text()
        assert "Serpent" in content
        assert "mat " in content or "surf " in content

    def test_serpent_import_parses_file(self, tmp_path):
        """Pro Serpent import returns parsed materials, surfaces, cells."""
        from smrforge_pro.converters.serpent import SerpentConverter

        # Write minimal Serpent input
        inp = tmp_path / "test.serp"
        inp.write_text(
            "% test\nmat fuel 1\n 92235 1e-4\nsurf 1 cyl 0 0 50 0 200\ncell 1 0 fuel -1\n"
        )
        data = SerpentConverter.import_reactor(inp)
        assert "materials" in data
        assert "surfaces" in data
        assert "cells" in data
        assert data["format"] == "serpent"
        assert len(data["materials"]) >= 1
        assert len(data["surfaces"]) >= 1

    def test_mcnp_converter_export_creates_file(self, tmp_path):
        """Pro MCNP export creates a file."""
        pytest.importorskip("smrforge")
        from smrforge.geometry import PrismaticCore
        from smrforge_pro.converters.mcnp import MCNPConverter

        core = PrismaticCore()
        core.core_diameter = 100.0
        core.core_height = 200.0

        class MiniReactor:
            core = core

        reactor = MiniReactor()
        out = tmp_path / "reactor.mcnp"
        MCNPConverter.export_reactor(reactor, out)
        assert out.exists()
        content = out.read_text()
        assert "MCNP" in content
        assert "RCC" in content or "1 " in content


class TestProOpenMCTallyViz:
    """Test Pro OpenMC tally visualization when Pro and openmc are installed."""

    def test_visualize_openmc_tallies_import(self):
        """visualize_openmc_tallies is importable."""
        pytest.importorskip("openmc")
        from smrforge_pro.visualization import visualize_openmc_tallies

        assert callable(visualize_openmc_tallies)

    def test_visualize_openmc_tallies_missing_file(self):
        """visualize_openmc_tallies raises FileNotFoundError for missing statepoint."""
        pytest.importorskip("openmc")
        from smrforge_pro.visualization import visualize_openmc_tallies

        with pytest.raises(FileNotFoundError, match="not found"):
            visualize_openmc_tallies("/nonexistent/statepoint.1.h5")
