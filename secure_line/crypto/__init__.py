"""Cryptographic core: X25519 key agreement, the per-conversation
ratchet, AES-GCM envelope helpers, and password-derived channel keys.
No networking, storage, or UI code lives here — this is the one
subpackage that should need security review after any change.

    encoding.py       base64 wire helpers
    keys.py            fingerprints, safety numbers, root-key derivation
    channel_keys.py    passphrase-derived shared-room keys
    ratchet.py         the per-conversation double-ratchet-style chain
    envelope.py        AES-GCM encrypt/decrypt

A brand-new crypto feature (e.g. a new AEAD, a group-channel scheme)
gets its own file here rather than growing one of the existing ones.
"""
from .encoding import b64e, b64d
from .keys import fingerprint, safety_number, derive_root_key
from .channel_keys import derive_channel_key, channel_fingerprint
from .ratchet import Ratchet
from .envelope import encrypt_with_key, decrypt_with_key
