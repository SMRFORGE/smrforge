import builtins
import importlib
import sys
from unittest.mock import patch


def test_fuel_cycle_init_exports_advanced_when_available():
    import smrforge.fuel_cycle as fc

    assert "FuelCycleOptimizer" in fc.__all__
    # In normal environments, advanced_optimization exists in the repo, so this should be available.
    assert fc._ADVANCED_OPT_AVAILABLE is True
    assert "GeneticAlgorithm" in fc.__all__


def test_fuel_cycle_init_handles_missing_advanced_optimization():
    """
    Force ImportError for smrforge.fuel_cycle.advanced_optimization and ensure the
    module falls back gracefully.
    """
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "smrforge.fuel_cycle.advanced_optimization":
            raise ImportError("forced ImportError for test")
        return real_import(name, globals, locals, fromlist, level)

    # Ensure a clean import (remove cached modules so __init__.py runs again).
    sys.modules.pop("smrforge.fuel_cycle.advanced_optimization", None)
    sys.modules.pop("smrforge.fuel_cycle", None)

    with patch("builtins.__import__", side_effect=guarded_import):
        fc = importlib.import_module("smrforge.fuel_cycle")
        assert fc._ADVANCED_OPT_AVAILABLE is False
        assert "GeneticAlgorithm" not in fc.__all__
        assert fc.GeneticAlgorithm is None
        assert fc.ParticleSwarmOptimization is None

