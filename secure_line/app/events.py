"""LineApp mixin: polls LineNode's thread-safe event queue on a Tk timer
and turns network events into UI updates -- new peers, incoming DMs,
channel posts and files, delivery/read receipts, channel disbands, and
incoming file saves (DM or channel, both land on disk the same way and
get a real file_path so Open/Save As always has something to act on)."""
import base64
import mimetypes
import os
import time

from ..constants import MSG_POLL_MS, RECEIVED_FILES_DIRNAME, STORE_ROOT
from ..models import ChatEntry
from .messaging import _extract_mentions, _unique_path


class _EventsMixin:
    def _poll_loop(self):
        for ev in self.node.poll_events():
            self._handle_event(ev)
        self.root.after(MSG_POLL_MS, self._poll_loop)

    def _handle_event(self, ev: dict):
        kind = ev["kind"]
        if kind == "peer_update":
            self._render_peers()
        elif kind == "dm_received":
            peer = ev["peer"]
            text = ev["text"]
            msg_kind = ev.get("msg_kind", "text")
            if msg_kind == "file" and "||" in text:
                b64_data, filename = text.split("||", 1)
                path, size = self._save_incoming_file(filename, b64_data)
                entry = ChatEntry(sender=peer, text=filename, ts=time.time(), mine=False,
                                   kind="file", mid=ev.get("mid", ""), file_path=path,
                                   file_size=size, file_mime=mimetypes.guess_type(filename)[0] or "",
                                   ephemeral=self.ephemeral_mode)
            else:
                entry = ChatEntry(sender=peer, text=text, ts=time.time(), mine=False,
                                   mid=ev.get("mid", ""), mentions=_extract_mentions(text),
                                   ephemeral=self.ephemeral_mode)
            self._append_entry(f"dm:{peer}", entry)
            if peer != self.active_chat:
                self.dm_unread[peer] = self.dm_unread.get(peer, 0) + 1
                self._render_sidebar()
        elif kind == "channel_message":
            channel = ev["channel"]
            ch = self.channels.get(channel)
            self._maybe_learn_creator(ch, ev.get("creator", ""))
            entry = ChatEntry(sender=ev["sender"], text=ev["text"], ts=time.time(), mine=False,
                               channel=channel, hops=ev.get("hops", 0), mid=ev.get("mid", ""),
                               mentions=_extract_mentions(ev["text"]), ephemeral=self.ephemeral_mode)
            self._append_entry(f"ch:{channel}", entry)
            if ch and channel != self.active_channel:
                ch.unread += 1
                self._render_sidebar()
        elif kind == "channel_file_received":
            channel = ev["channel"]
            ch = self.channels.get(channel)
            self._maybe_learn_creator(ch, ev.get("creator", ""))
            filename = ev["filename"]
            path, size = self._save_incoming_file(filename, ev["data"])
            entry = ChatEntry(sender=ev["sender"], text=filename, ts=time.time(), mine=False,
                               kind="file", mid=ev.get("mid", ""), channel=channel, file_path=path,
                               file_size=size, file_mime=mimetypes.guess_type(filename)[0] or "",
                               ephemeral=self.ephemeral_mode)
            self._append_entry(f"ch:{channel}", entry)
            if ch and channel != self.active_channel:
                ch.unread += 1
                self._render_sidebar()
        elif kind == "channel_disbanded":
            self._handle_channel_disbanded(ev["channel"], ev.get("by", ""))
        elif kind == "dm_status":
            self._update_status(ev["peer"], ev["mid"], ev["status"])
        elif kind == "receipt":
            self._update_status(ev["peer"], ev["mid"], ev["status"])

    def _maybe_learn_creator(self, ch, creator_hint: str):
        """Trust-on-first-use: only ever adopt a creator name for a channel
        we don't already have one recorded for. Never overwrites -- can't
        be used to hijack the delete button away from (or onto) anyone."""
        if ch is not None and not ch.creator and creator_hint:
            ch.creator = creator_hint

    def _handle_channel_disbanded(self, channel, by):
        ch = self.channels.get(channel)
        # Only honor this if the sender is the creator *we already
        # recorded* for this channel -- an unknown/unverified claim of
        # "I'm the creator, delete yourself" is ignored.
        if not ch or not ch.creator or ch.creator != by:
            return
        entry = ChatEntry(sender="system", text=f"{channel} was deleted by its creator ({by}).",
                           ts=time.time(), mine=False, kind="system", channel=channel)
        self._append_entry(f"ch:{channel}", entry)
        self._leave_channel(channel, broadcast_disband=False)

    def _update_status(self, peer, mid, status):
        key = f"dm:{peer}"
        for entry in self.histories.get(key, []):
            if entry.mid == mid:
                entry.status = status
        if key == self._history_key():
            self._render_messages()

    def _save_incoming_file(self, filename, b64_data):
        """Decodes and writes an incoming attachment to disk. Returns
        (path, size) -- (\"\", 0) if it couldn't be decoded/saved, in
        which case the resulting ChatEntry just shows as unavailable."""
        try:
            raw = base64.b64decode(b64_data)
        except Exception:
            return "", 0
        folder = os.path.join(STORE_ROOT, RECEIVED_FILES_DIRNAME)
        os.makedirs(folder, exist_ok=True)
        path = _unique_path(folder, filename)
        try:
            with open(path, "wb") as f:
                f.write(raw)
        except OSError:
            return "", 0
        return path, len(raw)
