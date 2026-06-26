def test_simple_assignment(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = ["foo", "bar"]', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["foo", "bar"]


def test_augmented_assignment(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = ["foo"]\n__all__ += ["bar"]', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["foo", "bar"]


def test_append(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = []\n__all__.append("foo")', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["foo"]


def test_extend(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = []\n__all__.extend(["bar", "baz"])', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["bar", "baz"]


def test_append_and_extend_combined(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text(
        '__all__ = []\n__all__.append("foo")\n__all__.extend(["bar", "baz"])',
        encoding="utf-8",
    )
    assert lazyutils.parse_all(f) == ["foo", "bar", "baz"]


def test_no_all(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("x = 1\ny = 2", encoding="utf-8")
    assert lazyutils.parse_all(f) == []


def test_empty_all(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("__all__ = []", encoding="utf-8")
    assert lazyutils.parse_all(f) == []


def test_multiple_assignments_last_wins(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = ["a"]\n__all__ = ["b", "c"]', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["b", "c"]


def test_non_string_elements_filtered(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text('__all__ = ["foo", 42, True, "bar"]', encoding="utf-8")
    assert lazyutils.parse_all(f) == ["foo", "bar"]


def test_all_patterns_combined(lazyutils, tmp_path):
    f = tmp_path / "sample.py"
    f.write_text(
        '__all__ = ["a"]\n'
        '__all__ += ["b"]\n'
        '__all__.append("c")\n'
        '__all__.extend(["d", "e"])\n',
        encoding="utf-8",
    )
    assert lazyutils.parse_all(f) == ["a", "b", "c", "d", "e"]
