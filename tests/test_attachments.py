from secure_line.app.messaging import _read_file_limited


def test_read_file_limited_accepts_file_at_limit(tmp_path):
    path = tmp_path / "small.bin"
    path.write_bytes(b"12345")

    assert _read_file_limited(str(path), 5) == b"12345"


def test_read_file_limited_rejects_oversized_file(tmp_path):
    path = tmp_path / "large.bin"
    path.write_bytes(b"123456")

    assert _read_file_limited(str(path), 5) is None