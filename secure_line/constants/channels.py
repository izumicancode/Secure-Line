"""Channels (public/topic rooms, bitchat-style '#channel' spaces)."""

CHANNEL_PREFIX = "#"
DEFAULT_CHANNEL = "#general"
CHANNEL_SCRYPT_N = 2 ** 13   # lighter than the account KDF — this only gates a shared room key
CHANNEL_SCRYPT_R = 8
CHANNEL_SCRYPT_P = 1
CHANNEL_SALT_BYTES = 16
MAX_CHANNEL_HISTORY = 500
