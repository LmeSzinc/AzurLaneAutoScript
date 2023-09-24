from module.config.stored.classes import (
    StoredAssignment,
    StoredBase,
    StoredBattlePassLevel,
    StoredBattlePassTodayQuest,
    StoredCounter,
    StoredDaily,
    StoredDailyActivity,
    StoredDungeonDouble,
    StoredExpiredAt0400,
    StoredInt,
    StoredSimulatedUniverse,
    StoredTrailblazePower,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    TrailblazePower = StoredTrailblazePower("Dungeon.DungeonStorage.TrailblazePower")
    DungeonDouble = StoredDungeonDouble("Dungeon.DungeonStorage.DungeonDouble")
    SimulatedUniverse = StoredSimulatedUniverse("Dungeon.DungeonStorage.SimulatedUniverse")
    DailyActivity = StoredDailyActivity("DailyQuest.DailyStorage.DailyActivity")
    DailyQuest = StoredDaily("DailyQuest.DailyStorage.DailyQuest")
    BattlePassLevel = StoredBattlePassLevel("BattlePass.BattlePassStorage.BattlePassLevel")
    BattlePassTodayQuest = StoredBattlePassTodayQuest("BattlePass.BattlePassStorage.BattlePassTodayQuest")
    Assignment = StoredAssignment("Assignment.Assignment.Assignment")
    Credit = StoredInt("DataUpdate.ItemStorage.Credit")
    StallerJade = StoredInt("DataUpdate.ItemStorage.StallerJade")
