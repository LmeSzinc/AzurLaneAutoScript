import numpy as np

from module.base.timer import Timer
from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.template.assets import TEMPLATE_FORMATION_1, TEMPLATE_FORMATION_2, TEMPLATE_FORMATION_3
from module.ui.switch import Switch

formation = Switch('Formation', offset=120)
formation.add_status('line_ahead', check_button=FORMATION_1)
formation.add_status('double_line', check_button=FORMATION_2)
formation.add_status('diamond', check_button=FORMATION_3)

submarine_hunt = Switch('Submarine_hunt', offset=120)
submarine_hunt.add_status('on', check_button=SUBMARINE_HUNT_ON)
submarine_hunt.add_status('off', check_button=SUBMARINE_HUNT_OFF)


class SwitchWithHandler(Switch):
    @staticmethod
    def handle_submarine_zone_icon_bug(main):
        """
        When switching the submarine zone, the icon in the strategy don't change.
        If click submarine hunt, submarine zone will show the correct icon.
        So the key to deal with submarine zone icon bug, is to double click submarine_hunt.

        Args:
            main (ModuleBase):
        """
        current = submarine_hunt.get(main=main)
        opposite = 'off' if current == 'on' else 'on'
        submarine_hunt.set(opposite, main=main)
        submarine_hunt.set(current, main=main)

    def set(self, status, main, skip_first_screenshot=True):
        """
        Args:
            status (str):
            main (ModuleBase):
            skip_first_screenshot (bool):

        Returns:
            bool:
        """
        changed = False
        warning_show_timer = Timer(5, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()
            print('scr')

            current = self.get(main=main)
            logger.attr(self.name, current)
            if current == status:
                return changed

            if current == 'unknown':
                if warning_show_timer.reached():
                    logger.warning(f'Unknown {self.name} switch')
                    warning_show_timer.reset()
                continue

            for data in self.status_list:
                if data['status'] == current:
                    main.device.click(data['click_button'])
                    main.device.sleep(data['sleep'])
                    self.handle_submarine_zone_icon_bug(main=main)  # Different from Switch.
                    changed = True


submarine_view = SwitchWithHandler('Submarine_view', offset=120)
submarine_view.add_status('on', check_button=SUBMARINE_VIEW_ON)
submarine_view.add_status('off', check_button=SUBMARINE_VIEW_OFF)


class StrategyHandler(InfoHandler):
    fleet_1_formation_fixed = False
    fleet_2_formation_fixed = False

    def handle_opened_strategy_bar(self):
        if self.appear_then_click(STRATEGY_OPENED, offset=120):
            self.device.sleep(0.5)
            return True

        return False

    def strategy_open(self):
        logger.info('Strategy open')
        while 1:
            if self.appear(IN_MAP, interval=5) and not self.appear(STRATEGY_OPENED, offset=120):
                self.device.click(STRATEGY_OPEN)
                self.device.sleep(0.5)

            if self.appear(STRATEGY_OPENED, offset=120):
                break

            self.device.screenshot()

    def strategy_close(self):
        logger.info('Strategy close')
        while 1:
            if self.appear_then_click(STRATEGY_OPENED, offset=120, interval=5):
                self.device.sleep(0.5)

            if not self.appear(STRATEGY_OPENED, offset=120):
                break

            self.device.screenshot()

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
        # Disable this until the icon bug of submarine zone is fixed
        # And don't enable MAP_HAS_DYNAMIC_RED_BORDER when using submarine
        # Submarine view check is back again, see SwitchWithHandler.
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
        if self.__getattribute__(f'fleet_{index}_formation_fixed'):
            return False
        expected_formation = self.config.__getattribute__(f'Fleet_Fleet{index}Formation')
        if self._strategy_get_from_map_buff() == expected_formation and not self.config.Submarine_Fleet:
            logger.info('Skip strategy bar check.')
            self.__setattr__(f'fleet_{index}_formation_fixed', True)
            return False

        self.strategy_set_execute(
            formation_index=expected_formation,
            sub_view=False,
            sub_hunt=bool(self.config.Submarine_Fleet) and self.config.Submarine_Mode == 'hunt_only'
        )
        self.__setattr__(f'fleet_{index}_formation_fixed', True)
        return True

    def _strategy_get_from_map_buff(self):
        """
        Returns:
            int: Formation index.
        """
        image = np.array(self.image_area(MAP_BUFF))
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
