"""Best-effort OS integration that has nothing to do with the app's
logic: opening the LAN discovery/chat ports in the local firewall, and
making sure Tk renders at the right size on high-DPI Windows displays.

    firewall.py   per-platform firewall rule setup
    hidpi.py       Windows DPI awareness + Tk scaling
"""
from .firewall import try_configure_firewall
from .hidpi import _enable_hidpi_awareness, _apply_tk_scaling
