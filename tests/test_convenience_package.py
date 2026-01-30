import builtins
import importlib

import pytest


def test_convenience_package_importerror_and_branch_coverage():
    import smrforge.convenience as c

    c = importlib.reload(c)

    # Cover the LWR presets ImportError/exception branch (lines 70-84)
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.endswith("smrforge.presets.smr_lwr") or name.endswith("presets.smr_lwr"):
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(builtins, "__import__", guarded_import)
        c2 = importlib.reload(c)
        assert c2._LWR_PRESETS_AVAILABLE is False
        # Dummy classes are defined in that branch
        assert hasattr(c2, "NuScalePWR77MWe")
        assert hasattr(c2, "SMART100MWe")
        assert hasattr(c2, "CAREM32MWe")
        assert hasattr(c2, "BWRX300")

    # Cover create_reactor() preset_names exception fallback (lines 139-140)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(c, "_PRESETS_AVAILABLE", True)
        mp.setattr(c, "list_presets", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        with pytest.raises(ValueError):
            c.create_reactor("valar-10")

    # Cover preset_class None path (line 175) with a preset name that isn't in map
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(c, "_PRESETS_AVAILABLE", True)
        mp.setattr(c, "list_presets", lambda: ["weird-preset"])
        with pytest.raises(ValueError):
            c.create_reactor("weird-preset")

    # Cover SimpleReactor kwargs pass-through for recognized fields (line 280)
    r = c.create_reactor(power_mw=10.0, description="hello")
    assert getattr(r.spec, "description", None) == "hello"

