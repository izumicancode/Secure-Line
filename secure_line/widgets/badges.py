"""Round avatar badge (emoji + colored ring) and the mesh-hop status dot
(solid = direct peer, hollow ring = reached via mesh relay only)."""
import tkinter as tk

from ..theme import PANEL_SOFT, EMOJI_FONT, SIGNAL, SIGNAL_GLOW, UNREAD_BG
from .shapes import draw_round_rect


def make_avatar_badge(parent, emoji, ring_color, diameter=40, bg_behind=None):
    bg_behind = bg_behind or parent["bg"]
    cvs = tk.Canvas(parent, width=diameter, height=diameter, bg=bg_behind, highlightthickness=0, bd=0)
    r = diameter / 2
    ring = draw_round_rect(cvs, 1.5, 1.5, diameter - 1.5, diameter - 1.5, (r, r, r, r),
                            fill=PANEL_SOFT, outline=ring_color, width=1.6)
    glyph = cvs.create_text(diameter / 2, diameter / 2, text=emoji, font=(EMOJI_FONT[0], int(diameter * 0.42)))

    def set_avatar(new_emoji, new_ring_color):
        cvs.itemconfig(glyph, text=new_emoji)
        cvs.itemconfig(ring, outline=new_ring_color)

    cvs.set_avatar = set_avatar
    return cvs


def make_mesh_dot(parent, hops=0, diameter=10, bg_behind=None):
    """A tiny status dot: solid signal-green for a direct peer, a hollow
    ring for one reached only via mesh relay — the same visual language
    bitchat uses to show 'direct' vs 'multi-hop' reachability."""
    bg_behind = bg_behind or parent["bg"]
    cvs = tk.Canvas(parent, width=diameter, height=diameter, bg=bg_behind, highlightthickness=0, bd=0)
    if hops <= 0:
        cvs.create_oval(1, 1, diameter - 1, diameter - 1, fill=SIGNAL, outline=SIGNAL)
    else:
        cvs.create_oval(1, 1, diameter - 1, diameter - 1, fill=bg_behind, outline=SIGNAL_GLOW, width=1.6)
    return cvs


def make_unread_dot(parent, diameter=9, bg_behind=None):
    """A small solid red dot marking unread activity -- same visual
    language as a notification dot on a channel/app icon. Used on a
    peer's sidebar row when a DM has arrived that the user hasn't
    opened yet."""
    bg_behind = bg_behind or parent["bg"]
    cvs = tk.Canvas(parent, width=diameter, height=diameter, bg=bg_behind, highlightthickness=0, bd=0)
    cvs.create_oval(1, 1, diameter - 1, diameter - 1, fill=UNREAD_BG, outline=UNREAD_BG)
    return cvs
