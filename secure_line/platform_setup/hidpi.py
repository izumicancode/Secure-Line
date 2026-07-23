"""High-DPI Windows fixes: DPI awareness + Tk scale sync."""
import platform


def _enable_hidpi_awareness():
    """Tell Windows we're DPI-aware *before* any Tk window is created, so
    Tk's own layout math matches the real scale factor from the start."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # Per-Monitor v2
        return
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor v1
        return
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()  # System DPI aware, last resort
    except Exception:
        pass


def _apply_tk_scaling(root):
    """Sync Tk's internal 'points-per-pixel' scaling with the display's
    actual DPI so point-sized fonts and pixel-sized widgets stay in
    proportion on every machine."""
    try:
        dpi = root.winfo_fpixels("1i")
        if dpi > 0:
            root.tk.call("tk", "scaling", dpi / 72.0)
    except Exception:
        pass
