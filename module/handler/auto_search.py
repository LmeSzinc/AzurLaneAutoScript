import numpy as np

from module.base.button import ButtonGrid
from module.base.decorator import Config
from module.handler.assets import *
from module.handler.enemy_searching import EnemySearchingHandler
from module.logger import logger
from module.map.assets import FLEET_PREPARATION_CHECK

AUTO_SEARCH_SETTINGS = [
    AUTO_SEARCH_SET_MOB,
    AUTO_SEARCH_SET_BOSS,
    AUTO_SEARCH_SET_ALL,
    AUTO_SEARCH_SET_STANDBY,
    AUTO_SEARCH_SET_SUB_AUTO,
    AUTO_SEARCH_SET_SUB_STANDBY
]
dic_setting_name_to_index = {
    'fleet1_mob_fleet2_boss': 0,
    'fleet1_boss_fleet2_mob': 1,
    'fleet1_all_fleet2_standby': 2,
    'fleet1_standby_fleet2_all': 3,
    'sub_auto_call': 4,
    'sub_standby': 5,
}
dic_setting_index_to_name = {v: k for k, v in dic_setting_name_to_index.items()}


class AutoSearchHandler(EnemySearchingHandler):
    @Config.when(SERVER='en')
    def _fleet_sidebar(self):
        if FLEET_PREPARATION_CHECK.match(self.device.image, offset=(20, 80)):
            offset = np.subtract(FLEET_PREPARATION_CHECK.button, FLEET_PREPARATION_CHECK._button)[1]
        else:
            offset = 0
        logger.attr('_fleet_sidebar_offset', offset)
        return ButtonGrid(
            origin=(1178, 171 + offset), delta=(0, 53),
            button_shape=(98, 42), grid_shape=(1, 3), name='FLEET_SIDEBAR')

    @Config.when(SERVER=None)
    def _fleet_sidebar(self):
        if FLEET_PREPARATION_CHECK.match(self.device.image, offset=(20, 80)):
            offset = np.subtract(FLEET_PREPARATION_CHECK.button, FLEET_PREPARATION_CHECK._button)[1]
        else:
            offset = 0
        logger.attr('_fleet_sidebar_offset', offset)
        return ButtonGrid(
            origin=(1185, 155 + offset), delta=(0, 111),
            button_shape=(53, 104), grid_shape=(1, 3), name='FLEET_SIDEBAR')

    def _fleet_preparation_sidebar_click(self, index):
        """
        Args:
            index (int):
                1 for formation
                2 for meowfficers
                3 for auto search setting

        Returns:
            bool: If changed.
        """
        if index <= 0 or index > 3:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0
        sidebar = self._fleet_sidebar()

        for idx, button in enumerate(sidebar.buttons):
            if self.image_color_count(button, color=(99, 235, 255), threshold=221, count=50):
                current = idx + 1
                total = idx + 1
                continue
            if self.image_color_count(button, color=(255, 255, 255), threshold=221, count=100):
                total = idx + 1
            else:
                break

        if not current:
            logger.warning('No fleet sidebar active.')
        logger.attr('Fleet_sidebar', f'{current}/{total}')
        if current == index:
            return False

        self.device.click(sidebar[0, index - 1])
        return True

    def fleet_preparation_sidebar_ensure(self, index, skip_first_screenshot=True):
        """
        Args:
            index (int):
                1 for formation
                2 for meowfficers
                3 for auto search setting
            skip_first_screenshot (bool):

            Returns:
                bool: whether sidebar could be ensured
                      at most 3 attempts are made before
                      return False otherwise True
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._fleet_preparation_sidebar_click(index):
                if counter >= 2:
                    logger.warning('Sidebar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.3, 0.5))
                continue
            else:
                return True

    def _auto_search_set_click(self, setting):
        """
        Args:
            setting (str):

        Returns:
            bool: If selected to the correct option.
        """
        active = []

        for index, button in enumerate(AUTO_SEARCH_SETTINGS):
            if self.image_color_count(button.button, color=(156, 255, 82), threshold=221, count=20):
                active.append(index)

        if not active:
            logger.warning('No active auto search setting found')
            return False

        logger.attr('Auto_Search_Setting', ', '.join([dic_setting_index_to_name[index] for index in active]))

        if setting not in dic_setting_name_to_index:
            logger.warning(f'Unknown auto search setting: {setting}')
        target_index = dic_setting_name_to_index[setting]

        if target_index in active:
            logger.info('Selected to the correct auto search setting')
            return True
        else:
            self.device.click(AUTO_SEARCH_SETTINGS[target_index])
            return False

    def auto_search_setting_ensure(self, setting, skip_first_screenshot=True):
        """
        Args:
            setting (str):
                fleet1_mob_fleet2_boss, fleet1_boss_fleet2_mob, fleet1_all_fleet2_standby, fleet1_standby_fleet2_all, sub_auto_call, sub_standby
            skip_first_screenshot (bool):

            Returns:
                bool: whether sidebar could be ensured
                      at most 3 attempts are made before
                      return False otherwise True
        """
        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self._auto_search_set_click(setting):
                return True
            else:
                if counter >= 5:
                    logger.warning('Auto search setting could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.3, 0.5))
                continue

    _auto_search_offset = (5, 5)
    # Move 213px left when MULTIPLE_SORTIE appears
    _auto_search_menu_offset = (250, 30)

    def is_auto_search_running(self):
        """
        Returns:
            bool:
        """
        return self.appear(AUTO_SEARCH_MAP_OPTION_ON, offset=self._auto_search_offset) \
               and self.appear(AUTO_SEARCH_MAP_OPTION_ON)

    def handle_auto_search_map_option(self):
        """
        Ensure auto search option in map is ON

        Returns:
            bool: If clicked
        """
        if self.appear(AUTO_SEARCH_MAP_OPTION_OFF, offset=self._auto_search_offset) \
                and self.appear_then_click(AUTO_SEARCH_MAP_OPTION_OFF, interval=2):
            return True

        return False

    def is_in_auto_search_menu(self):
        """
        Returns:
            bool:
        """
        return self.appear(AUTO_SEARCH_MENU_CONTINUE, offset=self._auto_search_menu_offset)

    def handle_auto_search_continue(self):
        return self.appear_then_click(AUTO_SEARCH_MENU_CONTINUE, offset=self._auto_search_menu_offset, interval=2)

    def handle_auto_search_exit(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool
        """
        if self.appear(AUTO_SEARCH_MENU_EXIT, offset=self._auto_search_menu_offset, interval=2):
            # Poor implementation here
            if drop:
                drop.handle_add(main=self, before=4)
            self.device.click(AUTO_SEARCH_MENU_EXIT)
            self.interval_reset(AUTO_SEARCH_MENU_EXIT)
            return True
        else:
            return False

    def ensure_auto_search_exit(self, skip_first_screenshot=True):
        """
        Page:
            in: is_in_auto_search_menu
            out: page_campaign or page_event or page_sp
        """
        if not self.is_in_auto_search_menu():
            return False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_auto_search_exit():
                continue

            # End
            if self.is_in_stage():
                break

        return True
