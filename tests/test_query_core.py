import query_core as qc


def test_dedup_preserves_order_and_strips_blanks():
    assert qc.dedup_preserve_order([" b ", "a", "b", "", "c", "a"]) == ["b", "a", "c"]


def test_build_query_two_values_single_quotes_no_spaces():
    assert qc.build_query("DBKEY", ["1840833", "1706494"]) == "DBKEY in ('1840833','1706494')"


def test_build_query_single_value():
    assert qc.build_query("DBKEY", ["1840833"]) == "DBKEY in ('1840833')"
