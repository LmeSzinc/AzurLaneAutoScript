import numpy as np
from module.base.switch import Switch
from module.handler.assets import *
from module.template.assets import TEMPLATE_FORMATION_1, TEMPLATE_FORMATION_2, TEMPLATE_FORMATION_3
from module.handler.info_bar import InfoBarHandler
from module.logger import logger

formation = Switch('Formation')
formation.add_status('1', check_button=FORMATION_1, offset=120)
formation.add_status('2', check_button=FORMATION_2, offset=120)
formation.add_status('3', check_button=FORMATION_3, offset=120)

submarine_view = Switch('Submarine_view')
submarine_view.add_status('on', check_button=SUBMARINE_VIEW_ON, offset=120)
submarine_view.add_status('off', check_button=SUBMARINE_VIEW_OFF, offset=120)

submarine_hunt = Switch('Submarine_hunt')
submarine_hunt.add_status('on', check_button=SUBMARINE_HUNT_ON, offset=120)
submarine_hunt.add_status('off', check_button=SUBMARINE_HUNT_OFF, offset=120)


class StrategyHandler(InfoBarHandler):
    fleet_1_formation_fixed = False
    fleet_2_formation_fixed = False

    def handle_opened_strategy_bar(self):
        if self.appear_then_click(STRATEGY_OPENED, offset=120):
            self.device.sleep(0.5)
            return True

        return False

    def strategy_open(self):
        self.device.click(STRATEGY_OPEN)
        self.device.sleep(0.5)

    def strategy_close(self):
        self.appear_then_click(STRATEGY_OPENED, offset=120)
        self.device.sleep(0.5)

    def strategy_set_execute(self, formation_index=2, sub_view=False, sub_hunt=False):
        """
        Args:
            formation_index (int):
            sub_view (bool):
            sub_hunt (bool):
        """
        logger.info(f'Strategy set: formation={formation_index}, submarine_view={sub_view}, submarine_hunt={sub_hunt}')
        self.strategy_open()
        self.device.screenshot()

        formation.set(str(formation_index), main=self)
        if submarine_view.appear(main=self):
            submarine_view.set('on' if sub_view else 'off', main=self)
        if submarine_hunt.appear(main=self):
            submarine_hunt.set('on' if sub_hunt else 'off', main=self)

        self.strategy_close()

    def handle_strategy(self, index):
        """

        Args:
            index (int): Fleet index.

        Returns:
            bool: If changed.
        """
        if not self.config.ENABLE_FLEET_CONTROL:
            return False
        if self.__getattribute__(f'fleet_{index}_formation_fixed'):
            return False
        expected_formation = self.config.__getattribute__(f'FLEET_{index}_FORMATION')
        if self._strategy_get_from_map_buff() == expected_formation and not self.config.SUBMARINE:
            logger.info('Skip strategy bar check.')
            self.__setattr__(f'fleet_{index}_formation_fixed', True)
            return False

        self.strategy_set_execute(
            formation_index=expected_formation,
            sub_view=False,
            sub_hunt=bool(self.config.SUBMARINE) and self.config.SUBMARINE_MODE == 'hunt_only'
        )
        self.__setattr__(f'fleet_{index}_formation_fixed', True)
        return True

    def _strategy_get_from_map_buff(self):
        """
        Returns:
            int: Formation index.
        """
        image = np.array(self.device.image.crop(MAP_BUFF.area))
        if TEMPLATE_FORMATION_2.match(image):
            buff = 2
        elif TEMPLATE_FORMATION_1.match(image):
            buff = 1
        elif TEMPLATE_FORMATION_3.match(image):
            buff = 3
        else:
            buff = 0

        logger.attr('Map_buff', buff)
        return buff
