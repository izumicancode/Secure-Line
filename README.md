<div align="center">


# 📡 L I N E

**A verified, end-to-end-encrypted, mesh-relayed chat app for your LAN.**
No servers. No cloud. No accounts anywhere but the device in your hands.

</div>

<br>

## What is this?

Line turns any local network — home WiFi, an office LAN, a conference
room, a boat with no signal — into a private, encrypted chat mesh. Every
device on the network discovers the others automatically, every
conversation is end-to-end encrypted with a ratcheting key schedule
(the same idea Signal uses), and nothing ever touches a server, because
there isn't one).

Open two laptops on the same WiFi, run `python -m secure_line` on both,
and you're talking — encrypted, peer-to-peer, no sign-up screen asking
for your phone number.

```
┌──────────┐   UDP broadcast    ┌──────────┐
│  laptop  │◄──── discovery ───►│  laptop  │
│  "alice" │                    │   "bob"  │
└────┬─────┘                    └────┬─────┘
     │       TCP, ratcheted AES-GCM  │
     └───────────────────────────────┘
              direct message
```

<br>

## ✨ Features

|                                   |                                                              |
| --------------------------------- | ------------------------------------------------------------ |
| 🔒 **Real E2E encryption**         | X25519 key agreement + a Double-Ratchet-style scheme, AES-GCM per message. Each message uses its own key; compromising one doesn't compromise the rest. |
| 🕸️ **Mesh relay**                  | Can't reach a peer directly? Nearby peers rebroadcast for you (hop-limited, no infinite loops). Every message shows how many hops it traveled. |
| 📡 **Zero-config discovery**       | Devices find each other over UDP broadcast the moment they're on the same network. No pairing codes, no QR scanning. |
| 💬 **Channels**                    | Open, ephemeral topic rooms (`#general`, `#kitchen-table`, whatever) — optionally locked with a shared password. |
| 📎 **Real file & folder transfer** | Send a file or a whole folder (auto-zipped) from a DM *or* a channel. Recipients get a thumbnail for images, an icon for everything else, and one-click **Open** / **Save As** — not just a filename in a bubble. |
| 🗑️ **Creator-owned channels**      | Whoever creates a channel is the only one who can delete it. Everyone else can join and leave freely. |
| 🔑 **One account, one device**     | Set a callsign and password once; every future launch just asks for the password. No juggling multiple identities on one machine. |
| 💾 **Saved locally by default**    | History, channels, and files persist in an encrypted local store — flip on ephemeral mode any time to go back to "nothing touches disk." |
| 📫 **Store-and-forward**           | Send a DM to someone who just stepped away — it's queued locally and delivered the moment they're back online. |
| ⭐ **Favorites**                   | Pin the people you talk to most to the top of your peer list. |
| ✅ **Safety numbers**              | Compare a short fingerprint out-of-band with a peer and mark them verified — the same trust model Signal popularized. |
| ☢️ **Panic wipe**                  | One confirmed tap instantly and irreversibly deletes your local identity and history. No undo, on purpose. |

<br>

## 🚀 Quick start

```bash
pip install -r requirements.txt
python -m secure_line
```

Or install it as a real command:

```bash
pip install .
secure-line
```

**First launch:** pick a callsign and a password. That's your one
account on this device — every launch after this just asks for the
password.

**Talking to someone:** run Line on another device on the *same*
network. They'll show up under "PEERS ON THE LINE" within a couple of
seconds. Click their name, type, hit enter.

**A private room:** click **+** next to CHANNELS, give it a name and
(optionally) a password. Anyone who joins with the same name + password
can read it.

**Sending a file:** open a chat or channel, click 📎, choose *Send a
file* or *Send a folder*. The recipient gets a real, openable,
downloadable copy — not just a name.

<br>

## 🔐 How the security actually works

- **Identity.** Each account is an X25519 keypair, generated on first
  signup and encrypted at rest with a key derived from your password
  (scrypt). Lose the password, lose the identity — there's no recovery
  by design.
- **Direct messages.** Two peers agree on a shared root key via X25519,
  then step forward one ratchet click per message with AES-GCM,
  independently in each direction. A message key is used once and
  discarded.
- **Channels.** A channel's key is derived from its name + password.
  Anyone who knows both can decrypt — this is a shared-secret model,
  like a WiFi password, not an account system. There is no central
  authority confirming who's really in a channel.
- **"Creator"** is an *informational* tag, not a cryptographic
  guarantee — channel passwords don't carry a signature. Each device
  trusts the first creator name it ever sees for a channel and never
  overwrites it after that (trust-on-first-use), which is enough to
  keep an honest room's delete button in the right hands but isn't
  proof against a determined impersonator. See the comments in
  `node/channels.py` if you want the full reasoning.
- **Files.** Encrypted the same way as text — DMs use the same
  ratcheted channel as everything else; channel files are pushed once,
  best-effort, over the same encrypted TCP path DMs use (broadcasting
  megabytes over UDP repeatedly isn't reliable, so files skip the mesh
  relay and just go straight to whoever's online right now).
- **At rest.** Your local store (history, channels, favorites) is
  encrypted with a key derived from your account password. Turn on
  ephemeral mode in the header to stop writing anything to disk at all.
- **Panic wipe.** Deletes your identity, your store, and your
  device-account binding. Immediate, irreversible, no confirmation
  beyond the one dialog.

This is a LAN chat tool built for a specific trust model (people who can
already reach your network), not a hardened messaging platform — treat
it accordingly.

<br>

## 🗂️ Project layout

Every concern lives in its own small file, grouped into one folder per
module — adding a feature is "add a file," not "grow a 2000-line one."

```
secure_line/
├── constants/     ports, timings, mesh/relay tuning, channel & panic settings
├── theme/         dark palette + monospace type system
├── crypto/        X25519 agreement, the ratchet, AES-GCM, channel-password keys
├── storage/       password-wrapped identity, encrypted local store, device-account binding
├── netutils/      LAN address discovery, callsign/channel-name validation
├── models/        Peer, Profile, Channel, ChatEntry dataclasses
├── mesh/          seen-message cache, store-and-forward queue, hop-limit helpers
├── node/          LineNode — discovery, ratcheted DMs, channel broadcast + files, mesh relay
├── widgets/       reusable dark-themed Tk drawing helpers (bubbles, file cards, pills, badges)
├── app/           LineApp — the GUI, one mixin per feature area
├── platform_setup/  best-effort firewall rules + high-DPI Windows fix
└── main.py / __main__.py   entry point
```

| Folder       | Key files                                                    |
| ------------ | ------------------------------------------------------------ |
| `constants/` | `network.py`, `mesh.py`, `channels.py`, `storage.py`, `ephemeral.py` |
| `crypto/`    | `encoding.py`, `keys.py`, `channel_keys.py`, `ratchet.py`, `envelope.py` |
| `storage/`   | `paths.py`, `identity.py`, `store.py`, `panic.py`            |
| `node/`      | `wire.py`, `discovery.py`, `messaging.py`, `channels.py`, `core.py` |
| `widgets/`   | `shapes.py`, `cards.py`, `bubbles.py`, `file_card.py`, `attach_menu.py`, `pills.py`, `badges.py`, `buttons.py`, `hover.py` |
| `app/`       | `login.py`, `core.py`, `layout.py`, `sidebar.py`, `channels.py`, `messaging.py`, `events.py`, `safety.py` |

<br>

## 🧠 Design notes worth knowing before you dig in

- **Everything is a mixin.** `LineApp` and `LineNode` are each assembled
  from several `_XyzMixin` classes so one feature = one file, and you
  can read `app/messaging.py` without also loading `app/sidebar.py`
  into your head.
- **The event queue is the only bridge between threads.** `LineNode`
  runs its networking on background threads and only ever talks to the
  UI by pushing events onto a thread-safe queue; `LineApp` polls it on
  a Tk timer. If you're adding a feature that touches the network, this
  is the pattern to follow — never touch a Tk widget from a background
  thread.
- **Files get their own copy, always.** Sending a file copies it into
  `line_data/sent_files/` and receiving one writes it to
  `line_data/received_files/` — a `ChatEntry` always points at a real
  local path, so *Open* and *Save As* never depend on the original file
  still existing where you picked it from.

<br>

## 🧭 Roadmap ideas

- [ ] Group DMs (more than 1:1, without a shared channel password)
- [ ] Read receipts inside channels, not just DMs
- [ ] Optional relay-through-internet for off-LAN reachability
- [ ] Mobile client

Pull requests welcome — see the project layout above for where a given
feature would live.

<br>

## ⚠️ Data & safety notes

- Local data lives in `line_data/` next to the package (portable — copy
  the folder and it moves with you), unless ephemeral mode is on.
- `line_data/device_account.json` holds the one callsign this device is
  bound to, in plaintext (it's a username, not a secret) — that's what
  lets the login screen skip straight to a password prompt.
- Panic wipe is irreversible. There is no recovery once confirmed.
- Attachments (files or zipped folders) are capped at 8 MB, for both
  DMs and channels.
- This project hasn't had a professional security audit. Don't bet
  anything you'd truly hate to lose on it being bug-free.

<br>

<div align="center">


Built for a LAN, not a data center. 📡

</div>
