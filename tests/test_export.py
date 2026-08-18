import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from secure_line.models import ChatEntry
from secure_line.storage.export import export_markdown, export_json, write_export


def _sample_entries():
    return [
        ChatEntry(sender="bob", text="hey there", ts=1700000000, mine=False),
        ChatEntry(sender="me", text="hi bob!", ts=1700000010, mine=True),
        ChatEntry(sender="", text="bob joined the line", ts=1700000005, mine=False, kind="system"),
        ChatEntry(sender="bob", text="", ts=1700000020, mine=False, kind="file",
                   file_path="/tmp/photo.png", file_size=2048),
    ]


def test_export_markdown_contains_all_messages():
    md = export_markdown("bob", _sample_entries())
    assert "hey there" in md
    assert "hi bob!" in md
    assert "bob joined the line" in md
    assert "photo.png" in md
    assert "# Conversation: bob" in md


def test_export_markdown_shows_hop_count():
    entries = [ChatEntry(sender="bob", text="relayed msg", ts=1, mine=False, hops=2)]
    md = export_markdown("bob", entries)
    assert "2 hops" in md


def test_export_json_roundtrips_fields():
    entries = _sample_entries()
    payload = json.loads(export_json("bob", entries))
    assert payload["conversation"] == "bob"
    assert payload["message_count"] == 4
    assert payload["messages"][0]["text"] == "hey there"
    assert payload["messages"][3]["file_path"] == "/tmp/photo.png"


def test_write_export_markdown(tmp_path):
    out = tmp_path / "chat.md"
    write_export(str(out), "bob", _sample_entries(), fmt="markdown")
    content = out.read_text(encoding="utf-8")
    assert "hey there" in content


def test_write_export_json(tmp_path):
    out = tmp_path / "chat.json"
    write_export(str(out), "bob", _sample_entries(), fmt="json")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["message_count"] == 4


def test_write_export_unknown_format_raises(tmp_path):
    import pytest
    out = tmp_path / "chat.txt"
    with pytest.raises(ValueError):
        write_export(str(out), "bob", _sample_entries(), fmt="xml")
