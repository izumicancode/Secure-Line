from secure_line.node.channels import _ChannelsMixin


class SeenRecorder:
    def __init__(self):
        self.ids = []

    def seen_before(self, mid):
        self.ids.append(mid)
        return False


def test_channel_wire_drops_invalid_hops_before_deduplication():
    node = object.__new__(_ChannelsMixin)
    node.name = "self"
    node.seen = SeenRecorder()

    for hops in (-1, 5, "bad", True):
        node._handle_channel_wire({
            "mid": f"invalid-{hops}", "channel": "#general", "from": "peer", "hops": hops,
        })

    assert node.seen.ids == []


def test_channel_wire_drops_invalid_field_types_before_deduplication():
    node = object.__new__(_ChannelsMixin)
    node.name = "self"
    node.seen = SeenRecorder()

    for message in (
        {"mid": [], "channel": "#general", "from": "peer", "hops": 0},
        {"mid": "id", "channel": [], "from": "peer", "hops": 0},
        {"mid": "id", "channel": "#general", "from": [], "hops": 0},
        {"mid": "id", "channel": "bad name", "from": "peer", "hops": 0},
    ):
        node._handle_channel_wire(message)

    assert node.seen.ids == []