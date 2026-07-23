"""One chat-history entry — whether it's a DM, a channel post, or a
system notice."""
from dataclasses import dataclass


@dataclass
class ChatEntry:
    sender: str
    text: str
    ts: float
    mine: bool
    kind: str = "text"        # "text" | "system" | "banner" | "file"
    mid: str = ""              # message id, matched against delivery/read receipts
    status: str = ""           # "" | "sent" | "delivered" | "read" | "failed" | "relayed"
    file_path: str = ""
    file_size: int = 0
    file_mime: str = ""
    channel: str = ""          # non-empty if this entry belongs to a channel, not a DM
    hops: int = 0              # how many mesh relays carried this message to us
    mentions: tuple = ()       # nicknames @mentioned in `text`, for highlighting
    ephemeral: bool = False    # True => never written to the encrypted store
