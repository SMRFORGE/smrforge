"""
Convenience modules for simplified APIs.

Provides high-level convenience functions for common operations,
wrapping more complex APIs for easier adoption.
"""

# Import main convenience functions from parent convenience.py file
# Note: We're in convenience/__init__.py, but list_presets() is in convenience.py
# We need to import from the parent module to avoid circular imports
try:
    # Import using sys.modules trick to access the parent convenience.py
    import sys
    import importlib
    
    # Check if the parent convenience module is already loaded
    if 'smrforge.convenience' in sys.modules:
        # Get the actual file module (not this package)
        parent_convenience = sys.modules.get('smrforge.convenience')
        # If it's this module, we need to load the file differently
        if parent_convenience is sys.modules[__name__]:
            # Load the actual file
            from pathlib import Path
            convenience_file = Path(__file__).parent.parent / "convenience.py"
            if convenience_file.exists():
                # Load under a non-conflicting module name *within* the smrforge package
                # so relative imports inside convenience.py (e.g. from .geometry...) work.
                spec = importlib.util.spec_from_file_location(
                    "smrforge._convenience_module", convenience_file
                )
                convenience_mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = convenience_mod
                spec.loader.exec_module(convenience_mod)
                
                list_presets = convenience_mod.list_presets
                get_preset = convenience_mod.get_preset
                create_reactor = convenience_mod.create_reactor
                analyze_preset = convenience_mod.analyze_preset
                compare_designs = convenience_mod.compare_designs
                quick_keff = convenience_mod.quick_keff
                SimpleReactor = convenience_mod.SimpleReactor
                # Private helpers (used by some tests / advanced use)
                _get_library = convenience_mod._get_library
                _design_library = convenience_mod._design_library
                _CONVENIENCE_MAIN_AVAILABLE = True
            else:
                _CONVENIENCE_MAIN_AVAILABLE = False
        else:
            # It's already the file module
            list_presets = parent_convenience.list_presets
            get_preset = parent_convenience.get_preset
            create_reactor = parent_convenience.create_reactor
            analyze_preset = parent_convenience.analyze_preset
            compare_designs = parent_convenience.compare_designs
            quick_keff = parent_convenience.quick_keff
            SimpleReactor = parent_convenience.SimpleReactor
            # Private helpers (used by some tests / advanced use)
            _get_library = parent_convenience._get_library
            _design_library = parent_convenience._design_library
            _CONVENIENCE_MAIN_AVAILABLE = True
    else:
        # Load from file directly
        from pathlib import Path
        import importlib.util
        convenience_file = Path(__file__).parent.parent / "convenience.py"
        if convenience_file.exists():
            # Load under a non-conflicting module name *within* the smrforge package
            # so relative imports inside convenience.py (e.g. from .geometry...) work.
            spec = importlib.util.spec_from_file_location(
                "smrforge._convenience_module", convenience_file
            )
            convenience_mod = importlib.util.module_from_spec(spec)
            # Add parent to path so relative imports work
            import sys
            parent_dir = str(convenience_file.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            sys.modules[spec.name] = convenience_mod
            spec.loader.exec_module(convenience_mod)
            
            list_presets = convenience_mod.list_presets
            get_preset = convenience_mod.get_preset
            create_reactor = convenience_mod.create_reactor
            analyze_preset = convenience_mod.analyze_preset
            compare_designs = convenience_mod.compare_designs
            quick_keff = convenience_mod.quick_keff
            SimpleReactor = convenience_mod.SimpleReactor
            # Private helpers (used by some tests / advanced use)
            _get_library = convenience_mod._get_library
            _design_library = convenience_mod._design_library
            _CONVENIENCE_MAIN_AVAILABLE = True
        else:
            _CONVENIENCE_MAIN_AVAILABLE = False
except Exception as e:
    import warnings
    warnings.warn(f"Could not import convenience functions from convenience.py: {e}", ImportWarning)
    _CONVENIENCE_MAIN_AVAILABLE = False

# Transient convenience functions (optional - requires safety module)
try:
    from smrforge.convenience.transients import (
        quick_transient,
        reactivity_insertion,
        decay_heat_removal,
    )

    _TRANSIENT_CONVENIENCE_AVAILABLE = True
except ImportError:
    _TRANSIENT_CONVENIENCE_AVAILABLE = False

__all__ = []

if _CONVENIENCE_MAIN_AVAILABLE:
    __all__.extend(
        [
            "list_presets",
            "get_preset",
            "create_reactor",
            "analyze_preset",
            "compare_designs",
            "quick_keff",
            "SimpleReactor",
        ]
    )

if _TRANSIENT_CONVENIENCE_AVAILABLE:
    __all__.extend(
        [
            "quick_transient",
            "reactivity_insertion",
            "decay_heat_removal",
        ]
    )
