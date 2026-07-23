"""A user's editable profile (avatar, color, status, bio)."""
import time
from dataclasses import dataclass, field, asdict

from ..theme import ACCENT


@dataclass
class Profile:
    avatar: str = "🙂"
    color: str = ACCENT
    status: str = ""
    bio: str = ""
    updated: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Profile":
        return Profile(
            avatar=str(d.get("avatar", "🙂"))[:8],
            color=str(d.get("color", ACCENT)),
            status=str(d.get("status", ""))[:80],
            bio=str(d.get("bio", ""))[:400],
            updated=float(d.get("updated", time.time())),
        )

    def preview_only(self) -> "Profile":
        """A stripped copy (avatar/status, no bio) sent along with a
        connection request, before the recipient has chosen to accept."""
        return Profile(avatar=self.avatar, color=self.color, status=self.status,
                        bio="", updated=self.updated)
