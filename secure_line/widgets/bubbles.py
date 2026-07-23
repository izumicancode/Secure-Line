"""Chat bubbles: the tightly-fitted rounded-rectangle message bubble
(with optional mesh-hop tag and fade-in) and the animated typing
indicator."""
import tkinter as tk

from ..theme import (
    BG, BODY, MONO_SMALL, TEXT, TEXT_FAINT, LINK, SIGNAL,
    BUBBLE_MINE, BUBBLE_MINE_BORDER, BUBBLE_THEIRS, BUBBLE_THEIRS_BORDER,
)
from .shapes import draw_round_rect, _lerp_color


def _colors():
    return BUBBLE_MINE, BUBBLE_MINE_BORDER, BUBBLE_THEIRS, BUBBLE_THEIRS_BORDER


def make_chat_bubble(parent, text, mine, max_width, bg_behind=BG, animate=False,
                      hops=0, mention=False):
    """`hops` > 0 draws a tiny mesh-relay tag ("2 hops") in the corner;
    `mention` outlines the bubble in the link color when it @mentions us."""
    bubble_mine, bubble_mine_border, bubble_theirs, bubble_theirs_border = _colors()
    color = bubble_mine if mine else bubble_theirs
    border = LINK if mention else (bubble_mine_border if mine else bubble_theirs_border)
    text_color = TEXT
    pad_x, pad_y = 15, 10
    cvs = tk.Canvas(parent, bg=bg_behind, highlightthickness=0, bd=0)
    probe = cvs.create_text(0, 0, text=text, font=BODY, width=max_width, anchor="nw", justify="left")
    bbox = cvs.bbox(probe)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    cvs.delete(probe)
    cw, ch = tw + pad_x * 2, th + pad_y * 2
    if hops:
        ch += 14
    cvs.config(width=cw, height=ch)
    full, flat = 12, 4
    radii = (full, full, flat, full) if mine else (full, full, full, flat)

    start_fill = bg_behind if animate else color
    start_border = bg_behind if animate else border
    start_text = bg_behind if animate else text_color
    rect_id = draw_round_rect(cvs, 1, 1, cw - 1, ch - 1, radii, fill=start_fill, outline=start_border, width=1)
    text_id = cvs.create_text(pad_x, pad_y, text=text, font=BODY, fill=start_text, width=max_width,
                               anchor="nw", justify="left")
    if hops:
        cvs.create_text(cw - pad_x, ch - 6, text=f"\u21bb {hops} hop{'s' if hops != 1 else ''}",
                         font=MONO_SMALL, fill=TEXT_FAINT, anchor="se")

    if animate:
        steps = 7

        def _step(i=0):
            try:
                t = i / steps
                cvs.itemconfig(rect_id, fill=_lerp_color(bg_behind, color, t),
                                outline=_lerp_color(bg_behind, border, t))
                cvs.itemconfig(text_id, fill=_lerp_color(bg_behind, text_color, t))
                if i < steps:
                    cvs.after(16, _step, i + 1)
            except tk.TclError:
                pass  # widget destroyed mid-animation (e.g. user switched chats)

        cvs.after(10, _step, 0)

    return cvs


def make_typing_bubble(parent, bg_behind=BG):
    """A small 'theirs'-style bubble with three dots bouncing in a
    staggered wave — the live typing indicator."""
    _, _, color, border = _colors()
    w, h = 54, 32
    cvs = tk.Canvas(parent, width=w, height=h, bg=bg_behind, highlightthickness=0, bd=0)
    draw_round_rect(cvs, 1, 1, w - 1, h - 1, (14, 14, 14, 4), fill=color, outline=border, width=1)
    dot_r = 3
    cy = h / 2
    xs = [w / 2 - 12, w / 2, w / 2 + 12]
    dots = [cvs.create_oval(x - dot_r, cy - dot_r, x + dot_r, cy + dot_r, fill=SIGNAL, outline="")
            for x in xs]

    def _pulse(i=0):
        try:
            if not cvs.winfo_exists():
                return
            for idx, d in enumerate(dots):
                local = (i - idx * 3) % 12
                t = local / 12
                lift = 3 * max(0.0, 1 - abs(t - 0.25) / 0.25) if t < 0.5 else 0.0
                cvs.coords(d, xs[idx] - dot_r, cy - lift - dot_r, xs[idx] + dot_r, cy - lift + dot_r)
            cvs.after(90, _pulse, i + 1)
        except tk.TclError:
            pass

    cvs.after(10, _pulse, 0)
    return cvs
