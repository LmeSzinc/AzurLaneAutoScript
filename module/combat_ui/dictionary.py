from module.combat.assets import *
from module.combat_ui.assets import *

pause_template = {
    "Old": PAUSE,
    "New": PAUSE_New,
    "Iridescent_Fantasy": PAUSE_Iridescent_Fantasy,
    "Christmas": PAUSE_Christmas,
    "Cyber": PAUSE_Cyber,
    "Neon": PAUSE_Neon,
    "HolyLight": PAUSE_HolyLight,
}

quit_template = {
    "Old": QUIT,
    "New": QUIT_New,
    "Iridescent_Fantasy": QUIT_Iridescent_Fantasy,
    "Christmas": QUIT_Christmas,
    "Cyber": QUIT_New,  # Battle UI PAUSE_Cyber uses QUIT_New
    "Neon": QUIT_New,  # Battle UI PAUSE_Neon uses QUIT_New
    "HolyLight": QUIT_New,  # Battle UI PAUSE_HolyLight uses QUIT_New
}

# combat_manual_template = {
# }

# combat_auto_template = {
# }

# submarine_template = {
# }