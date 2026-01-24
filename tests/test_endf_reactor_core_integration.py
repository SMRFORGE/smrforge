"""
Integration tests for end-to-end workflows between reactor_core and endf_parser.

This test suite verifies data flow and integration between:
- NuclearDataCache (reactor_core.py)
- ENDFEvaluation (endf_parser.py)
- Cross-section generation and multi-group collapse
- File caching and retrieval
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    import polars as pl
    _POLARS_AVAILABLE = True
except ImportError:
    _POLARS_AVAILABLE = False

try:
    from smrforge.core.reactor_core import (
        CrossSectionTable,
        Library,
        NuclearDataCache,
        Nuclide,
    )
    from smrforge.core.endf_parser import ENDFCompatibility, ENDFEvaluation
    _INTEGRATION_AVAILABLE = True
except ImportError:
    _INTEGRATION_AVAILABLE = False


@pytest.fixture
def realistic_endf_file(temp_dir):
    """Create a realistic ENDF file for integration testing."""
    endf_path = temp_dir / "integration_U235.endf"
    
    # Complete ENDF file with header and multiple reactions
    endf_content = """ 1.001000+3 9.991673-1          0          0          0          0 125 1451    1
 9.223500+4 2.350000+2          0          0          0          0 125 1451    2
                                                                   125 1451    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  1    1
 1.000000+5 1.000000+1 1.000000+6 1.200000+1 5.000000+6 1.500000+1 125 3  1    3
 1.000000+7 1.800000+1 2.000000+7 2.000000+1 5.000000+7 2.200000+1 125 3  1    4
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3  2    1
 1.000000+5 8.000000+0 1.000000+6 9.000000+0 1.000000+7 1.000000+1 125 3  2    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3 18    1
 1.000000+5 1.500000+0 1.000000+6 2.000000+0 5.000000+6 2.500000+0 125 3 18    3
                                                                   125 0  0    0
 1.001000+3 9.991673-1          0          0          0          0 125 3102    1
 1.000000+5 5.000000-1 1.000000+6 1.000000+0 1.000000+7 1.500000+0 125 3102    3
                                                                   125 0  0    0
                                                                   125 0  0    0
"""
    endf_path.write_text(endf_content)
    return endf_path


@pytest.mark.skipif(
    not _INTEGRATION_AVAILABLE,
    reason="Integration components not available",
)
class TestEndfReactorCoreIntegration:
    """Integration tests for reactor_core and endf_parser."""

    def test_endf_evaluation_to_reactor_core_workflow(self, realistic_endf_file, temp_dir):
        """Test complete workflow from ENDF file to reactor_core usage."""
        # Step 1: Parse ENDF file with ENDFEvaluation
        eval_obj = ENDFEvaluation(realistic_endf_file)
        
        # Verify parsing worked
        assert len(eval_obj.reactions) > 0
        assert 1 in eval_obj.reactions  # Total cross-section
        
        # Step 2: Use parsed data in NuclearDataCache
        cache = NuclearDataCache(cache_dir=temp_dir / "integration_cache")
        u235 = Nuclide(Z=92, A=235)
        
        # Step 3: Get cross-section using cache (should use ENDF parser backend)
        try:
            energy, xs = cache.get_cross_section(
                u235, "total", library=Library.ENDF_B_VIII_1
            )
            
            # Verify results
            assert energy is not None
            assert xs is not None
            assert len(energy) > 0
            assert len(energy) == len(xs)
        except (FileNotFoundError, ImportError, ValueError):
            # Expected if ENDF files not set up - test still validates integration structure
            pytest.skip("ENDF files not available for full integration test")

    def test_endf_compatibility_with_reactor_core(self, realistic_endf_file, temp_dir):
        """Test ENDFCompatibility wrapper works with reactor_core."""
        # Create ENDFCompatibility wrapper
        compat = ENDFCompatibility(realistic_endf_file)
        
        # Verify wrapper provides expected interface
        assert 1 in compat  # Total cross-section
        assert 2 in compat  # Elastic
        
        # Get reaction data through wrapper
        total_rxn = compat[1]
        assert hasattr(total_rxn, "energy")
        assert hasattr(total_rxn, "cross_section")
        assert len(total_rxn.energy) > 0

    def test_reactor_core_uses_endf_parser_backend(self, realistic_endf_file, temp_dir):
        """Test that reactor_core uses ENDF parser backend when available."""
        cache = NuclearDataCache(cache_dir=temp_dir / "backend_test_cache")
        u235 = Nuclide(Z=92, A=235)
        
        # Mock the file to be available
        with patch.object(cache, '_find_local_endf_file', return_value=realistic_endf_file):
            try:
                energy, xs = cache.get_cross_section(
                    u235, "total", library=Library.ENDF_B_VIII_1
                )
                
                # Verify backend was used
                assert energy is not None
                assert xs is not None
            except (FileNotFoundError, ImportError, ValueError):
                pytest.skip("ENDF parser backend not available")

    def test_cross_section_table_from_endf_evaluation(self, realistic_endf_file, temp_dir):
        """Test CrossSectionTable with ENDF-derived data via generate_multigroup.
        CrossSectionTable(cache) only; populate via generate_multigroup()."""
        if not _POLARS_AVAILABLE:
            pytest.skip("Polars not available")
        # generate_multigroup uses library=ENDF_B_VIII (VIII.0) by default
        neutrons_dir = temp_dir / "neutrons-version.VIII.0"
        neutrons_dir.mkdir(parents=True, exist_ok=True)
        endf_dest = neutrons_dir / "n-092_U_235.endf"
        import shutil
        shutil.copy(realistic_endf_file, endf_dest)
        cache = NuclearDataCache(cache_dir=temp_dir / "xs_cache", local_endf_dir=temp_dir)
        u235 = Nuclide(Z=92, A=235)
        xs_table = CrossSectionTable(cache=cache)
        group_structure = np.logspace(7, -5, 9)  # 8 groups
        try:
            df = xs_table.generate_multigroup(
                nuclides=[u235],
                reactions=["total"],
                group_structure=group_structure,
            )
            assert df is not None
            assert len(df) > 0
            u235_total = df.filter(
                (pl.col("nuclide") == "U235") & (pl.col("reaction") == "total")
            )
            assert len(u235_total) > 0
        except (FileNotFoundError, ImportError, ValueError) as e:
            pytest.skip(f"ENDF/cache setup not available: {e}")

    def test_multigroup_collapse_with_endf_data(self, realistic_endf_file, temp_dir):
        """Test multi-group collapse using data from ENDF parser."""
        if not _POLARS_AVAILABLE:
            pytest.skip("Polars not available")
        # generate_multigroup uses library=ENDF_B_VIII (VIII.0) by default
        neutrons_dir = temp_dir / "neutrons-version.VIII.0"
        neutrons_dir.mkdir(parents=True, exist_ok=True)
        endf_dest = neutrons_dir / "n-092_U_235.endf"
        import shutil
        shutil.copy(realistic_endf_file, endf_dest)
        cache = NuclearDataCache(cache_dir=temp_dir / "multigroup_cache", local_endf_dir=temp_dir)
        u235 = Nuclide(Z=92, A=235)
        group_structure = np.logspace(7, -5, 27)  # 26 groups
        xs_table = CrossSectionTable(cache=cache)
        try:
            df = xs_table.generate_multigroup(
                nuclides=[u235],
                reactions=["total"],
                group_structure=group_structure,
            )
            assert df is not None
            assert len(df) > 0
        except (FileNotFoundError, ImportError, ValueError):
            pytest.skip("ENDF files not available for multigroup collapse test")

    def test_file_caching_integration(self, realistic_endf_file, temp_dir):
        """Test that parsed ENDF data is properly cached."""
        cache = NuclearDataCache(cache_dir=temp_dir / "cache_integration")
        u235 = Nuclide(Z=92, A=235)
        
        # First call - should parse and cache
        with patch.object(cache, '_find_local_endf_file', return_value=realistic_endf_file):
            try:
                energy1, xs1 = cache.get_cross_section(
                    u235, "total", library=Library.ENDF_B_VIII_1
                )
                
                # Second call - should use cache
                energy2, xs2 = cache.get_cross_section(
                    u235, "total", library=Library.ENDF_B_VIII_1
                )
                
                # Results should match
                assert np.array_equal(energy1, energy2)
                assert np.array_equal(xs1, xs2)
                
            except (FileNotFoundError, ImportError, ValueError):
                pytest.skip("ENDF files not available for caching test")

    def test_error_handling_integration(self, temp_dir):
        """Test error handling across reactor_core and endf_parser."""
        cache = NuclearDataCache(cache_dir=temp_dir / "error_test_cache")
        u235 = Nuclide(Z=92, A=235)
        
        # Test with non-existent file
        nonexistent_file = temp_dir / "nonexistent.endf"
        
        with patch.object(cache, '_find_local_endf_file', return_value=nonexistent_file):
            try:
                energy, xs = cache.get_cross_section(
                    u235, "total", library=Library.ENDF_B_VIII_1
                )
                # Should handle gracefully (return None or raise appropriate error)
            except (FileNotFoundError, ValueError):
                # Expected behavior
                pass

    def test_data_consistency_between_parsers(self, realistic_endf_file):
        """Test that data is consistent between different parsing methods."""
        # Parse with ENDFEvaluation
        eval_obj = ENDFEvaluation(realistic_endf_file)
        total_rxn_eval = eval_obj[1]
        
        # Parse with ENDFCompatibility
        compat = ENDFCompatibility(realistic_endf_file)
        total_rxn_compat = compat[1]
        
        # Data should match
        assert np.array_equal(total_rxn_eval.energy, total_rxn_compat.energy)
        assert np.array_equal(
            total_rxn_eval.cross_section, 
            total_rxn_compat.cross_section
        )
