import builtins
import importlib
import sys
from types import ModuleType
from unittest.mock import patch


def test_canonical_import_returns_existing_module():
    from smrforge._import_compat import canonical_import

    mod = canonical_import("smrforge")
    assert mod is sys.modules["smrforge"]


def test_canonical_import_imports_when_missing():
    from smrforge._import_compat import canonical_import

    # Use a stdlib module name that should always be importable.
    sys.modules.pop("math", None)
    mod = canonical_import("math")
    assert mod.__name__ == "math"


def test_bind_parent_attr_from_modules_covers_early_returns_and_success():
    from smrforge._import_compat import bind_parent_attr_from_modules

    parent_name = "tmp_parent_pkg"
    child_attr = "child"
    child_name = f"{parent_name}.{child_attr}"

    # Parent missing -> early return
    sys.modules.pop(parent_name, None)
    sys.modules.pop(child_name, None)
    bind_parent_attr_from_modules(parent_name, child_attr)

    # Child missing -> early return
    sys.modules[parent_name] = ModuleType(parent_name)
    sys.modules.pop(child_name, None)
    bind_parent_attr_from_modules(parent_name, child_attr)

    # Success path: set attribute
    child_mod = ModuleType(child_name)
    sys.modules[child_name] = child_mod
    bind_parent_attr_from_modules(parent_name, child_attr)
    assert getattr(sys.modules[parent_name], child_attr) is child_mod


def test_bind_parent_attr_from_modules_swallows_setattr_errors():
    from smrforge._import_compat import bind_parent_attr_from_modules

    class NoSetAttrModule(ModuleType):
        def __setattr__(self, name, value):
            raise RuntimeError("no setattr")

    parent_name = "tmp_parent_pkg2"
    child_attr = "child"
    child_name = f"{parent_name}.{child_attr}"

    sys.modules[parent_name] = NoSetAttrModule(parent_name)
    sys.modules[child_name] = ModuleType(child_name)

    # Should not raise
    bind_parent_attr_from_modules(parent_name, child_attr)


def test_delete_attr_if_present_covers_missing_parent_and_delattr_exception():
    from smrforge._import_compat import delete_attr_if_present

    parent_name = "tmp_parent_pkg3"
    sys.modules.pop(parent_name, None)
    delete_attr_if_present(parent_name, "x")  # parent missing

    # parent present but attr missing -> AttributeError swallowed
    sys.modules[parent_name] = ModuleType(parent_name)
    delete_attr_if_present(parent_name, "x")


def test_delete_global_covers_success_and_exception():
    from smrforge._import_compat import delete_global

    g = {"x": 1}
    delete_global(g, "x")
    assert "x" not in g

    class BadDict(dict):
        def __delitem__(self, key):
            raise RuntimeError("no delete")

    g2 = BadDict({"y": 2})
    delete_global(g2, "y")  # should swallow exception
    assert "y" in g2

