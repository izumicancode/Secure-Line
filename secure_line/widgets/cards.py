"""Shadowed card frame, used for login/dialog surfaces."""
import tkinter as tk

from ..theme import SHADOW


def make_shadowed_card(parent, bg_root, fill, border, pad_x=0, pad_y=0):
    """A frame with a soft drop-shadow behind it, used for login/dialog cards."""
    outer = tk.Frame(parent, bg=bg_root)
    shadow = tk.Frame(outer, bg=SHADOW)
    shadow.place(x=4, y=6, relwidth=1, relheight=1)
    card = tk.Frame(outer, bg=fill, highlightbackground=border, highlightthickness=1)
    card.place(x=0, y=0, relwidth=1, relheight=1)
    return outer, card
