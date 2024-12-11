from module.combat.assets import GET_ITEMS_1
from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.template.assets import (TEMPLATE_FORMATION_1, TEMPLATE_FORMATION_2,
                                    TEMPLATE_FORMATION_3)
from module.ui.switch import Switch

# 2023.10.19, icons on one row increased from 2 to 3
FORMATION = Switch('Formation', offset=(100, 200))
FORMATION.add_state('line_ahead', check_button=FORMATION_1)
FORMATION.add_state('double_line', check_button=FORMATION_2)
FORMATION.add_state('diamond', check_button=SUBMARINE_HUNT_ON)

SUBMARINE_HUNT = Switch('Submarine_hunt', offset=(200, 200))
SUBMARINE_HUNT.add_state('on', check_button=SUBMARINE_HUNT_ON)
SUBMARINE_HUNT.add_state('off', check_button=SUBMARINE_HUNT_OFF)

SUBMARINE_VIEW = Switch('Submarine_view', offset=(100, 200))
SUBMARINE_VIEW.add_state('on', check_button=SUBMARINE_VIEW_ON)
SUBMARINE_VIEW.add_state('off', check_button=SUBMARINE_VIEW_OFF)

MOB_MOVE_OFFSET = (120, 200)


class StrategyHandler(InfoHandler):
    fleet_1_formation_fixed = False
    fleet_2_formation_fixed = False

    def strategy_open(self, skip_first_screenshot=True):
        logger.info('Strategy open')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STRATEGY_OPENED, offset=200):
                break

            if self.appear(IN_MAP, interval=5) and not self.appear(STRATEGY_OPENED, offset=200):
                self.device.click(STRATEGY_OPEN)
                continue

            # Handle missed mysteries
            if self.appear_then_click(GET_ITEMS_1, offset=5):
                continue

    def strategy_close(self, skip_first_screenshot=True):
        logger.info('Strategy close')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(STRATEGY_OPENED, offset=200, interval=5):
                continue

            if not self.appear(STRATEGY_OPENED, offset=200):
                break

    def strategy_set_execute(self, formation=None, sub_view=None, sub_hunt=None):
        """
        Args:
            formation (str): 'line_ahead', 'double_line', 'diamond', or None for don't change
            sub_view (bool):
            sub_hunt (bool):

        Pages:
            in: STRATEGY_OPENED
        """
        logger.info(f'Strategy set: formation={formation}, submarine_view={sub_view}, submarine_hunt={sub_hunt}')

        if formation is not None:
            FORMATION.set(formation, main=self)
        # Disable this until the icon bug of submarine zone is fixed
        # And don't enable MAP_HAS_DYNAMIC_RED_BORDER when using submarine

        # Submarine view check is back again, see SwitchWithHandler.

        # Don't know when but the game bug was fixed, remove the use of SwitchWithHandler
        if sub_view is not None:
            if SUBMARINE_VIEW.appear(main=self):
                SUBMARINE_VIEW.set('on' if sub_view else 'off', main=self)
            else:
                logger.warning('Setting up submarine_view but no icon appears')
        if sub_hunt is not None:
            if SUBMARINE_HUNT.appear(main=self):
                SUBMARINE_HUNT.set('on' if sub_hunt else 'off', main=self)
            else:
                logger.warning('Setting up submarine_hunt but no icon appears')

    def handle_strategy(self, index):
        """

        Args:
            index (int): Fleet index.

        Returns:
            bool: If changed.
        """
        if self.__getattribute__(f'fleet_{index}_formation_fixed'):
            return False
        expected_formation = self.config.__getattribute__(f'Fleet_Fleet{index}Formation')
        if self._strategy_get_from_map_buff() == expected_formation and not self.config.Submarine_Fleet:
            logger.info('Skip strategy bar check.')
            self.__setattr__(f'fleet_{index}_formation_fixed', True)
            return False

        self.strategy_open()
        self.strategy_set_execute(
            formation=expected_formation,
            sub_view=False,
            sub_hunt=bool(self.config.Submarine_Fleet) and self.config.Submarine_Mode in ['hunt_only', 'hunt_and_boss']
        )
        self.strategy_close()
        self.__setattr__(f'fleet_{index}_formation_fixed', True)
        return True

    def _strategy_get_from_map_buff(self):
        """
        Returns:
            int: Formation index.
        """
        image = self.image_crop(MAP_BUFF, copy=False)
        if TEMPLATE_FORMATION_2.match(image):
            buff = 'double_line'
        elif TEMPLATE_FORMATION_1.match(image):
            buff = 'line_ahead'
        elif TEMPLATE_FORMATION_3.match(image):
            buff = 'diamond'
        else:
            buff = 'unknown'

        logger.attr('Map_buff', buff)
        return buff

    def is_in_strategy_submarine_move(self):
        """
        Returns:
            bool:
        """
        return self.appear(SUBMARINE_MOVE_CONFIRM, offset=(20, 20))

    def strategy_submarine_move_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
            out: SUBMARINE_MOVE_CONFIRM
        """
        logger.info('Submarine move enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SUBMARINE_MOVE_ENTER, offset=200, interval=5):
                self.device.click(SUBMARINE_MOVE_ENTER)

            if self.appear(SUBMARINE_MOVE_CONFIRM, offset=(20, 20)):
                break

    def strategy_submarine_move_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: SUBMARINE_MOVE_CONFIRM
            out: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
        """
        logger.info('Submarine move confirm')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(SUBMARINE_MOVE_CONFIRM, offset=(20, 20), interval=5):
                pass
            if self.handle_popup_confirm('SUBMARINE_MOVE'):
                pass

            if self.appear(SUBMARINE_MOVE_ENTER, offset=200):
                break

    def strategy_submarine_move_cancel(self, skip_first_screenshot=True):
        """
        Pages:
            in: SUBMARINE_MOVE_CONFIRM
            out: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
        """
        logger.info('Submarine move cancel')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(SUBMARINE_MOVE_CANCEL, offset=(20, 20), interval=5):
                pass
            if self.handle_popup_confirm('SUBMARINE_MOVE'):
                pass

            if self.appear(SUBMARINE_MOVE_ENTER, offset=200):
                break

    def is_in_strategy_mob_move(self):
        """
        Returns:
            bool:
        """
        return self.appear(MOB_MOVE_CANCEL, offset=(20, 20))

    def strategy_has_mob_move(self):
        """
        Pages:
            in: STRATEGY_OPENED
            out: STRATEGY_OPENED
        """
        if self.match_template_color(MOB_MOVE_ENTER, offset=MOB_MOVE_OFFSET):
            return True
        else:
            return False

    def strategy_mob_move_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: STRATEGY_OPENED, MOB_MOVE_ENTER
            out: MOB_MOVE_CANCEL
        """
        logger.info('Mob move enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MOB_MOVE_CANCEL, offset=(20, 20)):
                break

            if self.appear_then_click(MOB_MOVE_ENTER, offset=MOB_MOVE_OFFSET, interval=5):
                continue

    def strategy_mob_move_cancel(self, skip_first_screenshot=True):
        """
        Pages:
            in: MOB_MOVE_CANCEL
            out: STRATEGY_OPENED, MOB_MOVE_ENTER
        """
        logger.info('Mob move cancel')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MOB_MOVE_ENTER, offset=MOB_MOVE_OFFSET):
                break

            if self.appear_then_click(MOB_MOVE_CANCEL, offset=(20, 20), interval=5):
                continue
