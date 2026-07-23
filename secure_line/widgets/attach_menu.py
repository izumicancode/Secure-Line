"""Modern attachment picker — a small floating popup (rounded card, hover
rows, subtle drop-shadow) that replaces jumping straight to the raw OS
file dialog. Lets the composer offer both "send a file" and "send a
folder" from the same paperclip button without cluttering the toolbar."""
import tkinter as tk

from ..theme import HULL_RAISED, LINE, TEXT, MONO_SMALL, ROW_HOVER, SHADOW


def make_attach_menu(root, anchor, on_file, on_folder):
    """Pops a small dark card above/near `anchor` with two rows. Closes
    itself on selection or on losing focus. Returns the Toplevel in case
    the caller wants to force-close it."""
    popup = tk.Toplevel(root)
    popup.withdraw()
    popup.overrideredirect(True)
    popup.configure(bg=SHADOW)
    try:
        popup.attributes("-topmost", True)
    except tk.TclError:
        pass

    shell = tk.Frame(popup, bg=SHADOW)
    shell.pack()
    card = tk.Frame(shell, bg=HULL_RAISED, highlightthickness=1, highlightbackground=LINE)
    card.pack(padx=(0, 3), pady=(0, 3))  # offsets a sliver of SHADOW behind/right for depth

    def close(_e=None):
        try:
            popup.destroy()
        except Exception:
            pass

    def add_row(icon, label, cmd, is_last=False):
        row = tk.Frame(card, bg=HULL_RAISED, cursor="hand2")
        row.pack(fill="x")
        lbl = tk.Label(row, text=f"{icon}   {label}", font=MONO_SMALL, bg=HULL_RAISED, fg=TEXT,
                        anchor="w", padx=16, pady=11)
        lbl.pack(fill="x")

        def on_enter(_e):
            row.configure(bg=ROW_HOVER)
            lbl.configure(bg=ROW_HOVER)

        def on_leave(_e):
            row.configure(bg=HULL_RAISED)
            lbl.configure(bg=HULL_RAISED)

        def on_click(_e):
            close()
            cmd()

        for w in (row, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
        if not is_last:
            tk.Frame(card, bg=LINE, height=1).pack(fill="x")

    add_row("📄", "Send a file", on_file)
    add_row("📁", "Send a folder (zipped)", on_folder, is_last=True)

    popup.update_idletasks()
    w = popup.winfo_reqwidth()
    h = popup.winfo_reqheight()
    x = anchor.winfo_rootx() - (w // 2) + (anchor.winfo_width() // 2)
    y = anchor.winfo_rooty() - h - 10
    if y < 0:
        y = anchor.winfo_rooty() + anchor.winfo_height() + 10
    popup.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    popup.deiconify()

    popup.bind("<FocusOut>", close)
    popup.bind("<Escape>", close)
    popup.after(20, lambda: popup.focus_force())
    return popup
