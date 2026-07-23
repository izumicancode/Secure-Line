"""Low-level key helpers: base64 wire encoding, identity fingerprints,
out-of-band safety numbers, and X25519 root-key derivation."""
import hashlib

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from .encoding import b64e, b64d  # noqa: F401 -- re-exported for convenience


def fingerprint(pub_bytes: bytes) -> str:
    h = hashlib.sha256(pub_bytes).hexdigest()[:16]
    return ":".join(h[i:i + 2] for i in range(0, len(h), 2)).upper()


def safety_number(pub_a: bytes, pub_b: bytes) -> str:
    """Order-independent fingerprint of both sides' identity keys. Compare
    this out-of-band (voice/in person) to defeat a first-contact MITM."""
    combined = b"".join(sorted([pub_a, pub_b]))
    h = hashlib.sha256(combined).hexdigest()[:30]
    return " ".join(h[i:i + 5] for i in range(0, 30, 5)).upper()


def derive_root_key(my_private_key: x25519.X25519PrivateKey, their_pub_bytes: bytes) -> bytes:
    their_public_key = x25519.X25519PublicKey.from_public_bytes(their_pub_bytes)
    shared_secret = my_private_key.exchange(their_public_key)
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"secure-line-root-v2").derive(shared_secret)
