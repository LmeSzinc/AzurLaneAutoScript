"""UI-layer asset bridge (P2.2).

Centralizes every import from business-module asset bundles that the UI
navigation layer (page.py / ui.py / navbar.py) needs. Before this module,
ui/ imported directly from 9 business modules; now the cross-layer surface
is a single explicit-import file that can be migrated button-by-button to
module/ui/assets.py (real page-check buttons belong to the UI layer).

Only names actually used by the UI layer are re-exported here (explicit
imports, not star). Do not add business logic; this is a pure re-export hub.
"""

from module.coalition.assets import HORROR_COALITION_CHECK
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_SHIP
from module.event_hospital.assets import HOSIPITAL_CHECK
from module.exercise.assets import EXERCISE_PREPARATION
from module.freebies.assets import MAIL_ENTER
from module.handler.assets import (
    AUTO_SEARCH_MENU_EXIT,
    BATTLE_PASS_NEW_SEASON,
    BATTLE_PASS_NOTICE,
    GAME_TIPS,
    LOGIN_ANNOUNCE,
    LOGIN_ANNOUNCE_2,
    LOGIN_CHECK,
    LOGIN_RETURN_SIGN,
    MAINTENANCE_ANNOUNCE,
    MONTHLY_PASS_NOTICE,
)
from module.map.assets import (
    FLEET_PREPARATION,
    MAP_PREPARATION,
    MAP_PREPARATION_CANCEL,
    MAP_PREPARATION_HARD,
    WITHDRAW,
)
from module.meowfficer.assets import MEOWFFICER_BUY
from module.os_handler.assets import (
    AUTO_SEARCH_REWARD,
    EXCHANGE_CHECK,
    RESET_FLEET_PREPARATION,
    RESET_TICKET_POPUP,
)
from module.raid.assets import (
    RAID_FLEET_PREPARATION,
    RPG_BACK,
    RPG_GOTO_STAGE,
    RPG_GOTO_STORY,
    RPG_HOME,
    RPG_LEAVE_CITY,
)
from module.retire.assets import DOCK_CHECK
from module.shop.assets import SHOP_CLICK_SAFE_AREA

__all__ = [
    "AUTO_SEARCH_MENU_EXIT",
    "AUTO_SEARCH_REWARD",
    "BATTLE_PASS_NEW_SEASON",
    "BATTLE_PASS_NOTICE",
    "DOCK_CHECK",
    "EXCHANGE_CHECK",
    "EXERCISE_PREPARATION",
    "FLEET_PREPARATION",
    "GAME_TIPS",
    "GET_ITEMS_1",
    "GET_ITEMS_2",
    "GET_SHIP",
    "HORROR_COALITION_CHECK",
    "HOSIPITAL_CHECK",
    "LOGIN_ANNOUNCE",
    "LOGIN_ANNOUNCE_2",
    "LOGIN_CHECK",
    "LOGIN_RETURN_SIGN",
    "MAIL_ENTER",
    "MAINTENANCE_ANNOUNCE",
    "MAP_PREPARATION",
    "MAP_PREPARATION_CANCEL",
    "MAP_PREPARATION_HARD",
    "MEOWFFICER_BUY",
    "MONTHLY_PASS_NOTICE",
    "RAID_FLEET_PREPARATION",
    "RESET_FLEET_PREPARATION",
    "RESET_TICKET_POPUP",
    "RPG_BACK",
    "RPG_GOTO_STAGE",
    "RPG_GOTO_STORY",
    "RPG_HOME",
    "RPG_LEAVE_CITY",
    "SHOP_CLICK_SAFE_AREA",
    "WITHDRAW",
]
