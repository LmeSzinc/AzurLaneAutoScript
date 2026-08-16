"""Verify ui.py resolves every business asset name via the bridge (P2.2)."""

import sys

sys.path.insert(0, ".")

import module.ui.ui as u  # noqa: E402,F401

names = [
    "GET_ITEMS_1", "GET_ITEMS_2", "GET_SHIP", "EXERCISE_PREPARATION",
    "AUTO_SEARCH_MENU_EXIT", "BATTLE_PASS_NEW_SEASON", "BATTLE_PASS_NOTICE",
    "GAME_TIPS", "LOGIN_ANNOUNCE", "LOGIN_ANNOUNCE_2", "LOGIN_CHECK",
    "LOGIN_RETURN_SIGN", "MAINTENANCE_ANNOUNCE", "MONTHLY_PASS_NOTICE",
    "FLEET_PREPARATION", "MAP_PREPARATION", "MAP_PREPARATION_CANCEL", "WITHDRAW",
    "MEOWFFICER_BUY", "AUTO_SEARCH_REWARD", "EXCHANGE_CHECK",
    "RESET_FLEET_PREPARATION", "RESET_TICKET_POPUP", "RAID_FLEET_PREPARATION",
    "RPG_GOTO_STAGE", "RPG_GOTO_STORY", "RPG_HOME", "RPG_LEAVE_CITY",
]
missing = [n for n in names if not hasattr(u, n)]
print(f"ui.py name resolution: {len(names) - len(missing)}/{len(names)}")
print(f"missing: {missing if missing else 'NONE'}")
