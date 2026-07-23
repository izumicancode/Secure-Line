"""Bitchat-style panic wipe: irreversibly delete local identity + history."""
import os
import shutil

from ..constants import STORE_ROOT
from .paths import _dir_id, _secure_makedirs, clear_device_account_name


def panic_wipe(name: str | None = None):
    """If `name` is given, wipes only that callsign's folder; otherwise
    wipes every local account under STORE_ROOT. Either way also clears the
    device-account binding — since a device holds one account at a time,
    wiping *the* account means this device no longer has one, and the
    login screen should offer signup again rather than being stuck asking
    for a password to an identity that no longer exists."""
    if name is not None:
        d = os.path.join(STORE_ROOT, _dir_id(name))
        shutil.rmtree(d, ignore_errors=True)
        clear_device_account_name()
        return
    shutil.rmtree(STORE_ROOT, ignore_errors=True)
    _secure_makedirs(STORE_ROOT)
    clear_device_account_name()
