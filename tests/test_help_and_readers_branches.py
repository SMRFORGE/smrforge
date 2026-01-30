import builtins
import importlib
from pathlib import Path
import sys

import pytest


def test_help_importerror_path_and_formatting_and_signature_cleanup(monkeypatch):
    # Be robust to other tests manipulating sys.modules / module metadata.
    h = importlib.import_module("smrforge.help")
    sys.modules[h.__name__] = h
    sys.modules.setdefault("help", h)
    h = importlib.reload(h)

    # Cover _format_docstring code-block closing branch (lines 958-960)
    out = h._format_docstring(">>> x = 1\nx\n\nAfter.")
    assert "```python" in out
    assert "```" in out

    # Cover annotation cleanup that strips "<class '...'>" wrapper (line 257)
    def fn(p: Path):
        return p

    # Use a real Console when available; otherwise a tiny stub.
    if getattr(h, "_RICH_AVAILABLE", False):
        from rich.console import Console

        console = Console(file=None, record=True, width=120)
        h._show_object_help(console, fn, show_examples=False)
    else:
        class DummyConsole:
            def print(self, *args, **kwargs):
                pass

        h._show_object_help(DummyConsole(), fn, show_examples=False)

    # Cover ImportError branch for rich import (lines 20-22) by reloading with forced ImportError
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("rich"):
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    h2 = importlib.reload(h)
    assert h2._RICH_AVAILABLE is False

    # Restore module for other tests
    monkeypatch.setattr(builtins, "__import__", orig_import)
    importlib.reload(h2)


def test_io_readers_yaml_importerror_branch(monkeypatch):
    import smrforge.io.readers as r

    r = importlib.reload(r)

    orig_import = builtins.__import__
    warn_calls = {"n": 0}

    def fake_warning(*args, **kwargs):
        warn_calls["n"] += 1

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "yaml":
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(r.logger, "warning", fake_warning)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    r2 = importlib.reload(r)

    assert r2._YAML_AVAILABLE is False
    assert warn_calls["n"] >= 1

    # Restore module
    monkeypatch.setattr(builtins, "__import__", orig_import)
    importlib.reload(r2)

