"""LineApp mixin: sidebar rendering — channel rows and peer rows
(favorites pinned to the top, mesh-hop dot, unread pills)."""
import tkinter as tk

from ..theme import *  # noqa: F401,F403
from ..widgets import make_pill, make_mesh_dot, make_unread_dot, bind_hover_bg


class _SidebarMixin:
    def _render_sidebar(self):
        self._render_channels()
        self._render_peers()

    def _render_channels(self):
        for w in self.channel_list.winfo_children():
            w.destroy()
        for name, ch in self.channels.items():
            self._render_channel_row(name, ch)

    def _render_peers(self):
        for w in self.peer_list.winfo_children():
            w.destroy()
        peers = sorted(self.node.peers.values(),
                        key=lambda p: (p.name not in self.favorites, p.name))
        for peer in peers:
            self._render_peer_row(peer)
        if not peers:
            tk.Label(self.peer_list, text="listening for peers…", font=MONO_SMALL,
                      bg=HULL, fg=TEXT_FAINT, anchor="w").pack(fill="x", pady=6)

    def _render_channel_row(self, name, ch):
        active = (self.active_channel == name and self.active_chat is None)
        row_bg = SIGNAL_DIM if active else HULL
        row = tk.Frame(self.channel_list, bg=row_bg, cursor="hand2")
        row.pack(fill="x", pady=1)
        lock = " 🔒" if ch.has_password else ""
        label = tk.Label(row, text=f"{name}{lock}", font=MONO_SMALL, bg=row_bg,
                          fg=(SIGNAL if active else TEXT), anchor="w")
        label.pack(side="left", fill="x", expand=True, padx=8, pady=5)

        is_creator = bool(ch.creator) and ch.creator == self.name
        close_glyph = "🗑" if is_creator else "⏻"
        close_lbl = tk.Label(row, text=close_glyph, font=MONO_SMALL, bg=row_bg,
                              fg=(DANGER if is_creator else TEXT_FAINT), cursor="hand2")
        close_lbl.pack(side="right", padx=(2, 8))
        close_lbl.bind("<Button-1>", lambda _e, n=name: self._channel_action_prompt(n))

        if ch.unread and not active:
            make_pill(row, str(ch.unread), UNREAD_FG, UNREAD_BG, 40, bg_behind=row_bg, italic=False).pack(
                side="right", padx=6)
        for w in (row, label):
            w.bind("<Button-1>", lambda _e, n=name: self._open_channel(n))
        bind_hover_bg([row, label], row_bg, ROW_HOVER if not active else row_bg)

    def _render_peer_row(self, peer):
        active = (self.active_chat == peer.name)
        row_bg = SIGNAL_DIM if active else HULL
        row = tk.Frame(self.peer_list, bg=row_bg, cursor="hand2")
        row.pack(fill="x", pady=1)

        dot = make_mesh_dot(row, hops=peer.hops, bg_behind=row_bg)
        dot.pack(side="left", padx=(6, 4))
        label = tk.Label(row, text=peer.name, font=MONO_SMALL, bg=row_bg,
                          fg=(SIGNAL if active else TEXT), anchor="w")
        label.pack(side="left", fill="x", expand=True, pady=5)
        star = "★" if peer.name in self.favorites else "☆"
        star_lbl = tk.Label(row, text=star, font=MONO_SMALL, bg=row_bg,
                             fg=(WARN if peer.name in self.favorites else TEXT_FAINT), cursor="hand2")
        star_lbl.pack(side="right", padx=6)
        star_lbl.bind("<Button-1>", lambda _e, n=peer.name: self._toggle_favorite(n))

        if self.dm_unread.get(peer.name) and not active:
            make_unread_dot(row, bg_behind=row_bg).pack(side="right", padx=(0, 2))

        for w in (row, label, dot):
            w.bind("<Button-1>", lambda _e, n=peer.name: self._open_dm(n))
        bind_hover_bg([row, label], row_bg, ROW_HOVER if not active else row_bg)

    def _toggle_favorite(self, name):
        if name in self.favorites:
            self.favorites.discard(name)
        else:
            self.favorites.add(name)
        self._render_sidebar()
        self._save_store()
