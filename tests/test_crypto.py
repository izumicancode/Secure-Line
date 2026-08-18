"""Unit tests for the crypto core: key agreement, ratchet, envelope,
channel keys. No networking, storage, or UI involved."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.asymmetric import x25519

from secure_line.crypto import (
    b64e, b64d, fingerprint, safety_number, derive_root_key,
    derive_channel_key, channel_fingerprint, Ratchet,
    encrypt_with_key, decrypt_with_key,
)


def test_b64_roundtrip():
    data = os.urandom(37)
    assert b64d(b64e(data)) == data


def test_fingerprint_deterministic_and_formatted():
    pub = os.urandom(32)
    fp1 = fingerprint(pub)
    fp2 = fingerprint(pub)
    assert fp1 == fp2
    assert len(fp1.replace(":", "")) == 16
    assert all(c in "0123456789ABCDEF:" for c in fp1)


def test_safety_number_is_order_independent():
    a = os.urandom(32)
    b = os.urandom(32)
    assert safety_number(a, b) == safety_number(b, a)


def test_safety_number_differs_for_different_keys():
    a, b, c = os.urandom(32), os.urandom(32), os.urandom(32)
    assert safety_number(a, b) != safety_number(a, c)


def test_derive_root_key_agreement_matches_both_sides():
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    priv_a = x25519.X25519PrivateKey.generate()
    priv_b = x25519.X25519PrivateKey.generate()
    pub_a = priv_a.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    pub_b = priv_b.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    root_a = derive_root_key(priv_a, pub_b)
    root_b = derive_root_key(priv_b, pub_a)
    assert root_a == root_b
    assert len(root_a) == 32


def test_channel_key_deterministic_for_same_name_and_password():
    k1 = derive_channel_key("#general", "hunter2")
    k2 = derive_channel_key("#general", "hunter2")
    assert k1 == k2
    assert len(k1) == 32


def test_channel_key_differs_for_different_password():
    k1 = derive_channel_key("#general", "hunter2")
    k2 = derive_channel_key("#general", "different")
    assert k1 != k2


def test_channel_fingerprint_short_and_stable():
    fp = channel_fingerprint("#kitchen-table", "pw")
    assert len(fp) == 6
    assert fp == channel_fingerprint("#kitchen-table", "pw")


def test_envelope_roundtrip():
    key = os.urandom(32)
    aad = b"context"
    nonce, ct = encrypt_with_key(key, aad, "hello, world")
    pt = decrypt_with_key(key, aad, nonce, ct)
    assert pt == "hello, world"


def test_envelope_tamper_detection():
    import pytest
    key = os.urandom(32)
    aad = b"context"
    nonce, ct = encrypt_with_key(key, aad, "secret message")
    # Flip a byte in the ciphertext -> should fail to decrypt
    bad_ct = b64e(bytearray(b64d(ct)[:-1]) + bytes([b64d(ct)[-1] ^ 0xFF]))
    with pytest.raises(Exception):
        decrypt_with_key(key, aad, nonce, bad_ct)


def test_ratchet_forward_secrecy_and_ordering():
    root = os.urandom(32)
    alice = Ratchet(root, am_i_a=True)
    bob = Ratchet(root, am_i_a=False)

    n1, k1 = alice.next_send_key()
    n2, k2 = alice.next_send_key()
    assert n1 == 0 and n2 == 1
    assert k1 != k2

    # Bob receives them in order
    assert bob.recv_key_for(n1) == k1
    assert bob.recv_key_for(n2) == k2


def test_ratchet_out_of_order_delivery():
    root = os.urandom(32)
    alice = Ratchet(root, am_i_a=True)
    bob = Ratchet(root, am_i_a=False)

    n0, k0 = alice.next_send_key()
    n1, k1 = alice.next_send_key()
    n2, k2 = alice.next_send_key()

    # Bob receives message 2 first (skips 0 and 1)
    assert bob.recv_key_for(n2) == k2
    # Then receives the skipped ones out of order
    assert bob.recv_key_for(n0) == k0
    assert bob.recv_key_for(n1) == k1


def test_ratchet_export_import_state():
    root = os.urandom(32)
    alice = Ratchet(root, am_i_a=True)
    alice.next_send_key()
    state = alice.export_state()

    restored = Ratchet(root, am_i_a=True, state=state)
    assert restored.send_n == alice.send_n
    n_next, k_next = restored.next_send_key()
    # Continues where it left off, not from scratch
    assert n_next == 1
