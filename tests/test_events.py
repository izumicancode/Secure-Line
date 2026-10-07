import base64

from secure_line.app import events as events_module
from secure_line.app.events import _EventsMixin


def test_save_incoming_file_rejects_invalid_base64(monkeypatch, tmp_path):
    monkeypatch.setattr(events_module, "STORE_ROOT", str(tmp_path))
    app = object.__new__(_EventsMixin)

    assert app._save_incoming_file("broken.txt", "YWJj$") == ("", 0)


def test_save_incoming_file_writes_valid_base64(monkeypatch, tmp_path):
    monkeypatch.setattr(events_module, "STORE_ROOT", str(tmp_path))
    app = object.__new__(_EventsMixin)
    encoded = base64.b64encode(b"attachment").decode("ascii")

    path, size = app._save_incoming_file("note.txt", encoded)

    assert size == len(b"attachment")
    with open(path, "rb") as saved_file:
        assert saved_file.read() == b"attachment"