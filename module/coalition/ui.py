from module.base.timer import Timer
from module.coalition.assets import *
from module.combat.assets import BATTLE_PREPARATION
from module.combat.combat import Combat
from module.exception import CampaignNameError, RequestHumanTakeover, ScriptError
from module.logger import logger
from module.ui.page import page_coalition
from module.ui.switch import Switch


class CoalitionUI(Combat):
    def in_coalition(self):
        # The same as raid
        return self.ui_page_appear(page_coalition, offset=(20, 20))

    def coalition_ensure_mode(self, event, mode):
        """
        Args:
            event (str): Event name.
            mode (str): 'story' or 'battle'

        Pages:
            in: in_coalition
        """
        MODE_SWITCH = Switch('CoalitionMode', offset=(20, 20))
        if event == 'coalition_20230323':
            MODE_SWITCH.add_state('story', FROSTFALL_MODE_STORY)
            MODE_SWITCH.add_state('battle', FROSTFALL_MODE_BATTLE)
        elif event == 'coalition_20240627':
            # Note that switch button are reversed
            MODE_SWITCH.add_state('story', ACADEMY_MODE_BATTLE)
            MODE_SWITCH.add_state('battle', ACADEMY_MODE_STORY)
        else:
            logger.error(f'MODE_SWITCH is not defined in event {event}')
            raise ScriptError

        if mode == 'story':
            MODE_SWITCH.set('battle', main=self)
        elif mode == 'battle':
            MODE_SWITCH.set('story', main=self)
        else:
            logger.warning(f'Unknown coalition campaign mode: {mode}')

    def coalition_ensure_fleet(self, event, mode):
        """
        Args:
            event (str): Event name.
            mode (str): 'single' or 'multi'

        Pages:
            in: FLEET_PREPARATION
        """
        FLEET_SWITCH = Switch('FleetMode', is_selector=True, offset=0)  # No offset for color match
        if event == 'coalition_20230323':
            FLEET_SWITCH.add_state('single', FROSTFALL_SWITCH_SINGLE)
            FLEET_SWITCH.add_state('multi', FROSTFALL_SWITCH_MULTI)
        elif event == 'coalition_20240627':
            FLEET_SWITCH.add_state('single', ACADEMY_SWITCH_SINGLE)
            FLEET_SWITCH.add_state('multi', ACADEMY_SWITCH_MULTI)
        else:
            logger.error(f'FLEET_SWITCH is not defined in event {event}')
            raise ScriptError

        if mode == 'single':
            FLEET_SWITCH.set('single', main=self)
        elif mode == 'multi':
            FLEET_SWITCH.set('multi', main=self)
        else:
            logger.warning(f'Unknown coalition fleet mode: {mode}')

    @staticmethod
    def coalition_get_entrance(event, stage):
        """
        Args:
            event (str): Event name.
            stage (str): Stage name.

        Returns:
            Button: Entrance button
        """
        dic = {
            ('coalition_20230323', 'tc1'): FROSTFALL_TC1,
            ('coalition_20230323', 'tc2'): FROSTFALL_TC2,
            ('coalition_20230323', 'tc3'): FROSTFALL_TC3,
            ('coalition_20230323', 'sp'): FROSTFALL_SP,
            ('coalition_20230323', 'ex'): FROSTFALL_EX,

            ('coalition_20240627', 'easy'): ACADEMY_EASY,
            ('coalition_20240627', 'normal'): ACADEMY_NORMAL,
            ('coalition_20240627', 'hard'): ACADEMY_HARD,
            ('coalition_20240627', 'sp'): ACADEMY_SP,
            ('coalition_20240627', 'ex'): ACADEMY_EX,
        }
        stage = stage.lower()
        try:
            return dic[(event, stage)]
        except KeyError as e:
            logger.error(e)
            raise CampaignNameError

    @staticmethod
    def coalition_get_battles(event, stage):
        """
        Args:
            event (str): Event name.
            stage (str): Stage name.

        Returns:
            int: Number of battles
        """
        dic = {
            ('coalition_20230323', 'tc1'): 1,
            ('coalition_20230323', 'tc2'): 2,
            ('coalition_20230323', 'tc3'): 3,
            ('coalition_20230323', 'sp'): 1,
            ('coalition_20230323', 'ex'): 1,

            ('coalition_20240627', 'easy'): 1,
            ('coalition_20240627', 'normal'): 2,
            ('coalition_20240627', 'hard'): 3,
            ('coalition_20240627', 'sp'): 4,
            ('coalition_20240627', 'ex'): 5,
        }
        stage = stage.lower()
        try:
            return dic[(event, stage)]
        except KeyError as e:
            logger.error(e)
            raise CampaignNameError

    @staticmethod
    def coalition_get_fleet_preparation(event):
        """
        Args:
            event (str): Event name.

        Returns:
            Button:
        """
        if event == 'coalition_20230323':
            return FROSTFALL_FLEET_PREPARATION
        elif event == 'coalition_20240627':
            return ACEDEMY_FLEET_PREPARATION
        else:
            logger.error(f'FLEET_PREPARATION is not defined in event {event}')
            raise ScriptError

    def handle_fleet_preparation(self, event, stage, mode):
        """
        Args:
            event (str): Event name.
            stage (str): Stage name.
            mode (str): 'single' or 'multi'

        Returns:
            bool: If success
        """
        stage = stage.lower()

        if event == 'coalition_20230323':
            # No fleet switch in TC1
            if stage in ['tc1', 'sp']:
                return False
        if event == 'coalition_20240627':
            if stage in ['easy', 'sp', 'ex']:
                return False

        self.coalition_ensure_fleet(event, mode)
        return True

    def enter_map(self, event, stage, mode, skip_first_screenshot=True):
        """
        Args:
            event (str): Event name such as 'coalition_20230323'
            stage (str): Stage name such as 'TC3'
            mode (str): 'single' or 'multi'
            skip_first_screenshot:

        Pages:
            in: in_coalition
            out: BATTLE_PREPARATION
        """
        button = self.coalition_get_entrance(event, stage)
        fleet_preparation = self.coalition_get_fleet_preparation(event)
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

            if self.handle_guild_popup_cancel():
                continue

            # Enter campaign
            if campaign_timer.reached() and self.in_coalition():
                self.device.click(button)
                campaign_click += 1
                campaign_timer.reset()
                continue

            # Fleet preparation
            if fleet_timer.reached() and self.appear(fleet_preparation, offset=(20, 50)):
                self.handle_fleet_preparation(event, stage, mode)
                self.device.click(fleet_preparation)
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
