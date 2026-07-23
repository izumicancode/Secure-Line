"""Local identity + trust store: password-wrapped X25519 identity keys
and the encrypted per-callsign store (channels, favorites, history).
Nothing here touches the network.

    paths.py       on-disk layout, directory naming/locking
    identity.py    create/unlock a password-wrapped identity
    store.py       load/save the encrypted per-callsign data blob
    panic.py       bitchat-style panic wipe

A new persisted feature (e.g. a new store field) touches store.py only;
a new identity scheme gets its own file alongside identity.py.
"""
from .paths import (
    account_exists, _secure_makedirs, _peer_dir, _identity_path, _dir_id,
    get_device_account_name, set_device_account_name, clear_device_account_name,
)
from .identity import create_account, unlock_account, WrongPassword, DeviceAlreadyHasAccount
from .store import load_store, save_store, _derive_store_key, _derive_file_key
from .panic import panic_wipe
