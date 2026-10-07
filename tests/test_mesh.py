import pytest

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