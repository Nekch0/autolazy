# autolazy

Utilities for building lazily imported Python packages.

`autolazy` provides helper functions that make it easy to set up
[`lazy_loader`](https://github.com/scientific-python/lazy_loader)-based packages.
It automatically discovers each submodule's public API by parsing `__all__`
declarations — no imports, no side effects, just AST analysis — and wires
everything up in a single call.

## Installation

```bash
pip install autolazy
```

Requires Python 3.12+.

## Quick start

Suppose you have a package like this:

```
mypkg/
├── __init__.py
├── audio.py       # __all__ = ["AudioLoader", "AudioWriter"]
└── vision.py      # __all__ = ["ImageLoader"]
```

Replace the usual eager imports in `__init__.py` with:

```python
from autolazy import lazy_attach

__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submod_attrs=["audio", "vision"],
)
```

Now symbols are imported on first access:

```python
import mypkg

mypkg.AudioLoader   # imports audio.py only at this point
mypkg.ImageLoader   # imports vision.py only at this point
```

Submodules themselves can also be exposed lazily:

```python
__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submodules=["utils"],       # exposed as mypkg.utils
    submod_attrs=["audio"],     # symbols exposed at mypkg level
)
```

## API

### `lazy_attach`

```python
lazy_attach(
    package_name: str,
    init_file_path: str,
    submodules: list[str] = [],
    submod_attrs: list[str] = [],
) -> tuple[__getattr__, __dir__, __all__]
```

Scans each name in `submod_attrs`, extracts its `__all__` via AST parsing,
and passes the result to `lazy_loader.attach()`.

| Parameter | Description |
|---|---|
| `package_name` | The package name — pass `__name__` |
| `init_file_path` | Path to `__init__.py` — pass `__file__` |
| `submodules` | Submodules exposed as `pkg.submod` (not flattened) |
| `submod_attrs` | Submodules whose public symbols are flattened into the package namespace |

If a name in `submod_attrs` has no `__all__` (or the file is missing), it
falls back to being treated as a plain submodule and a `UserWarning` is
emitted for missing files.

Dotted names (e.g. `"sub.module"`) are resolved relative to the package
directory, so nested packages work out of the box.

---

### `parse_all`

```python
parse_all(path: Path) -> list[str]
```

Parses a Python source file and returns the names declared in `__all__`,
without importing the module. Supports all common patterns:

```python
__all__ = ["a", "b"]       # assignment
__all__ += ["c"]           # augmented assignment
__all__.append("d")        # append
__all__.extend(["e", "f"]) # extend
```

Non-string elements in `__all__` are silently ignored. If multiple
assignments to `__all__` exist, the last one wins (matching Python semantics).

## How it compares to manual `lazy_loader` usage

Without `autolazy` you must maintain `submod_attrs` by hand:

```python
# manual — must be kept in sync with each module's __all__
__getattr__, __dir__, __all__ = lazy.attach(
    __name__,
    submod_attrs={
        "audio": ["AudioLoader", "AudioWriter"],
        "vision": ["ImageLoader"],
    },
)
```

With `autolazy`:

```python
# automatic — __all__ is read from each file at import time
__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submod_attrs=["audio", "vision"],
)
```

## Requirements

- Python >= 3.12
- [`lazy-loader`](https://pypi.org/project/lazy-loader/) >= 0.4

## License

MIT — see [LICENSE](LICENSE).
