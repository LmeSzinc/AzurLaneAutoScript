import numpy as np

from module.logger import logger
from module.map.fleet import Fleet
from module.map.map_grids import SelectedGrids
from module.os.camera import OSCamera
from module.os_ash.ash import OSAsh
from module.os_combat.combat import Combat


class OSFleet(OSCamera, Combat, Fleet, OSAsh):
    def _goto(self, location, expected=''):
        super()._goto(location, expected)
        self.update_radar()
        self.map.show()

        if self.handle_ash_beacon_attack():
            # After ash attack, camera refocus to current fleet.
            self.camera = location
            self.update()

    def map_init(self, map_):
        logger.hr('Map init')
        self.fleet_1_location = ()
        self.fleet_2_location = ()
        self.fleet_current_index = 1
        self.battle_count = 0
        self.mystery_count = 0
        self.carrier_count = 0
        self.siren_count = 0
        self.ammo_count = 3
        self.map = map_
        self.map.reset()
        self.handle_map_green_config_cover()
        self.map.poor_map_data = self.config.POOR_MAP_DATA
        self.map.load_map_data(use_loop=self.map_is_clear_mode)
        self.map.load_spawn_data(use_loop=self.map_is_clear_mode)
        self.map.load_mechanism(land_based=self.config.MAP_HAS_LAND_BASED)
        self.map.grid_connection_initial(
            wall=self.config.MAP_HAS_WALL,
            portal=self.config.MAP_HAS_PORTAL,
        )

        # self.handle_strategy(index=1 if not self.fleets_reversed() else 2)
        # self.update()
        # if self.handle_fleet_reverse():
        #     self.handle_strategy(index=1)
        self.hp_reset()
        self.hp_get()
        self.lv_reset()
        self.lv_get()
        self.ensure_edge_insight(preset=self.map.in_map_swipe_preset_data)
        # self.full_scan(must_scan=self.map.camera_data_spawn_point)
        self.find_current_fleet()
        self.find_path_initial()
        # self.map.show_cost()
        # self.round_reset()
        # self.round_battle()

    def find_current_fleet(self):
        self.fleet_1 = self.camera

    @property
    def _walk_sight(self):
        sight = (-4, -1, 3, 2)
        return sight

    _os_map_event_handled = False

    def ambush_color_initial(self):
        self._os_map_event_handled = False

    def handle_ambush(self):
        """
        Treat map events as ambush, to trigger walk retrying
        """
        if self.handle_map_get_items():
            self._os_map_event_handled = True
            return True
        elif self.handle_map_event():
            self.ensure_no_map_event()
            self._os_map_event_handled = True
            return True
        else:
            return False

    def handle_mystery(self, button=None):
        """
        After handle_ambush, if fleet has arrived, treat it as mystery, otherwise just ambush.
        """
        if self._os_map_event_handled and button.predict_fleet() and button.predict_current_fleet():
            return 'get_item'
        else:
            return False

    @staticmethod
    def _get_goto_expected(grid):
        """
        Argument `expected` used in _goto()
        """
        if grid.is_enemy:
            return 'combat'
        elif grid.is_resource or grid.is_meowfficer or grid.is_exclamation:
            return 'mystery'
        else:
            return ''

    def hp_get(self):
        pass

    def hp_withdraw_triggered(self):
        return False

    def lv_get(self, after_battle=False):
        pass

    def get_sea_grids(self):
        """
        Get sea grids on current view

        Returns:
            SelectedGrids:
        """
        sea = []
        for local in self.view:
            if not local.predict_sea() or local.predict_current_fleet():
                continue
            # local = np.array(location) - self.camera + self.view.center_loca
            location = np.array(local.location) + self.camera - self.view.center_loca
            location = tuple(location.tolist())
            if location == self.fleet_current or location not in self.map:
                continue
            sea.append(self.map[location])

        if len(self.fleet_current):
            center = self.fleet_current
        else:
            center = self.camera
        return SelectedGrids(sea).sort_by_camera_distance(center)
