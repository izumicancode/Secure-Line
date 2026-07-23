"""Password-wrapped X25519 identity: create a fresh account, or unlock an
existing one. Every function here is local-only — nothing in this module
touches the network."""
import os

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.exceptions import InvalidTag

from ..constants import ACCOUNT_SALT_BYTES, ACCOUNT_SCRYPT_N, ACCOUNT_SCRYPT_R, ACCOUNT_SCRYPT_P
from .paths import _peer_dir, _identity_path, get_device_account_name, set_device_account_name


class WrongPassword(Exception):
    pass


class DeviceAlreadyHasAccount(Exception):
    """Raised if code tries to create a second account on a device that's
    already bound to one — this app supports exactly one local account per
    device, so the UI should never actually hit this in practice, but the
    storage layer enforces it too rather than trusting the caller."""
    pass


def _derive_account_key(password: str, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=ACCOUNT_SCRYPT_N, r=ACCOUNT_SCRYPT_R,
                  p=ACCOUNT_SCRYPT_P).derive(password.encode("utf-8"))


def _write_identity_file(name: str, password: str, raw_key: bytes):
    salt = os.urandom(ACCOUNT_SALT_BYTES)
    wrap_key = _derive_account_key(password, salt)
    nonce = os.urandom(12)
    ct = AESGCM(wrap_key).encrypt(nonce, raw_key, name.encode("utf-8"))
    blob = salt + nonce + ct
    path = os.path.join(_peer_dir(name), "identity.key")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(blob)


def create_account(name: str, password: str) -> x25519.X25519PrivateKey:
    """First-time signup for this callsign on this device: mint a fresh
    identity and wrap it with the chosen password. One device holds at
    most one account — if this device is already bound to a different
    callsign, refuse rather than silently minting a second identity."""
    existing = get_device_account_name()
    if existing is not None and existing != name:
        raise DeviceAlreadyHasAccount(
            f"this device already has an account ({existing!r}); "
            "wipe it first to create a different one")
    key = x25519.X25519PrivateKey.generate()
    raw = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    _write_identity_file(name, password, raw)
    set_device_account_name(name)
    return key


def unlock_account(name: str, password: str) -> x25519.X25519PrivateKey:
    """Log in to an existing local account: unwrap identity.key with the
    given password. Raises WrongPassword if it doesn't match (or the file
    is corrupt), so the caller can show a clean error instead of silently
    minting a brand-new identity and orphaning the old history."""
    path = _identity_path(name)
    with open(path, "rb") as f:
        blob = f.read()
    if len(blob) == 32:
        # Legacy plaintext identity.key — accept whatever password is
        # given now and wrap the existing key with it going forward.
        raw = blob
        _write_identity_file(name, password, raw)
        return x25519.X25519PrivateKey.from_private_bytes(raw)
    if len(blob) < ACCOUNT_SALT_BYTES + 12 + 16:
        raise WrongPassword("identity.key is corrupt or truncated")
    salt = blob[:ACCOUNT_SALT_BYTES]
    nonce = blob[ACCOUNT_SALT_BYTES:ACCOUNT_SALT_BYTES + 12]
    ct = blob[ACCOUNT_SALT_BYTES + 12:]
    wrap_key = _derive_account_key(password, salt)
    try:
        raw = AESGCM(wrap_key).decrypt(nonce, ct, name.encode("utf-8"))
    except InvalidTag:
        raise WrongPassword("incorrect password")
    return x25519.X25519PrivateKey.from_private_bytes(raw)
