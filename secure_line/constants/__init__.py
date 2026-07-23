"""All fixed, non-visual configuration for Line, split one concern per
file so a new tuning knob for a feature (mesh, channels, ephemeral mode,
...) has an obvious, small home instead of one growing constants.py.

    network.py      ports, timings, wire-frame limits
    mesh.py          mesh-relay / store-and-forward tuning
    channels.py      channel (room) settings
    storage.py       on-disk layout + KDF cost parameters
    ephemeral.py     ephemeral-mode + panic-wipe settings, avatar/color presets

Everything is re-exported here so existing `from .constants import X`
imports keep working unchanged.
"""
from .network import *  # noqa: F401,F403
from .mesh import *  # noqa: F401,F403
from .channels import *  # noqa: F401,F403
from .storage import *  # noqa: F401,F403
from .ephemeral import *  # noqa: F401,F403
