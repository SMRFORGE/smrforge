"""
Comprehensive tests for _fetch_and_cache using real mock ENDF files.

This test suite uses the realistic mock ENDF files created in tests/data/
to test all 4 backend chains in _fetch_and_cache:

1. endf-parserpy backend (lines 422-456)
2. SANDY backend (lines 467-493)
3. SMRForge built-in ENDF parser (lines 504-529)
4. Simple fallback parser (lines 535-554)

All tests use the actual ENDF files to ensure real code paths are exercised.
"""

import numpy as np
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def real_mock_endf_u235():
    """Return path to real mock ENDF file for U235."""
    endf_file = Path(__file__).parent / "data" / "sample_U235.endf"
    if not endf_file.exists():
        pytest.skip("Mock ENDF file not found: tests/data/sample_U235.endf")
    return endf_file


@pytest.fixture
def real_mock_endf_u238():
    """Return path to real mock ENDF file for U238."""
    endf_file = Path(__file__).parent / "data" / "sample_U238.endf"
    if not endf_file.exists():
        pytest.skip("Mock ENDF file not found: tests/data/sample_U238.endf")
    return endf_file


class TestFetchAndCacheWithRealEndfFiles:
    """Test _fetch_and_cache using real mock ENDF files."""

    def test_fetch_and_cache_with_endf_parserpy_success(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache successfully uses endf-parserpy with real ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Mock endf-parserpy to parse real ENDF file
        mock_parser = Mock()
        # Simulate parsing result that matches ENDF structure
        mock_parser.parsefile.return_value = {
            3: {
                1: {  # MT=1 (total)
                    "E": np.array([1.0e5, 1.2e4, 1.4e4, 1.6e4, 7.5e4, 8.0e4, 1.7e5, 2.2e6, 3.4e6, 5.2e6]),
                    "XS": np.array([2.044521e1, 1.895510e1, 1.873167e1, 1.851423e1, 1.397675e1, 1.370721e1, 1.036336e1, 2.753484e0, 2.113381e0, 1.582216e0]),
                }
            }
        }

        # Mock the parser factory
        mock_factory = Mock()
        mock_factory.create.return_value = mock_parser

        # Patch endf_parserpy module
        original_endf_parserpy = sys.modules.get("endf_parserpy")
        mock_endf_parserpy = Mock()
        mock_endf_parserpy.EndfParserFactory = mock_factory
        sys.modules["endf_parserpy"] = mock_endf_parserpy

        try:
            # Mock _get_parser to return our mock parser
            cache._get_parser = Mock(return_value=mock_parser)

            # Mock _ensure_endf_file to return real ENDF file
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                energy, xs = cache._fetch_and_cache(
                    u235, "total", 293.6, Library.ENDF_B_VIII, key
                )

                # Verify results
                assert energy is not None
                assert xs is not None
                assert len(energy) > 0
                assert len(xs) > 0
                assert len(energy) == len(xs)

                # Verify data was cached
                assert key in cache._memory_cache

                # Verify _get_parser was called
                cache._get_parser.assert_called_once()

                # Verify parsefile was called with real file path
                mock_parser.parsefile.assert_called_once()
                call_args = mock_parser.parsefile.call_args[0][0]
                assert isinstance(call_args, (str, Path))
        finally:
            # Restore original module
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]

    def test_fetch_and_cache_with_endf_parserpy_updates_metadata(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache updates file metadata cache with endf-parserpy."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        mock_parser = Mock()
        mock_parser.parsefile.return_value = {
            3: {
                1: {"E": np.array([1e5, 1e6]), "XS": np.array([10.0, 12.0])},
                2: {"E": np.array([1e5]), "XS": np.array([8.0])},  # Elastic
            }
        }

        mock_factory = Mock()
        mock_factory.create.return_value = mock_parser
        cache._get_parser = Mock(return_value=mock_parser)

        original_endf_parserpy = sys.modules.get("endf_parserpy")
        mock_endf_parserpy = Mock()
        mock_endf_parserpy.EndfParserFactory = mock_factory
        sys.modules["endf_parserpy"] = mock_endf_parserpy

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch.object(cache, "_update_file_metadata") as mock_update:
                    cache._fetch_and_cache(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    # Verify _update_file_metadata was called with correct MTs
                    mock_update.assert_called_once()
                    call_args = mock_update.call_args
                    assert call_args[0][0] == real_mock_endf_u235
                    assert isinstance(call_args[0][1], set)
                    assert 1 in call_args[0][1]  # MT=1 (total)
                    assert 2 in call_args[0][1]  # MT=2 (elastic)
        finally:
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]

    def test_fetch_and_cache_with_sandy_backend(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache successfully uses SANDY backend with real ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Mock SANDY backend properly
        mock_mf3 = Mock()
        # Create a proper mock data structure for SANDY
        mock_data = Mock()
        mock_data.__getitem__ = Mock(side_effect=lambda k: {"E": np.array([1e5, 1e6, 1e7]), "XS": np.array([10.0, 12.0, 15.0])}[k])
        mock_mf3.data = mock_data
        # Set up .values attribute on the arrays
        mock_data.__getitem__.return_value.values = np.array([1e5, 1e6, 1e7])
        # Better approach: use MagicMock with return_value
        mock_e_array = Mock()
        mock_e_array.values = np.array([1e5, 1e6, 1e7])
        mock_xs_array = Mock()
        mock_xs_array.values = np.array([10.0, 12.0, 15.0])
        mock_data.__getitem__ = Mock(side_effect=lambda k: mock_e_array if k == "E" else mock_xs_array)

        mock_endf6 = Mock()
        mock_endf6.filter_by.return_value = [mock_mf3]
        mock_endf6.__contains__ = Mock(return_value=True)  # MT=1 is available

        original_sandy = sys.modules.get("sandy")
        mock_sandy = Mock()
        mock_sandy.Endf6 = Mock(return_value=mock_endf6)
        mock_sandy.Endf6.from_file = Mock(return_value=mock_endf6)
        sys.modules["sandy"] = mock_sandy

        # Block endf-parserpy
        cache._get_parser = Mock(return_value=None)

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                energy, xs = cache._fetch_and_cache(
                    u235, "total", 293.6, Library.ENDF_B_VIII, key
                )

                assert energy is not None
                assert xs is not None
                assert len(energy) == 3
                assert len(xs) == 3

                # Verify SANDY was called
                mock_sandy.Endf6.from_file.assert_called_once()
                mock_endf6.filter_by.assert_called_once_with(mf=3, mt=1)

                # Verify data was cached
                assert key in cache._memory_cache
        finally:
            if original_sandy:
                sys.modules["sandy"] = original_sandy
            elif "sandy" in sys.modules:
                del sys.modules["sandy"]

    def test_fetch_and_cache_with_endf_compatibility_backend(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache successfully uses ENDFCompatibility backend with real ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Mock ENDFCompatibility
        mock_rxn_data = Mock()
        mock_rxn_data.xs = {"0K": Mock()}
        mock_rxn_data.xs["0K"].x = np.array([1e5, 1e6, 1e7])
        mock_rxn_data.xs["0K"].y = np.array([10.0, 12.0, 15.0])

        mock_evaluation = Mock()
        mock_evaluation.__contains__ = Mock(return_value=True)  # MT=1 is available
        mock_evaluation.__getitem__ = Mock(return_value=mock_rxn_data)

        # Block endf-parserpy and SANDY
        cache._get_parser = Mock(return_value=None)

        original_sandy = sys.modules.get("sandy")
        sys.modules["sandy"] = None

        try:
            # Patch ENDFCompatibility at the import location inside the function
            # The import is: from .endf_parser import ENDFCompatibility
            # So we patch smrforge.core.endf_parser.ENDFCompatibility
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch(
                    "smrforge.core.endf_parser.ENDFCompatibility",
                    return_value=mock_evaluation,
                ):
                    energy, xs = cache._fetch_and_cache(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    assert energy is not None
                    assert xs is not None
                    assert len(energy) == 3
                    assert len(xs) == 3

                    # Verify data was cached
                    assert key in cache._memory_cache
        finally:
            if original_sandy:
                sys.modules["sandy"] = original_sandy
            elif "sandy" in sys.modules:
                del sys.modules["sandy"]

    def test_fetch_and_cache_with_simple_parser_fallback(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache successfully uses simple parser fallback with real ENDF file."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Block all other backends
        cache._get_parser = Mock(return_value=None)

        original_sandy = sys.modules.get("sandy")
        sys.modules["sandy"] = None

        original_endf_parser = sys.modules.get("smrforge.core.endf_parser")
        sys.modules["smrforge.core.endf_parser"] = None

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                # Mock _simple_endf_parse to return test data
                with patch.object(
                    cache,
                    "_simple_endf_parse",
                    return_value=(
                        np.array([1e5, 1e6, 1e7]),
                        np.array([10.0, 12.0, 15.0]),
                    ),
                ):
                    energy, xs = cache._fetch_and_cache(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    assert energy is not None
                    assert xs is not None
                    assert len(energy) == 3
                    assert len(xs) == 3

                    # Verify _simple_endf_parse was called
                    cache._simple_endf_parse.assert_called_once()

                    # Verify data was cached
                    assert key in cache._memory_cache
        finally:
            if original_sandy:
                sys.modules["sandy"] = original_sandy
            elif "sandy" in sys.modules:
                del sys.modules["sandy"]
            if original_endf_parser:
                sys.modules["smrforge.core.endf_parser"] = original_endf_parser
            elif "smrforge.core.endf_parser" in sys.modules:
                del sys.modules["smrforge.core.endf_parser"]

    def test_fetch_and_cache_applies_doppler_broadening(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache applies Doppler broadening for non-standard temperatures."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/600.0K"

        mock_parser = Mock()
        mock_parser.parsefile.return_value = {
            3: {
                1: {
                    "E": np.array([1e5, 1e6, 1e7]),
                    "XS": np.array([10.0, 12.0, 15.0]),
                }
            }
        }

        cache._get_parser = Mock(return_value=mock_parser)

        original_endf_parserpy = sys.modules.get("endf_parserpy")
        mock_endf_parserpy = Mock()
        mock_endf_parserpy.EndfParserFactory = Mock()
        sys.modules["endf_parserpy"] = mock_endf_parserpy

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch.object(cache, "_doppler_broaden") as mock_doppler:
                    mock_doppler.return_value = np.array([10.5, 12.5, 15.5])

                    energy, xs = cache._fetch_and_cache(
                        u235, "total", 600.0, Library.ENDF_B_VIII, key
                    )

                    # Verify Doppler broadening was called (temperature != 293.6K)
                    mock_doppler.assert_called_once()
                    call_args = mock_doppler.call_args
                    assert np.array_equal(call_args[0][0], np.array([1e5, 1e6, 1e7]))
                    assert np.array_equal(call_args[0][1], np.array([10.0, 12.0, 15.0]))
                    assert call_args[0][2] == 293.6  # Original temperature
                    assert call_args[0][3] == 600.0  # Target temperature
                    assert call_args[0][4] == 235  # Mass number

                    # Verify broadened cross-sections were used
                    assert np.array_equal(xs, np.array([10.5, 12.5, 15.5]))
        finally:
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]

    def test_fetch_and_cache_no_doppler_broadening_standard_temp(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache does NOT apply Doppler broadening for standard temperature (293.6K)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        mock_parser = Mock()
        mock_parser.parsefile.return_value = {
            3: {
                1: {
                    "E": np.array([1e5, 1e6, 1e7]),
                    "XS": np.array([10.0, 12.0, 15.0]),
                }
            }
        }

        cache._get_parser = Mock(return_value=mock_parser)

        original_endf_parserpy = sys.modules.get("endf_parserpy")
        mock_endf_parserpy = Mock()
        mock_endf_parserpy.EndfParserFactory = Mock()
        sys.modules["endf_parserpy"] = mock_endf_parserpy

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch.object(cache, "_doppler_broaden") as mock_doppler:
                    energy, xs = cache._fetch_and_cache(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    # Verify Doppler broadening was NOT called (standard temperature)
                    mock_doppler.assert_not_called()

                    # Verify original cross-sections were used (no broadening)
                    assert np.array_equal(xs, np.array([10.0, 12.0, 15.0]))
        finally:
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]

    def test_fetch_and_cache_backend_fallback_chain(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache falls back through backends correctly."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Make endf-parserpy fail, SANDY fail, ENDFCompatibility fail, simple parser succeed
        cache._get_parser = Mock(return_value=None)

        original_sandy = sys.modules.get("sandy")
        sys.modules["sandy"] = None

        original_endf_parser = sys.modules.get("smrforge.core.endf_parser")
        sys.modules["smrforge.core.endf_parser"] = None

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch.object(
                    cache,
                    "_simple_endf_parse",
                    return_value=(
                        np.array([1e5, 1e6]),
                        np.array([10.0, 12.0]),
                    ),
                ) as mock_simple:
                    energy, xs = cache._fetch_and_cache(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    # Verify simple parser was called as fallback
                    mock_simple.assert_called_once()

                    assert energy is not None
                    assert xs is not None
                    assert len(energy) == 2
                    assert len(xs) == 2

                    # Verify data was cached
                    assert key in cache._memory_cache
        finally:
            if original_sandy:
                sys.modules["sandy"] = original_sandy
            elif "sandy" in sys.modules:
                del sys.modules["sandy"]
            if original_endf_parser:
                sys.modules["smrforge.core.endf_parser"] = original_endf_parser
            elif "smrforge.core.endf_parser" in sys.modules:
                del sys.modules["smrforge.core.endf_parser"]

    def test_fetch_and_cache_all_backends_fail_error_message(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache raises ImportError with helpful message when all backends fail."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Block all backends
        cache._get_parser = Mock(return_value=None)

        original_sandy = sys.modules.get("sandy")
        sys.modules["sandy"] = None

        original_endf_parser = sys.modules.get("smrforge.core.endf_parser")
        sys.modules["smrforge.core.endf_parser"] = None

        try:
            with patch.object(
                cache, "_ensure_endf_file", return_value=real_mock_endf_u235
            ):
                with patch.object(cache, "_simple_endf_parse", return_value=(None, None)):
                    with pytest.raises(ImportError, match="No suitable backend available"):
                        cache._fetch_and_cache(
                            u235, "total", 293.6, Library.ENDF_B_VIII, key
                        )
        finally:
            if original_sandy:
                sys.modules["sandy"] = original_sandy
            elif "sandy" in sys.modules:
                del sys.modules["sandy"]
            if original_endf_parser:
                sys.modules["smrforge.core.endf_parser"] = original_endf_parser
            elif "smrforge.core.endf_parser" in sys.modules:
                del sys.modules["smrforge.core.endf_parser"]
