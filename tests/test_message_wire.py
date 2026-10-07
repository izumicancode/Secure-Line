from secure_line.node.messaging import _MessagingMixin


def test_dm_drops_invalid_envelope_before_advancing_ratchet():
    node = object.__new__(_MessagingMixin)
    node.name = "local"
    ratchet_calls = []
    node._ratchet_for = lambda peer: ratchet_calls.append(peer)

    for envelope in (
        {"from": [], "mid": "id", "n": 0, "nonce": "n", "ct": "c"},
        {"from": "peer", "mid": [], "n": 0, "nonce": "n", "ct": "c"},
        {"from": "peer", "mid": "id", "n": "0", "nonce": "n", "ct": "c"},
        {"from": "peer", "mid": "id", "n": -1, "nonce": "n", "ct": "c"},
        {"from": "peer", "mid": "id", "n": 0, "nonce": [], "ct": "c"},
        {"from": "peer", "mid": "id", "n": 0, "nonce": "n", "ct": "c", "kind": "unknown"},
    ):
        node._handle_dm(envelope)

    assert ratchet_calls == []