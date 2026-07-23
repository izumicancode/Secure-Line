"""A joined channel (bitchat-style public/topic room). Membership + the
derived key are entirely local; anyone who knows the name+password can
join."""
import time
from dataclasses import dataclass, field, asdict


@dataclass
class Channel:
    name: str                 # e.g. "#general", always includes the '#'
    has_password: bool = False
    joined: float = field(default_factory=time.time)
    unread: int = 0
    last_message_preview: str = ""
    # Callsign of whoever created this channel, from *this device's* point
    # of view. Set locally at creation time; other members only learn it
    # (informationally) from a "creator" tag on messages they receive, and
    # only ever adopt it once, first-seen — never overwritten afterwards.
    # There's no signature backing this (channel passwords are a shared
    # symmetric secret, not an identity), so it's trust-on-first-use, same
    # as everything else name-based in this app. "" means unknown/system
    # (e.g. the default #general every device auto-joins) — nobody gets a
    # delete button for those, only leave.
    creator: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Channel":
        return Channel(
            name=str(d.get("name", "#general")),
            has_password=bool(d.get("has_password", False)),
            joined=float(d.get("joined", time.time())),
            unread=int(d.get("unread", 0)),
            last_message_preview=str(d.get("last_message_preview", ""))[:120],
            creator=str(d.get("creator", ""))[:24],
        )
