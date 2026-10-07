from secure_line.node.wire import _recv_exact


class FragmentedSocket:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    def recv(self, _size):
        return self.chunks.pop(0) if self.chunks else b""


def test_recv_exact_combines_fragmented_reads():
    assert _recv_exact(FragmentedSocket([b"a", b"bc", b"d"]), 4) == b"abcd"


def test_recv_exact_raises_if_peer_closes_early():
    try:
        _recv_exact(FragmentedSocket([b"ab"]), 3)
    except ConnectionError:
        return
    raise AssertionError("expected ConnectionError when the peer closes early")


def test_recv_exact_rejects_negative_length():
    try:
        _recv_exact(FragmentedSocket([]), -1)
    except ValueError:
        return
    raise AssertionError("expected ValueError for a negative read length")


def test_recv_exact_accepts_zero_length_without_reading():
    assert _recv_exact(FragmentedSocket([]), 0) == b""