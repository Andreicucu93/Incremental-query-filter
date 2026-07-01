import storage


def test_write_and_read_lines_roundtrip(tmp_path):
    p = str(tmp_path / "all.txt")
    storage.write_lines(p, ["a", "b", "c"])
    assert storage.read_lines(p) == ["a", "b", "c"]


def test_read_lines_missing_file_returns_empty(tmp_path):
    assert storage.read_lines(str(tmp_path / "nope.txt")) == []


def test_read_lines_strips_and_skips_blanks(tmp_path):
    p = tmp_path / "all.txt"
    p.write_text("a\n\n b \n\n", encoding="utf-8")
    assert storage.read_lines(str(p)) == ["a", "b"]


def test_append_lines(tmp_path):
    p = str(tmp_path / "done.txt")
    storage.write_lines(p, ["a"])
    storage.append_lines(p, ["b", "c"])
    assert storage.read_lines(p) == ["a", "b", "c"]


def test_clear_file(tmp_path):
    p = str(tmp_path / "all.txt")
    storage.write_lines(p, ["a", "b"])
    storage.clear_file(p)
    assert storage.read_lines(p) == []


def test_settings_roundtrip(tmp_path):
    p = str(tmp_path / "settings.json")
    storage.save_settings(p, {"attribute": "DBKEY", "limit": 1200})
    assert storage.load_settings(p) == {"attribute": "DBKEY", "limit": 1200}


def test_load_settings_missing_returns_empty(tmp_path):
    assert storage.load_settings(str(tmp_path / "no.json")) == {}
