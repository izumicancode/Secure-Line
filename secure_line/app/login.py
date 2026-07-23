"""LoginScreen — one device, one account.

If this device has never created an account, shows the full signup form
(callsign + password). Once an account exists, every later launch skips
straight to a password-only unlock screen for that fixed callsign -- no
callsign entry, no way to accidentally spin up a second identity here.
The only way to change callsigns on this device is a panic wipe, which
clears the local account binding and returns to the signup form.

Card sizing note: the card's height is measured from its actual content
*after* everything is packed, then the outer placement is sized to fit --
never a guessed fixed height. That's what stops fields/buttons from ever
looking cramped or clipped on a different OS/DPI/font metrics.
"""
import tkinter as tk

from .. import storage
from ..netutils import valid_name
from ..theme import *  # noqa: F401,F403
from ..widgets import make_shadowed_card

CARD_WIDTH = 400


class LoginScreen(tk.Frame):
    def __init__(self, root, on_ready):
        super().__init__(root, bg=VOID)
        self.root = root
        self.on_ready = on_ready
        self.pack(fill="both", expand=True)
        self.device_name = storage.get_device_account_name()
        self._build()

    # ------------------------------------------------------------------
    # Shared chrome
    # ------------------------------------------------------------------
    def _new_card(self):
        outer, card = make_shadowed_card(self, VOID, HULL_RAISED, LINE)
        # No fixed height here -- see _finish_card, which measures the
        # card's real content height once everything is packed, so the
        # layout below never has to guess and risk squeezing.
        tk.Label(card, text="L I N E", font=DISPLAY, bg=HULL_RAISED, fg=SIGNAL).pack(pady=(38, 4))
        tk.Label(card, text="verified · end-to-end · mesh-relayed", font=MONO_SMALL,
                 bg=HULL_RAISED, fg=TEXT_DIM).pack(pady=(0, 26))
        return outer, card

    def _finish_card(self, outer, card):
        """Sizes+centers the card based on what it actually contains,
        instead of a fixed guess -- this is what keeps fields, labels,
        and buttons from ever overlapping or clipping."""
        card.update_idletasks()
        h = card.winfo_reqheight() + 4  # a hair of slack for border rounding
        outer.place(relx=0.5, rely=0.45, anchor="center", width=CARD_WIDTH, height=h)

    def _status_label(self, parent):
        self.status_var = tk.StringVar(value="")
        tk.Label(parent, textvariable=self.status_var, font=MONO_SMALL, bg=HULL_RAISED,
                 fg=DANGER, anchor="w", wraplength=CARD_WIDTH - 80, justify="left").pack(
            fill="x", pady=(6, 0))

    def _entry(self, form, label, show=None):
        tk.Label(form, text=label, font=MONO_SMALL, bg=HULL_RAISED, fg=TEXT_DIM,
                 anchor="w").pack(fill="x", pady=(0, 4))
        var = tk.StringVar()
        kwargs = {"show": show} if show else {}
        entry = tk.Entry(form, textvariable=var, font=BODY, bg=HULL_SOFT, fg=TEXT,
                          insertbackground=SIGNAL, relief="flat", highlightthickness=1,
                          highlightbackground=LINE, highlightcolor=SIGNAL, **kwargs)
        entry.pack(fill="x", ipady=9, pady=(0, 18))
        return var, entry

    def _primary_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, font=(MONO[0], 10, "bold"), bg=SIGNAL,
                         fg=TEXT_ON_ACCENT, activebackground=SIGNAL_HOVER,
                         activeforeground=TEXT_ON_ACCENT, relief="flat", bd=0,
                         cursor="hand2", command=command)
        btn.pack(fill="x", ipady=11)
        return btn

    def _build(self):
        if self.device_name:
            self._build_unlock()
        else:
            self._build_signup()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self.device_name = storage.get_device_account_name()
        self._build()

    # ------------------------------------------------------------------
    # Mode A: no account on this device yet -- full signup
    # ------------------------------------------------------------------
    def _build_signup(self):
        outer, card = self._new_card()
        form = tk.Frame(card, bg=HULL_RAISED)
        form.pack(fill="x", padx=40)

        self.name_var, name_entry = self._entry(form, "CHOOSE A CALLSIGN")
        name_entry.focus_set()
        self.pw_var, pw_entry = self._entry(form, "CHOOSE A PASSWORD")
        pw_entry.configure(show="•")
        pw_entry.bind("<Return>", lambda _e: self._signup())

        tk.Label(form, text="this device supports one account -- pick carefully",
                 font=MONO_SMALL, bg=HULL_RAISED, fg=TEXT_FAINT, anchor="w",
                 wraplength=CARD_WIDTH - 80, justify="left").pack(fill="x", pady=(0, 2))
        self._status_label(form)

        btn_row = tk.Frame(card, bg=HULL_RAISED)
        btn_row.pack(fill="x", padx=40, pady=(22, 32))
        self._primary_button(btn_row, "ENTER THE LINE", self._signup)

        self._finish_card(outer, card)

    def _signup(self):
        name = self.name_var.get().strip()
        password = self.pw_var.get()
        if not valid_name(name):
            self.status_var.set("callsign: 2-24 chars, letters/numbers/-_. only")
            return
        if len(password) < 4:
            self.status_var.set("password: at least 4 characters")
            return
        try:
            private_key = storage.create_account(name, password)
        except storage.DeviceAlreadyHasAccount:
            self._rebuild()
            return
        except Exception as e:
            self.status_var.set(f"local storage error: {e}")
            return
        self._enter_app(name, private_key)

    # ------------------------------------------------------------------
    # Mode B: this device already has an account -- password only
    # ------------------------------------------------------------------
    def _build_unlock(self):
        outer, card = self._new_card()

        badge = tk.Frame(card, bg=SIGNAL_DIM, highlightthickness=1, highlightbackground=SIGNAL_GLOW)
        badge.pack(pady=(0, 20))
        tk.Label(badge, text=f"⦿  {self.device_name}", font=(MONO[0], 11, "bold"),
                  bg=SIGNAL_DIM, fg=SIGNAL, padx=14, pady=6).pack()

        form = tk.Frame(card, bg=HULL_RAISED)
        form.pack(fill="x", padx=40)

        self.pw_var, pw_entry = self._entry(form, "PASSWORD")
        pw_entry.configure(show="•")
        pw_entry.focus_set()
        pw_entry.bind("<Return>", lambda _e: self._unlock())
        self._status_label(form)

        btn_row = tk.Frame(card, bg=HULL_RAISED)
        btn_row.pack(fill="x", padx=40, pady=(18, 6))
        self._primary_button(btn_row, "UNLOCK", self._unlock)

        wipe = tk.Label(card, text="not you? wipe this device's data to start over",
                         font=MONO_SMALL, bg=HULL_RAISED, fg=TEXT_FAINT, cursor="hand2")
        wipe.pack(pady=(14, 30))
        wipe.bind("<Button-1>", lambda _e: self._wipe_device())
        wipe.bind("<Enter>", lambda _e: wipe.configure(fg=DANGER))
        wipe.bind("<Leave>", lambda _e: wipe.configure(fg=TEXT_FAINT))

        self._finish_card(outer, card)

    def _unlock(self):
        password = self.pw_var.get()
        if len(password) < 4:
            self.status_var.set("password: at least 4 characters")
            return
        try:
            private_key = storage.unlock_account(self.device_name, password)
        except storage.WrongPassword:
            self.status_var.set("incorrect password")
            return
        except Exception as e:
            self.status_var.set(f"local storage error: {e}")
            return
        self._enter_app(self.device_name, private_key)

    def _wipe_device(self):
        from tkinter import messagebox
        if not messagebox.askyesno(
                "Wipe this device",
                f"This immediately and irreversibly deletes the local account "
                f"({self.device_name}) and all stored history on this device. "
                "There is no undo. Continue?"):
            return
        storage.panic_wipe(self.device_name)
        self._rebuild()

    # ------------------------------------------------------------------
    def _enter_app(self, name, private_key):
        self.destroy()
        self.on_ready(name, private_key)
