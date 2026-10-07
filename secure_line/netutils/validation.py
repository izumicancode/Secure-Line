"""Callsign / channel-name validation and normalization."""
from ..constants import CHANNEL_PREFIX


def valid_name(name: str) -> bool:
    return bool(name) and 2 <= len(name) <= 24 and all(
        "A" <= char <= "Z" or "a" <= char <= "z" or "0" <= char <= "9" or char in "-_."
        for char in name
    )


def valid_channel_name(name: str) -> bool:
    """A channel name is a callsign-shaped token with a leading '#',
    e.g. '#general', '#lobby-1'."""
    if not name.startswith(CHANNEL_PREFIX):
        return False
    body = name[len(CHANNEL_PREFIX):]
    return valid_name(body)


def normalize_channel_name(name: str) -> str:
    name = name.strip()
    if not name.startswith(CHANNEL_PREFIX):
        name = CHANNEL_PREFIX + name
    return name.lower()
