"""Export a conversation's chat history to a plain file the user controls
— Markdown for reading, JSON for anything programmatic. This is an
explicit, user-initiated local-decrypt-then-write operation: nothing
here is called automatically, and it never touches the network. Files
referenced by "file" entries are *not* copied — the export just notes
their local path, since attachments already live under
line_data/{sent,received}_files/ and copying them again would just
duplicate disk usage.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from ..models import ChatEntry


def _ts(entry: "ChatEntry") -> str:
    return datetime.fromtimestamp(entry.ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def export_markdown(conversation: str, entries: list, *, my_name: str = "me") -> str:
    """Render a conversation as a Markdown transcript."""
    lines = [f"# Conversation: {conversation}", "", f"_Exported {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_", ""]
    for e in entries:
        who = my_name if e.mine else e.sender
        if e.kind == "system":
            lines.append(f"> *{e.text}*  \n> `{_ts(e)}`")
        elif e.kind == "file":
            size_kb = (e.file_size or 0) / 1024
            lines.append(f"**{who}** ({_ts(e)}): 📎 `{e.file_path}` ({size_kb:.1f} KB)")
        else:
            hop_note = f" _(relayed, {e.hops} hop{'s' if e.hops != 1 else ''})_" if e.hops else ""
            lines.append(f"**{who}** ({_ts(e)}){hop_note}: {e.text}")
        lines.append("")
    return "\n".join(lines)


def export_json(conversation: str, entries: list) -> str:
    """Render a conversation as a JSON array, one object per entry."""
    payload = {
        "conversation": conversation,
        "exported_at": time.time(),
        "message_count": len(entries),
        "messages": [
            {
                "sender": e.sender,
                "text": e.text,
                "ts": e.ts,
                "mine": e.mine,
                "kind": e.kind,
                "status": e.status,
                "file_path": e.file_path,
                "file_size": e.file_size,
                "file_mime": e.file_mime,
                "channel": e.channel,
                "hops": e.hops,
            }
            for e in entries
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def write_export(path: str, conversation: str, entries: list, *, fmt: str = "markdown",
                  my_name: str = "me") -> None:
    """Write an export to `path`. `fmt` is 'markdown' or 'json'."""
    if fmt == "json":
        content = export_json(conversation, entries)
    elif fmt == "markdown":
        content = export_markdown(conversation, entries, my_name=my_name)
    else:
        raise ValueError(f"unknown export format: {fmt!r}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
