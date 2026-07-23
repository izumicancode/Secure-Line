"""The double-ratchet-style symmetric chain used per 1:1 conversation.

Both sides derive the same root key via ECDH (see keys.derive_root_key),
then independently walk two chains (one per direction) using deterministic
ordering ("A" = whichever name sorts first) so both ends agree on which
chain is "my send chain" vs "my receive chain" without any extra messages.
"""
import hashlib
import hmac
import threading

from ..constants import MAX_SKIPPED_KEYS


def _chain_step(chain_key: bytes):
    """One ratchet step: derive a message key + the next chain key from
    the current one. The caller then discards the old chain key, so past
    message keys can never be recomputed from present state (forward
    secrecy)."""
    msg_key = hmac.new(chain_key, b"message", hashlib.sha256).digest()
    next_chain = hmac.new(chain_key, b"chain", hashlib.sha256).digest()
    return msg_key, next_chain


class Ratchet:
    """Per-conversation, per-direction ratcheting key schedule."""

    def __init__(self, root_key: bytes, am_i_a: bool, state: dict | None = None):
        if state is not None:
            self.send_chain = state["send_chain"]
            self.recv_chain = state["recv_chain"]
            self.send_n = state["send_n"]
            self.recv_n = state["recv_n"]
            self.skipped = dict(state["skipped"])
        else:
            send_label = b"A2B" if am_i_a else b"B2A"
            recv_label = b"B2A" if am_i_a else b"A2B"
            self.send_chain = hmac.new(root_key, send_label, hashlib.sha256).digest()
            self.recv_chain = hmac.new(root_key, recv_label, hashlib.sha256).digest()
            self.send_n = 0
            self.recv_n = 0
            self.skipped = {}
        self.lock = threading.Lock()

    def next_send_key(self):
        with self.lock:
            msg_key, self.send_chain = _chain_step(self.send_chain)
            n = self.send_n
            self.send_n += 1
            return n, msg_key

    def recv_key_for(self, n: int):
        with self.lock:
            if n < self.recv_n:
                return self.skipped.pop(n, None)
            while self.recv_n < n:
                candidate, self.recv_chain = _chain_step(self.recv_chain)
                self.skipped[self.recv_n] = candidate
                self.recv_n += 1
                if len(self.skipped) > MAX_SKIPPED_KEYS:
                    del self.skipped[min(self.skipped)]
            key, self.recv_chain = _chain_step(self.recv_chain)
            self.recv_n += 1
            return key

    def export_state(self) -> dict:
        with self.lock:
            return {
                "send_chain": self.send_chain,
                "recv_chain": self.recv_chain,
                "send_n": self.send_n,
                "recv_n": self.recv_n,
                "skipped": dict(self.skipped),
            }
