"""LineApp — the GUI. Dark, monospace, mesh-radio inspired: a sidebar of
direct peers and joined channels, a chat pane with rounded bubbles, a
panic-wipe control, favorites, and channel join/create.

Split one feature area per file so a new UI feature is a new mixin file:

    login.py        LoginScreen (callsign + password, create/unlock account)
    core.py           LineApp: __init__, login handoff, local-state save/load
    layout.py         static window chrome (header/sidebar/chat-pane shells)
    sidebar.py         sidebar row rendering (channels, peers, favorites)
    channels.py        join/create/open a channel
    messaging.py        send/attach/render DM + channel messages
    events.py           poll LineNode's event queue, update the UI
    safety.py           ephemeral toggle, panic wipe, safety-number verify
"""
from .login import LoginScreen
from .core import LineApp
