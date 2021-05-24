from module.base.button import *
from module.base.decorator import Config
from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map.fleet import Fleet
from module.map.map_grids import SelectedGrids
from module.map.utils import location_ensure
from module.os.camera import OSCamera
from module.os.map_base import OSCampaignMap
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

    def map_init(self, map_=None):
        map_ = OSCampaignMap()
        map_.shape = self.zone.shape

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
            self.device.sleep(0.3)
            self.device.screenshot()
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

    def _hp_grid(self):
        hp_grid = super()._hp_grid()

        # Location of six HP bar, according to respective server for os
        if self.config.SERVER == 'en':
            hp_grid = ButtonGrid(origin=(35, 205), delta=(0, 100), button_shape=(66, 3), grid_shape=(1, 6))
        elif self.config.SERVER == 'jp':
            pass
        else:
            pass

        return hp_grid

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

    def port_goto(self, init=False):
        """
        Goto the port in current zone.
        Should be called in Azur Lane ports only. Shouldn't be called in Red Axis ports or zones with enemies.

        Args:
            init:

        Returns:
            bool: If executed.
        """
        if init:
            self.device.screenshot()
            self.map_init()

        dic_port = {0: 'C6', 1: 'H8', 2: 'E4', 3: 'H7'}
        list_surround = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (-1, 0), (-1, 1)]

        if self.zone.zone_id not in dic_port:
            logger.warning(f'Current zone do not have a port, zone={self.zone}')
            return False

        port = self.map[location_ensure(dic_port[self.zone.zone_id])]
        grids = self.map.grid_covered(port, location=list_surround).sort_by_camera_distance(self.camera)
        self.goto(grids[0])
        return True

    def port_goto2(self):
        """
        A simple and poor implement to goto port. Searching port on radar.

        In OpSi, camera always focus to fleet when fleet is moving which mess up `self.goto()`.
        In most situation, we use auto search to clear a map in OpSi, and classic methods are deprecated.
        But we still need to move fleet toward port, this method is for this situation.
        """
        view = self.os_default_view

        while 1:
            port = self.radar.port_predict(self.device.image)
            view.load(self.device.image)
            logger.info(f'Port route at {port}')
            if np.linalg.norm(port) == 0:
                logger.info('Arrive port')
                break

            port = point_limit(port, area=(-4, -2, 3, 2))
            port = view[np.add(port, view.center_loca)]
            self.device.click(port)
            prev = (0, 0)
            confirm_timer = Timer(1, count=2).start()
            while 1:
                self.device.screenshot()

                self.radar.port_predict(self.device.image)
                if np.linalg.norm(np.subtract(self.radar.port_loca, prev)) < 1:
                    if confirm_timer.reached():
                        break
                else:
                    confirm_timer.reset()

                prev = self.radar.port_loca
