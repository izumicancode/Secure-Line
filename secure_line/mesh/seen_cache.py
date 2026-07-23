"""Bounded, thread-safe set of message ids we've already relayed or
delivered, so a rebroadcast storm can't loop forever and a message
doesn't get shown twice after taking two different mesh paths."""
import collections
import threading

from ..constants import SEEN_ID_CACHE


class SeenCache:
    def __init__(self, maxlen=SEEN_ID_CACHE):
        self._order = collections.deque(maxlen=maxlen)
        self._set = set()
        self._lock = threading.Lock()

    def seen_before(self, mid: str) -> bool:
        with self._lock:
            if mid in self._set:
                return True
            if len(self._order) == self._order.maxlen:
                old = self._order.popleft()
                self._set.discard(old)
            self._order.append(mid)
            self._set.add(mid)
            return False
