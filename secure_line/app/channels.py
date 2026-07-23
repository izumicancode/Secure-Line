"""LineApp mixin: joining/creating a channel (with an optional shared
password), switching the chat pane into a channel, and leaving/deleting
one -- only the local creator of a channel gets a delete button; everyone
else only ever sees leave. See node/channels.py for the trust model
behind "creator"."""
from tkinter import messagebox, simpledialog

from ..constants import DEFAULT_CHANNEL
from ..crypto import derive_channel_key, channel_fingerprint
from ..models import Channel
from ..netutils import valid_channel_name, normalize_channel_name


class _ChannelsMixin:
    def _open_join_channel_dialog(self):
        raw = simpledialog.askstring("Join / create channel", "Channel name (e.g. #general):",
                                      parent=self.root)
        if not raw:
            return
        name = normalize_channel_name(raw)
        if not valid_channel_name(name):
            messagebox.showerror("Invalid name", "Channel names: 2-24 chars, letters/numbers/-_.")
            return
        password = simpledialog.askstring(
            "Channel password",
            "Optional password (leave blank for an open channel).\n"
            "Anyone with the same name+password can read this channel.",
            parent=self.root, show="•")
        # Only claim creator if this is genuinely new to us locally -- if we
        # already have a record for this channel (e.g. restored from our own
        # store, or we already learned a creator for it from the network),
        # re-joining shouldn't silently overwrite that.
        is_new_to_us = name not in self.channels
        self._join_channel_internal(name, password or None, persist=True,
                                     creator=(self.name if is_new_to_us else None))
        self._render_sidebar()
        self._open_channel(name)

    def _join_channel_internal(self, name, password, persist, creator=None):
        key = derive_channel_key(name, password or "")
        self.node.set_channel_key(name, key)
        existing = self.channels.get(name)
        resolved_creator = creator if creator is not None else (existing.creator if existing else "")
        self.channels[name] = Channel(name=name, has_password=bool(password), creator=resolved_creator)
        self.histories.setdefault(f"ch:{name}", [])
        if persist:
            self._save_store()

    def _open_channel(self, name):
        if name is None:
            return
        self.active_channel = name
        self.active_chat = None
        ch = self.channels.get(name)
        if ch:
            ch.unread = 0
        self.chat_title_var.set(name)
        pw_tag = "password-protected" if ch and ch.has_password else "open"
        cf = channel_fingerprint(name, "") if not (ch and ch.has_password) else "•• locked ••"
        subtitle = f"{pw_tag} channel"
        if ch and ch.creator:
            subtitle += f"  ·  created by {ch.creator}"
        self.chat_subtitle_var.set(subtitle)
        self.verify_btn.pack_forget()
        self._render_sidebar()
        self._render_messages()

    # ------------------------------------------------------------------
    # Leaving / deleting
    # ------------------------------------------------------------------
    def _channel_action_prompt(self, name):
        """Creator sees a delete confirmation (which notifies other online
        members); everyone else sees a plain leave confirmation."""
        ch = self.channels.get(name)
        if ch is None:
            return
        is_creator = bool(ch.creator) and ch.creator == self.name
        if is_creator:
            if messagebox.askyesno(
                    "Delete channel",
                    f"Delete {name}? You created this channel -- deleting it removes it from "
                    "your device and lets other members currently online know it's gone. "
                    "This can't be undone."):
                self._leave_channel(name, broadcast_disband=True)
        else:
            if messagebox.askyesno(
                    "Leave channel",
                    f"Leave {name}? You can rejoin later with its name (and password, if any)."):
                self._leave_channel(name, broadcast_disband=False)

    def _leave_channel(self, name, broadcast_disband=False):
        ch = self.channels.get(name)
        if ch is None:
            return
        if broadcast_disband and ch.creator == self.name:
            try:
                self.node.send_channel_disband(name)
            except Exception:
                pass
        self.node.set_channel_key(name, None)
        del self.channels[name]
        self.histories.pop(f"ch:{name}", None)
        if self.active_channel == name:
            self.active_channel = None
            self.chat_title_var.set("")
            self.chat_subtitle_var.set("")
            self._render_messages()
        if not self.channels:
            # Never leave the app with zero channels -- fall back to the
            # system default, same as a fresh account gets on first login.
            self._join_channel_internal(DEFAULT_CHANNEL, password=None, persist=True, creator="")
            self._open_channel(DEFAULT_CHANNEL)
        self._render_sidebar()
        self._save_store()
