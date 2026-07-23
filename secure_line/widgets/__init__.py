"""Reusable low-level Tk drawing helpers for the dark/terminal theme.
Pure widget factories — none of these hold app state, they just build
and return Tk objects for app/ to place.

    shapes.py     rounded-rect drawing primitives, color lerp, file-size format
    cards.py       shadowed dialog/login card
    bubbles.py     chat bubble + typing indicator
    pills.py       system-notice / unread-count pill
    badges.py      avatar badge + mesh-hop status dot
    buttons.py     round icon button
    hover.py       hover-background row binder
    attach_menu.py  modern floating "send a file / send a folder" popup
    file_card.py    thumbnail/icon file-attachment card with open/save
    file_browser.py themed in-app file/folder picker (replaces native OS dialog)

A new drawing primitive (e.g. a reaction chip, a read-receipt tick row)
is a new file here, imported wherever app/ needs it.
"""
from .shapes import draw_round_rect, human_file_size
from .cards import make_shadowed_card
from .bubbles import make_chat_bubble, make_typing_bubble
from .pills import make_pill
from .badges import make_avatar_badge, make_mesh_dot, make_unread_dot
from .buttons import make_round_button
from .hover import bind_hover_bg
from .attach_menu import make_attach_menu
from .file_card import make_file_card, make_thumbnail_image
from .file_browser import ask_path
