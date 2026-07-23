"""AES-GCM envelope helpers: encrypt/decrypt a plaintext string under a
given 32-byte key + associated data, used for both DM message keys and
channel keys."""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .encoding import b64e, b64d


def encrypt_with_key(key: bytes, aad: bytes, plaintext: str):
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), aad)
    return b64e(nonce), b64e(ct)


def decrypt_with_key(key: bytes, aad: bytes, nonce_b64: str, ct_b64: str) -> str:
    pt = AESGCM(key).decrypt(b64d(nonce_b64), b64d(ct_b64), aad)
    return pt.decode("utf-8")
