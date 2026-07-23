"""Wire framing helpers shared by every socket path: message ids, and
length-prefixed JSON framing for the TCP DM/receipt connections.

Wire format (all JSON over UDP broadcast for discovery/channels, length-
prefixed JSON over TCP for direct messages):

  announce   {type, name, pub, port, hops, mid}
  dm         {type, mid, from, to, n, nonce, ct, kind, aad_extra?}
  receipt    {type, mid, from, to, status}
  channel    {type, mid, channel, from, nonce, ct, hops}
"""
import json
import socket
import struct
import uuid

from ..constants import FRAME_LEN_BYTES, MAX_FRAME_SIZE, MIN_DELIVERY_TIMEOUT, DELIVERY_SECONDS_PER_MB


def _new_mid() -> str:
    return uuid.uuid4().hex


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("peer closed connection")
        buf += chunk
    return buf


def _send_framed(sock: socket.socket, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    if len(data) > MAX_FRAME_SIZE:
        raise ValueError("frame too large")
    sock.sendall(struct.pack(">I", len(data)) + data)


def _recv_framed(sock: socket.socket) -> dict:
    header = _recv_exact(sock, FRAME_LEN_BYTES)
    (length,) = struct.unpack(">I", header)
    if length > MAX_FRAME_SIZE:
        raise ValueError("incoming frame too large")
    # The listening socket carries a short accept-loop timeout so it can
    # poll `_stop` responsively; a freshly-accepted connection used to
    # inherit that same short timeout on some platforms, which was long
    # enough for a text message but could cut off a large file mid-
    # transfer before all of it arrived. Re-arm the timeout here, scaled
    # to how much data is actually coming, before reading the body.
    try:
        sock.settimeout(MIN_DELIVERY_TIMEOUT + (length / (1024 * 1024)) * DELIVERY_SECONDS_PER_MB)
    except OSError:
        pass
    return json.loads(_recv_exact(sock, length).decode("utf-8"))
