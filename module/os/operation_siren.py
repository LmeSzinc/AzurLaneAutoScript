import numpy as np

from module.logger import logger
from module.os.assets import *
from module.os.map import OSMap
from module.ui.ui import page_os


class OperationSiren(OSMap):
    def os_init(self):
        """
        Call this method before doing any Operation functions.

        Pages:
            in: IN_MAP or IN_GLOBE or page_os or any page
            out: IN_MAP
        """
        logger.hr('OS init')
        self.device.screenshot()
        if self.is_in_map():
            logger.info('Already in os map')
        elif self.ui_page_appear(page_os):
            if self.is_in_globe():
                self.os_globe_goto_map()
                # Zone header has an animation to show.
                self.device.sleep(0.3)
                self.device.screenshot()
        else:
            self.ui_ensure(page_os)
            # Zone header has an animation to show.
            self.device.sleep(0.3)
            self.device.screenshot()

        # self.map_init()

    def os_port_daily(self, mission=True, supply=True):
        """
        Accept all missions and buy all supplies in all ports.
        If reach the maximum number of missions, skip accept missions in next port.
        If not having enough yellow coins or purple coins, skip buying supplies in next port.

        Args:
            mission (bool): If needs to accept missions.
            supply (bool): If needs to buy supplies.

        Returns:
            bool: True if all finished.
        """
        logger.hr('OS port daily', level=1)
        if np.random.uniform() > 0.5:
            # St. Petersburg => Liverpool => Gibraltar => NY City
            ports = [3, 1, 2, 0]
        else:
            # NY City => Gibraltar => Liverpool => St. Petersburg
            ports = [0, 2, 1, 3]

        mission_success = True
        supply_success = True
        for port in ports:
            port = self.name_to_zone(port)
            logger.hr(f'OS port daily in {port}', level=2)
            self.globe_goto(port)
            self.map_init()
            self.port_goto()
            self.port_enter()
            if mission and mission_success:
                mission_success &= self.port_mission_accept()
            if supply and supply_success:
                supply_success &= self.port_supply_buy()
            self.port_quit()
            if not ((mission and mission_success) or (supply and supply_success)):
                return False

        return True
