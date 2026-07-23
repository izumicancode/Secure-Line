"""LineApp mixin: builds the static window chrome — header, sidebar
shell, and chat pane shell. Rendering the *contents* of those shells
(sidebar rows, message bubbles) lives in sidebar.py / messaging.py."""
import tkinter as tk

from ..crypto import fingerprint
from ..theme import *  # noqa: F401,F403
from ..widgets import make_round_button


class _LayoutMixin:
    _resize_after_id = None

    def _on_msg_canvas_configure(self, event):
        self.msg_canvas.itemconfig(self._msg_window, width=event.width)
        last_w = getattr(self, "_last_msg_canvas_w", None)
        self._last_msg_canvas_w = event.width
        if last_w is not None and abs(event.width - last_w) < 24:
            return  # small nudge, not worth a full re-render
        if self._resize_after_id is not None:
            try:
                self.root.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.root.after(120, self._render_messages)

    def _build_main_ui(self):
        self.main = tk.Frame(self.root, bg=VOID)
        self.main.pack(fill="both", expand=True)

        self._build_header()

        body = tk.Frame(self.main, bg=VOID)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_chat_pane(body)

        self._render_sidebar()
        from ..constants import DEFAULT_CHANNEL
        self._open_channel(DEFAULT_CHANNEL if DEFAULT_CHANNEL in self.channels
                            else next(iter(self.channels), None))

    def _build_header(self):
        header = tk.Frame(self.main, bg=HULL, height=52, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header, text="LINE", font=DISPLAY_SMALL, bg=HULL, fg=SIGNAL).pack(side="left", padx=(16, 6))
        my_fp = fingerprint(self.node.pub_bytes)
        tk.Label(header, text=f"{self.name}  ·  {my_fp}", font=MONO_SMALL, bg=HULL,
                 fg=TEXT_DIM).pack(side="left", padx=8)

        self.ephemeral_var = tk.BooleanVar(value=self.ephemeral_mode)
        eph_chk = tk.Checkbutton(header, text="ephemeral", variable=self.ephemeral_var,
                                  onvalue=True, offvalue=False, font=MONO_SMALL,
                                  bg=HULL, fg=WARN, selectcolor=HULL, activebackground=HULL,
                                  activeforeground=WARN, relief="flat", highlightthickness=0,
                                  command=self._toggle_ephemeral)
        eph_chk.pack(side="right", padx=(6, 16))

        panic = tk.Button(header, text="⚠ PANIC", font=(MONO[0], 10, "bold"), bg=HULL, fg=DANGER,
                           activebackground=DANGER_DIM, activeforeground=DANGER, relief="flat",
                           cursor="hand2", command=self._panic_tap,
                           highlightthickness=1, highlightbackground=DANGER)
        panic.pack(side="right", padx=6, ipadx=6, ipady=2)

    def _build_sidebar(self, parent):
        self.sidebar = tk.Frame(parent, bg=HULL, width=240, highlightthickness=1, highlightbackground=LINE)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        chan_row = tk.Frame(self.sidebar, bg=HULL)
        chan_row.pack(fill="x", pady=(12, 4), padx=10)
        tk.Label(chan_row, text="CHANNELS", font=MONO_SMALL, bg=HULL, fg=TEXT_FAINT).pack(side="left")
        tk.Button(chan_row, text="+", font=(MONO[0], 10, "bold"), bg=HULL, fg=SIGNAL,
                  relief="flat", cursor="hand2", command=self._open_join_channel_dialog,
                  activebackground=HULL, activeforeground=SIGNAL_HOVER).pack(side="right")

        self.channel_list = tk.Frame(self.sidebar, bg=HULL)
        self.channel_list.pack(fill="x", padx=6)

        tk.Frame(self.sidebar, bg=LINE, height=1).pack(fill="x", pady=10, padx=10)

        peer_row = tk.Frame(self.sidebar, bg=HULL)
        peer_row.pack(fill="x", padx=10)
        tk.Label(peer_row, text="PEERS ON THE LINE", font=MONO_SMALL, bg=HULL, fg=TEXT_FAINT).pack(side="left")

        self.peer_list = tk.Frame(self.sidebar, bg=HULL)
        self.peer_list.pack(fill="both", expand=True, padx=6, pady=(4, 10))

    def _build_chat_pane(self, parent):
        pane = tk.Frame(parent, bg=VOID)
        pane.pack(side="left", fill="both", expand=True)

        self.chat_header = tk.Frame(pane, bg=HULL, height=44, highlightthickness=1, highlightbackground=LINE)
        self.chat_header.pack(fill="x")
        self.chat_header.pack_propagate(False)
        self.chat_title_var = tk.StringVar(value="")
        tk.Label(self.chat_header, textvariable=self.chat_title_var, font=(MONO[0], 12, "bold"),
                 bg=HULL, fg=TEXT).pack(side="left", padx=14)
        self.chat_subtitle_var = tk.StringVar(value="")
        tk.Label(self.chat_header, textvariable=self.chat_subtitle_var, font=MONO_SMALL,
                 bg=HULL, fg=TEXT_DIM).pack(side="left", padx=6)

        self.verify_btn = tk.Button(self.chat_header, text="verify", font=MONO_SMALL, bg=HULL,
                                     fg=LINK, relief="flat", cursor="hand2",
                                     command=self._show_safety_number, activebackground=HULL)
        self.verify_btn.pack(side="right", padx=10)

        canvas_wrap = tk.Frame(pane, bg=VOID)
        canvas_wrap.pack(fill="both", expand=True)
        self.msg_canvas = tk.Canvas(canvas_wrap, bg=VOID, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(canvas_wrap, orient="vertical", command=self.msg_canvas.yview)
        self.msg_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.msg_canvas.pack(side="left", fill="both", expand=True)
        self.msg_frame = tk.Frame(self.msg_canvas, bg=VOID)
        self._msg_window = self.msg_canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.msg_frame.bind("<Configure>",
                             lambda _e: self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all")))
        self.msg_canvas.bind("<Configure>", self._on_msg_canvas_configure)
        self.msg_canvas.bind_all("<MouseWheel>",
                                  lambda e: self.msg_canvas.yview_scroll(int(-e.delta / 120), "units"))

        composer = tk.Frame(pane, bg=HULL, height=58, highlightthickness=1, highlightbackground=LINE)
        composer.pack(fill="x", side="bottom")
        composer.pack_propagate(False)

        self.attach_btn = make_round_button(composer, 34, "📎", HULL_SOFT, TEXT, self._attach_file)
        self.attach_btn.pack(side="left", padx=(10, 6), pady=12)

        self.compose_var = tk.StringVar()
        entry = tk.Entry(composer, textvariable=self.compose_var, font=BODY, bg=HULL_SOFT, fg=TEXT,
                          insertbackground=SIGNAL, relief="flat", highlightthickness=1,
                          highlightbackground=LINE, highlightcolor=SIGNAL)
        entry.pack(side="left", fill="both", expand=True, pady=12, ipady=4)
        entry.bind("<Return>", lambda _e: self._send_current())

        make_round_button(composer, 34, "➤", SIGNAL, TEXT_ON_ACCENT, self._send_current,
                           hover_fill=SIGNAL_HOVER).pack(side="left", padx=10, pady=12)

        self.compose_entry = entry
