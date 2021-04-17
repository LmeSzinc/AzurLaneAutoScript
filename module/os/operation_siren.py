import numpy as np

from module.exception import ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
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
        elif self.is_in_globe():
            self.os_globe_goto_map()
            # Zone header has an animation to show.
            self.device.sleep(0.3)
            self.device.screenshot()
        else:
            if self.ui_page_appear(page_os):
                self.ui_goto_main()
            self.ui_ensure(page_os)
            # Zone header has an animation to show.
            self.device.sleep(0.3)
            self.device.screenshot()

        self.get_current_zone()
        # self.map_init()

    def globe_goto(self, zone, types=('SAFE', 'DANGEROUS')):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, LOGGER, STRONGHOLD.
                Try the the first selection in type list, if not available, try the next one.

        Pages:
            in: IN_MAP or IN_GLOBE
            out: IN_MAP
        """
        zone = self.name_to_zone(zone)
        logger.hr(f'Globe goto: {zone}')
        # IN_MAP
        if self.is_in_map():
            self.os_map_goto_globe()
        # IN_GLOBE
        if not self.is_in_globe():
            logger.warning('Trying to move in globe, but not in os globe map')
            raise ScriptError('Trying to move in globe, but not in os globe map')
        self.ensure_no_zone_pinned()
        self.globe_update()
        self.globe_focus_to(zone)
        self.zone_type_select(types=types)
        self.globe_enter(zone)
        # IN_MAP
        if hasattr(self, 'zone'):
            del self.zone
        self.get_current_zone()
        # self.map_init()

    def fleet_repair(self, revert=True):
        """
        Repair fleets in nearest port.

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet repair')
        prev = self.zone
        if self.zone.is_azur_port:
            logger.info('Already in azur port')
        else:
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

        self.port_goto2()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)

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
            self.port_goto2()
            self.port_enter()
            if mission and mission_success:
                mission_success &= self.port_mission_accept()
            if supply and supply_success:
                supply_success &= self.port_supply_buy()
            self.port_quit()
            if not ((mission and mission_success) or (supply and supply_success)):
                return False

        return True

    def os_finish_daily_mission(self):
        """
        Finish all daily mission in Operation Siren.
        Suggest to run os_port_daily to accept missions first.
        """
        logger.hr('OS finish daily mission', level=1)
        while 1:
            zone = self.os_get_next_mission()
            if zone is None:
                break

            self.globe_goto(zone)
            self.run_auto_search()

    def os_meowfficer_farming(self, hazard_level=5):
        """
        Args:
            hazard_level (int): 1 to 6. Recommend 3 or 5 for higher meowfficer searching point per action points.
        """
        logger.hr(f'OS meowfficer farming, hazard_level={hazard_level}', level=1)
        while 1:
            # (1252, 1012) is the coordinate of zone 134 (the center zone) in os_globe_map.png
            zones = self.zone_select(hazard_level=hazard_level) \
                .delete(SelectedGrids([self.zone])) \
                .sort_by_clock_degree(center=(1252, 1012), start=self.zone.location)

            self.globe_goto(zones[0])
            self.run_auto_search()
