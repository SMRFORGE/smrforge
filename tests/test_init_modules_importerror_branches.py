import builtins
import importlib
import sys

import pytest


def _reload_with_forced_importerror(module, *, name_predicate):
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name_predicate(name, globals, locals, fromlist, level):
            raise ImportError("forced for coverage")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)
        return importlib.reload(module)


def test_core_init_importerror_branches_and_getattr():
    # Be robust to other tests manipulating sys.modules.
    core = importlib.import_module("smrforge.core")
    sys.modules["smrforge.core"] = core
    core = importlib.reload(core)

    # Force each optional import to fail at least once to cover the except blocks.
    core = _reload_with_forced_importerror(
        core, name_predicate=lambda n, *_: n.endswith("smrforge.core.control_rod_worth")
    )
    assert core._CONTROL_ROD_WORTH_AVAILABLE is False

    core = _reload_with_forced_importerror(
        core,
        name_predicate=lambda n, *_: n.endswith("smrforge.core.multigroup_advanced"),
    )
    assert core._MULTIGROUP_ADVANCED_AVAILABLE is False

    core = _reload_with_forced_importerror(
        core,
        name_predicate=lambda n, *_: n.endswith("smrforge.core.energy_angle_parser"),
    )
    assert core._ENERGY_ANGLE_PARSER_AVAILABLE is False

    core = _reload_with_forced_importerror(
        core,
        name_predicate=lambda n, *_: n.endswith(
            "smrforge.core.self_shielding_integration"
        ),
    )
    assert core._SELF_SHIELDING_INTEGRATION_AVAILABLE is False

    core = _reload_with_forced_importerror(
        core, name_predicate=lambda n, *_: n.endswith("smrforge.core.decay_chain_utils")
    )
    assert core._DECAY_CHAIN_UTILS_AVAILABLE is False

    core = _reload_with_forced_importerror(
        core, name_predicate=lambda n, *_: n.endswith("smrforge.core.endf_extractors")
    )
    assert core._ENDF_EXTRACTORS_AVAILABLE is False

    # __getattr__ happy path for self_shielding_integration
    core = importlib.reload(core)
    mod = getattr(core, "self_shielding_integration")
    assert mod is not None
    # __getattr__ unknown attribute
    with pytest.raises(AttributeError):
        getattr(core, "does_not_exist")


def test_thermal_init_importerror_branches():
    import smrforge.thermal as th

    th = importlib.reload(th)

    # Force lumped import failure branch
    th2 = _reload_with_forced_importerror(
        th, name_predicate=lambda n, *_: n.endswith("smrforge.thermal.lumped")
    )
    assert th2._LUMPED_THERMAL_AVAILABLE is False

    # Force two-phase advanced import failure branch
    th3 = _reload_with_forced_importerror(
        th,
        name_predicate=lambda n, *_: n.endswith("smrforge.thermal.two_phase_advanced"),
    )
    assert th3._TWO_PHASE_ADVANCED_AVAILABLE is False


def test_smrforge_init_convenience_fallback_exec_module_failure():
    import importlib.machinery
    import sys
    import warnings

    import smrforge

    smrforge = importlib.reload(smrforge)

    # Force `from smrforge.convenience import ...` to fail; __init__.py handles
    # ImportError with warning and sets _CONVENIENCE_AVAILABLE=False.
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "smrforge.convenience":
            raise ImportError("forced e1")
        return orig_import(name, globals, locals, fromlist, level)

    warn_calls = []

    def fake_warn(message, *args, **kwargs):
        warn_calls.append(str(message))

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)
        mp.setattr(warnings, "warn", fake_warn)

        sys.modules.pop("smrforge.convenience", None)
        if hasattr(smrforge, "convenience"):
            delattr(smrforge, "convenience")

        smrforge2 = importlib.reload(smrforge)
        assert smrforge2._CONVENIENCE_AVAILABLE is False
        assert any("Could not import convenience functions" in m for m in warn_calls)

    importlib.reload(smrforge)
