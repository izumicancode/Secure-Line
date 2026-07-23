"""Small helpers for LAN discovery and name validation.

    discovery.py     local IP enumeration, broadcast targets
    validation.py    callsign / channel-name rules
"""
from .discovery import local_ips, broadcast_targets
from .validation import valid_name, valid_channel_name, normalize_channel_name
