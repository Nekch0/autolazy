import pytest


def _make_pkg(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    init = pkg / "__init__.py"
    init.write_text("", encoding="utf-8")
    return pkg, init


def test_submod_attrs_found(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    (pkg / "foo.py").write_text('__all__ = ["a", "b"]', encoding="utf-8")

    ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["foo"])

    assert ret[0] == "pkg"
    assert ret[1] is None
    assert ret[2] == {"foo": ["a", "b"]}


def test_submod_attrs_missing_file_warns_and_falls_back(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)

    with pytest.warns(UserWarning):
        ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["missing"])

    assert ret[1] == ["missing"]
    assert ret[2] is None


def test_submod_attrs_no_all_falls_back(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    (pkg / "empty.py").write_text("x = 1", encoding="utf-8")

    ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["empty"])

    assert ret[1] == ["empty"]
    assert ret[2] is None


def test_explicit_submodules(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)

    ret = lazyutils.lazy_attach("pkg", str(init), submodules=["mod1", "mod2"])

    assert ret[1] == ["mod1", "mod2"]
    assert ret[2] is None


def test_mix_submodules_and_submod_attrs(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    (pkg / "bar.py").write_text('__all__ = ["x"]', encoding="utf-8")

    ret = lazyutils.lazy_attach(
        "pkg", str(init), submodules=["mod"], submod_attrs=["bar"]
    )

    assert ret[1] == ["mod"]
    assert ret[2] == {"bar": ["x"]}


def test_submod_attrs_package_with_init(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "__init__.py").write_text('__all__ = ["MyClass"]', encoding="utf-8")

    ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["sub"])

    assert ret[2] == {"sub": ["MyClass"]}


def test_submod_attrs_package_missing_init_warns_and_falls_back(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    (pkg / "sub").mkdir()

    with pytest.warns(UserWarning):
        ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["sub"])

    assert ret[1] == ["sub"]
    assert ret[2] is None


def test_nested_dotted_submod(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "mod.py").write_text('__all__ = ["func"]', encoding="utf-8")

    ret = lazyutils.lazy_attach("pkg", str(init), submod_attrs=["sub.mod"])

    assert ret[2] == {"sub.mod": ["func"]}


def test_empty_inputs(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)

    ret = lazyutils.lazy_attach("pkg", str(init))

    assert ret[0] == "pkg"
    assert ret[1] is None
    assert ret[2] is None


def test_multiple_submod_attrs_mixed(lazyutils, tmp_path):
    pkg, init = _make_pkg(tmp_path)
    (pkg / "found.py").write_text('__all__ = ["z"]', encoding="utf-8")

    with pytest.warns(UserWarning):
        ret = lazyutils.lazy_attach(
            "pkg", str(init), submod_attrs=["found", "missing"]
        )

    assert ret[2] == {"found": ["z"]}
    assert "missing" in ret[1]
