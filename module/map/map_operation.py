import numpy as np

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

    def fleet_switch_click(self):
        """
        Switch fleet.
        """
        logger.info('Switch over')
        if self.appear_then_click(SWITCH_OVER):
            pass
        else:
            logger.warning('No buttons detected.')

        self.device.sleep((1, 1.5))
        # self.ensure_no_info_bar()

    def enter_map(self, button, mode='normal'):
        """Enter a campaign.

        Args:
            button: Campaign to enter.
            mode (str): 'normal' or 'hard' or 'cd'
        """
        logger.hr('Enter map')
        campaign_timer = Timer(2)
        map_timer = Timer(1)
        fleet_timer = Timer(1)
        checked_in_map = False
        while 1:
            self.device.screenshot()

            if not checked_in_map and self.is_in_map():
                logger.info('Already in map, skip enter_map.')
                return False
            else:
                checked_in_map = True

            # Map preparation
            if map_timer.reached() and self.appear(MAP_PREPARATION):
                self.device.sleep(0.3)  # Wait for map information.
                self.device.screenshot()
                if self.handle_map_clear_mode_stop():
                    self.enter_map_cancel()
                    raise ScriptEnd(f'Reach condition: {self.config.CLEAR_MODE_STOP_CONDITION}')
                self.handle_fast_forward()
                self.device.click(MAP_PREPARATION)
                map_timer.reset()
                campaign_timer.reset()
                continue

            # Fleet preparation
            if fleet_timer.reached() and self.appear(FLEET_PREPARATION):
                if self.config.ENABLE_FLEET_CONTROL:
                    if mode == 'normal' or mode == 'hard':
                        self.fleet_preparation()
                self.device.click(FLEET_PREPARATION)
                fleet_timer.reset()
                campaign_timer.reset()
                continue

            # Retire
            if self.handle_retirement():
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
            if campaign_timer.reached() and self.is_in_stage():
                self.device.click(button)
                campaign_timer.reset()
                continue

            # End
            if self.handle_in_map_with_enemy_searching():
                break

        return True

    def enter_map_cancel(self, skip_first_screenshot=True):
        logger.hr('Enter map cancel')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MAP_PREPARATION) or self.appear(FLEET_PREPARATION):
                self.device.click(MAP_PREPARATION_CANCEL)
                continue

            if self.is_in_stage():
                break

        return True

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

    def handle_fleet_reverse(self):
        """
        The game chooses the fleet with a smaller index to be the first fleet,
        no matter what we choose in fleet preparation.

        Returns:
            bool: Fleet changed
        """
        if (self.config.FLEET_2 == 0) or (self.config.FLEET_2 > self.config.FLEET_1):
            return False

        self.fleet_switch_click()
        return True

    def handle_spare_fleet(self):
        pass
