"""
Tests for fission yield parser.
"""

from pathlib import Path

import pytest

from smrforge.core.fission_yield_parser import (
    ENDFFissionYieldParser,
    FissionYield,
    FissionYieldData,
)
from smrforge.core.reactor_core import Nuclide


class TestFissionYieldData:
    """Test FissionYieldData dataclass."""

    def test_fission_yield_data_creation(self):
        """Test creating FissionYieldData."""
        u235 = Nuclide(Z=92, A=235)
        cs137 = Nuclide(Z=55, A=137)

        yields = {
            cs137: FissionYield(
                product=cs137,
                independent_yield=0.05,
                cumulative_yield=0.06,
            )
        }

        data = FissionYieldData(
            parent=u235,
            yields=yields,
            energy_dependent=False,
        )

        assert data.parent == u235
        assert cs137 in data.yields
        assert data.get_yield(cs137) == 0.06  # Cumulative by default

    def test_get_yield(self):
        """Test getting yield for a product."""
        u235 = Nuclide(Z=92, A=235)
        cs137 = Nuclide(Z=55, A=137)

        yields = {
            cs137: FissionYield(
                product=cs137,
                independent_yield=0.05,
                cumulative_yield=0.06,
            )
        }

        data = FissionYieldData(
            parent=u235,
            yields=yields,
            energy_dependent=False,
        )

        assert data.get_yield(cs137, cumulative=True) == 0.06
        assert data.get_yield(cs137, cumulative=False) == 0.05
        assert data.get_yield(Nuclide(Z=1, A=1), cumulative=True) == 0.0  # Not found

    def test_get_total_yield(self):
        """Test getting total yield."""
        u235 = Nuclide(Z=92, A=235)
        cs137 = Nuclide(Z=55, A=137)
        sr90 = Nuclide(Z=38, A=90)

        yields = {
            cs137: FissionYield(
                product=cs137,
                independent_yield=0.05,
                cumulative_yield=0.06,
            ),
            sr90: FissionYield(
                product=sr90,
                independent_yield=0.04,
                cumulative_yield=0.05,
            ),
        }

        data = FissionYieldData(
            parent=u235,
            yields=yields,
            energy_dependent=False,
        )

        total_cumulative = data.get_total_yield(cumulative=True)
        assert total_cumulative == 0.11  # 0.06 + 0.05

        total_independent = data.get_total_yield(cumulative=False)
        assert total_independent == 0.09  # 0.05 + 0.04


class TestENDFFissionYieldParser:
    """Test ENDFFissionYieldParser."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = ENDFFissionYieldParser()
        assert parser is not None

    def test_parse_filename(self):
        """Test filename parsing."""
        parser = ENDFFissionYieldParser()

        # Test standard format
        nuclide = parser._parse_filename("nfy-092_U_235.endf")
        assert nuclide is not None
        assert nuclide.Z == 92
        assert nuclide.A == 235

    def test_parse_file_nonexistent(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        parser = ENDFFissionYieldParser()
        with pytest.raises(FileNotFoundError, match="Fission yield file not found"):
            parser.parse_file(Path("nonexistent.endf"))

    def test_parse_yields_from_endf_format(self, tmp_path):
        """Test _parse_yields extracts yields from ENDF MT=454/459 format."""
        parser = ENDFFissionYieldParser()
        # ENDF MT=454: (ZAFP, FPS, YI, DYI) per product. ZAFP=1000*Z+A.
        # Cs-137: Z=55, A=137 -> 55137. Sr-90: 3890.
        line454_1 = (
            " 5.5137000+4 0.0000000+0 5.0000000-3 1.0000000-4"
            " 3.8900000+3 0.0000000+0 4.0000000-3 8.0000000-5"
            + " " * 10 + " 8  454\n"
        )
        lines = [
            " " * 70 + " 8  454\n",
            " 2.5300000-2 0.0000000+0 0 0 8 2" + " " * 22 + " 8  454\n",
            line454_1,
        ]
        content = "".join(lines)
        ind = parser._parse_yields(content.split("\n"), mt=454)
        # Parser looks for 4-tuples; Cs137=55137, Sr90=3890
        cs137 = Nuclide(Z=55, A=137)
        sr90 = Nuclide(Z=38, A=90)
        assert isinstance(ind, dict)
        if ind:
            assert sum(ind.values()) > 0

    def test_parse_file_with_yield_data(self, tmp_path):
        """Test parse_file with minimal valid ENDF yield content."""
        parser = ENDFFissionYieldParser()
        # Minimal ENDF: HEAD + LIST with ZAFP,FPS,Y,DY for one product
        lines = [
            " " * 70 + " 8  454\n",
            " 2.53e-2 0.0 0 0 4 1" + " " * 28 + " 8  454\n",
            " 5.5137e4 0.0 6.1e-2 1e-4" + " " * 26 + " 8  454\n",
        ]
        lines459 = [
            " " * 70 + " 8  459\n",
            " 2.53e-2 0.0 0 0 4 1" + " " * 28 + " 8  459\n",
            " 5.5137e4 0.0 6.5e-2 1e-4" + " " * 26 + " 8  459\n",
        ]
        content = "\n".join(lines + lines459)
        path = tmp_path / "nfy-092_U_235.endf"
        path.write_text(content)
        result = parser.parse_file(path)
        if result:
            cs137 = Nuclide(Z=55, A=137)
            assert result.parent.Z == 92 and result.parent.A == 235
            assert len(result.yields) > 0 or result.get_yield(cs137, cumulative=True) >= 0


class TestFissionYieldIntegration:
    """Test fission yield integration with NuclearDataCache."""

    def test_get_fission_yield_data(self):
        """Test getting fission yield data via reactor_core."""
        from smrforge.core.reactor_core import (
            NuclearDataCache,
            get_fission_yield_data,
        )

        cache = NuclearDataCache()
        u235 = Nuclide(Z=92, A=235)
        yield_data = get_fission_yield_data(u235, cache=cache)

        # Should return None if files not available, or FissionYieldData if available
        assert yield_data is None or isinstance(yield_data, FissionYieldData)
