# Changelog

All notable changes to this project are documented in this file.

## [3.2.0] — 2026-08-17

### Added
- **Offline chat search** (`secure_line/storage/search.py`) — search across
  every DM and channel history at once, case-sensitive or not, with a
  `highlight()` helper for marking up matched spans in the UI. Fully
  local: it operates on already-decrypted in-memory history and never
  touches the network.
- **Conversation export** (`secure_line/storage/export.py`) — export any
  DM or channel history to a readable Markdown transcript or a structured
  JSON file, entirely under user control (nothing is exported
  automatically). Attachment *paths* are noted in the export; the files
  themselves stay where they already live under `line_data/`.
- **`secure-line --version`** — a proper CLI flag to print the installed
  version and exit, instead of having to dig through `pyproject.toml`.
- **Test suite** (`tests/`) — 36 unit tests covering the crypto core (key
  agreement, ratchet forward-secrecy and out-of-order delivery, envelope
  tamper detection, channel-key derivation), the storage layer (identity
  create/unlock, wrong-password handling, the one-account-per-device
  guard, encrypted store roundtrips, panic wipe), search, and export.
  Runs against a temp `STORE_ROOT`, so it never touches real local data.
- **CI** (`.github/workflows/ci.yml`) — runs the test suite on Python
  3.10–3.12 on every push/PR, plus a package build check.
- **`dev` extra** in `pyproject.toml` (`pip install .[dev]`) for
  pytest.

### Fixed
- **Package was unusable without a display.** `secure_line/__init__.py`
  eagerly imported the GUI entry point, which imports `tkinter` — so
  even `import secure_line.crypto` failed on any machine or CI runner
  without Tk installed. The GUI import is now lazy (`from secure_line
  import main` still works when Tk is present; every non-GUI subpackage
  now works standalone).
- **Version mismatch** — `pyproject.toml` (`3.0.0`) and
  `secure_line/__init__.py` (`3.1.0`) disagreed with each other. Both
  now report `3.2.0`, and `--version` reads the single source of truth
  in `secure_line/__init__.py`.

## [3.1.0] and earlier

See git history — this file starts tracking from 3.2.0 onward.
