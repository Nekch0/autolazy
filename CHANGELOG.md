# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-26

### Added

- `parse_all(path)` — AST-based extraction of `__all__` declarations from
  Python source files. Supports assignment (`=`), augmented assignment (`+=`),
  `append`, and `extend` patterns.
- `lazy_attach(package_name, init_file_path, submodules, submod_attrs)` —
  wrapper around `lazy_loader.attach()` that auto-discovers public symbols
  from submodules so callers do not need to maintain symbol lists manually.
- Fallback logic: submodules with no `__all__` (or a missing file) are
  automatically demoted to plain lazy submodule entries.
- Support for nested/dotted submodule names (e.g. `"sub.module"`).
