import numpy as np

from module.exception import CampaignEnd
from module.logger import logger
from module.map.map import Map
from module.map.map_grids import SelectedGrids
from module.os.fleet import OSFleet
from module.os.globe_camera import GlobeCamera
from module.ui.assets import OS_CHECK


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

    def clear_akashi2(self):
        """
        Handle Akashi's shop after auto search.
        After auto search, fleet will near akashi.
        This method detect where akashi stands, enter shop, buy items and exit.

        Returns:
            bool: If found and handled.
        """
        if not self.config.ENABLE_OS_AKASHI_SHOP_BUY:
            return False
        if self.zone.is_port:
            logger.info('Current zone is a port, do not have akashi')
            return False

        grid = self.radar.predict_akashi(self.device.image)
        if grid is None:
            logger.info('No akashi on this map')
            return False

        logger.info(f'Found Akashi on {grid}')
        view = self.os_default_view
        grid = view[np.add(grid, view.center_loca)]
        self.handle_akashi_supply_buy(grid)
        return True

    def run(self):
        self.device.screenshot()
        self.handle_siren_platform()
        self.map_init()
        self.full_clear()

    _auto_search_battle_count = 0

    def os_auto_search_daemon(self):
        logger.hr('OS auto search', level=2)
        self._auto_search_battle_count = 0

        while 1:
            self.device.screenshot()

            if self.is_in_map():
                self.device.stuck_record_clear()
            if self.combat_appear():
                self._auto_search_battle_count += 1
                logger.attr('battle_count', self._auto_search_battle_count)
                self.auto_search_combat()
            if self.handle_os_auto_search_map_option():
                continue
            if self.handle_ash_popup():
                continue
            if self.handle_story_skip():
                # Auto search can not handle siren searching device.
                continue

    def run_auto_search(self):
        self.handle_ash_beacon_attack()

        for _ in range(3):
            try:
                self.os_auto_search_daemon()
            except CampaignEnd:
                logger.info('Get OS auto search reward')
                self.wait_until_appear(OS_CHECK, offset=(20, 20))
                logger.info('OS auto search finished')

            if self.handle_ash_beacon_attack():
                continue
            else:
                break

        self.clear_akashi2()
