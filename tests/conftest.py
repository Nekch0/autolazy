import importlib
import sys
import types

import pytest


@pytest.fixture
def lazyutils(monkeypatch):
    """Import lazyutils with a mocked lazy_loader."""

    fake = types.ModuleType("lazy_loader")

    def attach(package_name, submodules=None, submod_attrs=None):
        return (
            package_name,
            submodules,
            submod_attrs,
        )

    fake.attach = attach # type: ignore

    monkeypatch.setitem(sys.modules, "lazy_loader", fake)

    sys.modules.pop("autolazy", None)

    return importlib.import_module("autolazy")