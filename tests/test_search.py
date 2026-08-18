import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from secure_line.models import ChatEntry
from secure_line.storage.search import search_histories, highlight


def _entry(sender, text, ts, mine=False, kind="text", **kw):
    return ChatEntry(sender=sender, text=text, ts=ts, mine=mine, kind=kind, **kw)


def test_search_finds_case_insensitive_match_by_default():
    histories = {
        "bob": [
            _entry("bob", "let's meet at the Lighthouse", 1),
            _entry("me", "sounds good", 2, mine=True),
        ]
    }
    results = search_histories(histories, "lighthouse")
    assert len(results) == 1
    assert results[0].conversation == "bob"


def test_search_case_sensitive():
    histories = {"bob": [_entry("bob", "Hello there", 1)]}
    assert len(search_histories(histories, "hello", case_sensitive=True)) == 0
    assert len(search_histories(histories, "Hello", case_sensitive=True)) == 1


def test_search_orders_newest_first():
    histories = {
        "bob": [
            _entry("bob", "apple one", 1),
            _entry("bob", "apple two", 5),
            _entry("bob", "apple three", 3),
        ]
    }
    results = search_histories(histories, "apple")
    timestamps = [r.entry.ts for r in results]
    assert timestamps == sorted(timestamps, reverse=True)


def test_search_across_multiple_conversations():
    histories = {
        "bob": [_entry("bob", "shared secret plan", 1)],
        "#general": [_entry("carol", "another plan here", 2, channel="#general")],
    }
    results = search_histories(histories, "plan")
    convos = {r.conversation for r in results}
    assert convos == {"bob", "#general"}


def test_search_respects_limit():
    histories = {"bob": [_entry("bob", f"msg {i} apple", i) for i in range(10)]}
    results = search_histories(histories, "apple", limit=3)
    assert len(results) == 3


def test_search_empty_query_returns_nothing():
    histories = {"bob": [_entry("bob", "hello", 1)]}
    assert search_histories(histories, "") == []


def test_search_matches_file_path():
    histories = {"bob": [_entry("bob", "", 1, kind="file", file_path="/tmp/vacation-photo.png")]}
    results = search_histories(histories, "vacation")
    assert len(results) == 1


def test_highlight_splits_matches():
    segments = highlight("hello world hello", "hello")
    matched = [s for s, is_match in segments if is_match]
    assert matched == ["hello", "hello"]


def test_highlight_empty_query_returns_whole_string_unmatched():
    segments = highlight("hello", "")
    assert segments == [("hello", False)]
