from collections import deque

from obsiflask.hint import NaiveStringIndex, HintIndex


def test_update_index_rebuild_and_state_change():
    idx = NaiveStringIndex(ngram_order=2, max_ngrams=5, max_ratio_in_ngram=0.9)
    idx.update_index({"foo", "bar"})
    state1 = idx.current_state
    assert isinstance(state1, int)
    idx.update_index({"foo", "bar"})
    assert idx.current_state == state1


def test_update_index_no_reset_on_same_strings_deep():
    idx = NaiveStringIndex(ngram_order=2,
                           max_ngrams=10,
                           max_ratio_in_ngram=0.9)
    strings = {"foo", "bar", "baz"}
    idx.update_index(strings)

    state_before = idx.current_state
    ngrams_before = idx.ngrams_to_strings
    sets_ids_before = {k: id(v) for k, v in ngrams_before.items()}

    idx.update_index(strings)
    assert idx.current_state == state_before
    # referene is the same
    assert idx.ngrams_to_strings is ngrams_before
    # no recreation
    sets_ids_after = {k: id(v) for k, v in idx.ngrams_to_strings.items()}
    assert sets_ids_before == sets_ids_after


def test_search_too_short_query_returns_list():
    idx = NaiveStringIndex(2, 5, 0.9)
    idx.update_index({"foo", "bar"})
    res = idx.search("f")
    assert res == ([], 0)


def test_search_with_match_returns_best_candidates():
    idx = NaiveStringIndex(2, 10, 1.0)
    idx.update_index({"foo", "food"})
    results = idx.search("foo")
    assert isinstance(results, tuple)
    candidates, best = results
    assert best > 0
    assert any(c[0] in ("foo", "food") for c in candidates)


def test_hint_index_populate_and_update_file():
    h = HintIndex(ngram_order=2, max_ngrams=5, max_ratio_in_ngram=0.9)
    h.populate_default_files(None, ["a.md", "b.md"])
    assert isinstance(h.default_files_per_user[None], deque)
    assert list(h.default_files_per_user[None]) == ["a.md", "b.md"]

    h.update_file("c.md")
    assert h.default_files_per_user[None][0] == "c.md"

    h.update_file("a.md")
    assert h.default_files_per_user[None][0] == "a.md"
