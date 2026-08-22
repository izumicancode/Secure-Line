"""Per-recipient store-and-forward mailbox. A message that can't be
delivered right now (recipient offline / unreachable) waits here —
capped in count and age — until the recipient is seen online again, at
which point node/messaging.py flushes everything queued for them and if connected to the same network no need to open the app it does it's job in the background ."""
import collections
import threading
import time

from ..constants import RELAY_QUEUE_MAX, RELAY_TTL_SECONDS


class RelayQueue:
    def __init__(self):
        self._queues: dict[str, list[dict]] = collections.defaultdict(list)
        self._lock = threading.Lock()

    def enqueue(self, recipient: str, envelope: dict):
        with self._lock:
            q = self._queues[recipient]
            q.append({"queued_at": time.time(), "envelope": envelope})
            if len(q) > RELAY_QUEUE_MAX:
                q.pop(0)  # drop oldest rather than grow unbounded

    def drain_for(self, recipient: str) -> list[dict]:
        """Pop and return every still-fresh envelope queued for
        `recipient`, expiring anything older than RELAY_TTL_SECONDS."""
        now = time.time()
        with self._lock:
            items = self._queues.pop(recipient, [])
        fresh = [it["envelope"] for it in items if now - it["queued_at"] <= RELAY_TTL_SECONDS]
        return fresh

    def pending_count(self, recipient: str) -> int:
        with self._lock:
            return len(self._queues.get(recipient, []))

    def sweep_expired(self):
        """Drop stale queued mail across all recipients; call periodically."""
        now = time.time()
        with self._lock:
            for recipient in list(self._queues.keys()):
                fresh = [it for it in self._queues[recipient]
                         if now - it["queued_at"] <= RELAY_TTL_SECONDS]
                if fresh:
                    self._queues[recipient] = fresh
                else:
                    del self._queues[recipient]
