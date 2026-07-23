"""Network ports, timings, and framing limits for LAN discovery + chat."""

DISCOVERY_PORT = 50999
MCAST_GROUP = "239.255.42.99"       # secondary discovery channel, more reliable than broadcast
CHAT_PORT_BASE = 51000
HEARTBEAT_INTERVAL = 2.0
PEER_TIMEOUT = 7.0
UI_REFRESH_MS = 1000
MSG_POLL_MS = 200
MAX_SKIPPED_KEYS = 50        # out-of-order ratchet keys retained per peer
NAME_CLAIM_WINDOW = 2.5      # seconds to listen for a name clash before entering the line
NO_PEERS_WARN_AFTER = 12.0   # seconds with zero peers before we suggest a firewall check

FRAME_LEN_BYTES = 4
MAX_FILE_SIZE = 100 * 1024 * 1024
# A file payload is base64-encoded, then AES-GCM encrypted, then the
# ciphertext is base64-encoded again for the wire -- two rounds of base64
# expansion (~4/3 each) plus the tag/nonce/JSON envelope overhead. Worst
# case that's ~1.8x the raw file size, so the frame cap has to leave
# real headroom above MAX_FILE_SIZE or legitimate max-size attachments
# get rejected as "frame too large" before they ever reach the network.
MAX_FRAME_SIZE = int(MAX_FILE_SIZE * 2) + (2 * 1024 * 1024)
# Minimum time budget (seconds) for a single-shot TCP delivery (connect +
# send). Small messages don't need this long, but it's the floor so a
# slow/busy LAN link doesn't time out mid-send.
MIN_DELIVERY_TIMEOUT = 5.0
# Extra seconds of send budget granted per MB of payload, on top of the
# minimum -- keeps big file transfers from racing a fixed short timeout.
# At 100MB that's ~3.5 minutes of headroom, generous enough for a slow
# Wi-Fi link without letting a truly dead peer hang forever.
DELIVERY_SECONDS_PER_MB = 2.0
# How long to wait for the initial TCP handshake before giving up. This
# is deliberately independent of and much shorter than the send timeout
# above -- connect time has nothing to do with payload size, and an
# unreachable peer should fail fast so a retry can happen again soon,
# instead of tying up a send for as long as a multi-hundred-MB transfer
# would be allowed to take.
CONNECT_TIMEOUT = 2.5
# How long a reused, idle per-peer connection can sit with nothing coming
# in before this side gives up on it and lets the thread reading it exit.
# Generous compared to HEARTBEAT_INTERVAL/PEER_TIMEOUT since a
# conversation can easily go quiet for a while without the peer actually
# being gone -- this only needs to reclaim connections whose peer vanished
# without a clean close (sleep, network loss), not police normal pauses.
IDLE_CONN_TIMEOUT = 120.0
RECEIVED_FILES_DIRNAME = "received_files"
SENT_FILES_DIRNAME = "sent_files"
IMAGE_THUMB_MIMES = ("image/png", "image/gif", "image/jpeg", "image/bmp", "image/webp")
