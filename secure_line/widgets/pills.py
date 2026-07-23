"""Centered rounded pill, used for system/dropped/banner notices and
unread-count badges."""
import tkinter as tk

from ..theme import BG, MONO_SMALL
from .shapes import draw_round_rect


def make_pill(parent, text, fg, fill, max_width, bg_behind=BG, italic=True):
    font = (MONO_SMALL[0], MONO_SMALL[1], "italic") if italic else MONO_SMALL
    pad_x, pad_y = 12, 7
    cvs = tk.Canvas(parent, bg=bg_behind, highlightthickness=0, bd=0)
    probe = cvs.create_text(0, 0, text=text, font=font, width=max_width, anchor="nw", justify="center")
    bbox = cvs.bbox(probe)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    cvs.delete(probe)
    cw, ch = tw + pad_x * 2, th + pad_y * 2
    cvs.config(width=cw, height=ch)
    r = 9
    draw_round_rect(cvs, 1, 1, cw - 1, ch - 1, (r, r, r, r), fill=fill, outline=fill)
    cvs.create_text(cw / 2, ch / 2, text=text, font=font, fill=fg, width=max_width, anchor="center", justify="center")
    return cvs
