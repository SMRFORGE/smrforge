"""
Comprehensive tests for async methods in reactor_core.py.

This test suite covers:
1. get_cross_section_async (lines 700-734)
   - Memory cache hit path
   - Zarr cache hit path
   - Cache miss (calls _fetch_and_cache_async)

2. _fetch_and_cache_async (lines 735-900)
   - All 4 backend chains (endf-parserpy, SANDY, ENDFCompatibility, simple)
   - Temperature broadening
   - Fallback chains
   - Error handling

Uses real mock ENDF files from tests/data/ to exercise actual code paths.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

# Check if pytest-asyncio is available
try:
    import pytest_asyncio

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

from smrforge.core.reactor_core import Library, NuclearDataCache, Nuclide


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


@pytest.mark.skipif(not ASYNC_AVAILABLE, reason="pytest-asyncio not installed")
class TestGetCrossSectionAsync:
    """Test get_cross_section_async method (lines 700-734)."""

    @pytest.mark.asyncio
    async def test_get_cross_section_async_memory_cache_hit(self, temp_cache_dir):
        """Test get_cross_section_async returns data from memory cache (lines 716-718)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Pre-populate memory cache
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0])
        cache._memory_cache[key] = (energy, xs)

        # Should return from memory cache immediately (no async needed)
        result_energy, result_xs = await cache.get_cross_section_async(
            u235, "total", 293.6, Library.ENDF_B_VIII
        )

        assert np.array_equal(result_energy, energy)
        assert np.array_equal(result_xs, xs)

    @pytest.mark.asyncio
    async def test_get_cross_section_async_zarr_cache_hit(self, temp_cache_dir):
        """Test get_cross_section_async returns data from zarr cache (lines 721-727)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Pre-populate zarr cache
        energy = np.array([1e5, 1e6, 1e7])
        xs = np.array([10.0, 12.0, 15.0])
        cache._save_to_cache(key, energy, xs)

        # Clear memory cache to force zarr lookup
        cache._memory_cache.clear()

        # Should retrieve from zarr cache and update memory cache
        result_energy, result_xs = await cache.get_cross_section_async(
            u235, "total", 293.6, Library.ENDF_B_VIII
        )

        assert np.array_equal(result_energy, energy)
        assert np.array_equal(result_xs, xs)

        # Should now be in memory cache
        assert key in cache._memory_cache

    @pytest.mark.asyncio
    async def test_get_cross_section_async_cache_miss_calls_fetch_async(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test get_cross_section_async calls _fetch_and_cache_async on cache miss (lines 728-733)."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)

        # Mock _fetch_and_cache_async
        mock_energy = np.array([1e5, 1e6, 1e7])
        mock_xs = np.array([10.0, 12.0, 15.0])

        mock_parser = Mock()
        mock_parser.parsefile.return_value = {
            3: {
                1: {
                    "E": mock_energy,
                    "XS": mock_xs,
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                # Memory cache and zarr cache both empty, should call _fetch_and_cache_async
                result_energy, result_xs = await cache.get_cross_section_async(
                    u235, "total", 293.6, Library.ENDF_B_VIII
                )

                # Verify _ensure_endf_file_async was called
                cache._ensure_endf_file_async.assert_called_once()

                assert np.array_equal(result_energy, mock_energy)
                assert np.array_equal(result_xs, mock_xs)

                # Should be cached now
                key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"
                assert key in cache._memory_cache
        finally:
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]


@pytest.mark.skipif(not ASYNC_AVAILABLE, reason="pytest-asyncio not installed")
class TestFetchAndCacheAsync:
    """Test _fetch_and_cache_async method (lines 735-900)."""

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_with_endf_parserpy_success(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache_async successfully uses endf-parserpy backend."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                energy, xs = await cache._fetch_and_cache_async(
                    u235, "total", 293.6, Library.ENDF_B_VIII, key
                )

                assert energy is not None
                assert xs is not None
                assert len(energy) == 3
                assert len(xs) == 3

                # Verify _ensure_endf_file_async was called (async version)
                cache._ensure_endf_file_async.assert_called_once()

                # Verify data was cached
                assert key in cache._memory_cache
        finally:
            if original_endf_parserpy:
                sys.modules["endf_parserpy"] = original_endf_parserpy
            elif "endf_parserpy" in sys.modules:
                del sys.modules["endf_parserpy"]

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_with_sandy_backend(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache_async successfully uses SANDY backend."""
        cache = NuclearDataCache(cache_dir=temp_cache_dir)
        cache.local_endf_dir = real_mock_endf_u235.parent
        u235 = Nuclide(Z=92, A=235)
        key = f"{Library.ENDF_B_VIII.value}/{u235.name}/total/293.6K"

        # Mock SANDY backend
        mock_mf3 = Mock()
        mock_e_array = Mock()
        mock_e_array.values = np.array([1e5, 1e6, 1e7])
        mock_xs_array = Mock()
        mock_xs_array.values = np.array([10.0, 12.0, 15.0])
        mock_data = Mock()
        mock_data.__getitem__ = Mock(
            side_effect=lambda k: mock_e_array if k == "E" else mock_xs_array
        )
        mock_mf3.data = mock_data

        mock_endf6 = Mock()
        mock_endf6.filter_by.return_value = [mock_mf3]
        mock_endf6.__contains__ = Mock(return_value=True)

        original_sandy = sys.modules.get("sandy")
        mock_sandy = Mock()
        mock_sandy.Endf6 = Mock(return_value=mock_endf6)
        mock_sandy.Endf6.from_file = Mock(return_value=mock_endf6)
        sys.modules["sandy"] = mock_sandy

        # Block endf-parserpy
        cache._get_parser = Mock(return_value=None)

        try:
            with patch.object(
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                energy, xs = await cache._fetch_and_cache_async(
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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_with_endf_compatibility_backend(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache_async successfully uses ENDFCompatibility backend."""
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
        mock_evaluation.__contains__ = Mock(return_value=True)
        mock_evaluation.__getitem__ = Mock(return_value=mock_rxn_data)

        # Block endf-parserpy and SANDY
        cache._get_parser = Mock(return_value=None)

        original_sandy = sys.modules.get("sandy")
        sys.modules["sandy"] = None

        try:
            with patch.object(
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch(
                    "smrforge.core.endf_parser.ENDFCompatibility",
                    return_value=mock_evaluation,
                ):
                    energy, xs = await cache._fetch_and_cache_async(
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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_with_simple_parser_fallback(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test _fetch_and_cache_async successfully uses simple parser fallback."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch.object(
                    cache,
                    "_simple_endf_parse",
                    return_value=(
                        np.array([1e5, 1e6, 1e7]),
                        np.array([10.0, 12.0, 15.0]),
                    ),
                ) as mock_simple:
                    energy, xs = await cache._fetch_and_cache_async(
                        u235, "total", 293.6, Library.ENDF_B_VIII, key
                    )

                    assert energy is not None
                    assert xs is not None
                    assert len(energy) == 3
                    assert len(xs) == 3

                    # Verify _simple_endf_parse was called
                    mock_simple.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_applies_doppler_broadening(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache_async applies Doppler broadening for non-standard temperatures."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch.object(cache, "_doppler_broaden") as mock_doppler:
                    mock_doppler.return_value = np.array([10.5, 12.5, 15.5])

                    energy, xs = await cache._fetch_and_cache_async(
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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_no_doppler_broadening_standard_temp(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache_async does NOT apply Doppler broadening for standard temperature (293.6K)."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch.object(cache, "_doppler_broaden") as mock_doppler:
                    energy, xs = await cache._fetch_and_cache_async(
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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_backend_fallback_chain(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache_async falls back through backends correctly."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch.object(
                    cache,
                    "_simple_endf_parse",
                    return_value=(
                        np.array([1e5, 1e6]),
                        np.array([10.0, 12.0]),
                    ),
                ) as mock_simple:
                    energy, xs = await cache._fetch_and_cache_async(
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

    @pytest.mark.asyncio
    async def test_fetch_and_cache_async_all_backends_fail_error_message(
        self, temp_cache_dir, real_mock_endf_u235
    ):
        """Test that _fetch_and_cache_async raises ImportError with helpful message when all backends fail (lines 908-941)."""
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
                cache,
                "_ensure_endf_file_async",
                new_callable=AsyncMock,
                return_value=real_mock_endf_u235,
            ):
                with patch.object(
                    cache, "_simple_endf_parse", return_value=(None, None)
                ):
                    with pytest.raises(
                        ImportError, match="No suitable backend available"
                    ):
                        await cache._fetch_and_cache_async(
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
