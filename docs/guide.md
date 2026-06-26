# Usage Guide

## Overview

`autolazy` is designed for one task: making it painless to build packages
that defer module imports until the first attribute access. This keeps
`import mypkg` fast even if `mypkg` has heavy dependencies.

Under the hood it delegates to
[`lazy_loader`](https://github.com/scientific-python/lazy_loader) (the same
library used by NumPy, SciPy, and scikit-image). `autolazy` adds automatic
`__all__` discovery on top, so you never have to duplicate symbol lists.

---

## Basic usage

### Flat package

```
mypkg/
├── __init__.py
├── foo.py
└── bar.py
```

`foo.py`:
```python
__all__ = ["Foo", "foo_helper"]

class Foo: ...
def foo_helper(): ...
```

`bar.py`:
```python
__all__ = ["Bar"]

class Bar: ...
```

`__init__.py`:
```python
from autolazy import lazy_attach

__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submod_attrs=["foo", "bar"],
)
```

After this setup:

```python
import mypkg

# Neither foo.py nor bar.py has been imported yet.
mypkg.Foo        # foo.py is imported here
mypkg.Bar        # bar.py is imported here
mypkg.__all__    # ['Foo', 'foo_helper', 'Bar']
```

---

### Exposing submodules without flattening

Use `submodules` when you want `mypkg.utils` to be accessible as a module
object, rather than pulling its symbols into `mypkg` directly:

```python
__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submodules=["utils"],
    submod_attrs=["core"],
)
```

```python
import mypkg

mypkg.utils          # the utils module (imported lazily)
mypkg.core_function  # a symbol from core.py
```

---

### Nested packages

Dotted names work for submodules inside a sub-package:

```
mypkg/
├── __init__.py
└── io/
    ├── __init__.py   # __all__ = ["read", "write"]
    └── formats.py    # __all__ = ["JSON", "CSV"]
```

```python
__getattr__, __dir__, __all__ = lazy_attach(
    package_name=__name__,
    init_file_path=__file__,
    submod_attrs=["io", "io.formats"],
)
```

`io` resolves to `io/__init__.py`; `io.formats` resolves to `io/formats.py`.

---

## Fallback behaviour

If a name in `submod_attrs` cannot be resolved (the file does not exist) or
has no `__all__`, it is silently demoted to a plain submodule entry — the
same as listing it in `submodules`. A `UserWarning` is emitted when the file
is missing so you can catch typos early.

```python
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    lazy_attach("mypkg", __file__, submod_attrs=["nonexistent"])

print(w[0].message)
# UserWarning: '.../mypkg/nonexistent.py' was not found.
```

---

## Standalone use of `parse_all`

`parse_all` is useful on its own whenever you need to read a module's public
API without importing it — for example, in build scripts, linters, or
documentation generators.

```python
from pathlib import Path
from autolazy import parse_all

symbols = parse_all(Path("mypkg/audio.py"))
print(symbols)  # ['AudioLoader', 'AudioWriter']
```

All four patterns are supported:

```python
__all__ = ["a"]          # simple assignment
__all__ += ["b"]         # augmented assignment
__all__.append("c")      # append call
__all__.extend(["d"])    # extend call
```

If a file has no `__all__`, an empty list is returned.
