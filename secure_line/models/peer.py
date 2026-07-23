"""A discovered LAN peer."""
from dataclasses import dataclass


@dataclass
class Peer:
    name: str
    ip: str
    chat_port: int
    pub_bytes: bytes          # the *announced* key from the latest broadcast
    last_seen: float
    hops: int = 0              # 0 = heard directly, >0 = reached us via mesh relay
