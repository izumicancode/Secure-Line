"""LineNode — networking core, split into one file per feature area so a
new networking feature (e.g. group DMs, typing indicators over the wire)
is a new mixin file instead of a growing monolith.

    wire.py         message ids + TCP length-prefixed framing
    discovery.py    peer announce/listen/reap (mixin)
    messaging.py    1:1 ratcheted DMs, receipts, store-and-forward (mixin)
    channels.py     public/topic channel broadcast (mixin)
    core.py          LineNode: lifecycle + combines the mixins above
"""
from .core import LineNode
