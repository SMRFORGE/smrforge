"""
Extended tests for smrforge.convenience module to improve coverage.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import using the same approach as test_convenience.py
try:
    from smrforge.convenience import (
        analyze_preset,
        compare_designs,
        create_reactor,
        get_preset,
        list_presets,
        quick_keff,
    )
    import smrforge.convenience as convenience_module
except ImportError:
    pytest.skip("Convenience module not available", allow_module_level=True)

# SimpleReactor may need to be imported differently
try:
    from smrforge.convenience import SimpleReactor, _get_library
except ImportError:
    # Try importing from the file directly via importlib
    import importlib.util
    from pathlib import Path
    convenience_file = Path(__file__).parent.parent / "smrforge" / "convenience.py"
    if convenience_file.exists():
        # Add parent to path for relative imports to work
        import sys
        parent_dir = str(convenience_file.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        spec = importlib.util.spec_from_file_location("_convenience", convenience_file)
        _conv_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_conv_mod)
        SimpleReactor = _conv_mod.SimpleReactor
        _get_library = _conv_mod._get_library
    else:
        SimpleReactor = None
        _get_library = None
        pytest.skip("Cannot import SimpleReactor or _get_library", allow_module_level=True)


class TestGetLibrary:
    """Tests for _get_library function."""
    
    def test_get_library_returns_library(self):
        """Test _get_library returns DesignLibrary."""
        library = _get_library()
        assert library is not None
        assert hasattr(library, 'list_designs')
    
    @patch('smrforge.convenience._PRESETS_AVAILABLE', False)
    def test_get_library_without_presets(self):
        """Test _get_library raises ImportError when presets not available."""
        # This tests the error path
        # We need to reload the module to pick up the change
        import importlib
        import sys
        if 'smrforge.convenience' in sys.modules:
            # Save original
            original = sys.modules['smrforge.convenience']._PRESETS_AVAILABLE
            sys.modules['smrforge.convenience']._PRESETS_AVAILABLE = False
            try:
                with pytest.raises(ImportError, match="Preset designs not available"):
                    _get_library()
            finally:
                # Restore
                sys.modules['smrforge.convenience']._PRESETS_AVAILABLE = original


class TestCompareDesigns:
    """Extended tests for compare_designs function."""
    
    def test_compare_designs_single_design(self):
        """Test compare_designs with single design."""
        presets = convenience_module.list_presets()
        if presets:
            results = compare_designs([presets[0]])
            assert isinstance(results, dict)
            assert len(results) == 1
            assert presets[0] in results
    
    def test_compare_designs_handles_error_in_design(self):
        """Test compare_designs handles errors for one design gracefully."""
        presets = convenience_module.list_presets()
        if presets:
            # Mock analyze_preset to raise error for one design
            original_analyze = convenience_module.analyze_preset
            
            def mock_analyze(name):
                if name == presets[0]:
                    raise ValueError("Test error")
                return original_analyze(name)
            
            with patch('smrforge.convenience.analyze_preset', side_effect=mock_analyze):
                results = compare_designs(presets[:2] if len(presets) >= 2 else [presets[0]])
                assert isinstance(results, dict)
                # Should have error entry for failed design
                assert any("error" in str(r) for r in results.values() if isinstance(r, dict))
    
    def test_compare_designs_empty_list(self):
        """Test compare_designs with empty list."""
        results = compare_designs([])
        assert isinstance(results, dict)
        assert len(results) == 0


class TestSimpleReactorExtended:
    """Extended tests for SimpleReactor class methods."""
    
    def test_simple_reactor_from_preset(self):
        """Test SimpleReactor.from_preset class method."""
        presets = convenience_module.list_presets()
        if presets:
            # Get a preset reactor
            preset_spec = convenience_module.get_preset(presets[0])
            
            # Create mock preset object
            mock_preset = Mock()
            mock_preset.spec = preset_spec
            mock_preset.build_core = Mock()
            mock_preset.get_cross_sections = Mock()
            
            reactor = SimpleReactor.from_preset(mock_preset)
            
            assert isinstance(reactor, SimpleReactor)
            assert reactor.spec == preset_spec
            assert hasattr(reactor, '_preset')
    
    def test_simple_reactor_get_core_with_preset(self):
        """Test _get_core method when created from preset."""
        presets = convenience_module.list_presets()
        if presets:
            preset_spec = convenience_module.get_preset(presets[0])
            mock_preset = Mock()
            mock_preset.spec = preset_spec
            mock_core = Mock()
            mock_preset.build_core = Mock(return_value=mock_core)
            mock_preset.get_cross_sections = Mock()
            
            reactor = SimpleReactor.from_preset(mock_preset)
            core = reactor._get_core()
            
            assert core == mock_core
            mock_preset.build_core.assert_called_once()
    
    def test_simple_reactor_get_core_custom(self):
        """Test _get_core method for custom reactor."""
        reactor = SimpleReactor(
            power_mw=10.0,
            core_height=200.0,
            core_diameter=100.0,
        )
        
        core = reactor._get_core()
        
        assert core is not None
        assert reactor._core is not None
    
    def test_simple_reactor_get_xs_data_with_preset(self):
        """Test _get_xs_data method when created from preset."""
        presets = convenience_module.list_presets()
        if presets:
            preset_spec = convenience_module.get_preset(presets[0])
            mock_preset = Mock()
            mock_preset.spec = preset_spec
            mock_preset.build_core = Mock()
            mock_xs = Mock()
            mock_preset.get_cross_sections = Mock(return_value=mock_xs)
            
            reactor = SimpleReactor.from_preset(mock_preset)
            xs_data = reactor._get_xs_data()
            
            assert xs_data == mock_xs
            mock_preset.get_cross_sections.assert_called_once()
    
    def test_simple_reactor_get_xs_data_custom(self):
        """Test _get_xs_data method for custom reactor."""
        reactor = SimpleReactor(
            power_mw=10.0,
            core_height=200.0,
            core_diameter=100.0,
        )
        
        xs_data = reactor._get_xs_data()
        
        assert xs_data is not None
        assert reactor._xs_data is not None
    
    def test_simple_reactor_create_simple_xs(self):
        """Test _create_simple_xs method."""
        reactor = SimpleReactor(
            power_mw=10.0,
            core_height=200.0,
            core_diameter=100.0,
        )
        
        xs_data = reactor._create_simple_xs()
        
        assert xs_data is not None
        assert xs_data.n_groups == 2
        assert xs_data.n_materials == 2
    
    def test_simple_reactor_get_solver(self):
        """Test _get_solver method."""
        reactor = SimpleReactor(
            power_mw=10.0,
            core_height=200.0,
            core_diameter=100.0,
        )
        
        solver = reactor._get_solver()
        
        assert solver is not None
        assert reactor._solver is not None
    
    def test_simple_reactor_with_custom_kwargs(self):
        """Test SimpleReactor with custom kwargs."""
        reactor = SimpleReactor(
            power_mw=10.0,
            core_height=200.0,
            core_diameter=100.0,
            name="Custom-Test-Reactor",
            inlet_temperature=800.0,
            outlet_temperature=1000.0,
        )
        
        assert reactor.spec.name == "Custom-Test-Reactor"
        assert reactor.spec.inlet_temperature == 800.0
        assert reactor.spec.outlet_temperature == 1000.0
    
    def test_simple_reactor_heavy_metal_loading_estimation(self):
        """Test SimpleReactor estimates heavy metal loading."""
        reactor = SimpleReactor(
            power_mw=10.0,
        )
        
        # Should estimate HM loading from power
        assert reactor.spec.heavy_metal_loading > 0
        # Typical: ~10-15 kg/MWth
        assert 100 <= reactor.spec.heavy_metal_loading <= 200  # 10 MW * 10-20 kg/MW
