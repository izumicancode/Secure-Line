"""Type system — monospace-forward, terminal-radio feel. Bold mono for
identity/brand, regular mono for body text (readable, not decorative), a
plain sans kept only for emoji rendering fallback. Sized per-OS so the
app looks right on Windows/macOS/Linux without any manual tweaking.
"""
import platform

_OS = platform.system()
if _OS == "Windows":
    MONO = ("Cascadia Mono", 10)
    MONO_SMALL = ("Cascadia Mono", 9)
    DISPLAY = ("Cascadia Mono", 20, "bold")
    DISPLAY_SMALL = ("Cascadia Mono", 13, "bold")
    BODY = ("Cascadia Mono", 11)
    BODY_SMALL = ("Cascadia Mono", 9)
    EMOJI_FONT = ("Segoe UI Emoji", 16)
elif _OS == "Darwin":
    MONO = ("Menlo", 11)
    MONO_SMALL = ("Menlo", 9)
    DISPLAY = ("Menlo", 21, "bold")
    DISPLAY_SMALL = ("Menlo", 14, "bold")
    BODY = ("Menlo", 12)
    BODY_SMALL = ("Menlo", 10)
    EMOJI_FONT = ("Apple Color Emoji", 16)
else:
    MONO = ("DejaVu Sans Mono", 10)
    MONO_SMALL = ("DejaVu Sans Mono", 9)
    DISPLAY = ("DejaVu Sans Mono", 19, "bold")
    DISPLAY_SMALL = ("DejaVu Sans Mono", 13, "bold")
    BODY = ("DejaVu Sans Mono", 11)
    BODY_SMALL = ("DejaVu Sans Mono", 9)
    EMOJI_FONT = ("Noto Color Emoji", 16)
