"""LineNode mixin: public/topic channel (room) messaging.

Text posts stay mesh-relayed over UDP broadcast, same as before. Files
are different: broadcasting a multi-megabyte payload over UDP repeatedly
across hops isn't reliable, so a channel file is instead pushed once,
best-effort, over the same TCP path DMs use, fanned out to every peer
currently known to this node. Peers who aren't joined to that channel
(no matching key) just drop it; peers who are offline right now simply
miss it -- there's no store-and-forward for files, only for DMs.

"creator" is carried on every channel message/file as a plain informational
tag, not a proof of anything -- channel passwords are a shared symmetric
secret, not an identity, so there's no signature to check. Each node only
*adopts* a creator name for a channel once, the first time it sees one (or
locally, at the moment it creates the channel) -- see app/channels.py for
how that gates the delete button.
"""
import base64

from ..crypto import encrypt_with_key, decrypt_with_key
from ..mesh import should_relay, next_hop_count
from .wire import _new_mid


class _ChannelsMixin:
    def set_channel_key(self, channel_name: str, key: bytes | None):
        if key is None:
            self.channel_keys.pop(channel_name, None)
        else:
            self.channel_keys[channel_name] = key

    # ------------------------------------------------------------------
    # Text (UDP broadcast, mesh-relayed)
    # ------------------------------------------------------------------
    def send_channel_message(self, channel_name: str, plaintext: str, creator: str = "") -> str:
        mid = _new_mid()
        key = self.channel_keys.get(channel_name)
        if key is None:
            raise KeyError(f"not joined to {channel_name!r}")
        aad = f"channel:{channel_name}:{mid}".encode("utf-8")
        nonce_b64, ct_b64 = encrypt_with_key(key, aad, plaintext)
        payload = {
            "type": "channel", "mid": mid, "channel": channel_name,
            "from": self.name, "nonce": nonce_b64, "ct": ct_b64, "hops": 0,
            "creator": creator,
        }
        self.seen.seen_before(mid)  # mark our own message so we ignore any relay echo
        self._broadcast(payload)
        return mid

    def _handle_channel_wire(self, msg: dict):
        mid = msg.get("mid", "")
        channel_name = msg.get("channel", "")
        sender = msg.get("from", "")
        if not mid or not channel_name or sender == self.name:
            return
        if self.seen.seen_before(mid):
            return
        key = self.channel_keys.get(channel_name)
        hops = int(msg.get("hops", 0))
        if key is not None:
            try:
                aad = f"channel:{channel_name}:{mid}".encode("utf-8")
                plaintext = decrypt_with_key(key, aad, msg["nonce"], msg["ct"])
                self._emit("channel_message", channel=channel_name, sender=sender,
                           text=plaintext, mid=mid, hops=hops, creator=msg.get("creator", ""))
            except Exception:
                pass  # wrong password for this channel name -- can't read it, that's fine
        if should_relay(hops):
            relayed = dict(msg)
            relayed["hops"] = next_hop_count(hops)
            self._broadcast(relayed)

    # ------------------------------------------------------------------
    # Files/folders (TCP fan-out to currently known peers, best-effort)
    # ------------------------------------------------------------------
    def send_channel_file(self, channel_name: str, filename: str, raw: bytes, creator: str = "") -> tuple:
        """Encrypts `raw` under the channel key and pushes it to every
        peer we currently know about. Returns (mid, delivered_count) so
        the UI can note how many peers actually got it right now."""
        key = self.channel_keys.get(channel_name)
        if key is None:
            raise KeyError(f"not joined to {channel_name!r}")
        mid = _new_mid()
        plaintext = base64.b64encode(raw).decode("ascii") + "||" + filename
        aad = f"channelfile:{channel_name}:{mid}".encode("utf-8")
        nonce_b64, ct_b64 = encrypt_with_key(key, aad, plaintext)
        envelope = {
            "type": "channel_file", "mid": mid, "channel": channel_name,
            "from": self.name, "nonce": nonce_b64, "ct": ct_b64, "creator": creator,
        }
        self.seen.seen_before(mid)
        delivered = 0
        for peer_name in list(self.peers.keys()):
            if self._try_deliver(peer_name, envelope):
                delivered += 1
        return mid, delivered

    def _handle_channel_file(self, envelope: dict):
        mid = envelope.get("mid", "")
        channel_name = envelope.get("channel", "")
        sender = envelope.get("from", "")
        if not mid or not channel_name or sender == self.name:
            return
        if self.seen.seen_before(mid):
            return
        key = self.channel_keys.get(channel_name)
        if key is None:
            return  # not joined to this channel -- can't decrypt, nothing to do
        try:
            aad = f"channelfile:{channel_name}:{mid}".encode("utf-8")
            plaintext = decrypt_with_key(key, aad, envelope["nonce"], envelope["ct"])
            b64_data, filename = plaintext.split("||", 1)
        except Exception:
            return
        self._emit("channel_file_received", channel=channel_name, sender=sender,
                    filename=filename, data=b64_data, mid=mid,
                    creator=envelope.get("creator", ""))

    # ------------------------------------------------------------------
    # Disband (creator-only delete, broadcast so other members find out)
    # ------------------------------------------------------------------
    def send_channel_disband(self, channel_name: str) -> str:
        mid = _new_mid()
        payload = {"type": "channel_disband", "mid": mid, "channel": channel_name, "from": self.name}
        self.seen.seen_before(mid)
        self._broadcast(payload)
        return mid

    def _handle_channel_disband(self, msg: dict):
        mid = msg.get("mid", "")
        channel_name = msg.get("channel", "")
        sender = msg.get("from", "")
        if not mid or not channel_name or sender == self.name:
            return
        if self.seen.seen_before(mid):
            return
        self._emit("channel_disbanded", channel=channel_name, by=sender)
