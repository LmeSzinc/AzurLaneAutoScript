import numpy as np

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_similarity_2d
from module.exception import CampaignEnd
from module.exception import ScriptEnd
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
    _emotion_expected_reduce: tuple

    def fleet_switch_click(self):
        """
        Switch fleet.
        """
        logger.info('Switch over')
        self.wait_until_appear(SWITCH_OVER, skip_first_screenshot=True)

        FLEET_NUM.load_color(self.device.image)
        FLEET_NUM._match_init = True
        while 1:
            self.device.click(SWITCH_OVER)
            self.device.sleep((1, 1.5))
            self.device.screenshot()
            if not FLEET_NUM.match(self.device.image, offset=(0, 0), threshold=0.9):
                break
            logger.warning('Fleet switch failed. Retrying.')

    def enter_map(self, button, mode='normal'):
        """Enter a campaign.

        Args:
            button: Campaign to enter.
            mode (str): 'normal' or 'hard' or 'cd'
        """
        logger.hr('Enter map')
        campaign_timer = Timer(5)
        map_timer = Timer(5)
        fleet_timer = Timer(5)
        checked_in_map = False
        self.stage_entrance = button

        while 1:
            self.device.screenshot()

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
                    self.device.send_notification('Reach condition:', self.config.STOP_IF_MAP_REACH)
                    raise ScriptEnd(f'Reach condition: {self.config.STOP_IF_MAP_REACH}')
                self.device.click(MAP_PREPARATION)
                map_timer.reset()
                campaign_timer.reset()
                continue

            # Fleet preparation
            if fleet_timer.reached() and self.appear(FLEET_PREPARATION, offset=(20, 20)):
                if self.config.ENABLE_FLEET_CONTROL:
                    if mode == 'normal' or mode == 'hard':
                        self.handle_2x_book_setting(mode='prep')
                        self.fleet_preparation()
                        self.handle_auto_search_setting()
                        self.handle_auto_search_emotion_wait()
                self.device.click(FLEET_PREPARATION)
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
            if self.handle_urgent_commission():
                continue

            # Story skip
            if self.handle_story_skip():
                campaign_timer.reset()
                continue

            # Enter campaign
            if campaign_timer.reached() and self.appear_then_click(button):
                campaign_timer.reset()
                continue

            # End
            if self.map_is_auto_search:
                if self.is_auto_search_running():
                    break
            else:
                if self.handle_in_map_with_enemy_searching():
                    self.handle_map_after_combat_story()
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
        if abs(percent - self.map_clear_percentage_prev) < 0.02:
            self.map_clear_percentage_prev = percent
            if self.map_clear_percentage_timer.reached():
                return True

        else:
            self.map_clear_percentage_prev = percent
            self.map_clear_percentage_timer.reset()
            return False

    def withdraw(self):
        """
        Withdraw campaign.
        """
        logger.hr('Map withdraw')
        while 1:
            self.device.screenshot()

            if self.handle_popup_confirm():
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
        if np.sum(color_similarity_2d(self.image_area(MAP_CAT_ATTACK), (255, 231, 123)) > 221) > 100:
            logger.info('Skip map cat attack')
            self.device.click(MAP_CAT_ATTACK)
            self.map_cat_attack_timer.reset()
            return True

        return False

    @property
    def fleets_reversed(self):
        if self.map_is_auto_search:
            return self.config.AUTO_SEARCH_SETTING in ['fleet1_boss_fleet2_mob', 'fleet1_standby_fleet2_all']
        else:
            # return (self.config.FLEET_2 != 0) and (self.config.FLEET_2 < self.config.FLEET_1)
            return self.map_is_hard_mode and self.config.ENABLE_FLEET_REVERSE_IN_HARD

    def handle_fleet_reverse(self):
        """
        The game chooses the fleet with a smaller index to be the first fleet,
        no matter what we choose in fleet preparation.

        After the update of auto-search, the game no longer ignore user settings.

        Returns:
            bool: Fleet changed
        """
        if not self.fleets_reversed:
            return False

        self.fleet_switch_click()
        self.ensure_no_info_bar()  # The info_bar which shows "Changed to fleet 2", will block the ammo icon
        return True

    @cached_property
    def _emotion_expected_reduce(self):
        """
        Returns:
            tuple(int): Mob fleet emotion reduce, BOSS fleet emotion reduce
        """
        default = (self.emotion.get_expected_reduce, self.emotion.get_expected_reduce)
        if hasattr(self, 'map'):
            for data in self.map.spawn_data:
                if 'boss' in data:
                    battle = data.get('battle')
                    reduce = (battle * default[0], default[1])
                    if self.config.AUTO_SEARCH_SETTING in ['fleet1_all_fleet2_standby', 'fleet1_standby_fleet2_all']:
                        reduce = (reduce[0] + reduce[1], 0)
                    return reduce

            logger.warning('No boss data found in spawn_data')
            return default
        else:
            logger.info('Unable to get _emotion_expected_reduce, because map is not loaded. Return default value.')
            return default

    def handle_auto_search_emotion_wait(self):
        """
        If enable auto search, wait emotion before entering.
        In first run, wait before clicking FLEET_PREPARATION.
        In second and subsequent run, wait before clicking AUTO_SEARCH_MENU_CONTINUE.
        """
        if not self.config.ENABLE_EMOTION_REDUCE:
            return False
        if not self.config.ENABLE_AUTO_SEARCH:
            return False

        if hasattr(self, 'emotion'):
            logger.info(f'Expected emotion reduce: {self._emotion_expected_reduce}')
            self.emotion.wait(expected_reduce=self._emotion_expected_reduce)
        else:
            logger.info('Emotion instance not loaded, skip emotion wait')
