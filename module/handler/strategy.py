import numpy as np

from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.template.assets import (TEMPLATE_FORMATION_1, TEMPLATE_FORMATION_2,
                                    TEMPLATE_FORMATION_3)
from module.ui.switch import Switch

formation = Switch('Formation', offset=120)
formation.add_status('line_ahead', check_button=FORMATION_1)
formation.add_status('double_line', check_button=FORMATION_2)
formation.add_status('diamond', check_button=FORMATION_3)

submarine_hunt = Switch('Submarine_hunt', offset=120)
submarine_hunt.add_status('on', check_button=SUBMARINE_HUNT_ON)
submarine_hunt.add_status('off', check_button=SUBMARINE_HUNT_OFF)

submarine_view = Switch('Submarine_view', offset=120)
submarine_view.add_status('on', check_button=SUBMARINE_VIEW_ON)
submarine_view.add_status('off', check_button=SUBMARINE_VIEW_OFF)


class StrategyHandler(InfoHandler):
    fleet_1_formation_fixed = False
    fleet_2_formation_fixed = False

    def strategy_open(self):
        logger.info('Strategy open')
        while 1:
            if self.appear(IN_MAP, interval=5) and not self.appear(STRATEGY_OPENED, offset=120):
                self.device.click(STRATEGY_OPEN)

            if self.appear(STRATEGY_OPENED, offset=120):
                break

            self.device.screenshot()

    def strategy_close(self):
        logger.info('Strategy close')
        while 1:
            if self.appear_then_click(STRATEGY_OPENED, offset=120, interval=5):
                pass

            if not self.appear(STRATEGY_OPENED, offset=120):
                break

            self.device.screenshot()

    def strategy_set_execute(self, formation_index=None, sub_view=None, sub_hunt=None):
        """
        Args:
            formation_index (int): 1-3, or None for don't change
            sub_view (bool):
            sub_hunt (bool):

        Pages:
            in: STRATEGY_OPENED
        """
        logger.info(f'Strategy set: formation={formation_index}, submarine_view={sub_view}, submarine_hunt={sub_hunt}')

        if formation_index is not None:
            formation.set(str(formation_index), main=self)
        # Disable this until the icon bug of submarine zone is fixed
        # And don't enable MAP_HAS_DYNAMIC_RED_BORDER when using submarine

        # Submarine view check is back again, see SwitchWithHandler.

        # Don't know when but the game bug was fixed, remove the use of SwitchWithHandler
        if sub_view is not None:
            if submarine_view.appear(main=self):
                submarine_view.set('on' if sub_view else 'off', main=self)
        if sub_hunt is not None:
            if submarine_hunt.appear(main=self):
                submarine_hunt.set('on' if sub_hunt else 'off', main=self)

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
            formation_index=expected_formation,
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
        image = self.image_crop(MAP_BUFF)
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

    def strategy_submarine_move_enter(self):
        """
        Pages:
            in: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
            out: SUBMARINE_MOVE_CONFIRM
        """
        logger.info('Submarine move enter')
        while 1:
            if self.appear(SUBMARINE_MOVE_ENTER, offset=120, interval=5):
                self.device.click(SUBMARINE_MOVE_ENTER)

            if self.appear(SUBMARINE_MOVE_CONFIRM, offset=(20, 20)):
                break

            self.device.screenshot()

    def strategy_submarine_move_confirm(self):
        """
        Pages:
            in: SUBMARINE_MOVE_CONFIRM
            out: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
        """
        logger.info('Submarine move confirm')
        while 1:
            if self.appear_then_click(SUBMARINE_MOVE_CONFIRM, offset=(20, 20), interval=5):
                pass
            if self.handle_popup_confirm('SUBMARINE_MOVE'):
                pass

            if self.appear(SUBMARINE_MOVE_ENTER, offset=120):
                break

            self.device.screenshot()

    def strategy_submarine_move_cancel(self):
        """
        Pages:
            in: SUBMARINE_MOVE_CONFIRM
            out: STRATEGY_OPENED, SUBMARINE_MOVE_ENTER
        """
        logger.info('Submarine move cancel')
        while 1:
            if self.appear_then_click(SUBMARINE_MOVE_CANCEL, offset=(20, 20), interval=5):
                pass
            if self.handle_popup_confirm('SUBMARINE_MOVE'):
                pass

            if self.appear(SUBMARINE_MOVE_ENTER, offset=120):
                break

            self.device.screenshot()
