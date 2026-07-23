"""Mesh relay / store-and-forward tuning.

LAN messages travel one broadcast hop for free; MESH_MAX_HOPS lets a node
re-broadcast a message it isn't the target of, so delivery still works
across routed segments / VLANs a plain broadcast can't reach on its own.
"""

MESH_MAX_HOPS = 4
SEEN_ID_CACHE = 4096          # de-dup window for relayed message ids
RELAY_QUEUE_MAX = 500         # store-and-forward cap per offline peer
RELAY_TTL_SECONDS = 6 * 3600  # give up forwarding a queued message after this long
RELAY_RETRY_MS = 1000          # how often we retry flushing queued mail to peers that reappear
