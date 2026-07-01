import query_core as qc


def test_dedup_preserves_order_and_strips_blanks():
    assert qc.dedup_preserve_order([" b ", "a", "b", "", "c", "a"]) == ["b", "a", "c"]


def test_build_query_two_values_single_quotes_no_spaces():
    assert qc.build_query("DBKEY", ["1840833", "1706494"]) == "DBKEY in ('1840833','1706494')"


def test_build_query_single_value():
    assert qc.build_query("DBKEY", ["1840833"]) == "DBKEY in ('1840833')"


def test_query_length_matches_build_query():
    ids = [str(i) for i in range(1000, 1123)]
    assert qc.query_length("DBKEY", ids) == len(qc.build_query("DBKEY", ids))


def test_query_length_empty():
    assert qc.query_length("DBKEY", []) == len("DBKEY in ()")


def test_pack_batch_fills_up_to_limit_in_order():
    pending = ["11", "22", "33", "44"]
    batch = qc.pack_batch(pending, "A", 20)
    assert batch == pending[:len(batch)]                     # order preserved, prefix only
    assert qc.query_length("A", batch) <= 20
    if len(batch) < len(pending):
        assert qc.query_length("A", pending[:len(batch) + 1]) > 20  # one more would overflow


def test_pack_batch_single_id_too_big_returns_empty():
    assert qc.pack_batch(["1840833"], "DBKEY", 10) == []


def test_pending_records_excludes_done_preserves_order():
    assert qc.pending_records(["a", "b", "c", "d"], ["b", "d"]) == ["a", "c"]


def test_count_batches_exact():
    pending = ["11", "22", "33", "44", "55", "66"]
    limit = qc.query_length("A", ["11", "22"])   # exactly fits two per batch
    assert qc.count_batches(pending, "A", limit) == 3


def test_count_batches_none_when_single_too_big():
    assert qc.count_batches(["1840833"], "DBKEY", 10) is None


def test_full_round_trip_reproduces_pending_in_order():
    pending = [str(i) for i in range(1000, 1075)]
    remaining, collected = list(pending), []
    while remaining:
        b = qc.pack_batch(remaining, "COL", 60)
        assert b, "at least one ID must always fit"
        collected.extend(b)
        remaining = remaining[len(b):]
    assert collected == pending      # no gaps, no dupes, original order
