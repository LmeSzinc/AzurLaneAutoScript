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

    def _get_map_outside_button(self):
        """
        Returns:
            Button: Click outside of map.
        """
        if self.view.left_edge:
            edge = self.view.backend.left_edge
            area = (113, 185, edge.get_x(290), 290)
        elif self.view.right_edge:
            edge = self.view.backend.right_edge
            area = (edge.get_x(360), 360, 1280, 560)
        else:
            logger.warning('No left edge or right edge')
            return None

        button = Button(area=area, color=(), button=area, name='MAP_OUTSIDE')
        return button

    def globe_goto(self, zone):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.

        Pages:
            in: IN_MAP
            out: IN_MAP
        """
        # IN_MAP
        self.device.screenshot()
        self.map_init()
        self.ensure_edge_insight()
        button = self._get_map_outside_button()
        self.ui_click(button,
                      appear_button=self.is_in_map, check_button=self.is_zone_pinned, skip_first_screenshot=True)
        # IN_GLOBE
        self.ensure_no_zone_pinned()
        self.globe_update()
        self.globe_focus_to(zone)
        self.ui_click(ZONE_ENTRANCE, appear_button=self.is_zone_pinned, check_button=self.is_in_map,
                      skip_first_screenshot=True, additional=self.handle_map_event)
        # IN_MAP
        pass
