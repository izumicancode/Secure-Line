"""LineNode mixin: 1:1 direct messages — ratchet key agreement, sending
with store-and-forward fallback, delivery receipts, and the TCP chat
server that receives them."""
import socket
import threading
import time

from ..constants import (RELAY_RETRY_MS, MIN_DELIVERY_TIMEOUT, DELIVERY_SECONDS_PER_MB,
                         CONNECT_TIMEOUT, IDLE_CONN_TIMEOUT)
from ..crypto import derive_root_key, Ratchet, encrypt_with_key, decrypt_with_key
from .wire import _new_mid, _send_framed, _recv_framed


class _MessagingMixin:
    # ------------------------------------------------------------------
    # Ratchets / key agreement
    # ------------------------------------------------------------------
    def _ratchet_for(self, peer_name: str) -> Ratchet:
        # Every outgoing DM is sent from its own background thread (see
        # app/messaging.py), so two messages fired to the same new peer
        # in quick succession can both reach here before either has
        # created the ratchet -- without a lock they'd race to build two
        # separate Ratchet objects from the same root key, and whichever
        # write lost would leave its sender using a ratchet state no
        # longer reachable from self.ratchets, desyncing that
        # conversation. A lock around the check-and-create makes it
        # atomic.
        with self._ratchets_lock:
            if peer_name not in self.ratchets:
                their_pub = self.peer_pub.get(peer_name)
                if their_pub is None:
                    raise KeyError(f"no public key known for {peer_name!r} yet")
                root = derive_root_key(self.private_key, their_pub)
                am_i_a = self.name < peer_name
                self.ratchets[peer_name] = Ratchet(root, am_i_a)
            return self.ratchets[peer_name]

    def restore_ratchet(self, peer_name: str, root_key: bytes, am_i_a: bool, state: dict):
        with self._ratchets_lock:
            self.ratchets[peer_name] = Ratchet(root_key, am_i_a, state=state)

    def restore_ratchet_state(self, peer_name: str, state: dict):
        """Restore a previously persisted symmetric-ratchet state.

        ``Ratchet`` only uses ``root_key`` when constructing a *new* chain;
        a complete saved state already contains both current chain keys.
        Keeping this separate from ``restore_ratchet`` makes that fact
        explicit and lets the UI restore state before peer discovery has
        provided the peer's public key again.
        """
        with self._ratchets_lock:
            self.ratchets[peer_name] = Ratchet(b"\0" * 32, False, state=state)

    def export_ratchet(self, peer_name: str):
        with self._ratchets_lock:
            r = self.ratchets.get(peer_name)
            return r.export_state() if r else None

    def export_ratchets(self) -> dict[str, dict]:
        """Return an atomic snapshot of all active direct-message chains."""
        with self._ratchets_lock:
            return {peer_name: ratchet.export_state()
                    for peer_name, ratchet in self.ratchets.items()}

    # ------------------------------------------------------------------
    # Direct messages (1:1, ratcheted, store-and-forward on failure)
    # ------------------------------------------------------------------
    def send_dm(self, peer_name: str, plaintext: str, kind: str = "text") -> tuple:
        mid = _new_mid()
        ratchet = self._ratchet_for(peer_name)
        n, msg_key = ratchet.next_send_key()
        aad = f"{self.name}->{peer_name}:{n}".encode("utf-8")
        nonce_b64, ct_b64 = encrypt_with_key(msg_key, aad, plaintext)
        envelope = {
            "type": "dm", "mid": mid, "from": self.name, "to": peer_name,
            "n": n, "nonce": nonce_b64, "ct": ct_b64, "kind": kind,
        }
        delivered = self._try_deliver(peer_name, envelope)
        if not delivered:
            self.relay_queue.enqueue(peer_name, envelope)
            status = "queued"
        else:
            status = "sent"
        # Still emitted for later re-flushes of this same mid (e.g. the
        # retry loop eventually delivering a queued message), but the
        # caller of *this* send must not rely on racing the event queue
        # to learn its own outcome -- by the time this event is polled,
        # the caller may not have created the UI entry it belongs to yet,
        # silently dropping the update. Return the status directly instead.
        self._emit("dm_status", mid=mid, peer=peer_name, status=status)
        return mid, status

    def _get_conn(self, peer_name: str, ip: str, port: int) -> socket.socket:
        """Returns an open, reusable socket to `peer_name`, connecting one
        if none is pooled yet. Caller must hold that peer's send lock."""
        with self._conns_lock:
            sock = self._conns.get(peer_name)
        if sock is not None:
            return sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(CONNECT_TIMEOUT)
        sock.connect((ip, port))
        with self._conns_lock:
            self._conns[peer_name] = sock
        return sock

    def _drop_conn(self, peer_name: str):
        with self._conns_lock:
            sock = self._conns.pop(peer_name, None)
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def _send_lock_for(self, peer_name: str) -> threading.Lock:
        with self._conns_lock:
            lock = self._send_locks.get(peer_name)
            if lock is None:
                lock = threading.Lock()
                self._send_locks[peer_name] = lock
            return lock

    def _try_deliver(self, peer_name: str, envelope: dict) -> bool:
        peer = self.peers.get(peer_name)
        if peer is None:
            return False
        # A fixed short timeout works fine for a few bytes of text but
        # starves a multi-megabyte file transfer on anything less than a
        # very fast/quiet LAN -- scale the *send* budget with payload
        # size. The *connect* budget is unrelated to payload size and
        # stays short and fixed, so an unreachable peer fails fast
        # instead of the attempt hanging for as long as a large transfer
        # would be allowed to take.
        approx_size_mb = len(envelope.get("ct", "")) / (1024 * 1024)
        send_timeout = MIN_DELIVERY_TIMEOUT + approx_size_mb * DELIVERY_SECONDS_PER_MB
        # One TCP connection per peer, reused across every message instead
        # of opened and closed fresh each time. Connecting fresh for every
        # single chat message and file chunk works for a handful of sends,
        # but many routers/OS firewalls rate-limit or throttle a burst of
        # new connection attempts from the same host -- which looks
        # exactly like "the first few messages go through fine, then it
        # starts delaying/queuing." Reusing one long-lived connection per
        # peer avoids that churn entirely and is also just faster (no
        # repeated handshake). A lock per peer serializes writes so two
        # concurrent sends to the same peer can't interleave their framed
        # messages on the one shared socket.
        with self._send_lock_for(peer_name):
            for attempt in (1, 2):
                try:
                    sock = self._get_conn(peer_name, peer.ip, peer.chat_port)
                    sock.settimeout(send_timeout)
                    _send_framed(sock, envelope)
                    return True
                except ValueError:
                    # _send_framed's own "frame too large" guard -- not a
                    # connection problem, retrying won't help.
                    return False
                except OSError:
                    # Connect/send failure -- unreachable, refused, timed
                    # out, or a pooled connection that's gone stale (peer
                    # restarted, network blip). Drop it and, on the first
                    # attempt only, try one fresh connection before
                    # giving up and queuing for the retry loop instead.
                    self._drop_conn(peer_name)
                    if attempt == 2:
                        return False
        return False

    def _flush_relay_queue(self, peer_name: str):
        pending = self.relay_queue.drain_for(peer_name)
        for envelope in pending:
            if not self._try_deliver(peer_name, envelope):
                self.relay_queue.enqueue(peer_name, envelope)
            else:
                self._emit("dm_status", mid=envelope.get("mid", ""), peer=peer_name, status="sent")

    def _relay_retry_loop(self):
        # A message only gets flushed from the queue today when its
        # recipient re-announces as a *new* peer entry (see
        # _handle_announce -> was_new). That misses the common case: the
        # peer never actually left (still online, still in self.peers),
        # the send just failed once -- a busy socket, a slow LAN, a
        # one-off refusal -- and nothing ever retries it. This loop is
        # the retry: for anyone currently online with mail waiting,
        # actually attempt delivery on every tick, not just expire stale
        # entries.
        #
        # Each peer's flush runs on its own short-lived thread rather
        # than looping through peers one at a time on this thread --
        # otherwise one slow or unreachable peer (blocking here for up
        # to the connect+send timeout) would delay every other peer's
        # retry behind it on the same tick, which looked exactly like
        # "everything is stuck" even though only one peer actually was.
        while not self._stop.is_set():
            time.sleep(RELAY_RETRY_MS / 1000.0)
            for peer_name in list(self.peers.keys()):
                if self.relay_queue.pending_count(peer_name):
                    threading.Thread(target=self._flush_relay_queue, args=(peer_name,),
                                      daemon=True).start()
            self.relay_queue.sweep_expired()

    def send_receipt(self, peer_name: str, mid: str, status: str):
        envelope = {"type": "receipt", "mid": mid, "from": self.name, "to": peer_name, "status": status}
        if not self._try_deliver(peer_name, envelope):
            self.relay_queue.enqueue(peer_name, envelope)

    def _chat_server_loop(self):
        while not self._stop.is_set():
            try:
                conn, _addr = self._chat_srv_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_chat_conn, args=(conn,), daemon=True).start()

    def _handle_chat_conn(self, conn: socket.socket):
        # Senders now keep one connection per peer open and reuse it for
        # every subsequent message (see _try_deliver) instead of opening
        # a fresh one each time, so this side has to keep reading frames
        # off the same connection for as long as it stays open, rather
        # than handling exactly one message and closing. An idle timeout
        # keeps a connection whose peer vanished without closing it (put
        # the laptop to sleep, lost the network, etc.) from leaving this
        # thread blocked on recv() forever.
        try:
            with conn:
                conn.settimeout(IDLE_CONN_TIMEOUT)
                while not self._stop.is_set():
                    envelope = _recv_framed(conn)
                    self._handle_incoming_envelope(envelope)
                    conn.settimeout(IDLE_CONN_TIMEOUT)
        except Exception:
            pass

    def _handle_incoming_envelope(self, envelope: dict):
        mtype = envelope.get("type")
        if mtype == "dm":
            self._handle_dm(envelope)
        elif mtype == "receipt":
            self._emit("receipt", mid=envelope.get("mid"), status=envelope.get("status"),
                       peer=envelope.get("from"))
        elif mtype == "channel_file":
            self._handle_channel_file(envelope)

    def _handle_dm(self, envelope: dict):
        peer_name = envelope.get("from")
        if not peer_name:
            return
        try:
            ratchet = self._ratchet_for(peer_name)
            n = int(envelope["n"])
            msg_key = ratchet.recv_key_for(n)
            if msg_key is None:
                return  # replay or out-of-window — silently drop
            aad = f"{peer_name}->{self.name}:{n}".encode("utf-8")
            plaintext = decrypt_with_key(msg_key, aad, envelope["nonce"], envelope["ct"])
        except Exception:
            return
        self._emit("dm_received", peer=peer_name, mid=envelope.get("mid", ""),
                   text=plaintext, msg_kind=envelope.get("kind", "text"))
        self.send_receipt(peer_name, envelope.get("mid", ""), "delivered")
