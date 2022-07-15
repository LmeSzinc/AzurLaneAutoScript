from module.base.timer import Timer
from module.exception import CampaignEnd, RequestHumanTakeover, ScriptEnd
from module.handler.fast_forward import FastForwardHandler
from module.handler.mystery import MysteryHandler
from module.logger import logger
from module.map.assets import *
from module.map.map_fleet_preparation import FleetPreparation
from module.retire.retirement import Retirement


class MapOperation(MysteryHandler, FleetPreparation, Retirement, FastForwardHandler):
    map_cat_attack_timer = Timer(2)
    map_clear_percentage_prev = -1
    map_clear_percentage_timer = Timer(0.3, count=1)

    # Fleet that shows on screen.
    fleet_show_index = 1
    # Note that this is different from get_fleet_current_index()
    # In fleet_current_index, 1 means mob fleet, 2 means boss fleet.
    fleet_current_index = 1

    def get_fleet_show_index(self):
        """
        Get the fleet that shows on screen.

        Returns:
            int: 1 or 2

        Pages:
            in: in_map
        """
        if self.appear(FLEET_NUM_1, offset=(20, 20)):
            self.fleet_show_index = 1
            return 1
        elif self.appear(FLEET_NUM_2, offset=(20, 20)):
            self.fleet_show_index = 2
            return 2
        else:
            logger.warning('Unknown fleet current index, use 1 by default')
            self.fleet_show_index = 1
            return 1

    def get_fleet_current_index(self):
        """
        Returns:
            int: 1 or 2
        """
        if self.fleets_reversed:
            self.fleet_current_index = 3 - self.fleet_show_index
            return self.fleet_current_index
        else:
            self.fleet_current_index = self.fleet_show_index
            return self.fleet_current_index

    def fleet_set(self, index=None, skip_first_screenshot=True):
        """
        Args:
            index (int): Target fleet_current_index
            skip_first_screenshot (bool):

        Returns:
            bool: If switched.
        """
        logger.info(f'Fleet set to {index}')
        timeout = Timer(5, count=10).start()
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Fleet set timeout, assume current fleet is correct')
                break

            if self.handle_story_skip():
                timeout.reset()
                continue
            if self.handle_in_stage():
                timeout.reset()
                continue

            self.get_fleet_show_index()
            self.get_fleet_current_index()
            logger.info(f'Fleet: {self.fleet_show_index}, fleet_current_index: {self.fleet_current_index}')
            if self.fleet_current_index == index:
                break
            elif self.appear_then_click(SWITCH_OVER):
                count += 1
                self.device.sleep((1, 1.5))
                timeout.reset()
                continue
            else:
                logger.warning('SWITCH_OVER not found')
                continue

        return count > 0

    def enter_map(self, button, mode='normal', skip_first_screenshot=True):
        """Enter a campaign.

        Args:
            button: Campaign to enter.
            mode (str): 'normal' or 'hard' or 'cd'
            skip_first_screenshot (bool):
        """
        logger.hr('Enter map')
        campaign_timer = Timer(5)
        map_timer = Timer(5)
        fleet_timer = Timer(5)
        campaign_click = 0
        map_click = 0
        fleet_click = 0
        checked_in_map = False
        self.stage_entrance = button

        with self.stat.new(
                genre=self.config.campaign_name, method=self.config.DropRecord_CombatRecord
        ) as drop:
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # Check errors
                if campaign_click > 5:
                    logger.critical(f"Failed to enter {button}, too many click on {button}")
                    logger.critical("Possible reason #1: You haven't reached the commander level to unlock this stage.")
                    raise RequestHumanTakeover
                if fleet_click > 5:
                    logger.critical(f"Failed to enter {button}, too many click on FLEET_PREPARATION")
                    logger.critical("Possible reason #1: "
                                    "Your fleets haven't satisfied the stat restrictions of this stage.")
                    logger.critical("Possible reason #2: "
                                    "This stage can only be farmed once a day, "
                                    "but it's the second time that you are entering")
                    raise RequestHumanTakeover

                # Already in map
                if not checked_in_map and self.is_in_map():
                    logger.info('Already in map, skip enter_map.')
                    return False
                else:
                    checked_in_map = True

                # Map preparation
                if map_timer.reached() and self.handle_map_preparation():
                    self.map_get_info()
                    self.handle_fast_forward()
                    self.handle_auto_search()
                    if self.triggered_map_stop():
                        self.enter_map_cancel()
                        self.handle_map_stop()
                        raise ScriptEnd(f'Reach condition: {self.config.StopCondition_MapAchievement}')
                    self.device.click(MAP_PREPARATION)
                    map_click += 1
                    map_timer.reset()
                    campaign_timer.reset()
                    continue

                # Fleet preparation
                if fleet_timer.reached() and self.appear(FLEET_PREPARATION, offset=(20, 20)):
                    if mode == 'normal' or mode == 'hard':
                        self.handle_2x_book_setting(mode='prep')
                        self.fleet_preparation()
                        self.handle_auto_submarine_call_disable()
                        self.handle_auto_search_setting()
                        self.map_fleet_checked = True
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

                # Use Data Key
                if self.handle_use_data_key():
                    continue

                # Emotion
                if self.handle_combat_low_emotion():
                    continue

                # Urgent commission
                if self.handle_urgent_commission(drop=drop):
                    continue

                # 2X book popup
                if self.handle_2x_book_popup():
                    continue

                # Story skip
                if self.handle_story_skip():
                    campaign_timer.reset()
                    continue

                # Enter campaign
                if campaign_timer.reached() and self.appear_then_click(button):
                    campaign_click += 1
                    campaign_timer.reset()
                    continue

                # End
                if self.map_is_auto_search:
                    if self.is_auto_search_running():
                        break
                else:
                    if self.handle_in_map_with_enemy_searching():
                        # self.handle_map_after_combat_story()
                        break

        return True

    def enter_map_cancel(self, skip_first_screenshot=True):
        logger.hr('Enter map cancel')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MAP_PREPARATION, offset=(20, 20)) or self.appear(FLEET_PREPARATION, offset=(20, 20)):
                self.device.click(MAP_PREPARATION_CANCEL)
                continue

            if self.is_in_stage():
                break

        return True

    def handle_map_preparation(self):
        """
        Returns:
            bool: If MAP_PREPARATION and tha animation of map information finished
        """
        if not self.appear(MAP_PREPARATION, offset=(20, 20)):
            self.map_clear_percentage_prev = -1
            self.map_clear_percentage_timer.reset()
            return False

        percent = self.get_map_clear_percentage()
        logger.attr('Map_clear_percentage', percent)
        # Comment this because percentage starts from 100% and increase from 0% to actual value
        # if percent > 0.95:
        #     # map clear percentage 100%, exit directly
        #     return True
        if abs(percent - self.map_clear_percentage_prev) < 0.02:
            self.map_clear_percentage_prev = percent
            if self.map_clear_percentage_timer.reached():
                return True
            else:
                return False
        else:
            self.map_clear_percentage_prev = percent
            self.map_clear_percentage_timer.reset()
            return False

    def withdraw(self, skip_first_screenshot=True):
        """
        Withdraw campaign.
        """
        logger.hr('Map withdraw')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_popup_confirm('WITHDRAW'):
                continue
            if self.appear_then_click(WITHDRAW, interval=5):
                continue
            if self.handle_auto_search_exit():
                continue

            # End
            if self.handle_in_stage():
                raise CampaignEnd('Withdraw')

    def handle_map_cat_attack(self):
        """
        Click to skip the animation when cat attacks.
        """
        if not self.map_cat_attack_timer.reached():
            return False
        if self.image_color_count(MAP_CAT_ATTACK, color=(255, 231, 123), threshold=221, count=100):
            logger.info('Skip map cat attack')
            self.device.click(MAP_CAT_ATTACK)
            self.map_cat_attack_timer.reset()
            return True
        if not self.map_is_clear_mode:
            # Threat: Med has 106 pixels count, MAP_CAT_ATTACK_MIRROR has 290.
            if self.image_color_count(MAP_CAT_ATTACK_MIRROR, color=(255, 231, 123), threshold=221, count=200):
                logger.info('Skip map being attack')
                self.device.click(MAP_CAT_ATTACK)
                self.map_cat_attack_timer.reset()
                return True

        return False

    @property
    def fleets_reversed(self):
        if not self.config.FLEET_2:
            return False
        return self.config.Fleet_FleetOrder in ['fleet1_boss_fleet2_mob', 'fleet1_standby_fleet2_all']

    def handle_fleet_reverse(self):
        """
        The game chooses the fleet with a smaller index to be the first fleet,
        no matter what we choose in fleet preparation.

        After the update of auto-search, the game no longer ignore user settings.

        Returns:
            bool: Fleet changed
        """
        if not self.map_is_hard_mode \
                and self.config.Fleet_FleetOrder in ['fleet1_boss_fleet2_mob', 'fleet1_standby_fleet2_all']:
            logger.warning(f"You shouldn't use a reversed fleet order ({self.config.Fleet_FleetOrder}) in normal mode.")
            logger.warning('Please reverse your Fleet 1 and Fleet 2, '
                           'use "fleet1_mob_fleet2_boss" or "fleet1_all_fleet2_standby"')
            # raise RequestHumanTakeover

        if not self.fleets_reversed:
            return False

        return self.fleet_set(index=2)
