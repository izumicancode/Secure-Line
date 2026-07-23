"""LineApp mixin: ephemeral-mode toggle, bitchat-style triple-tap panic
wipe, and out-of-band safety-number verification."""
import time
from tkinter import messagebox

from .. import storage
from ..constants import PANIC_TAP_WINDOW, PANIC_TAPS_REQUIRED
from ..crypto import safety_number


class _SafetyMixin:
    def _toggle_ephemeral(self):
        self.ephemeral_mode = bool(self.ephemeral_var.get())
        self._save_store()

    def _panic_tap(self):
        now = time.time()
        self._panic_taps = [t for t in self._panic_taps if now - t < PANIC_TAP_WINDOW]
        self._panic_taps.append(now)
        remaining = PANIC_TAPS_REQUIRED - len(self._panic_taps)
        if remaining > 0:
            self.chat_subtitle_var.set(f"tap panic {remaining} more time(s) to wipe everything")
            return
        self._panic_taps = []
        if not messagebox.askyesno(
                "Panic wipe",
                "This immediately and irreversibly deletes your local identity and all "
                "stored history on this device. There is no undo. Continue?"):
            return
        try:
            if self.node:
                self.node.stop()
        except Exception:
            pass
        storage.panic_wipe(self.name)
        messagebox.showinfo("Wiped", "Local identity and history have been deleted.")
        self.root.destroy()

    def _show_safety_number(self):
        if not self.active_chat:
            return
        pub = self.node.peer_pub.get(self.active_chat)
        if pub is None:
            messagebox.showinfo("Not available", "No key from this peer yet — wait for their next announce.")
            return
        code = safety_number(self.node.pub_bytes, pub)
        if messagebox.askyesno(
                "Safety number",
                f"Compare this code out-of-band (voice or in person) with {self.active_chat}:\n\n{code}\n\n"
                "Mark as verified if it matches?"):
            verified = set(self.store.get("verified", []))
            verified.add(self.active_chat)
            self.store["verified"] = list(verified)
            self._save_store()
            self._open_dm(self.active_chat)
