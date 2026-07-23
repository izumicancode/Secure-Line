"""LineApp — owns the single LineNode for the session, login/boot,
persisting local state, and combining every feature mixin (layout,
sidebar, channels, messaging, events, safety) into the one running app.
All networking happens on background threads and is only ever touched
here through `node.poll_events()`.
"""
from ..constants import DEFAULT_CHANNEL, EPHEMERAL_DEFAULT
from ..crypto import b64e, b64d
from ..models import Profile, Channel, ChatEntry
from ..node import LineNode
from ..theme import VOID
from .. import storage
from .login import LoginScreen
from .layout import _LayoutMixin
from .sidebar import _SidebarMixin
from .channels import _ChannelsMixin
from .messaging import _MessagingMixin
from .events import _EventsMixin
from .safety import _SafetyMixin


def _ratchet_state_to_store(state: dict) -> dict:
    """Make a Ratchet state JSON-safe without putting raw key material in
    the application data structure by accident."""
    return {
        "send_chain": b64e(state["send_chain"]),
        "recv_chain": b64e(state["recv_chain"]),
        "send_n": state["send_n"],
        "recv_n": state["recv_n"],
        "skipped": {str(n): b64e(key) for n, key in state["skipped"].items()},
    }


def _ratchet_state_from_store(state: dict) -> dict:
    """Decode and validate the serialized form before giving it to Ratchet."""
    return {
        "send_chain": b64d(state["send_chain"]),
        "recv_chain": b64d(state["recv_chain"]),
        "send_n": int(state["send_n"]),
        "recv_n": int(state["recv_n"]),
        "skipped": {int(n): b64d(key) for n, key in state.get("skipped", {}).items()},
    }


class LineApp(_LayoutMixin, _SidebarMixin, _ChannelsMixin, _MessagingMixin,
              _EventsMixin, _SafetyMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("Line")
        self.root.configure(bg=VOID)
        self.root.geometry("1040x680")
        self.root.minsize(760, 480)

        self.name = None
        self.private_key = None
        self.node: LineNode | None = None
        self.store = {}
        self.profile = Profile()

        self.active_chat = None       # peer name, when in a DM
        self.active_channel = None    # channel name (with '#'), when in a room
        self.histories = {}           # key ("dm:name" / "ch:#name") -> list[ChatEntry]
        self.channels = {}            # "#name" -> Channel
        self.favorites = set()
        self.dm_unread = {}            # peer name -> count of unread DMs (sidebar red dot)
        self._thumb_cache = {}        # file_path -> PhotoImage, kept alive across re-renders
        self.ephemeral_mode = EPHEMERAL_DEFAULT

        self._panic_taps = []

        LoginScreen(self.root, self._on_login)

    # ------------------------------------------------------------------
    # Login -> boot the node + restore local state
    # ------------------------------------------------------------------
    def _on_login(self, name, private_key):
        self.name = name
        self.private_key = private_key
        self.store = storage.load_store(name, private_key)
        self.ephemeral_mode = bool(self.store.get("ephemeral_mode", EPHEMERAL_DEFAULT))
        self.favorites = set(self.store.get("favorites", []))
        prof = self.store.get("profile")
        if prof:
            self.profile = Profile.from_dict(prof)

        self.node = LineNode(name, private_key)
        self.node.start()

        # A DM chain advances independently on each device. Restoring it
        # is essential: resetting our counter after an app restart makes a
        # peer that stayed online treat every new message as a replay.
        for peer_name, saved_state in self.store.get("ratchets", {}).items():
            try:
                self.node.restore_ratchet_state(peer_name, _ratchet_state_from_store(saved_state))
            except (KeyError, TypeError, ValueError):
                # A malformed/old entry must not block login. A fresh
                # conversation can still be established for that peer.
                continue

        for ch_dict in self.store.get("channels", []):
            ch = Channel.from_dict(ch_dict)
            self.channels[ch.name] = ch
            key = self.store.get("channel_keys", {}).get(ch.name)
            if key:
                self.node.set_channel_key(ch.name, b64d(key))

        for key, entries in self.store.get("histories", {}).items():
            self.histories[key] = [self._entry_from_dict(d) for d in entries]

        if not self.channels:
            self._join_channel_internal(DEFAULT_CHANNEL, password=None, persist=True, creator="")

        self._build_main_ui()
        self._save_store()
        self._poll_loop()

    def _save_store(self):
        if self.node is None:
            return
        data = {
            "profile": self.profile.to_dict(),
            "favorites": list(self.favorites),
            "ephemeral_mode": self.ephemeral_mode,
            "channels": [c.to_dict() for c in self.channels.values()],
            "channel_keys": {name: b64e(key) for name, key in self.node.channel_keys.items()},
            "ratchets": {
                peer_name: _ratchet_state_to_store(state)
                for peer_name, state in self.node.export_ratchets().items()
            },
            # Every message remembers its own ephemeral flag from the moment it was
            # sent/received, so toggling the header switch mid-session never leaks
            # earlier ephemeral messages into the store, and never silently drops
            # earlier persisted ones either -- each entry is judged on its own flag,
            # not on whatever the toggle happens to be set to right now.
            "histories": {
                key: [self._entry_to_dict(e) for e in entries[-2000:] if not e.ephemeral]
                for key, entries in self.histories.items()
            },
        }
        storage.save_store(self.name, self.private_key, data)

    @staticmethod
    def _entry_to_dict(e: ChatEntry) -> dict:
        return {
            "sender": e.sender, "text": e.text, "ts": e.ts, "mine": e.mine, "kind": e.kind,
            "mid": e.mid, "status": e.status, "channel": e.channel, "hops": e.hops,
            "mentions": list(e.mentions), "file_path": e.file_path, "file_size": e.file_size,
            "file_mime": e.file_mime,
        }

    @staticmethod
    def _entry_from_dict(d: dict) -> ChatEntry:
        return ChatEntry(
            sender=str(d.get("sender", "")), text=str(d.get("text", "")),
            ts=float(d.get("ts", 0.0)), mine=bool(d.get("mine", False)),
            kind=str(d.get("kind", "text")), mid=str(d.get("mid", "")),
            status=str(d.get("status", "")), channel=str(d.get("channel", "")),
            hops=int(d.get("hops", 0)), mentions=tuple(d.get("mentions", []) or ()),
            file_path=str(d.get("file_path", "")), file_size=int(d.get("file_size", 0)),
            file_mime=str(d.get("file_mime", "")),
            ephemeral=False,  # only non-ephemeral entries are ever persisted -- see _save_store
        )
