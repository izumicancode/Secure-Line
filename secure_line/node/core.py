"""LineNode — the networking core: LAN peer discovery, encrypted 1:1
messaging over a per-conversation ratchet, encrypted channel (room)
broadcast, mesh-style relay, and store-and-forward for peers who are
briefly offline. No Tk/UI code lives here; the app talks to a LineNode
purely through thread-safe queues of events.

The actual feature logic is split across sibling files and mixed in
here — discovery.py, messaging.py, channels.py — so adding a new
networking feature means adding a new mixin file instead of growing
this one.
"""
import socket
import threading

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from ..constants import DISCOVERY_PORT, CHAT_PORT_BASE
from ..mesh import SeenCache, RelayQueue
from ..models import Peer
from .discovery import _DiscoveryMixin
from .messaging import _MessagingMixin
from .channels import _ChannelsMixin


class LineNode(_DiscoveryMixin, _MessagingMixin, _ChannelsMixin):
    """One running node: my identity, my known peers, my open ratchets,
    my joined channels. Every public method is safe to call from the Tk
    main thread; every callback fires from a background thread and simply
    appends to `self.events` for the UI to poll on a timer."""

    def __init__(self, name: str, private_key: x25519.X25519PrivateKey):
        self.name = name
        self.private_key = private_key
        self.pub_bytes = private_key.public_key().public_bytes(
            encoding=Encoding.Raw, format=PublicFormat.Raw)

        self.chat_port = CHAT_PORT_BASE + (int.from_bytes(self.pub_bytes[:2], "big") % 100)

        self.peers: dict[str, Peer] = {}
        self.ratchets: dict = {}
        self._ratchets_lock = threading.Lock()
        self.peer_pub: dict[str, bytes] = {}
        # One reused outbound TCP connection per peer (see
        # node/messaging.py _try_deliver) instead of opening a fresh one
        # per message, plus a lock per peer serializing writes to it.
        self._conns: dict = {}
        self._conns_lock = threading.Lock()
        self._send_locks: dict = {}
        # channel_name -> derived AES key (32 bytes), or None for an
        # unlocked/no-password channel (still keyed off the name itself
        # so traffic isn't plaintext-obvious on the wire).
        self.channel_keys: dict[str, bytes] = {}

        self.seen = SeenCache()
        self.relay_queue = RelayQueue()

        self.events: list[dict] = []
        self._events_lock = threading.Lock()

        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

        self._disc_sock = None
        self._chat_srv_sock = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        self._disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                self._disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        self._disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._disc_sock.bind(("", DISCOVERY_PORT))
        self._disc_sock.settimeout(0.5)

        self._chat_srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._chat_srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._chat_srv_sock.bind(("", self.chat_port))
        self._chat_srv_sock.listen(16)
        self._chat_srv_sock.settimeout(0.5)

        self._spawn(self._discovery_listen_loop)
        self._spawn(self._announce_loop)
        self._spawn(self._chat_server_loop)
        self._spawn(self._peer_reaper_loop)
        self._spawn(self._relay_retry_loop)

    def stop(self):
        self._stop.set()
        for sock in (self._disc_sock, self._chat_srv_sock):
            try:
                sock.close()
            except Exception:
                pass
        with self._conns_lock:
            for sock in self._conns.values():
                try:
                    sock.close()
                except Exception:
                    pass
            self._conns.clear()
        for t in self._threads:
            t.join(timeout=1.0)

    def _spawn(self, target):
        t = threading.Thread(target=target, daemon=True)
        t.start()
        self._threads.append(t)

    def _emit(self, kind: str, **data):
        with self._events_lock:
            self.events.append({"kind": kind, **data})

    def poll_events(self) -> list[dict]:
        """Called from the UI thread on a timer; drains and returns
        everything queued since the last call."""
        with self._events_lock:
            out, self.events = self.events, []
        return out
