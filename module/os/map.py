from module.logger import logger
from module.map.map import Map
from module.map.map_grids import SelectedGrids
from module.os.fleet import OSFleet
from module.os.map_base import OSCampaignMap


class OSMap(OSFleet, Map):
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
            self.goto(grids[0])
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
        self.device.send_notification('AzurLaneAutoScript', 'Operation Siren Full clear end')

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
        map_ = OSCampaignMap()
        map_.shape = self.get_map_shape()
        self.map_init(map_)
        self.full_clear()
