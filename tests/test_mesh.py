import pytest

from secure_line.mesh.hops import should_relay
from secure_line.mesh.seen_cache import SeenCache


def test_seen_cache_rejects_nonpositive_capacity():
    with pytest.raises(ValueError):
        SeenCache(maxlen=0)
    with pytest.raises(ValueError):
        SeenCache(maxlen=-1)


def test_seen_cache_evicts_oldest_id_at_capacity():
    cache = SeenCache(maxlen=2)

    assert not cache.seen_before("first")
    assert not cache.seen_before("second")
    assert not cache.seen_before("third")
    assert not cache.seen_before("first")


def test_should_relay_rejects_negative_hop_counts():
    assert not should_relay(-1)
    assert should_relay(0)