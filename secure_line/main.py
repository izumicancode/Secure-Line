"""Entry point: prepares the local data directory and display, then hands
off to LineApp. Run with `python -m secure_line`."""
import argparse
import sys
import tkinter as tk
from tkinter import font as tkfont

from .app import LineApp
from .constants import STORE_ROOT
from .platform_setup import _apply_tk_scaling, _enable_hidpi_awareness, try_configure_firewall
from .storage import _secure_makedirs
from .theme import BODY, VOID


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="secure-line",
        description="A verified, end-to-end-encrypted, mesh-relayed LAN chat app.",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="print the installed Secure Line version and exit",
    )
    return parser.parse_args(argv)


def main():
    args = _parse_args()
    if args.version:
        from . import __version__
        print(f"secure-line {__version__}")
        sys.exit(0)

    _secure_makedirs(STORE_ROOT)
    _enable_hidpi_awareness()
    try_configure_firewall()
    root = tk.Tk()
    root.configure(bg=VOID)
    _apply_tk_scaling(root)
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=BODY[0], size=11)
    except Exception:
        pass

    root.title("LINE")
    root.minsize(760, 520)
    width, height = 1180, 760
    root.update_idletasks()
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 3)
    root.geometry(f"{width}x{height}+{x}+{y}")

    LineApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
