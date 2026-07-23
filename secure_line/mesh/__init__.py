"""Mesh relay + store-and-forward — the piece that makes this feel like
bitchat instead of a plain LAN chat: messages that can't reach their
target directly get relayed by other online nodes (bounded by a hop
limit), and messages addressed to a peer who's currently offline are
queued locally and flushed automatically the moment that peer reappears.
No Tk/UI code lives here.

    seen_cache.py    de-dup cache for relayed message ids
    relay_queue.py   store-and-forward mailbox
    hops.py           hop-limit helpers

A new relay strategy (e.g. priority queuing, per-channel TTLs) is a new
file here rather than a new branch inside one growing module.
"""
from .seen_cache import SeenCache
from .relay_queue import RelayQueue
from .hops import should_relay, next_hop_count
