"""The encrypted per-callsign store: connections, ratchet state, chat
history, profile, joined channels, favorites, ephemeral-mode preference.
The store's encryption key is derived from the identity private key
(HKDF with a domain-separated info string, distinct from per-peer
root-key derivation), so only this device's identity can read its own
data back."""
import json
import os

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

from ..constants import STORE_FORMAT_VERSION, EPHEMERAL_DEFAULT
from .paths import _peer_dir


def _derive_store_key(private_key: x25519.X25519PrivateKey) -> bytes:
    raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"secure-line-local-store-v2").derive(raw)


def _derive_file_key(private_key: x25519.X25519PrivateKey) -> bytes:
    """Separate, domain-distinct key for received-file-at-rest encryption
    — deliberately not the store key, so a bug in one path can't
    cross-decrypt the other."""
    raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"secure-line-file-store-v2").derive(raw)


def load_store(name: str, private_key: x25519.X25519PrivateKey) -> dict:
    """Returns the decrypted store dict, or {} if there's nothing yet (or
    it can't be read — e.g. the identity was rotated so the old store's
    key no longer matches; we start clean rather than crash)."""
    path = os.path.join(_peer_dir(name), "store.enc")
    try:
        with open(path, "rb") as f:
            blob = f.read()
        nonce, ct = blob[:12], blob[12:]
        key = _derive_store_key(private_key)
        plaintext = AESGCM(key).decrypt(nonce, ct, b"secure-line-store")
        data = json.loads(plaintext.decode("utf-8"))
        if isinstance(data, dict) and data.get("version") in (1, STORE_FORMAT_VERSION):
            data.setdefault("channels", [])
            data.setdefault("favorites", [])
            data.setdefault("ephemeral_mode", EPHEMERAL_DEFAULT)
            return data
    except FileNotFoundError:
        pass
    except Exception:
        pass  # unreadable/corrupt/wrong-key — treat as no prior state
    return {"channels": [], "favorites": [], "ephemeral_mode": EPHEMERAL_DEFAULT}


def save_store(name: str, private_key: x25519.X25519PrivateKey, data: dict):
    data = dict(data)
    data["version"] = STORE_FORMAT_VERSION
    key = _derive_store_key(private_key)
    nonce = os.urandom(12)
    plaintext = json.dumps(data).encode("utf-8")
    ct = AESGCM(key).encrypt(nonce, plaintext, b"secure-line-store")
    path = os.path.join(_peer_dir(name), "store.enc")
    tmp_path = path + ".tmp"
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(nonce + ct)
        os.replace(tmp_path, path)  # atomic — never leaves a half-written store
    except Exception:
        pass  # best-effort; app keeps running even if the disk write failed
