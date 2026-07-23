"""A themed, in-app file/folder browser -- replaces the native OS file
dialog (which can't be restyled and looks out of place next to the rest
of Line's dark UI) for picking an attachment to send.

Native "Save As" dialogs are left alone (see app/messaging.py) since
that's a different, universally-understood OS flow; this one is
specifically for *picking something to send*, which is the flow that
gets used constantly and is worth making feel native to the app.
"""
import os
import tkinter as tk
from tkinter import messagebox

from ..theme import (
    VOID, HULL, HULL_RAISED, HULL_SOFT, LINE, TEXT, TEXT_DIM, TEXT_FAINT,
    TEXT_ON_ACCENT, SIGNAL, SIGNAL_HOVER, MONO, MONO_SMALL, BODY,
)

_SELECTED_BG = HULL_SOFT

_FOLDER_ICON = "📁"
_FILE_ICONS = {
    ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼", ".bmp": "🖼", ".webp": "🖼",
    ".pdf": "📕", ".doc": "📄", ".docx": "📄", ".txt": "📄", ".md": "📄",
    ".zip": "🗜", ".rar": "🗜", ".7z": "🗜", ".tar": "🗜", ".gz": "🗜",
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".m4a": "🎵",
    ".mp4": "🎬", ".mov": "🎬", ".mkv": "🎬", ".avi": "🎬",
    ".py": "🐍", ".js": "📜", ".json": "🧾", ".csv": "📊", ".xlsx": "📊",
}


def _file_icon(name):
    return _FILE_ICONS.get(os.path.splitext(name)[1].lower(), "📄")


def _human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _list_dir(path):
    try:
        entries = list(os.scandir(path))
    except OSError:
        return [], []
    dirs = sorted((e for e in entries if e.is_dir(follow_symlinks=False)), key=lambda e: e.name.lower())
    files = sorted((e for e in entries if e.is_file(follow_symlinks=False)), key=lambda e: e.name.lower())
    return dirs, files


class _FileBrowserDialog(tk.Toplevel):
    def __init__(self, parent, mode, title):
        super().__init__(parent)
        self.mode = mode  # "file" or "folder"
        self.result = None
        self.current_dir = os.path.abspath(os.path.expanduser("~"))
        self.selected_file = None
        self.selected_row = None  # currently-highlighted row Frame, if any

        self.title(title)
        self.configure(bg=VOID)
        width, height = 640, 480
        self.geometry(f"{width}x{height}")
        self.minsize(480, 380)
        self.transient(parent)

        self._build()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _e: self._cancel())

        # geometry() above only sets a size, not a position -- Tk's
        # default placement for that is the top-left corner of the
        # screen, which is why this used to pop up jammed in a corner
        # instead of centered like every other dialog in the app.
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # grab_set() requires the window to actually be viewable first --
        # calling it too early raises "grab failed: window not viewable",
        # and since this fires inside a Tk callback, it was getting
        # silently swallowed (printed to stderr) with the dialog never
        # appearing at all.
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    # ------------------------------------------------------------------
    def _build(self):
        top = tk.Frame(self, bg=HULL, height=54, highlightthickness=1, highlightbackground=LINE)
        top.pack(fill="x")
        top.pack_propagate(False)

        up_btn = tk.Button(top, text="⬆", font=(MONO[0], 13), bg=HULL_SOFT, fg=TEXT,
                            activebackground=LINE, relief="flat", cursor="hand2",
                            command=self._go_up, width=3, bd=0)
        up_btn.pack(side="left", padx=(12, 8), pady=10)

        home_btn = tk.Button(top, text="⌂", font=(MONO[0], 13), bg=HULL_SOFT, fg=TEXT,
                              activebackground=LINE, relief="flat", cursor="hand2",
                              command=self._go_home, width=3, bd=0)
        home_btn.pack(side="left", padx=(0, 8), pady=10)

        self.path_var = tk.StringVar()
        path_entry = tk.Entry(top, textvariable=self.path_var, font=MONO_SMALL, bg=HULL_SOFT,
                               fg=TEXT_DIM, relief="flat", insertbackground=SIGNAL,
                               highlightthickness=1, highlightbackground=LINE,
                               highlightcolor=SIGNAL)
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=12, ipady=5)
        path_entry.bind("<Return>", lambda _e: self._go_to_typed_path())

        body = tk.Frame(self, bg=VOID)
        body.pack(fill="both", expand=True)

        list_wrap = tk.Frame(body, bg=VOID)
        list_wrap.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        canvas = tk.Canvas(list_wrap, bg=VOID, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.list_frame = tk.Frame(canvas, bg=VOID)
        window = canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        bottom = tk.Frame(self, bg=HULL, highlightthickness=1, highlightbackground=LINE)
        bottom.pack(fill="x", side="bottom")

        self.selection_var = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.selection_var, font=MONO_SMALL, bg=HULL,
                 fg=TEXT_DIM, anchor="w").pack(side="left", padx=16, pady=14, fill="x", expand=True)

        tk.Button(bottom, text="Cancel", font=MONO_SMALL, bg=HULL_SOFT, fg=TEXT, bd=0,
                  activebackground=LINE, relief="flat", cursor="hand2",
                  command=self._cancel, padx=16, pady=7).pack(side="right", padx=(6, 14), pady=12)

        action_text = "Select this folder" if self.mode == "folder" else "Send this file"
        self.action_btn = tk.Button(
            bottom, text=action_text, font=(MONO[0], 10, "bold"), bg=SIGNAL, fg=TEXT_ON_ACCENT,
            activebackground=SIGNAL_HOVER, activeforeground=TEXT_ON_ACCENT, relief="flat", bd=0,
            cursor="hand2", command=self._confirm, padx=18, pady=7,
            state=("normal" if self.mode == "folder" else "disabled"))
        self.action_btn.pack(side="right", padx=6, pady=12)

    # ------------------------------------------------------------------
    def _refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.path_var.set(self.current_dir)
        self.selected_file = None
        self.selected_row = None
        if self.mode == "file":
            self.action_btn.configure(state="disabled")
            self.selection_var.set("no file selected")
        else:
            self.selection_var.set(self.current_dir)

        dirs, files = _list_dir(self.current_dir)
        if not dirs and not files:
            tk.Label(self.list_frame, text="(this folder is empty)", font=MONO_SMALL, bg=VOID,
                      fg=TEXT_FAINT).pack(anchor="w", padx=8, pady=14)
            return

        for entry in dirs:
            self._row(entry.name, _FOLDER_ICON, "", is_dir=True, full_path=entry.path)
        if self.mode == "file":
            for entry in files:
                try:
                    size_label = _human_size(entry.stat().st_size)
                except OSError:
                    size_label = ""
                self._row(entry.name, _file_icon(entry.name), size_label, is_dir=False, full_path=entry.path)

    def _row(self, name, icon, size_label, is_dir, full_path):
        row = tk.Frame(self.list_frame, bg=VOID, cursor="hand2")
        row.pack(fill="x")
        lbl = tk.Label(row, text=f"{icon}  {name}", font=BODY, bg=VOID, fg=TEXT, anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        size_lbl = None
        if size_label:
            size_lbl = tk.Label(row, text=size_label, font=MONO_SMALL, bg=VOID, fg=TEXT_FAINT)
            size_lbl.pack(side="right", padx=10)

        widgets = [row, lbl] + ([size_lbl] if size_lbl else [])

        def is_selected():
            return (not is_dir) and self.selected_row is row

        def enter(_e):
            if not is_selected():
                for w in widgets:
                    w.configure(bg=HULL_SOFT)

        def leave(_e):
            if not is_selected():
                for w in widgets:
                    w.configure(bg=VOID)

        def click(_e):
            if is_dir:
                self.current_dir = full_path
                self._refresh()
            else:
                # Clear the previous selection's highlight before marking
                # the new one, so exactly one row stays lit.
                if self.selected_row is not None and self.selected_row.winfo_exists():
                    for w in self.selected_row.winfo_children() + [self.selected_row]:
                        w.configure(bg=VOID)
                self.selected_file = full_path
                self.selected_row = row
                for w in widgets:
                    w.configure(bg=_SELECTED_BG)
                self.selection_var.set(name)
                self.action_btn.configure(state="normal")

        for w in widgets:
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", click)

    # ------------------------------------------------------------------
    def _go_up(self):
        parent = os.path.dirname(self.current_dir.rstrip(os.sep))
        if parent and parent != self.current_dir:
            self.current_dir = parent
            self._refresh()

    def _go_home(self):
        self.current_dir = os.path.abspath(os.path.expanduser("~"))
        self._refresh()

    def _go_to_typed_path(self):
        path = os.path.expanduser(self.path_var.get().strip())
        if path and os.path.isdir(path):
            self.current_dir = os.path.abspath(path)
            self._refresh()
        else:
            messagebox.showerror("Not found", "That path doesn't exist or isn't a folder.", parent=self)

    def _confirm(self):
        self.result = self.current_dir if self.mode == "folder" else self.selected_file
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


def ask_path(parent, mode="file", title=None):
    """Opens the themed modal picker and blocks until the user chooses
    or cancels. `mode` is "file" or "folder". Returns an absolute path,
    or None if cancelled."""
    title = title or ("Choose a folder to send" if mode == "folder" else "Choose a file to send")
    dlg = _FileBrowserDialog(parent, mode, title)
    parent.wait_window(dlg)
    return dlg.result
