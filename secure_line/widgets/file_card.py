"""File attachment card: the thing a "file" ChatEntry renders as instead
of a plain text bubble. Shows an image thumbnail (via Pillow) when the
attachment is a picture, otherwise a type icon; always shows the
filename, a human size, and Open / Save As buttons that work on the
sender's own copy just as well as a recipient's downloaded one.
"""
import os
import tkinter as tk

from ..theme import (
    BG, BODY, BODY_SMALL, MONO_SMALL, TEXT, TEXT_DIM, TEXT_ON_ACCENT, TEXT_FAINT,
    SIGNAL, SIGNAL_HOVER, HULL_SOFT, LINE,
    BUBBLE_MINE, BUBBLE_MINE_BORDER, BUBBLE_THEIRS, BUBBLE_THEIRS_BORDER,
)
from .shapes import draw_round_rect

try:
    from PIL import Image, ImageTk, ImageOps
    _HAS_PIL = True
except Exception:  # Pillow not installed -- fall back to icon-only cards
    _HAS_PIL = False

_THUMB_SIZE = (168, 168)

_ICONS = {
    ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼", ".bmp": "🖼", ".webp": "🖼",
    ".pdf": "📕", ".doc": "📄", ".docx": "📄", ".txt": "📄", ".md": "📄",
    ".zip": "🗜", ".rar": "🗜", ".7z": "🗜", ".tar": "🗜", ".gz": "🗜",
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".m4a": "🎵",
    ".mp4": "🎬", ".mov": "🎬", ".mkv": "🎬", ".avi": "🎬",
    ".py": "🐍", ".js": "📜", ".json": "🧾", ".csv": "📊", ".xlsx": "📊",
}


def _icon_for(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return _ICONS.get(ext, "📎")


def make_thumbnail_image(path: str):
    """Returns a Tk-compatible PhotoImage thumbnail for an image file on
    disk, or None if it isn't an image / Pillow isn't available / the
    file can't be decoded. Caller must keep a reference (Tk drops
    PhotoImages with no live Python reference)."""
    if not _HAS_PIL or not path or not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail(_THUMB_SIZE, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def make_file_card(parent, filename, size_label, mine, thumbnail_photo=None,
                    on_open=None, on_save=None, bg_behind=BG, available=True):
    """A rounded card (same family as the chat bubble) showing a file
    attachment: thumbnail-or-icon, name, size, and Open/Save buttons.
    `available=False` greys the buttons out (e.g. the file no longer
    exists on disk -- moved, deleted, or never finished downloading)."""
    color = BUBBLE_MINE if mine else BUBBLE_THEIRS
    border = BUBBLE_MINE_BORDER if mine else BUBBLE_THEIRS_BORDER

    cvs = tk.Canvas(parent, bg=bg_behind, highlightthickness=0, bd=0)
    inner = tk.Frame(cvs, bg=color)

    if thumbnail_photo is not None:
        thumb = tk.Label(inner, image=thumbnail_photo, bg=color)
        thumb.image = thumbnail_photo  # keep a reference alive
        thumb.pack(padx=14, pady=(14, 8))
    else:
        tk.Label(inner, text=_icon_for(filename), font=(BODY[0], 30), bg=color, fg=TEXT).pack(
            padx=14, pady=(16, 6))

    tk.Label(inner, text=filename, font=BODY_SMALL, bg=color, fg=TEXT, wraplength=190,
              justify="center").pack(padx=14)
    tk.Label(inner, text=size_label, font=MONO_SMALL, bg=color, fg=TEXT_DIM).pack(pady=(2, 10))

    btn_row = tk.Frame(inner, bg=color)
    btn_row.pack(pady=(0, 14))

    def _btn(row, text, cmd, primary=False):
        fg = TEXT_ON_ACCENT if primary else TEXT
        bg = SIGNAL if primary else HULL_SOFT
        hover = SIGNAL_HOVER if primary else LINE
        state = "normal" if available else "disabled"
        b = tk.Button(row, text=text, font=MONO_SMALL, bg=bg, fg=fg, activebackground=hover,
                       activeforeground=fg, relief="flat", cursor="hand2" if available else "arrow",
                       state=state, padx=10, pady=4, command=cmd if available else None,
                       disabledforeground=TEXT_FAINT)
        b.pack(side="left", padx=4)
        return b

    _btn(btn_row, "Open", on_open, primary=True)
    _btn(btn_row, "Save As\u2026", on_save)

    if not available:
        tk.Label(inner, text="no longer available locally", font=MONO_SMALL, bg=color,
                  fg=TEXT_FAINT).pack(pady=(0, 10))

    inner.update_idletasks()
    w = inner.winfo_reqwidth()
    h = inner.winfo_reqheight()
    cvs.config(width=w, height=h)
    radii = (12, 12, 4, 12) if mine else (12, 12, 12, 4)
    draw_round_rect(cvs, 1, 1, w - 1, h - 1, radii, fill=color, outline=border, width=1)
    cvs.create_window(0, 0, window=inner, anchor="nw")
    return cvs
