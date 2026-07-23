"""Visual identity: a near-black, terminal-inspired dark theme — the look
bitchat made familiar (monospace type, a black hull, one signal-green
accent) redrawn for a Tk chat client.

    colors.py   the palette
    fonts.py     the per-OS monospace type system

Import colors/fonts from here rather than redefining them near any one
widget. A new visual variant (e.g. a light theme, a high-contrast theme)
can be added as its own module and swapped in without touching either
file above.
"""
from .colors import *  # noqa: F401,F403
from .fonts import *  # noqa: F401,F403
