from module.config.stored.classes import (
    StoredAssignment,
    StoredBase,
    StoredBattlePassLevel,
    StoredBattlePassQuestCalyx,
    StoredBattlePassQuestCavernOfCorrosion,
    StoredBattlePassQuestCredits,
    StoredBattlePassQuestEchoOfWar,
    StoredBattlePassQuestSynthesizeConsumables,
    StoredBattlePassQuestTrailblazePower,
    StoredBattlePassSimulatedUniverse,
    StoredBattlePassWeeklyQuest,
    StoredCounter,
    StoredDaily,
    StoredDailyActivity,
    StoredDungeonDouble,
    StoredEchoOfWar,
    StoredExpiredAt0400,
    StoredExpiredAtMonday0400,
    StoredImmersifier,
    StoredInt,
    StoredSimulatedUniverse,
    StoredTrailblazePower,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    TrailblazePower = StoredTrailblazePower("Dungeon.DungeonStorage.TrailblazePower")
    Immersifier = StoredImmersifier("Dungeon.DungeonStorage.Immersifier")
    DungeonDouble = StoredDungeonDouble("Dungeon.DungeonStorage.DungeonDouble")
    EchoOfWar = StoredEchoOfWar("Dungeon.DungeonStorage.EchoOfWar")
    SimulatedUniverse = StoredSimulatedUniverse("Dungeon.DungeonStorage.SimulatedUniverse")
    DailyActivity = StoredDailyActivity("DailyQuest.DailyStorage.DailyActivity")
    DailyQuest = StoredDaily("DailyQuest.DailyStorage.DailyQuest")
    BattlePassLevel = StoredBattlePassLevel("BattlePass.BattlePassStorage.BattlePassLevel")
    BattlePassWeeklyQuest = StoredBattlePassWeeklyQuest("BattlePass.BattlePassStorage.BattlePassWeeklyQuest")
    BattlePassSimulatedUniverse = StoredBattlePassSimulatedUniverse("BattlePass.BattlePassStorage.BattlePassSimulatedUniverse")
    BattlePassQuestCalyx = StoredBattlePassQuestCalyx("BattlePass.BattlePassStorage.BattlePassQuestCalyx")
    BattlePassQuestEchoOfWar = StoredBattlePassQuestEchoOfWar("BattlePass.BattlePassStorage.BattlePassQuestEchoOfWar")
    BattlePassQuestCredits = StoredBattlePassQuestCredits("BattlePass.BattlePassStorage.BattlePassQuestCredits")
    BattlePassQuestSynthesizeConsumables = StoredBattlePassQuestSynthesizeConsumables("BattlePass.BattlePassStorage.BattlePassQuestSynthesizeConsumables")
    BattlePassQuestCavernOfCorrosion = StoredBattlePassQuestCavernOfCorrosion("BattlePass.BattlePassStorage.BattlePassQuestCavernOfCorrosion")
    BattlePassQuestTrailblazePower = StoredBattlePassQuestTrailblazePower("BattlePass.BattlePassStorage.BattlePassQuestTrailblazePower")
    Assignment = StoredAssignment("Assignment.Assignment.Assignment")
    Credit = StoredInt("DataUpdate.ItemStorage.Credit")
    StallerJade = StoredInt("DataUpdate.ItemStorage.StallerJade")
