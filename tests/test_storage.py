"""Tests for the local storage layer: password-wrapped identity, the
encrypted per-callsign store, and panic wipe. Uses a temp STORE_ROOT so
these never touch a real line_data/ folder."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

import secure_line.constants.storage as storage_constants
import secure_line.storage.paths as paths_mod


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    """Point STORE_ROOT (in both the constants module and every module
    that already imported it) at a fresh temp dir for the duration of a
    test."""
    new_root = str(tmp_path / "line_data")
    monkeypatch.setattr(storage_constants, "STORE_ROOT", new_root)
    monkeypatch.setattr(paths_mod, "STORE_ROOT", new_root)
    import secure_line.storage.identity as identity_mod
    import secure_line.storage.store as store_mod
    import secure_line.storage.panic as panic_mod
    monkeypatch.setattr(panic_mod, "STORE_ROOT", new_root)
    return new_root


def test_create_and_unlock_account_roundtrip(isolated_store):
    from secure_line.storage.identity import create_account, unlock_account
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

    key = create_account("alice", "correct horse battery staple")
    raw1 = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())

    unlocked = unlock_account("alice", "correct horse battery staple")
    raw2 = unlocked.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    assert raw1 == raw2


def test_unlock_with_wrong_password_raises(isolated_store):
    from secure_line.storage.identity import create_account, unlock_account, WrongPassword

    create_account("bob", "correct-password")
    with pytest.raises(WrongPassword):
        unlock_account("bob", "wrong-password")


def test_device_already_has_account_guard(isolated_store):
    from secure_line.storage.identity import create_account, DeviceAlreadyHasAccount

    create_account("carol", "pw1")
    with pytest.raises(DeviceAlreadyHasAccount):
        create_account("dave", "pw2")


def test_account_exists(isolated_store):
    from secure_line.storage.identity import create_account
    from secure_line.storage.paths import account_exists

    assert not account_exists("erin")
    create_account("erin", "pw")
    assert account_exists("erin")


def test_dir_id_does_not_leak_plaintext_name():
    from secure_line.storage.paths import _dir_id

    d = _dir_id("alice")
    assert "alice" not in d
    assert len(d) == 32


def test_store_roundtrip(isolated_store):
    from secure_line.storage.identity import create_account
    from secure_line.storage.store import load_store, save_store

    key = create_account("frank", "pw")
    empty = load_store("frank", key)
    assert empty["channels"] == []

    empty["channels"] = [{"name": "#general"}]
    empty["favorites"] = ["someone"]
    save_store("frank", key, empty)

    reloaded = load_store("frank", key)
    assert reloaded["channels"] == [{"name": "#general"}]
    assert reloaded["favorites"] == ["someone"]


def test_store_unreadable_with_wrong_identity(isolated_store):
    from secure_line.storage.identity import create_account
    from secure_line.storage.store import load_store, save_store
    from cryptography.hazmat.primitives.asymmetric import x25519

    key = create_account("grace", "pw")
    data = load_store("grace", key)
    data["favorites"] = ["x"]
    save_store("grace", key, data)

    wrong_key = x25519.X25519PrivateKey.generate()
    # Wrong key can't decrypt -> falls back to a fresh empty store rather
    # than crashing or leaking data.
    result = load_store("grace", wrong_key)
    assert result["favorites"] == []


def test_panic_wipe_removes_account_and_binding(isolated_store):
    from secure_line.storage.identity import create_account
    from secure_line.storage.paths import account_exists, get_device_account_name
    from secure_line.storage.panic import panic_wipe

    create_account("hank", "pw")
    assert account_exists("hank")
    assert get_device_account_name() == "hank"

    panic_wipe("hank")

    assert not account_exists("hank")
    assert get_device_account_name() is None
