"""Ephemeral messaging + panic wipe (bitchat-style: nothing is kept unless
you say so, and one gesture erases everything)."""

EPHEMERAL_DEFAULT = False         # fresh accounts persist everything locally by default;
                                   # ephemeral mode is still there as an opt-in toggle
PANIC_TAP_WINDOW = 1.2            # seconds allowed between panic-button clicks
PANIC_TAPS_REQUIRED = 3           # triple-tap wipe, same gesture as bitchat's panic button

AVATAR_PRESETS = ["🙂", "🦊", "🐢", "🐙", "🌵", "🚀", "🎧", "🔥", "🌊", "🐧", "🧭", "⚡", "👾", "🛰️"]
COLOR_PRESETS = ["#39FF88", "#5CC8FF", "#FFB454", "#FF6E6E", "#C792EA", "#7FE3D0"]
