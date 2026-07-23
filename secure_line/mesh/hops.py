"""Hop-limit helpers shared by discovery relay and channel relay."""
from ..constants import MESH_MAX_HOPS


def should_relay(hops: int) -> bool:
    """Whether a message that has already traveled `hops` hops is still
    allowed one more relay bounce."""
    return hops < MESH_MAX_HOPS


def next_hop_count(hops: int) -> int:
    return hops + 1
