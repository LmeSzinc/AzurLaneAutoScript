from module.base.timer import Timer
from module.handler.enemy_searching import EnemySearchingHandler
from module.handler.urgent_commission import UrgentCommissionHandler
from module.logger import logger
from module.map.assets import *
from module.map.exception import CampaignEnd
from module.map.map_fleet_preparation import FleetPreparation
from module.retire.retirement import Retirement


class MapOperation(UrgentCommissionHandler, EnemySearchingHandler, FleetPreparation, Retirement):
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

            # Enter campaign
            if campaign_timer.reached() and self.appear_then_click(button):
                campaign_timer.reset()
                continue

            # Map preparation
            if map_timer.reached() and self.appear(MAP_PREPARATION):
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
            pass

            # Urgent commission
            if self.handle_urgent_commission():
                continue

            # End
            if self.handle_in_map_with_enemy_searching():
                break

        return True

    def withdraw(self):
        """
        Withdraw campaign.
        """
        logger.hr('Map withdraw')
        while 1:
            self.device.screenshot()

            if self.appear_then_click(WITHDRAW, interval=2):
                continue
            if self.appear_then_click(WITHDRAW_CONFIRM, offset=True, interval=2):
                continue

            # End
            if self.handle_in_stage():
                raise CampaignEnd('Withdraw')

    def handle_map_cat_attack(self):
        """
        Click to skip the animation when cat attacks.
        """
        if self.appear_then_click(MAP_CAT_ATTACK, genre='cat_attack', interval=2):
            logger.info('Skip map cat attack')
            return True

        return False

    def handle_map_fleet_lock(self, lock=None, skip_first_screenshot=True):
        """
        Args:
            lock (bool, optional): Set to lock or unlock.
            skip_first_screenshot (bool):

        Returns:
            bool: If fleet lock changed.
        """
        if lock is None:
            lock = self.config.ENABLE_MAP_FLEET_LOCK

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if lock:
                if self.appear(FLEET_LOCKED):
                    logger.attr('Map_fleet', 'locked')
                    return False
                elif self.appear_then_click(FLEET_UNLOCKED, interval=1):
                    continue

            else:
                if self.appear(FLEET_UNLOCKED):
                    logger.attr('Map_fleet', 'unlocked')
                    return False
                elif self.appear_then_click(FLEET_LOCKED, interval=1):
                    continue

        return True

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
