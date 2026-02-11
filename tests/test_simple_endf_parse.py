"""Tests for _simple_endf_parse method."""

import numpy as np
import pytest


class TestSimpleEndfParse:
    """Test _simple_endf_parse method comprehensively."""

    def test_simple_endf_parse_realistic_total(self, temp_dir, realistic_endf_file):
        """Test _simple_endf_parse with realistic ENDF file for total cross section."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        energy, xs = cache._simple_endf_parse(realistic_endf_file, "total", nuc)

        assert energy is not None
        assert xs is not None
        assert isinstance(energy, np.ndarray)
        assert isinstance(xs, np.ndarray)
        assert len(energy) > 0
        assert len(xs) == len(energy)

    def test_simple_endf_parse_realistic_elastic(self, temp_dir, realistic_endf_file):
        """Test _simple_endf_parse with realistic ENDF file for elastic cross section."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        energy, xs = cache._simple_endf_parse(realistic_endf_file, "elastic", nuc)

        assert energy is not None
        assert xs is not None
        assert len(energy) > 0
        assert len(xs) == len(energy)

    def test_simple_endf_parse_realistic_fission(self, temp_dir, realistic_endf_file):
        """Test _simple_endf_parse with realistic ENDF file for fission cross section."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        energy, xs = cache._simple_endf_parse(realistic_endf_file, "fission", nuc)

        assert energy is not None
        assert xs is not None
        assert len(energy) > 0
        assert len(xs) == len(energy)

    def test_simple_endf_parse_realistic_capture(self, temp_dir, realistic_endf_file):
        """Test _simple_endf_parse with realistic ENDF file for capture cross section."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        energy, xs = cache._simple_endf_parse(realistic_endf_file, "capture", nuc)

        assert energy is not None
        assert xs is not None
        assert len(energy) > 0
        assert len(xs) == len(energy)

    def test_simple_endf_parse_nonexistent_reaction(
        self, temp_dir, realistic_endf_file
    ):
        """Test _simple_endf_parse returns None for non-existent reaction."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        # Try to parse a reaction that doesn't exist in the file
        energy, xs = cache._simple_endf_parse(realistic_endf_file, "n,2n", nuc)

        assert energy is None
        assert xs is None

    def test_simple_endf_parse_nonexistent_file(self, temp_dir):
        """Test _simple_endf_parse handles non-existent file gracefully."""
        from smrforge.core.reactor_core import NuclearDataCache, Nuclide

        cache = NuclearDataCache(cache_dir=temp_dir / "test_cache")
        nuc = Nuclide(Z=92, A=235, m=0)

        nonexistent_file = temp_dir / "nonexistent.endf"
        energy, xs = cache._simple_endf_parse(nonexistent_file, "total", nuc)

        assert energy is None
        assert xs is None
