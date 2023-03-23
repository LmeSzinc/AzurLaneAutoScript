from module.base.timer import Timer
from module.coalition.assets import *
from module.combat.assets import BATTLE_PREPARATION
from module.combat.combat import Combat
from module.exception import CampaignNameError, RequestHumanTakeover
from module.logger import logger
from module.ui.assets import COALITION_CHECK
from module.ui.switch import Switch

MODE_SWITCH = Switch('CoalitionMode', offset=(20, 20))
MODE_SWITCH.add_status('story', MODE_SWITCH_STORY)
MODE_SWITCH.add_status('battle', MODE_SWITCH_BATTLE)

FLEET_SWITCH = Switch('FleetMode', is_selector=True, offset=0)  # No offset for color match
FLEET_SWITCH.add_status('single', FLEET_SWITCH_SINGLE)
FLEET_SWITCH.add_status('multi', FLEET_SWITCH_MULTI)


class CoalitionUI(Combat):
    def in_coalition(self):
        # The same as raid
        return self.appear(COALITION_CHECK, offset=(20, 20))

    def coalition_ensure_mode(self, mode):
        """
        Args:
            mode (str): 'story' or 'battle'

        Pages:
            in: in_coalition
        """
        if mode == 'story':
            MODE_SWITCH.set('battle', main=self)
        elif mode == 'battle':
            MODE_SWITCH.set('story', main=self)
        else:
            logger.warning(f'Unknown coalition campaign mode: {mode}')

    def coalition_ensure_fleet(self, mode):
        """
        Args:
            mode (str): 'single' or 'multi'

        Pages:
            in: FLEET_PREPARATION
        """
        if mode == 'single':
            FLEET_SWITCH.set('single', main=self)
        elif mode == 'multi':
            FLEET_SWITCH.set('multi', main=self)
        else:
            logger.warning(f'Unknown coalition fleet mode: {mode}')

    @staticmethod
    def coalition_get_entrance(stage):
        """
        Args:
            stage (str): Stage name.

        Returns:
            Button: Entrance button
        """
        stage = stage.lower()
        if stage == 'tc1':
            return FROSTFALL_TC1
        if stage == 'tc2':
            return FROSTFALL_TC2
        if stage == 'tc3':
            return FROSTFALL_TC3
        if stage == 'sp':
            return FROSTFALL_SP
        if stage == 'ex':
            return FROSTFALL_EX

        raise CampaignNameError

    @staticmethod
    def coalition_get_battles(stage):
        """
        Args:
            stage (str): Stage name.

        Returns:
            int: Number of battles
        """
        if stage == 'tc1':
            return 1
        if stage == 'tc2':
            return 2
        if stage == 'tc3':
            return 3

        return 1

    def handle_fleet_preparation(self, stage, fleet):
        stage = stage.lower()

        # No fleet switch in TC1
        if stage in ['tc1', 'sp']:
            return False

        self.coalition_ensure_fleet(fleet)
        return True

    def enter_map(self, stage, fleet, skip_first_screenshot=True):
        """
        Args:
            stage (str): Stage name such as 'TC3'
            fleet (str): 'single' or 'multi'
            skip_first_screenshot:

        Pages:
            in: in_coalition
            out: BATTLE_PREPARATION
        """
        button = self.coalition_get_entrance(stage)
        campaign_timer = Timer(5)
        fleet_timer = Timer(5)
        campaign_click = 0
        fleet_click = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Check errors
            if campaign_click > 5:
                logger.critical(f"Failed to enter {button}, too many click on {button}")
                logger.critical("Possible reason #1: You haven't cleared previous stage to unlock the stage.")
                raise RequestHumanTakeover
            if fleet_click > 5:
                logger.critical(f"Failed to enter {button}, too many click on FLEET_PREPARATION")
                logger.critical("Possible reason #1: "
                                "Your fleets haven't satisfied the stat restrictions of this stage.")
                logger.critical("Possible reason #2: "
                                "This stage can only be farmed once a day, "
                                "but it's the second time that you are entering")
                raise RequestHumanTakeover
            if self.appear(FLEET_NOT_PREPARED, offset=(20, 20)):
                logger.critical('FLEET_NOT_PREPARED')
                logger.critical('Please prepare you fleets before running coalition battles')
                raise RequestHumanTakeover

            # End
            if self.appear(BATTLE_PREPARATION, offset=(20, 20)):
                break

            # Enter campaign
            if campaign_timer.reached() and self.in_coalition():
                self.device.click(button)
                campaign_click += 1
                campaign_timer.reset()
                continue

            # Fleet preparation
            if fleet_timer.reached() and self.appear(FLEET_PREPARATION, offset=(20, 20)):
                self.handle_fleet_preparation(stage, fleet)
                self.device.click(FLEET_PREPARATION)
                fleet_click += 1
                fleet_timer.reset()
                campaign_timer.reset()
                continue

            # Auto search continue
            if self.handle_auto_search_continue():
                campaign_timer.reset()
                continue

            # Retire
            if self.handle_retirement():
                continue

            # Emotion
            if self.handle_combat_low_emotion():
                continue

            # Urgent commission
            if self.handle_urgent_commission(drop=None):
                continue

            # Story skip
            if self.handle_story_skip():
                campaign_timer.reset()
                continue

            # Auto confirm
            if self.handle_combat_automation_confirm():
                continue
