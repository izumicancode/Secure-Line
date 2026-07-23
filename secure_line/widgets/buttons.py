"""Rounded-square icon button drawn on a Canvas so it matches the
rounded-square badge language used for avatars."""
import tkinter as tk

from ..theme import PANEL_SOFT, MONO, TEXT_FAINT
from .shapes import draw_round_rect


def make_round_button(parent, diameter, glyph, fill, glyph_color, command, hover_fill=None):
    """Exposes .set_enabled(bool) since Canvas has no native disabled
    visual state."""
    hover_fill = hover_fill or fill
    disabled_fill = PANEL_SOFT
    cvs = tk.Canvas(parent, width=diameter, height=diameter, bg=parent["bg"],
                     highlightthickness=0, bd=0, cursor="hand2")
    r = diameter * 0.28
    shape = draw_round_rect(cvs, 2, 2, diameter - 2, diameter - 2, (r, r, r, r), fill=fill, outline=fill)
    glyph_id = cvs.create_text(diameter / 2, diameter / 2, text=glyph, fill=glyph_color,
                                font=(MONO[0], int(diameter * 0.36), "bold"))
    cvs.enabled = True

    def on_enter(_e):
        if cvs.enabled:
            cvs.itemconfig(shape, fill=hover_fill, outline=hover_fill)

    def on_leave(_e):
        if cvs.enabled:
            cvs.itemconfig(shape, fill=fill, outline=fill)

    def on_click(_e):
        if cvs.enabled:
            command()

    def set_enabled(is_enabled: bool):
        cvs.enabled = is_enabled
        if is_enabled:
            cvs.itemconfig(shape, fill=fill, outline=fill)
            cvs.itemconfig(glyph_id, fill=glyph_color)
            cvs.config(cursor="hand2")
        else:
            cvs.itemconfig(shape, fill=disabled_fill, outline=disabled_fill)
            cvs.itemconfig(glyph_id, fill=TEXT_FAINT)
            cvs.config(cursor="arrow")

    cvs.set_enabled = set_enabled
    for tag in (shape, glyph_id):
        cvs.tag_bind(tag, "<Enter>", on_enter)
        cvs.tag_bind(tag, "<Leave>", on_leave)
        cvs.tag_bind(tag, "<Button-1>", on_click)
    cvs.bind("<Enter>", on_enter)
    cvs.bind("<Leave>", on_leave)
    cvs.bind("<Button-1>", on_click)
    return cvs
