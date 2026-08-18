"""Line — a verified, end-to-end-encrypted, mesh-relayed LAN chat.

Bitchat-inspired: no server, no accounts beyond a local password-wrapped
identity, public/topic channels, mesh relay + store-and-forward for peers
who are briefly offline, favorites, and a one-tap panic wipe.

Every module now lives in its own folder (subpackage), split one feature
per file, so adding or upgrading a feature means adding/editing one small
file instead of a large monolith:

    constants/       network/timing/on-disk-layout numbers, presets — one file per concern
    theme/            dark, monospace/terminal palette + fonts
    crypto/           X25519, the per-conversation ratchet, AES-GCM, channel keys
    storage/          password-wrapped identity + encrypted local store
    netutils/         LAN address discovery, callsign/channel-name validation
    models/           Peer / Profile / Channel / ChatEntry data classes, one per file
    mesh/             seen-cache, relay queue, hop-limit helpers
    node/             LineNode — discovery + DM + channel networking core, one mixin per feature
    widgets/          reusable Tk drawing helpers (bubbles, pills, mesh dot), one per widget kind
    app/              LineApp — the GUI, one mixin per feature area
    platform_setup/   firewall / high-DPI OS integration
    main.py           entry point (`python -m secure_line`)

See each subpackage's __init__.py for the file-by-file breakdown.
"""
__version__ = "3.2.0"


def __getattr__(name):
    # Lazy: `secure_line.main` pulls in tkinter (GUI), which isn't
    # installed in every environment (headless CI, unit tests that only
    # exercise crypto/storage/etc.). Importing it eagerly here used to
    # make the whole package - including non-GUI subpackages - unusable
    # without a display/Tk. Deferring the import means
    # `from secure_line import main` still works when Tk is available,
    # while `import secure_line.crypto` (etc.) works everywhere.
    if name == "main":
        from .main import main as _main
        return _main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
