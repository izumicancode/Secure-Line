"""Local, offline search over a decrypted chat history list.

This never touches the network or re-encrypts anything — it operates on
the same in-memory `ChatEntry` objects the app already holds after
`load_store` + reconstruction, and is used by the search bar in the UI
(`app/messaging.py`) as well as being usable standalone/for tests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import ChatEntry


@dataclass
class SearchResult:
    entry: "ChatEntry"
    conversation: str   # peer callsign or "#channel" this entry belongs to
    index: int          # position of the entry within that conversation's history list


def _matches(text: str, needle: str, case_sensitive: bool) -> bool:
    if not case_sensitive:
        return needle in text.lower()
    return needle in text


def search_histories(histories: dict, query: str, *, case_sensitive: bool = False,
                      kinds: tuple = ("text", "file"), limit: int = 200) -> list[SearchResult]:
    """Search across every conversation's history.

    `histories` maps a conversation key (peer callsign, or a channel name
    like "#general") to a list of ChatEntry objects, matching the shape
    the app already keeps in memory. Returns matches ordered newest-first,
    capped at `limit` so a broad query on a huge history stays cheap.
    """
    query = query if case_sensitive else query.lower()
    if not query:
        return []
    results: list[SearchResult] = []
    for convo, entries in histories.items():
        for i, entry in enumerate(entries):
            if entry.kind not in kinds:
                continue
            haystack = entry.text if entry.kind == "text" else (entry.file_path or "")
            haystack_name = getattr(entry, "file_path", "") or ""
            if _matches(entry.text or "", query, case_sensitive) or \
               (entry.kind == "file" and _matches(haystack_name, query, case_sensitive)):
                results.append(SearchResult(entry=entry, conversation=convo, index=i))
    results.sort(key=lambda r: r.entry.ts, reverse=True)
    return results[:limit]


def highlight(text: str, query: str, *, case_sensitive: bool = False) -> list[tuple[str, bool]]:
    """Split `text` into (chunk, is_match) segments for a UI to bold/highlight.
    Empty query returns the whole string as a single non-match segment."""
    if not query:
        return [(text, False)]
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)
    segments: list[tuple[str, bool]] = []
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            segments.append((text[pos:m.start()], False))
        segments.append((text[m.start():m.end()], True))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], False))
    return segments or [(text, False)]
