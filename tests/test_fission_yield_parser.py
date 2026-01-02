"""
Tests for fission yield parser.
"""

import pytest
from pathlib import Path

from smrforge.core.reactor_core import Nuclide
from smrforge.core.fission_yield_parser import (
    ENDFFissionYieldParser,
    FissionYield,
    FissionYieldData,
)


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
        """Test parsing non-existent file returns None."""
        parser = ENDFFissionYieldParser()
        result = parser.parse_file(Path("nonexistent.endf"))
        assert result is None


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

