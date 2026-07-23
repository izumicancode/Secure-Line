"""Plain data types shared across the app.

    peer.py         a discovered LAN peer
    profile.py      the user's editable profile
    channel.py      a joined topic room
    chat_entry.py   one chat-history entry (DM / channel / system)

Adding a new kind of persisted object (e.g. a saved file attachment
record) means adding one file here, not touching the others.
"""
from .peer import Peer
from .profile import Profile
from .channel import Channel
from .chat_entry import ChatEntry
