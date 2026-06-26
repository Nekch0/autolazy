"""
Utilities for building lazily imported Python packages.

This module provides helper functions for constructing packages based on
``lazy_loader``. It automatically scans ``__all__`` declarations in
submodules and generates the information required by
``lazy_loader.attach()``.

Features:
    * Automatically parses public APIs from ``__all__``.
    * Supports nested packages and modules.
    * Falls back gracefully when modules are not found.
    * Reduces import time by loading modules only when they are accessed.

Functions:
    parse_all(path):
        Extracts public symbols from a module by parsing its ``__all__``
        declaration.

    lazy_attach(package_name, init_file_path, submodules, submod_attrs):
        Creates lazy imports for a package using ``lazy_loader.attach()``.

Example:
    Simple package structure::

        mypkg/
        ├── __init__.py
        ├── foo.py
        └── bar.py

    foo.py::

        __all__ = ["hello"]

        def hello():
            print("Hello")

    __init__.py::

        from libutils import lazy_attach

        __getattr__, __dir__, __all__ = lazy_attach(
            package_name=__name__,
            init_file_path=__file__,
            submod_attrs=[
                "foo",
                "bar",
            ],
        )

    Usage::

        >>> import mypkg
        >>> mypkg.hello()
        Hello

The corresponding module is imported only when ``mypkg.hello`` is first
accessed.
"""
import sys as _sys
import warnings as _warnings

_REQUIRED_PYTHON_VERSION = (3, 12)

if _sys.version_info < _REQUIRED_PYTHON_VERSION:
    _required_ver = '.'.join(str(v) for v in _REQUIRED_PYTHON_VERSION)
    _current_ver = '.'.join(str(v) for v in _sys.version_info)
    _warnings.warn(
        f"PythonのVersionは {_required_ver} 以上である必要があります"
        f"（現在のVersionは {_current_ver} です）"
    )
    exit()


import ast
import warnings
import lazy_loader as lazy
from pathlib import Path
from typing import Any
from types import ModuleType
from collections.abc import Callable


class _Collector(ast.NodeVisitor):

    def __init__(self):
        self.pub_modules = []

    def visit_Assign(self, node):
        """ `__all__ = [...]` の形式を検出 """
        targets = node.targets
        if len(targets) != 1:
            return
        if not (isinstance(targets[0], ast.Name) and targets[0].id == "__all__"):
            return
        if isinstance(node.value, ast.List):
            self.pub_modules = [
                elt.value for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
            
    def visit_AugAssign(self, node):
        """ `__all__ += [...]` の形式を検出 """
        if not (isinstance(node.target, ast.Name) and node.target.id == "__all__"):
            return
        if isinstance(node.value, ast.List):
            self.pub_modules += [
                elt.value for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
            
    def visit_Call(self, node):
        """ `__all__.append(...)` および `__all__.extend(...)` を検出 """
        func = node.func
        if not isinstance(func, ast.Attribute):
            return
        if not isinstance(func.value, ast.Name):
            return
        if not func.value.id == "__all__":
            return
        arg = node.args[0]
        if func.attr == "append":
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                self.pub_modules.append(arg.value)
        elif func.attr == "extend":
            if isinstance(arg, ast.List):
                self.pub_modules += [
                    elt.value for elt in arg.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
            
            
def parse_all(path: Path) -> list[str]:
    """Extract public symbols defined in ``__all__``.

    The module is parsed using Python's AST instead of being imported,
    allowing public APIs to be discovered without executing the module.

    Supported patterns include:

    * ``__all__ = [...]``
    * ``__all__ += [...]``
    * ``__all__.append(...)``
    * ``__all__.extend(...)``

    Args:
        path: Path to the Python source file.

    Returns:
        A list of public symbol names defined in ``__all__``.

    Example:
        >>> parse_all(Path("foo.py"))
        ['func1', 'ClassA']
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    collector = _Collector()
    collector.visit(tree)
    return collector.pub_modules


def lazy_attach(
    package_name: str,
    init_file_path: str,
    submodules: list[str] | None = None,
    submod_attrs: list[str] | None = None,
) -> tuple[Callable[[str], ModuleType | Any], Callable[[], list[str]], list[str]]:
    """Create lazy imports for a package.

    This function scans the specified submodules, extracts their public
    symbols from ``__all__``, and constructs the arguments required by
    ``lazy_loader.attach()``.

    Modules without a detectable ``__all__`` are registered as lazy
    submodules instead of attribute providers.

    Args:
        package_name: Package name, typically ``__name__``.
        init_file_path: Path to the package's ``__init__.py`` file,
            typically ``__file__``.
        submodules: Submodules to expose as lazy modules.
        submod_attrs: Submodules whose public symbols should be exposed
            directly from the package namespace.

    Returns:
        The tuple returned by ``lazy_loader.attach()``::

            (__getattr__, __dir__, __all__)

    Example:
        >>> __getattr__, __dir__, __all__ = lazy_attach(
        ...     package_name=__name__,
        ...     init_file_path=__file__,
        ...     submod_attrs=[
        ...         "audio",
        ...         "vision",
        ...     ],
        ... )
    """
    pkg_dir = Path(init_file_path).parent
    submodules_scanned = list(submodules) if submodules is not None else []
    submod_attrs_scanned = dict[str, list[str]]()

    def _get_all(directory: Path, submod_name: str) -> list[str]:
        submod_path = directory / Path(submod_name.replace(".", "/"))
        if submod_path.is_dir():
            init = submod_path / "__init__.py"
            if not init.exists():
                warnings.warn(f"'{submod_path}' was not found.")
                return []
            return parse_all(init)
        submod_file = Path(f"{submod_path}.py")
        if not submod_file.exists():
            warnings.warn(f"'{submod_path}.py' was not found.")
            return []

        return parse_all(submod_file)

    for submod_name in (submod_attrs or []):
        public_modules = _get_all(pkg_dir, submod_name)
        if public_modules:
            submod_attrs_scanned[submod_name] = public_modules
        else:
            submodules_scanned.append(submod_name)

    return lazy.attach(
        package_name, 
        submodules_scanned if submodules_scanned else None, 
        submod_attrs_scanned if submod_attrs_scanned else None
    )
    
    
__all__ = [
    "parse_all",
    "lazy_attach"
]

del _sys
del _warnings