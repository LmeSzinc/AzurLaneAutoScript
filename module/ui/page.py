import traceback

from module.ui.assets import *

MAIN_CHECK = MAIN_GOTO_CAMPAIGN


class Page:
    parent = None

    def __init__(self, check_button):
        self.check_button = check_button
        self.links = {}
        (filename, line_number, function_name, text) = traceback.extract_stack()[-2]
        self.name = text[:text.find('=')].strip()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def link(self, button, destination):
        self.links[destination] = button


# Main
page_main = Page(MAIN_CHECK)
page_campaign = Page(CAMPAIGN_CHECK)
page_fleet = Page(FLEET_CHECK)
page_main.link(button=MAIN_GOTO_CAMPAIGN, destination=page_campaign)
page_main.link(button=MAIN_GOTO_FLEET, destination=page_fleet)
page_campaign.link(button=GOTO_MAIN, destination=page_main)
page_fleet.link(button=GOTO_MAIN, destination=page_main)

# Unknown
page_unknown = Page(None)
page_unknown.link(button=GOTO_MAIN, destination=page_main)

# Exercise
page_exercise = Page(EXERCISE_CHECK)
page_exercise.link(button=GOTO_MAIN, destination=page_main)
page_exercise.link(button=BACK_ARROW, destination=page_campaign)
page_campaign.link(button=CAMPAIGN_GOTO_EXERCISE, destination=page_exercise)

# Daily
page_daily = Page(DAILY_CHECK)
page_daily.link(button=GOTO_MAIN, destination=page_main)
page_daily.link(button=BACK_ARROW, destination=page_campaign)
page_campaign.link(button=CAMPAIGN_GOTO_DAILY, destination=page_daily)

# Event
page_event = Page(EVENT_CHECK)
page_event.link(button=GOTO_MAIN, destination=page_main)
page_event.link(button=BACK_ARROW, destination=page_campaign)
page_campaign.link(button=CAMPAIGN_GOTO_EVENT, destination=page_event)

# SP
page_sp = Page(SP_CHECK)
page_sp.link(button=GOTO_MAIN, destination=page_main)
page_sp.link(button=BACK_ARROW, destination=page_campaign)
page_campaign.link(button=CAMPAIGN_GOTO_EVENT, destination=page_sp)

# Reward
page_reward = Page(REWARD_CHECK)
page_reward.link(button=REWARD_GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_REWARD, destination=page_reward)

# Mission
page_mission = Page(MISSION_CHECK)
page_mission.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_MISSION, destination=page_mission)

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

# Event list
page_event_list = Page(EVENT_LIST_CHECK)
page_event_list.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_EVENT_LIST, destination=page_event_list)

# Raid
page_raid = Page(RAID_CHECK)
page_raid.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_RAID, destination=page_raid)

# Research
# Please don't goto page_research from page_reward.
page_research = Page(RESEARCH_CHECK)
page_research.link(button=GOTO_MAIN, destination=page_main)

# Research menu
page_reshmenu = Page(RESHMENU_CHECK)
page_reshmenu.link(button=RESHMENU_GOTO_RESEARCH, destination=page_research)
page_reshmenu.link(button=GOTO_MAIN, destination=page_main)
page_main.link(button=MAIN_GOTO_RESHMENU, destination=page_reshmenu)
