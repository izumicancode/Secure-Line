"""Colors — dark hull, one phosphor-green signal accent, amber for
warnings, red for danger/panic, blue for links/mentions. Inspired by
terminal UIs and bitchat's mesh-radio aesthetic rather than a generic
messenger. Every surface is a shade of near-black charcoal, never pure
white-on-black, so long sessions stay easy on the eyes.
"""

VOID = "#05070A"            # outermost app background — almost black
HULL = "#0B0F14"            # sidebar / header / composer surfaces
HULL_RAISED = "#10151C"     # cards, panels, "their" bubble
HULL_SOFT = "#161C24"       # input fields, hovered rows, chips
LINE = "#212A34"            # hairline borders
LINE_BRIGHT = "#2E3A47"     # focused borders

TEXT = "#E7EDF2"            # primary text — soft white, not pure #fff
TEXT_DIM = "#7C8894"
TEXT_FAINT = "#4B555F"
TEXT_ON_ACCENT = "#04120A"  # dark text sits on the bright green accent

SIGNAL = "#39FF88"          # phosphor green — primary action, "mine" bubble, mesh-online dot
SIGNAL_DIM = "#122619"      # green tinted near-black, for soft chips / selected rows
SIGNAL_HOVER = "#5BFFA0"
SIGNAL_GLOW = "#1E7A47"      # dimmer green for rings / low-emphasis accents

LINK = "#5CC8FF"             # cool blue — links, @mentions, channel names
LINK_DIM = "#0F2733"

WARN = "#FFB454"            # amber — pending, ephemeral-mode badge, low battery/no-peers notice
WARN_DIM = "#2B2110"

DANGER = "#FF5C5C"          # red — panic button, declined, delete, danger
DANGER_DIM = "#2B1414"

SHADOW = "#000000"

# Legacy-shaped aliases kept so drawing helpers can stay generic.
BG = VOID
PANEL = HULL
PANEL_RAISED = HULL_RAISED
PANEL_SOFT = HULL_SOFT
BORDER = LINE
BUBBLE_MINE = SIGNAL_DIM
BUBBLE_MINE_BORDER = SIGNAL_GLOW
BUBBLE_THEIRS = HULL_RAISED
BUBBLE_THEIRS_BORDER = LINE
ACCENT = SIGNAL
ACCENT_DIM = SIGNAL_DIM
ACCENT_HOVER = SIGNAL_HOVER
FLARE = SIGNAL
DANGER_ = DANGER
UNREAD_BG = DANGER
UNREAD_FG = "#0A0000"
READ_TICK = SIGNAL
SENT_TICK = TEXT_DIM
ONLINE = SIGNAL
ROW_HOVER = HULL_SOFT
BTN_HOVER_SOFT = "#1B222B"
