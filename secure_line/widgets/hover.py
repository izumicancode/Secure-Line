"""Hover-background binder for grouping widgets into one logical hover
row (sidebar peer/channel rows)."""
import tkinter as tk


def bind_hover_bg(widgets, normal_bg, hover_bg):
    def set_bg(color):
        for w in widgets:
            try:
                w.configure(bg=color)
            except tk.TclError:
                pass

    def on_enter(_e=None):
        set_bg(hover_bg)

    def on_leave(_e=None):
        set_bg(normal_bg)

    for w in widgets:
        w.bind("<Enter>", on_enter, add="+")
        w.bind("<Leave>", on_leave, add="+")
    return on_enter, on_leave
