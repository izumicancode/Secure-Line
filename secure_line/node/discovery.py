"""LineNode mixin: peer discovery — periodic announce, listening for
announces/channel traffic, and reaping peers that went quiet. Rebroadcasts
announces one more hop so nodes beyond our direct broadcast domain
(routed segments) can still discover this peer — the mesh-relay behavior
that gives multi-hop reach on a plain LAN."""
import json
import socket
import threading
import time

from ..constants import DISCOVERY_PORT, HEARTBEAT_INTERVAL, PEER_TIMEOUT
from ..crypto import b64e, b64d
from ..constants import MESH_MAX_HOPS
from ..mesh import should_relay, next_hop_count
from ..models import Peer
from ..netutils import local_ips, broadcast_targets, valid_name
from .wire import _new_mid


def _parse_announce(msg: dict):
    name = msg.get("name")
    pub = msg.get("pub")
    hops = msg.get("hops", 0)
    port = msg.get("port")
    if not valid_name(name) or not isinstance(pub, str):
        return None
    if type(hops) is not int or not 0 <= hops <= MESH_MAX_HOPS:
        return None
    if type(port) is not int or not 1 <= port <= 65535:
        return None
    try:
        pub_bytes = b64d(pub)
    except (ValueError, UnicodeError):
        return None
    if len(pub_bytes) != 32:
        return None
    return name, pub_bytes, hops, port


def _decode_wire_message(data: bytes):
    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return message if isinstance(message, dict) else None


class _DiscoveryMixin:
    def _announce_loop(self):
        while not self._stop.is_set():
            self._send_announce()
            time.sleep(HEARTBEAT_INTERVAL)

    def _send_announce(self, hops=0):
        payload = {
            "type": "announce",
            "name": self.name,
            "pub": b64e(self.pub_bytes),
            "port": self.chat_port,
            "hops": hops,
            "mid": _new_mid(),
        }
        self._broadcast(payload)

    def _broadcast(self, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        for target in broadcast_targets():
            try:
                self._disc_sock.sendto(data, (target, DISCOVERY_PORT))
            except OSError:
                pass

    def _discovery_listen_loop(self):
        my_ips = local_ips()
        while not self._stop.is_set():
            try:
                data, addr = self._disc_sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            msg = _decode_wire_message(data)
            if msg is None:
                continue
            mtype = msg.get("type")
            if mtype == "announce":
                self._handle_announce(msg, addr, my_ips)
            elif mtype == "channel":
                self._handle_channel_wire(msg)
            elif mtype == "channel_disband":
                self._handle_channel_disband(msg)

    def _handle_announce(self, msg: dict, addr, my_ips: set):
        parsed = _parse_announce(msg)
        if parsed is None:
            return
        name, pub_bytes, hops, chat_port = parsed
        if not name or name == self.name:
            return
        ip = addr[0]
        existing = self.peers.get(name)
        was_new = existing is None
        addr_changed = (not was_new) and (existing.ip != ip or existing.chat_port != chat_port)
        # last_seen always ticks forward (needed for the reaper's timeout
        # check), but that alone shouldn't repaint the sidebar -- only a
        # genuinely new peer or a change in how we reach them should.
        changed = was_new or existing.hops != hops or addr_changed or existing.pub_bytes != pub_bytes
        self.peers[name] = Peer(name=name, ip=ip, chat_port=chat_port,
                                 pub_bytes=pub_bytes, last_seen=time.time(), hops=hops)
        self.peer_pub[name] = pub_bytes
        if addr_changed:
            # A pooled outbound connection (see node/messaging.py) would
            # otherwise keep pointing at the peer's old, no-longer-valid
            # address -- drop it so the next send reconnects fresh.
            self._drop_conn(name)
        if changed:
            self._emit("peer_update", name=name, online=True, hops=hops)
        if was_new:
            # _flush_relay_queue does blocking TCP connects (one per
            # queued message, each up to several seconds on an
            # unreachable/slow peer). This method runs on the *single*
            # discovery-listener thread that every peer's announces and
            # all channel traffic flow through -- calling it inline used
            # to freeze that thread, so nobody else's announces or
            # messages could be processed until the flush finished.
            # That's what made delivery to *other* peers look randomly
            # "stuck": whichever peer's mail happened to be flushing at
            # that moment blocked everyone else. Run it on its own
            # thread so the listener stays free.
            threading.Thread(target=self._flush_relay_queue, args=(name,), daemon=True).start()
        mid = msg.get("mid")
        if mid and not self.seen.seen_before("disc:" + mid) and should_relay(hops):
            relay_msg = dict(msg)
            relay_msg["hops"] = next_hop_count(hops)
            self._broadcast(relay_msg)

    def _peer_reaper_loop(self):
        while not self._stop.is_set():
            time.sleep(1.0)
            now = time.time()
            for name, peer in list(self.peers.items()):
                if now - peer.last_seen > PEER_TIMEOUT:
                    del self.peers[name]
                    self._drop_conn(name)
                    self._emit("peer_update", name=name, online=False, hops=0)
