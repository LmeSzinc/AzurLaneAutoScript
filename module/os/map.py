from module.exception import ScriptError
from module.logger import logger
from module.map.map import Map
from module.map.map_grids import SelectedGrids
from module.os.assets import *
from module.os.fleet import OSFleet
from module.os.globe_camera import GlobeCamera


class OSMap(OSFleet, Map, GlobeCamera):
    def clear_all_objects(self, grid=None):
        """Method to clear all objects around specific grid.

        Args:
            grid (GridInfo):

        Returns:
            int: Cleared count
        """
        if grid is not None:
            logger.hr(f'clear_all_objects: {grid}', level=2)
        for count in range(0, 10):
            grids = self.map.select(is_resource=True) \
                .add(self.map.select(is_enemy=True)) \
                .add(self.map.select(is_meowfficer=True)) \
                .add(self.map.select(is_exclamation=True)).delete(self.map.select(is_interactive_only=True))
            if grid is not None:
                grids = SelectedGrids([g for g in grids if self.grid_is_in_sight(g, camera=grid)])

            if not grids:
                logger.info(f'OS object cleared: {count}')
                return count

            grids = grids.sort_by_camera_distance(self.fleet_current)
            logger.hr('Clear all resource')
            logger.info(f'Grids: {grids}')
            logger.info(f'Clear object {grids[0]}')
            self.goto(grids[0], expected=self._get_goto_expected(grids[0]))
            self.handle_meowfficer_searching()

        logger.warning('Too many objects to clear, stopped')
        return 10

    def handle_meowfficer_searching(self):
        """
        Move back and forth to handle meowfficer farming

        Returns:
            bool: If handled
        """
        if not self.is_meowfficer_searching():
            return False

        logger.hr('Meowfficer searching')
        back = self.fleet_current
        sea = self.get_sea_grids()[:4]
        logger.info(f'Sea grids: {sea}')
        forth = sea[0]

        # Meowfficer searching finishes in 8 steps at max
        # If found good items in current step, progress bar doesn't increase
        for grid in [forth, back] * 7:
            self.goto(grid)
            if self.is_meowfficer_searching():
                percent = self.get_meowfficer_searching_percentage()
                logger.attr('Meowfficer_searching', f'{int(percent * 100)}%')
            else:
                logger.hr('Meowfficer searching end')
                return True

        logger.warning('Too many meowfficer searching steps')
        return True

    def clear_remain_grids(self):
        logger.hr('Clear remain grids', level=2)
        self.clear_all_objects()

    def full_clear(self):
        """
        Clear the whole map.
        """
        logger.info(f'Full scan start')
        self.map.reset_fleet()

        queue = self.map.camera_data

        while len(queue) > 0:
            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0])
            self.focus_to_grid_center(0.25)
            self.view.predict()
            self.map.update(grids=self.view, camera=self.camera)
            self.map.show()

            self.clear_all_objects(queue[0])
            queue = queue[1:]

        self.clear_remain_grids()
        self.clear_akashi()
        logger.info('Full clear end')
        self.device.send_notification('Operation Siren', 'Full clear end')

    def clear_akashi(self):
        grids = self.map.select(is_akashi=True)
        if grids:
            logger.info(f'Found Akashi in {grids}')
        else:
            logger.info('No Akashi in this map')
            return False

        return True

    def run(self):
        self.device.screenshot()
        self.handle_siren_platform()
        self.map_init()
        self.full_clear()

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
        self.globe_update()
        self.globe_focus_to(zone)
        self.zone_type_select(types=types)
        self.ui_click(ZONE_ENTRANCE, appear_button=self.is_zone_pinned, check_button=self.is_in_map,
                      skip_first_screenshot=True, additional=self.handle_map_event)
        # IN_MAP
        if hasattr(self, 'zone'):
            del self.zone
        # self.map_init()

    def fleet_repair(self, revert=True):
        """
        Repair fleets in nearest port.

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet repair')
        prev = self.zone
        if self.zone_is_azur_lane_port(self.zone):
            logger.info('Already in azur lane port')
        else:
            self.globe_goto(self.zone_nearest_azur_lane_port(self.zone))
            self.map_init()

        self.port_goto()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)
