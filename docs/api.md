# API Reference

## `parse_all`

```python
autolazy.parse_all(path: Path) -> list[str]
```

Parse a Python source file and return the public symbols declared in
`__all__`, without importing the module.

### Parameters

| Name | Type | Description |
|------|------|-------------|
| `path` | `pathlib.Path` | Path to the `.py` file to parse |

### Returns

`list[str]` — names listed in `__all__`. Returns `[]` if no `__all__` is
found.

### Supported patterns

| Pattern | Example |
|---------|---------|
| Assignment | `__all__ = ["a", "b"]` |
| Augmented assignment | `__all__ += ["c"]` |
| `append` call | `__all__.append("d")` |
| `extend` call | `__all__.extend(["e", "f"])` |

Patterns are additive: augmented assignment and method calls accumulate on
top of whatever was assigned last. If multiple plain assignments appear, the
last one replaces all previous values (matching Python's own semantics).
Non-string elements are ignored.

### Example

```python
from pathlib import Path
from autolazy import parse_all

parse_all(Path("mypkg/audio.py"))
# ['AudioLoader', 'AudioWriter']
```

---

## `lazy_attach`

```python
autolazy.lazy_attach(
    package_name: str,
    init_file_path: str,
    submodules: list[str] = [],
    submod_attrs: list[str] = [],
) -> tuple[
    Callable[[str], ModuleType | Any],
    Callable[[], list[str]],
    list[str],
]
```

Create lazy imports for a package and return the triple expected by Python's
import protocol: `(__getattr__, __dir__, __all__)`.

### Parameters

| Name | Type | Description |
|------|------|-------------|
| `package_name` | `str` | The package name. Pass `__name__` from `__init__.py`. |
| `init_file_path` | `str` | Absolute path to `__init__.py`. Pass `__file__`. |
| `submodules` | `list[str]` | Submodules to expose as `pkg.submod` objects (not flattened). |
| `submod_attrs` | `list[str]` | Submodules whose public symbols are exposed directly in the package namespace. |

### Returns

The exact tuple returned by `lazy_loader.attach()`:

```python
__getattr__, __dir__, __all__ = lazy_attach(...)
```

Assigning all three names in `__init__.py` is required for lazy loading to
work correctly.

### Resolution rules for `submod_attrs`

For each name `n` in `submod_attrs`:

1. Replace `.` with `/` to get a relative path.
2. If that path is a **directory**, look for `__init__.py` inside it.
3. Otherwise, look for `{n}.py`.
4. Call `parse_all` on the found file.
5. If `__all__` is non-empty → add `{n: symbols}` to `submod_attrs` dict.
6. Otherwise (empty or file missing) → add `n` to `submodules` instead.
   A `UserWarning` is emitted when the file does not exist.

### Example

```python
# mypkg/__init__.py
from autolazy import lazy_attach

__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submodules=["_internals"],
    submod_attrs=["audio", "vision"],
)
```
