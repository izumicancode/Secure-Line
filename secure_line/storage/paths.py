"""On-disk layout helpers: deterministic, privacy-preserving folder names
per callsign, and locked-down directory creation."""
import hashlib
import json
import os

from ..constants import STORE_ROOT


def _dir_id(name: str) -> str:
    """Deterministic, one-way folder name for a callsign, derived from a
    fixed domain-separated hash. Anyone who browses line_data on disk sees
    only opaque hex directory names — never the plaintext callsign."""
    return hashlib.sha256(b"secure-line-dir-v2:" + name.encode("utf-8")).hexdigest()[:32]


def _secure_makedirs(path: str):
    """Create a directory (and parents) locked to the current user only.
    Best-effort on Windows, where NTFS ACLs already default to the owning
    user's profile."""
    os.makedirs(path, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def _peer_dir(name: str) -> str:
    d = os.path.join(STORE_ROOT, _dir_id(name))
    _secure_makedirs(d)
    return d


def _identity_path(name: str) -> str:
    return os.path.join(STORE_ROOT, _dir_id(name), "identity.key")


def account_exists(name: str) -> bool:
    """An 'account' is just a callsign that already has an identity.key on
    this machine — there's no server, so this only ever answers 'does
    *this device* already know a user by this name'."""
    return os.path.isfile(_identity_path(name))


def _device_account_path() -> str:
    return os.path.join(STORE_ROOT, "device_account.json")


def get_device_account_name() -> str | None:
    """The single callsign this device is bound to, if one has ever been
    created here. Plaintext and not secret — it's just a username, kept so
    the login screen can skip straight to a password prompt next time
    instead of asking for a callsign again. Folder names on disk are a
    one-way hash of the callsign (see `_dir_id`), so this file is the only
    place the plaintext callsign is recorded locally."""
    try:
        with open(_device_account_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name")
        return name if isinstance(name, str) and name else None
    except Exception:
        return None


def set_device_account_name(name: str):
    _secure_makedirs(STORE_ROOT)
    tmp = _device_account_path() + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f)
    os.replace(tmp, _device_account_path())


def clear_device_account_name():
    try:
        os.remove(_device_account_path())
    except OSError:
        pass
