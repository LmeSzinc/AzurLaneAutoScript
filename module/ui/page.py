import traceback

from module.coalition.assets import *
from module.raid.assets import *
from module.retire.assets import DOCK_CHECK
from module.ui.assets import *
from module.ui_white.assets import *


class Page:
    # Key: str, page name like "page_main"
    # Value: Page, page instance
    all_pages = {}

    @classmethod
    def clear_connection(cls):
        for page in cls.all_pages.values():
            page.parent = None

    @classmethod
    def init_connection(cls, destination):
        """
        Initialize an A* path finding among pages.

        Args:
            destination (Page):
        """
        cls.clear_connection()

        visited = [destination]
        visited = set(visited)
        while 1:
            new = visited.copy()
            for page in visited:
                for link in cls.iter_pages():
                    if link in visited:
                        continue
                    if page in link.links:
                        link.parent = page
                        new.add(link)
            if len(new) == len(visited):
                break
            visited = new

    @classmethod
    def iter_pages(cls):
        return cls.all_pages.values()

    @classmethod
    def iter_check_buttons(cls):
        for page in cls.all_pages.values():
            yield page.check_button

    def __init__(self, check_button):
        self.check_button = check_button
        self.links = {}
        (filename, line_number, function_name, text) = traceback.extract_stack()[-2]
        self.name = text[:text.find('=')].strip()
        self.parent = None
        Page.all_pages[self.name] = self

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def link(self, button, destination):
        self.links[destination] = button


"""
Define UI pages
"""

# Main
# Use MAIN_GOTO_FLEET instead of MAIN_GOTO_CAMPAIGN for faster switches with info_bar
page_main = Page(MAIN_GOTO_FLEET)
page_campaign_menu = Page(CAMPAIGN_MENU_CHECK)
page_campaign = Page(CAMPAIGN_CHECK)
page_fleet = Page(FLEET_CHECK)
page_main.link(button=MAIN_GOTO_CAMPAIGN, destination=page_campaign_menu)
page_main.link(button=MAIN_GOTO_FLEET, destination=page_fleet)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_CAMPAIGN, destination=page_campaign)
page_campaign_menu.link(button=GOTO_MAIN, destination=page_main)
page_campaign.link(button=GOTO_MAIN, destination=page_main)
page_campaign.link(button=BACK_ARROW, destination=page_campaign_menu)
page_fleet.link(button=GOTO_MAIN, destination=page_main)

# Main
# 2024.05.22, in new UI, MAIN_GOTO_CAMPAIGN_WHITE is the last shown button in page main
page_main_white = Page(MAIN_GOTO_CAMPAIGN_WHITE)
page_main_white.link(button=MAIN_GOTO_CAMPAIGN_WHITE, destination=page_campaign_menu)
page_main_white.link(button=MAIN_GOTO_FLEET_WHITE, destination=page_fleet)

# Unknown
page_unknown = Page(None)
page_unknown.link(button=GOTO_MAIN, destination=page_main)

# Exercise
# Don't enter page_exercise from page_campaign
page_exercise = Page(EXERCISE_CHECK)
page_exercise.link(button=GOTO_MAIN, destination=page_main)
page_exercise.link(button=BACK_ARROW, destination=page_campaign_menu)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EXERCISE, destination=page_exercise)

# Daily
# Don't enter page_daily from page_campaign
page_daily = Page(DAILY_CHECK)
page_daily.link(button=GOTO_MAIN, destination=page_main)
page_daily.link(button=BACK_ARROW, destination=page_campaign_menu)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_DAILY, destination=page_daily)

# Event
page_event = Page(EVENT_CHECK)
page_event.link(button=GOTO_MAIN, destination=page_main)
page_event.link(button=BACK_ARROW, destination=page_campaign)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EVENT, destination=page_event)
page_campaign.link(button=CAMPAIGN_GOTO_EVENT, destination=page_event)

# SP
page_sp = Page(SP_CHECK)
page_sp.link(button=GOTO_MAIN, destination=page_main)
page_sp.link(button=BACK_ARROW, destination=page_campaign)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EVENT, destination=page_sp)
page_campaign.link(button=CAMPAIGN_GOTO_EVENT, destination=page_sp)

# Coalition
# FROSTFALL
# page_coalition = Page(COALITION_CHECK)
# page_coalition.link(button=GOTO_MAIN, destination=page_main)
# page_coalition.link(button=BACK_ARROW, destination=page_campaign)
# page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EVENT, destination=page_coalition)
# ACADEMY
page_coalition_menu = Page(COALITION_ACADEMY_MAIN_CHECK)
page_coalition_menu.link(button=COALITION_ACADEMY_HOME, destination=page_main)
page_coalition = Page(COALITION_ACADEMY_CAMPAIGN_CHECK)
page_coalition.link(button=COALITION_ACADEMY_HOME, destination=page_main)
page_coalition.link(button=COALITION_ACADEMY_BACK, destination=page_coalition_menu)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EVENT, destination=page_coalition)
page_coalition_menu.link(button=COALITION_ACADEMY_GOTO_CAMPAIGN, destination=page_coalition)

# Operation Siren
page_os = Page(OS_CHECK)
page_os.link(button=GOTO_MAIN, destination=page_main)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_OS, destination=page_os)

# War Archives
# Don't enter page_archives from page_campaign
page_archives = Page(WAR_ARCHIVES_CHECK)
page_archives.link(button=WAR_ARCHIVES_GOTO_CAMPAIGN_MENU, destination=page_campaign_menu)
page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_WAR_ARCHIVES, destination=page_archives)

# Reward
page_reward = Page(REWARD_CHECK)
page_reward.link(button=REWARD_GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_REWARD, destination=page_reward)
page_main_white.link(button=MAIN_GOTO_REWARD_WHITE, destination=page_reward)

# Mission
page_mission = Page(MISSION_CHECK)
page_mission.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_MISSION, destination=page_mission)
page_main_white.link(button=MAIN_GOTO_MISSION_WHITE, destination=page_mission)

# Guild
page_guild = Page(GUILD_CHECK)
page_guild.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_GUILD, destination=page_guild)
page_main_white.link(button=MAIN_GOTO_GUILD_WHITE, destination=page_guild)

# Commission
# Please don't goto commission from campaign.
page_commission = Page(COMMISSION_CHECK)
page_commission.link(button=GOTO_MAIN, destination=page_main)
page_commission.link(button=BACK_ARROW, destination=page_reward)
page_reward.link(button=REWARD_GOTO_COMMISSION, destination=page_commission)

# Tactical class
# Please don't goto tactical class from academy.
page_tactical = Page(TACTICAL_CHECK)
page_tactical.link(button=GOTO_MAIN, destination=page_main)
page_tactical.link(button=BACK_ARROW, destination=page_reward)
page_reward.link(button=REWARD_GOTO_TACTICAL, destination=page_tactical)

# Battle pass
page_battle_pass = Page(BATTLE_PASS_CHECK)
page_battle_pass.link(button=GOTO_MAIN, destination=page_main)
page_reward.link(button=REWARD_GOTO_BATTLE_PASS, destination=page_battle_pass)

# Event list
page_event_list = Page(EVENT_LIST_CHECK)
page_event_list.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_EVENT_LIST, destination=page_event_list)
page_main_white.link(button=MAIN_GOTO_EVENT_LIST_WHITE, destination=page_event_list)

# Raid
page_raid = Page(RAID_CHECK)
page_raid.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_RAID, destination=page_raid)
page_main_white.link(button=MAIN_GOTO_RAID_WHITE, destination=page_raid)

# Dock
page_dock = Page(DOCK_CHECK)
page_dock.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_DOCK, destination=page_dock)
page_main_white.link(button=MAIN_GOTO_DOCK_WHITE, destination=page_dock)

# Research
# Please don't goto page_research from page_reward.
page_research = Page(RESEARCH_CHECK)
page_research.link(button=GOTO_MAIN, destination=page_main)

# Shipyard
page_shipyard = Page(SHIPYARD_CHECK)
page_shipyard.link(button=GOTO_MAIN, destination=page_main)

# Meta
page_meta = Page(META_CHECK)
page_meta.link(button=GOTO_MAIN, destination=page_main)

# Storage
page_storage = Page(STORAGE_CHECK)
page_storage.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_STORAGE, destination=page_storage)
page_main_white.link(button=MAIN_GOTO_STORAGE_WHITE, destination=page_storage)

# Research menu
page_reshmenu = Page(RESHMENU_CHECK)
page_reshmenu.link(button=RESHMENU_GOTO_RESEARCH, destination=page_research)
page_reshmenu.link(button=RESHMENU_GOTO_SHIPYARD, destination=page_shipyard)
page_reshmenu.link(button=RESHMENU_GOTO_META, destination=page_meta)
page_reshmenu.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_RESHMENU, destination=page_reshmenu)
page_main_white.link(button=MAIN_GOTO_RESHMENU, destination=page_reshmenu)

# Dorm menu
page_dormmenu = Page(DORMMENU_CHECK)
page_dormmenu.link(button=DORMMENU_GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_DORMMENU, destination=page_dormmenu)
page_main_white.link(button=MAIN_GOTO_DORMMENU_WHITE, destination=page_dormmenu)

# Dorm
# DORM_CHECK is the `manage` button (the third from the right), because it's the last button to load.
page_dorm = Page(DORM_CHECK)
page_dormmenu.link(button=DORMMENU_GOTO_DORM, destination=page_dorm)
page_dorm.link(button=DORM_GOTO_MAIN, destination=page_main)

# Meowfficer
page_meowfficer = Page(MEOWFFICER_CHECK)
page_dormmenu.link(button=DORMMENU_GOTO_MEOWFFICER, destination=page_meowfficer)
page_meowfficer.link(button=MEOWFFICER_GOTO_DORMMENU, destination=page_main)

# Academy
page_academy = Page(ACADEMY_CHECK)
page_dormmenu.link(button=DORMMENU_GOTO_ACADEMY, destination=page_academy)
page_academy.link(button=GOTO_MAIN, destination=page_main)

# Game room & choose game
page_game_room = Page(GAME_ROOM_CHECK)
page_academy.link(button=ACADEMY_GOTO_GAME_ROOM, destination=page_game_room)
page_game_room.link(button=GAME_ROOM_GOTO_MAIN, destination=page_main)

# Shop
page_shop = Page(SHOP_CHECK)
page_shop.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_SHOP, destination=page_shop)
page_main_white.link(button=MAIN_GOTO_SHOP_WHITE, destination=page_shop)

# Munitions
page_munitions = Page(MUNITIONS_CHECK)
# Prefer latter path since defaults to shop_general on load, stable background color
# page_shop.link(button=SHOP_GOTO_MUNITIONS, destination=page_munitions)
page_academy.link(button=ACADEMY_GOTO_MUNITIONS, destination=page_munitions)
page_munitions.link(button=GOTO_MAIN, destination=page_main)

# Supply pack
page_supply_pack = Page(SUPPLY_PACK_CHECK)
page_shop.link(button=SHOP_GOTO_SUPPLY_PACK, destination=page_supply_pack)
page_supply_pack.link(button=GOTO_MAIN, destination=page_main)

# Build / Construct
page_build = Page(BUILD_CHECK)
page_build.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_BUILD, destination=page_build)
page_main_white.link(button=MAIN_GOTO_BUILD_WHITE, destination=page_build)

# Mail
page_mail = Page(MAIL_CHECK)
page_mail.link(button=GOTO_MAIN_WHITE, destination=page_main)
# Mail enter varies from different UI
page_main_white.link(button=MAIL_ENTER_WHITE, destination=page_mail)

# World channel
# Both old and new UI have CHANNEL_CHECK
# Click somewhere left to leave
page_channel = Page(CHANNEL_CHECK)
page_channel.link(button=CAMPAIGN_MENU_GOTO_CAMPAIGN, destination=page_main)

# RPG event (raid_20240328)
page_rpg_stage = Page(RPG_GOTO_STORY)
page_rpg_story = Page(RPG_GOTO_STAGE)
page_rpg_stage.link(button=RPG_GOTO_STORY, destination=page_rpg_story)
page_rpg_stage.link(button=RPG_HOME, destination=page_main)
page_rpg_story.link(button=RPG_GOTO_STAGE, destination=page_rpg_stage)
page_rpg_story.link(button=RPG_HOME, destination=page_main)

page_campaign_menu.link(button=CAMPAIGN_MENU_GOTO_EVENT, destination=page_rpg_stage)
# page_main.link(button=MAIN_GOTO_RAID, destination=page_rpg_stage)
# page_main_white.link(button=MAIN_GOTO_RAID_WHITE, destination=page_rpg_stage)

page_rpg_city = Page(RPG_LEAVE_CITY)
page_rpg_city.link(button=RPG_LEAVE_CITY, destination=page_rpg_stage)
page_rpg_city.link(button=RPG_HOME, destination=page_main)

# Keep page_rpg_stage, so Raid can import
# page_rpg_stage = page_raid
