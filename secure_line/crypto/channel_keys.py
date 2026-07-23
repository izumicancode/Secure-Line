"""Channel keys — a shared room secret derived from a passphrase, so any
member who knows the passphrase can decrypt without a pairwise handshake.
Salt is fixed per-channel-name so every member derives the same key from
the same password without exchanging anything else first.
"""
import hashlib

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from ..constants import CHANNEL_SCRYPT_N, CHANNEL_SCRYPT_R, CHANNEL_SCRYPT_P


def derive_channel_key(channel_name: str, password: str) -> bytes:
    salt = hashlib.sha256(b"secure-line-channel-salt:" + channel_name.encode("utf-8")).digest()[:16]
    return Scrypt(salt=salt, length=32, n=CHANNEL_SCRYPT_N, r=CHANNEL_SCRYPT_R,
                  p=CHANNEL_SCRYPT_P).derive(password.encode("utf-8"))


def channel_fingerprint(channel_name: str, password: str) -> str:
    """Short tag members can read aloud/compare to confirm they typed the
    same channel password, without revealing the password or key itself."""
    key = derive_channel_key(channel_name, password)
    return hashlib.sha256(key).hexdigest()[:6].upper()
