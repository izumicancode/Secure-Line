"""Local persistence layout (identity + encrypted trust/history/ratchet store).

    <app folder>/line_data/<name>/identity.key   password-wrapped X25519 key
    <app folder>/line_data/<name>/store.enc      AES-GCM blob: trust/connections/
                                     ratchet state/profile/history/channels/favorites

Everything lives next to the top-level package, not the home directory, so
the app stays fully portable — copy the folder and it all moves with it.
"""
import os

# secure_line/constants/storage.py -> up three levels to reach the app folder
# that contains the secure_line package itself.
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STORE_ROOT = os.path.join(APP_DIR, "line_data")
STORE_FORMAT_VERSION = 2
MAX_HISTORY_PER_PEER = 2000
ACCOUNT_SALT_BYTES = 16
ACCOUNT_SCRYPT_N = 2 ** 14
ACCOUNT_SCRYPT_R = 8
ACCOUNT_SCRYPT_P = 1

# Connection states (profile-sharing relationship, independent of "verified")
CONN_NONE = "none"
CONN_SENT = "sent"
CONN_RECEIVED = "received"
CONN_CONNECTED = "connected"
