"""Task registry: declarative mapping of scheduler task names to task classes.

Replaces the ~70 hand-written boilerplate methods in alas.py (P1.4 refactor).
Each entry declares where the task class lives and how to run it, so adding a
new task is one line here plus the task class itself.

Entry fields:
    module (str):           dotted module path, imported lazily on first run
    class (str):            class name in that module
    method (str):           method to call on the instance; default "run"
    kwargs (callable|dict): extra kwargs for the CONSTRUCTOR, or a callable
                            taking the config to build them dynamically
    method_kwargs (callable|dict):
                            extra kwargs for the METHOD call (e.g. the
                            name/folder/mode of CampaignRun.run), or a
                            callable taking the config to build them
    function (str):         alternative to class+method: a module-level
                            function to call with config/device kwargs
    task_arg (bool):        pass the scheduler task name as task=... kwarg
                            (used by daemon/eventstory/planner tasks)
    family (str|None):      task family tag (Phase 4D). Canonical families:
                            main/event/gems/raid/war_archives/coalition/
                            maritime/hospital. Config generation and campaign
                            event logic derive their task lists from here.

The registry is intentionally data-only; azurlane_auto_script.py resolves
entries so the scheduler keeps a single execution path.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass

import inflection

if t.TYPE_CHECKING:
    from module.config.config import AzurLaneConfig


@dataclass(frozen=True)
class TaskEntry:
    module: str
    class_name: str | None = None
    method: str = "run"
    kwargs: t.Callable[[AzurLaneConfig], dict] | dict | None = None
    method_kwargs: t.Callable[[AzurLaneConfig], dict] | dict | None = None
    function: str | None = None
    task_arg: bool = False
    family: str | None = None


def _campaign_kwargs(config):
    return {
        "name": config.Campaign_Name,
        "folder": config.Campaign_Event,
        "mode": config.Campaign_Mode,
    }


# Task name (as in config Scheduler Command) -> entry.
# Name is PascalCase in config (e.g. "Main", "OpsiExplore"); the scheduler
# resolves it via inflection.underscore() (e.g. "opsi_explore"), so each
# entry is also indexed by its snake_case command form. Building the alias
# map here (instead of camelize-back at runtime) avoids lossy round-trips
# like RaidDaily -> raid_daily -> Raid_daily.
TASK_REGISTRY: dict[str, TaskEntry] = {
    "Research": TaskEntry("module.research.research", "RewardResearch"),
    "Commission": TaskEntry("module.commission.commission", "RewardCommission"),
    "Tactical": TaskEntry("module.tactical.tactical_class", "RewardTacticalClass"),
    "Dorm": TaskEntry("module.dorm.dorm", "RewardDorm"),
    "Meowfficer": TaskEntry("module.meowfficer.meowfficer", "RewardMeowfficer"),
    "Guild": TaskEntry("module.guild.guild_reward", "RewardGuild"),
    "Reward": TaskEntry("module.reward.reward", "Reward"),
    "Awaken": TaskEntry("module.awaken.awaken", "Awaken"),
    "ShopFrequent": TaskEntry("module.shop.shop_reward", "RewardShop", method="run_frequent"),
    "ShopOnce": TaskEntry("module.shop.shop_reward", "RewardShop", method="run_once"),
    "EventShop": TaskEntry("module.shop_event.shop_event", "EventShop"),
    "Shipyard": TaskEntry("module.shipyard.shipyard_reward", "RewardShipyard"),
    "Gacha": TaskEntry("module.gacha.gacha_reward", "RewardGacha"),
    "Freebies": TaskEntry("module.freebies.freebies", "Freebies"),
    "Minigame": TaskEntry("module.minigame.minigame", "Minigame"),
    "PrivateQuarters": TaskEntry("module.private_quarters.private_quarters", "PrivateQuarters"),
    "Daily": TaskEntry("module.daily.daily", "Daily"),
    "Hard": TaskEntry("module.hard.hard", "CampaignHard"),
    "Exercise": TaskEntry("module.exercise.exercise", "Exercise"),
    "Sos": TaskEntry("module.sos.sos", "CampaignSos"),
    "WarArchives": TaskEntry(
        "module.war_archives.war_archives", "CampaignWarArchives", method_kwargs=_campaign_kwargs,
        family="war_archives"
    ),
    "RaidDaily": TaskEntry("module.raid.daily", "RaidDaily", family="raid"),
    "EventA": TaskEntry("module.event.campaign_abcd", "CampaignABCD", family="event"),
    "EventB": TaskEntry("module.event.campaign_abcd", "CampaignABCD", family="event"),
    "EventC": TaskEntry("module.event.campaign_abcd", "CampaignABCD", family="event"),
    "EventD": TaskEntry("module.event.campaign_abcd", "CampaignABCD", family="event"),
    "EventSp": TaskEntry("module.event.campaign_sp", "CampaignSP", family="event"),
    "MaritimeEscort": TaskEntry("module.event.maritime_escort", "MaritimeEscort", family="maritime"),
    "OpsiAshAssist": TaskEntry("module.os_ash.meta", "AshBeaconAssist"),
    "OpsiAshBeacon": TaskEntry("module.os_ash.meta", "OpsiAshBeacon"),
    "OpsiExplore": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_explore"),
    "OpsiShop": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_shop"),
    "OpsiVoucher": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_voucher"),
    "OpsiDaily": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_daily"),
    "OpsiObscure": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_obscure"),
    "OpsiMonthBoss": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_month_boss"),
    "OpsiAbyssal": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_abyssal"),
    "OpsiArchive": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_archive"),
    "OpsiStronghold": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_stronghold"),
    "OpsiMeowfficerFarming": TaskEntry(
        "module.campaign.os_run", "OSCampaignRun", method="opsi_meowfficer_farming"
    ),
    "OpsiHazard1Leveling": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_hazard1_leveling"),
    "OpsiCrossMonth": TaskEntry("module.campaign.os_run", "OSCampaignRun", method="opsi_cross_month"),
    "Main": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs, family="main"),
    "Main2": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs, family="main"),
    "Main3": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs, family="main"),
    "Event": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs, family="event"),
    "Event2": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs, family="event"),
    "Raid": TaskEntry("module.raid.run", "RaidRun", family="raid"),
    "Hospital": TaskEntry("module.event_hospital.hospital", "Hospital", family="hospital"),
    "Coalition": TaskEntry("module.coalition.coalition", "Coalition", family="coalition"),
    "CoalitionSp": TaskEntry("module.coalition.coalition_sp", "CoalitionSP", family="coalition"),
    "C72MysteryFarming": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs),
    "C122MediumLeveling": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs),
    "C124LargeLeveling": TaskEntry("module.campaign.run", "CampaignRun", method_kwargs=_campaign_kwargs),
    "GemsFarming": TaskEntry("module.campaign.gems_farming", "GemsFarming", method_kwargs=_campaign_kwargs, family="gems"),
    "IslandProduction": TaskEntry("module.island.production", "IslandProduction"),
    "IslandOrder": TaskEntry("module.island.order", "IslandOrder"),
    "IslandFreebie": TaskEntry("module.island.freebie", "IslandFreebie"),
    "IslandCollect": TaskEntry("module.island.collect", "IslandCollect"),
    "IslandSeasonTask": TaskEntry("module.island.season_task", "IslandSeasonTask"),
    "IslandBusiness": TaskEntry("module.island.business", "IslandBusiness"),
    "Daemon": TaskEntry("module.daemon.daemon", "AzurLaneDaemon", task_arg=True),
    "OpsiDaemon": TaskEntry("module.daemon.os_daemon", "AzurLaneDaemon", task_arg=True),
    "EventStory": TaskEntry("module.eventstory.eventstory", "EventStory", task_arg=True),
    "IslandProductionPlanner": TaskEntry(
        "module.island_handler.production_planner", "IslandProductionPlanner", task_arg=True
    ),
    "AzurLaneUncensored": TaskEntry("module.daemon.uncensored", "AzurLaneUncensored", task_arg=True),
    "Benchmark": TaskEntry("module.daemon.benchmark", function="run_benchmark"),
    "GameManager": TaskEntry("module.daemon.game_manager", "GameManager", task_arg=True),
}

# snake_case command form (what the scheduler passes to run()) -> task name.
# Precomputed here so runtime lookup is a plain dict hit.
TASK_BY_COMMAND: dict[str, str] = {
    inflection.underscore(name): name for name in TASK_REGISTRY
}

# Family -> task names, in registry declaration order.
# Phase 4D: this is the single source of truth for the task families that
# config generation and campaign event logic used to hand-maintain as
# constants (MAINS/EVENTS/RAIDS/... in config_updater.py).
TASK_FAMILIES: dict[str, list[str]] = {}
for _name, _entry in TASK_REGISTRY.items():
    if _entry.family:
        TASK_FAMILIES.setdefault(_entry.family, []).append(_name)


def family_tasks(family: str) -> list[str]:
    """Tasks of a family. Consumers must treat the result as a set; order is
    registry declaration order and is not part of the contract."""
    return list(TASK_FAMILIES.get(family, []))
