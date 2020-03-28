import traceback

from module.ui.assets import *

MAIN_CHECK = MAIN_GOTO_CAMPAIGN
CAMPAIGN_CHECK = CAMPAIGN_GOTO_EXERCISE


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
