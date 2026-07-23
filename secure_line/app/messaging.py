"""LineApp mixin: sending DMs/channel posts, file & folder attachments
(DMs and channels both), and rendering the message list (bubbles, file
cards, system pills, mention highlight).

File handling in one sentence: whatever gets sent is *also* saved to a
local folder (line_data/sent_files for outgoing, line_data/received_files
for incoming) and every file ChatEntry remembers that path, so "Open" and
"Save As..." always have a real file to act on -- not just a filename
string in a chat bubble.
"""
import base64
import io
import mimetypes
import os
import shutil
import subprocess
import sys
import threading
import time
import re
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox

from ..constants import MAX_FILE_SIZE, SENT_FILES_DIRNAME, STORE_ROOT, IMAGE_THUMB_MIMES
from ..models import ChatEntry
from ..theme import *  # noqa: F401,F403
from ..widgets import (
    make_chat_bubble, make_pill, make_attach_menu, make_file_card,
    make_thumbnail_image, human_file_size, ask_path,
)

MENTION_RE = re.compile(r"@([A-Za-z0-9\-_.]{2,24})")


def _extract_mentions(text: str) -> tuple:
    return tuple(sorted(set(MENTION_RE.findall(text))))


def _zip_folder(folder_path: str) -> tuple:
    """Zips a folder in memory, preserving its internal structure. Returns
    (raw_zip_bytes, download_name)."""
    base_name = os.path.basename(os.path.normpath(folder_path)) or "folder"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(folder_path):
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, folder_path)
                zf.write(full, arcname=os.path.join(base_name, rel))
    return buf.getvalue(), f"{base_name}.zip"


def _unique_path(folder: str, filename: str) -> str:
    """Avoids clobbering an existing file with the same name -- appends
    ' (2)', ' (3)', etc. before the extension."""
    safe_name = os.path.basename(filename) or "file"
    stem, ext = os.path.splitext(safe_name)
    candidate = os.path.join(folder, safe_name)
    n = 2
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem} ({n}){ext}")
        n += 1
    return candidate


class _MessagingMixin:
    def _open_dm(self, peer_name):
        self.active_chat = peer_name
        self.active_channel = None
        self.dm_unread.pop(peer_name, None)
        self.chat_title_var.set(peer_name)
        peer = self.node.peers.get(peer_name)
        hop_note = "direct" if (peer and peer.hops == 0) else f"via mesh, {peer.hops if peer else '?'} hop(s)"
        verified = peer_name in self.store.get("verified", [])
        self.chat_subtitle_var.set(f"{hop_note}{'  ✓ verified' if verified else ''}")
        if verified:
            self.verify_btn.pack_forget()
        else:
            self.verify_btn.pack(side="right", padx=10)
        self._render_sidebar()
        self._render_messages()

    def _history_key(self):
        if self.active_chat:
            return f"dm:{self.active_chat}"
        if self.active_channel:
            return f"ch:{self.active_channel}"
        return None

    def _send_current(self):
        text = self.compose_var.get().strip()
        if not text:
            return
        self.compose_var.set("")
        mentions = _extract_mentions(text)
        if self.active_chat:
            # send_dm does a live TCP connect + send. Doing that on the Tk
            # main thread meant the message bubble wouldn't even appear
            # until the network attempt finished -- and if the peer was
            # slow to reach or briefly unreachable, the whole app would
            # visibly stall on every single message. Channel text doesn't
            # have this problem (it's a non-blocking UDP broadcast below),
            # so only the DM path needs to move to a background thread.
            peer_name = self.active_chat
            threading.Thread(target=self._send_dm_worker, args=(peer_name, text, mentions),
                              daemon=True).start()
        elif self.active_channel:
            ch = self.channels.get(self.active_channel)
            creator = ch.creator if ch else ""
            try:
                mid = self.node.send_channel_message(self.active_channel, text, creator=creator)
            except KeyError:
                messagebox.showerror("Not joined", "Join this channel again to send.")
                return
            entry = ChatEntry(sender=self.name, text=text, ts=time.time(), mine=True,
                               mid=mid, channel=self.active_channel, mentions=mentions,
                               ephemeral=self.ephemeral_mode)
            self._append_entry(f"ch:{self.active_channel}", entry)

    def _send_dm_worker(self, peer_name, text, mentions):
        try:
            mid, status = self.node.send_dm(peer_name, text)
        except KeyError:
            self.root.after(0, lambda: messagebox.showerror(
                "Can't reach peer", f"{peer_name} hasn't been discovered yet -- try again in a moment."))
            return

        def finish():
            entry = ChatEntry(sender=self.name, text=text, ts=time.time(), mine=True,
                               mid=mid, status=status, mentions=mentions,
                               ephemeral=self.ephemeral_mode)
            self._append_entry(f"dm:{peer_name}", entry)
        self.root.after(0, finish)

    # ------------------------------------------------------------------
    # Attachments -- available in both DMs and channels
    # ------------------------------------------------------------------
    def _attach_file(self):
        if not self.active_chat and not self.active_channel:
            messagebox.showinfo("Select a chat", "Open a direct chat or a channel to send a file.")
            return
        make_attach_menu(self.root, self.attach_btn,
                          on_file=self._pick_and_send_file,
                          on_folder=self._pick_and_send_folder)

    def _pick_and_send_file(self):
        path = ask_path(self.root, mode="file")
        if not path:
            return
        # Reading, zipping, and encrypting a large file on the Tk main
        # thread used to freeze the whole app for the entire send --
        # including the timer that polls for *incoming* messages, so
        # nothing else could arrive or render until the send finished.
        # Do the heavy lifting on a background thread instead; only the
        # final UI update is marshalled back onto the main thread.
        target = self._current_send_target()
        threading.Thread(target=self._send_file_worker, args=(path, target), daemon=True).start()

    def _pick_and_send_folder(self):
        path = ask_path(self.root, mode="folder")
        if not path:
            return
        target = self._current_send_target()
        threading.Thread(target=self._send_folder_worker, args=(path, target), daemon=True).start()

    def _current_send_target(self):
        """Snapshots which chat an attachment is headed for at the moment
        the user picked it, so the send still goes to the right place
        even if they switch chats before it finishes."""
        if self.active_chat:
            return ("dm", self.active_chat, "")
        ch = self.channels.get(self.active_channel) if self.active_channel else None
        return ("channel", self.active_channel, ch.creator if ch else "")

    def _send_file_worker(self, path, target):
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as e:
            self.root.after(0, lambda: messagebox.showerror("Read error", str(e)))
            return
        self._send_raw_attachment(raw, os.path.basename(path), target)

    def _send_folder_worker(self, path, target):
        try:
            raw, filename = _zip_folder(path)
        except OSError as e:
            self.root.after(0, lambda: messagebox.showerror("Read error", str(e)))
            return
        self._send_raw_attachment(raw, filename, target)

    def _send_raw_attachment(self, raw: bytes, filename: str, target):
        # Runs on a background thread (see _pick_and_send_file/_folder).
        # node.send_dm / node.send_channel_file / self._emit-style event
        # paths are already thread-safe; only the final histories/UI
        # update needs to be handed back to the main thread via `after`.
        size = len(raw)
        if size > MAX_FILE_SIZE:
            self.root.after(0, lambda: messagebox.showerror(
                "Too large", f"Attachments are capped at {human_file_size(MAX_FILE_SIZE)}."))
            return

        # Save our own copy first -- this is what makes "Open" / "Save As"
        # on the sender's own bubble actually work, and means the send
        # doesn't depend on the original file staying put on disk.
        sent_dir = os.path.join(STORE_ROOT, SENT_FILES_DIRNAME)
        os.makedirs(sent_dir, exist_ok=True)
        local_path = _unique_path(sent_dir, filename)
        try:
            with open(local_path, "wb") as f:
                f.write(raw)
        except OSError as e:
            self.root.after(0, lambda: messagebox.showerror("Couldn't save locally", str(e)))
            return
        mime = mimetypes.guess_type(filename)[0] or ""

        kind, name, creator = target
        if kind == "dm":
            payload = base64.b64encode(raw).decode("ascii") + "||" + filename
            mid, status = self.node.send_dm(name, payload, kind="file")

            def finish():
                entry = ChatEntry(sender=self.name, text=filename, ts=time.time(), mine=True,
                                   kind="file", mid=mid, file_size=size, file_path=local_path,
                                   file_mime=mime, status=status, ephemeral=self.ephemeral_mode)
                self._append_entry(f"dm:{name}", entry)
            self.root.after(0, finish)
        elif kind == "channel":
            try:
                mid, delivered = self.node.send_channel_file(name, filename, raw, creator=creator)
            except KeyError:
                self.root.after(0, lambda: messagebox.showerror(
                    "Not joined", "Join this channel again to send."))
                return

            def finish():
                status = f"sent · {delivered} online" if delivered else "sent · no one online yet"
                entry = ChatEntry(sender=self.name, text=filename, ts=time.time(), mine=True,
                                   kind="file", mid=mid, file_size=size, file_path=local_path,
                                   file_mime=mime, channel=name,
                                   status=status, ephemeral=self.ephemeral_mode)
                self._append_entry(f"ch:{name}", entry)
            self.root.after(0, finish)

    def _append_entry(self, key, entry: ChatEntry):
        self.histories.setdefault(key, []).append(entry)
        if key == self._history_key():
            self._render_messages()
        if not entry.ephemeral:
            self._save_store()

    # ------------------------------------------------------------------
    # Open / Save As -- works for both sent and received files, since
    # both get a real local file_path the moment they're sent/received.
    # ------------------------------------------------------------------
    def _open_file_entry(self, entry: ChatEntry):
        if not entry.file_path or not os.path.isfile(entry.file_path):
            messagebox.showerror("File unavailable", "This file isn't available on this device anymore.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(entry.file_path)  # noqa: F821 -- Windows-only builtin
            elif sys.platform == "darwin":
                subprocess.Popen(["open", entry.file_path])
            else:
                subprocess.Popen(["xdg-open", entry.file_path])
        except Exception as e:
            messagebox.showerror("Couldn't open file", str(e))

    def _save_file_entry_as(self, entry: ChatEntry):
        if not entry.file_path or not os.path.isfile(entry.file_path):
            messagebox.showerror("File unavailable", "This file isn't available on this device anymore.")
            return
        base = os.path.basename(entry.file_path)
        stem, ext = os.path.splitext(base)
        dest = filedialog.asksaveasfilename(title="Save as", initialfile=base,
                                             defaultextension=ext or None)
        if not dest:
            return
        try:
            shutil.copyfile(entry.file_path, dest)
        except OSError as e:
            messagebox.showerror("Couldn't save file", str(e))

    # ------------------------------------------------------------------
    # Message rendering
    # ------------------------------------------------------------------
    def _render_messages(self):
        for w in self.msg_frame.winfo_children():
            w.destroy()
        key = self._history_key()
        if key is None:
            return
        for entry in self.histories.get(key, [])[-400:]:
            self._render_one_entry(entry)
        self.root.after(30, lambda: self.msg_canvas.yview_moveto(1.0))

    def _render_one_entry(self, entry: ChatEntry):
        row = tk.Frame(self.msg_frame, bg=VOID)
        row.pack(fill="x", pady=3, padx=12)
        if entry.kind == "system":
            make_pill(row, entry.text, TEXT_DIM, HULL_SOFT, 500).pack()
            return

        anchor_side = "e" if entry.mine else "w"
        wrap = tk.Frame(row, bg=VOID)
        wrap.pack(anchor=anchor_side)
        if not entry.mine and entry.channel:
            tk.Label(wrap, text=entry.sender, font=MONO_SMALL, bg=VOID, fg=TEXT_DIM,
                     anchor="w").pack(anchor="w")

        if entry.kind == "file":
            available = bool(entry.file_path) and os.path.isfile(entry.file_path)
            thumb = None
            if available and entry.file_mime in IMAGE_THUMB_MIMES:
                thumb = self._thumb_cache.get(entry.file_path)
                if thumb is None:
                    thumb = make_thumbnail_image(entry.file_path)
                    if thumb is not None:
                        self._thumb_cache[entry.file_path] = thumb
            card = make_file_card(
                wrap, entry.text, human_file_size(entry.file_size), entry.mine,
                thumbnail_photo=thumb, bg_behind=VOID, available=available,
                on_open=lambda e=entry: self._open_file_entry(e),
                on_save=lambda e=entry: self._save_file_entry_as(e),
            )
            card.pack(anchor=anchor_side)
        else:
            mention = self.name in entry.mentions
            canvas_w = self.msg_canvas.winfo_width() or 900
            max_w = max(220, min(560, canvas_w - 180))
            bubble = make_chat_bubble(wrap, entry.text, entry.mine, max_width=max_w,
                                       hops=entry.hops, mention=mention)
            bubble.pack(anchor=anchor_side)

        meta = time.strftime("%H:%M", time.localtime(entry.ts))
        if entry.mine and entry.status:
            meta += f"  ·  {entry.status}"
        tk.Label(wrap, text=meta, font=MONO_SMALL, bg=VOID, fg=TEXT_FAINT).pack(anchor=anchor_side)
