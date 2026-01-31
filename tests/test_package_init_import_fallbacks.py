import builtins
import importlib
import sys


def _import_with_blocked(monkeypatch, module_name: str, blocked_prefixes: list[str]):
    """
    Import a module while forcing ImportError for selected module prefixes.

    This is used to cover import-time fallback branches in package __init__.py files.
    """
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        for pref in blocked_prefixes:
            if name == pref or name.startswith(pref + "."):
                raise ImportError(f"blocked import: {pref}")
        return real_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as mp:
        mp.setattr(builtins, "__import__", fake_import)
        sys.modules.pop(module_name, None)
        for pref in blocked_prefixes:
            sys.modules.pop(pref, None)
        return importlib.import_module(module_name)


def test_geometry_init_import_fallbacks(monkeypatch):
    mod = _import_with_blocked(
        monkeypatch,
        "smrforge.geometry",
        [
            "smrforge.geometry.mesh_3d",
            "smrforge.geometry.lwr_smr",
            "smrforge.geometry.fast_reactor_smr",
            "smrforge.geometry.smr_mesh_optimization",
            "smrforge.geometry.smr_fuel_management",
            "smrforge.geometry.smr_compact_core",
            "smrforge.geometry.smr_scram_system",
            "smrforge.geometry.two_phase_flow",
            "smrforge.geometry.molten_salt_smr",
        ],
    )

    assert mod._MESH_3D_AVAILABLE is False
    assert mod._LWR_SMR_AVAILABLE is False
    assert mod._FAST_REACTOR_SMR_AVAILABLE is False
    assert mod._SMR_MESH_OPTIMIZATION_AVAILABLE is False
    assert mod._SMR_FUEL_MANAGEMENT_AVAILABLE is False
    assert mod._SMR_COMPACT_CORE_AVAILABLE is False
    assert mod._SMR_SCRAM_SYSTEM_AVAILABLE is False
    assert mod._TWO_PHASE_FLOW_AVAILABLE is False
    assert mod._MOLTEN_SALT_SMR_AVAILABLE is False

    # Restore to the normal state for the rest of the suite.
    import smrforge.geometry as geom

    importlib.reload(geom)


def test_visualization_init_import_fallbacks(monkeypatch):
    mod = _import_with_blocked(
        monkeypatch,
        "smrforge.visualization",
        [
            "smrforge.visualization.advanced",
            "smrforge.visualization.plot_api",
            "smrforge.visualization.voxel_plots",
            "smrforge.visualization.mesh_tally",
            "smrforge.visualization.geometry_verification",
            "smrforge.visualization.material_composition",
            "smrforge.visualization.tally_data",
            "smrforge.visualization.transients",
            "smrforge.visualization.mesh_diagnostics",
            "smrforge.visualization.sweep_plots",
            "smrforge.visualization.validation_plots",
            "smrforge.visualization.economics_plots",
            "smrforge.visualization.optimization_plots",
        ],
    )

    assert mod._ADVANCED_VIS_AVAILABLE is False
    assert mod._PLOT_API_AVAILABLE is False
    assert mod._VOXEL_PLOTS_AVAILABLE is False
    assert mod._MESH_TALLY_AVAILABLE is False
    assert mod._MATERIAL_COMPOSITION_AVAILABLE is False
    assert mod._TALLY_DATA_AVAILABLE is False

    # Restore to the normal state for the rest of the suite.
    import smrforge.visualization as viz

    importlib.reload(viz)
