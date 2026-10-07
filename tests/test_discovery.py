from secure_line.crypto import b64e
from secure_line.node.discovery import _parse_announce


def _announce(**overrides):
    message = {"name": "alice", "pub": b64e(b"k" * 32), "hops": 0, "port": 4321}
    message.update(overrides)
    return message


def test_parse_announce_accepts_valid_fields():
    parsed = _parse_announce(_announce())

    assert parsed == ("alice", b"k" * 32, 0, 4321)


def test_parse_announce_rejects_invalid_port_and_hops():
    assert _parse_announce(_announce(port=0)) is None
    assert _parse_announce(_announce(port=65536)) is None
    assert _parse_announce(_announce(hops=-1)) is None
    assert _parse_announce(_announce(hops=True)) is None


def test_parse_announce_rejects_bad_name_and_public_key():
    assert _parse_announce(_announce(name="bad name")) is None
    assert _parse_announce(_announce(pub="not-base64!")) is None
    assert _parse_announce(_announce(pub=b64e(b"short"))) is None