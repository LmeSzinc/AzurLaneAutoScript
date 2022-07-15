import copy

import numpy as np

from module.base.timer import Timer
from module.base.utils import area_offset
from module.combat.assets import GET_ITEMS_1
from module.exception import CampaignEnd, MapDetectionError
from module.handler.assets import AUTO_SEARCH_MENU_CONTINUE, GAME_TIPS
from module.logger import logger
from module.map.map_base import CampaignMap, location2node
from module.map.map_operation import MapOperation
from module.map.utils import location_ensure, random_direction
from module.map_detection.grid import Grid
from module.map_detection.utils import area2corner, trapezoid2area
from module.map_detection.view import View
from module.os.assets import GLOBE_GOTO_MAP
from module.os_handler.assets import AUTO_SEARCH_REWARD


class Camera(MapOperation):
    view: View
    map: CampaignMap
    camera = (0, 0)
    grid_class = Grid
    _prev_view = None
    _prev_swipe = None

    def _map_swipe(self, vector, box=(123, 159, 1175, 628)):
        """
        Args:
            vector (tuple, np.ndarray): float
            box (tuple): Area that allows to swipe.

        Returns:
            bool: if camera moved.
        """
        vector = np.array(vector)
        name = 'MAP_SWIPE_' + '_'.join([str(int(round(x))) for x in vector])
        if np.any(np.abs(vector) > self.config.MAP_SWIPE_DROP):
            # Map grid fit
            if self.config.DEVICE_CONTROL_METHOD == 'minitouch':
                distance = self.view.swipe_base * self.config.MAP_SWIPE_MULTIPLY_MINITOUCH
            else:
                distance = self.view.swipe_base * self.config.MAP_SWIPE_MULTIPLY
            # Optimize swipe path
            if self.config.MAP_SWIPE_OPTIMIZE:
                whitelist, blacklist = self.get_swipe_area_opt(vector)
            else:
                whitelist, blacklist = None, None

            vector = distance * vector
            vector = -vector
            self.device.swipe_vector(vector, name=name, box=box, whitelist_area=whitelist, blacklist_area=blacklist)
            self.device.sleep(0.3)
            self.update()
        else:
            # Drop swipe
            # self.update(camera=False)
            pass

    def map_swipe(self, vector):
        """
        Swipe to a grid using relative position.
        Remember to update before calling this.

        Args:
            vector(tuple): int
        Returns:
            bool: if camera moved.
        """
        logger.info('Map swipe: %s' % str(vector))
        self._prev_view = copy.copy(self.view)
        self._prev_swipe = vector
        vector = np.array(vector)
        vector = np.array([0.5, 0.5]) - self.view.center_offset + vector
        self._map_swipe(vector)

    def focus_to_grid_center(self, tolerance=None):
        """
        Re-focus to the center of a grid.

        Args:
            tolerance (float): 0 to 0.5. If None, use MAP_GRID_CENTER_TOLERANCE

        Returns:
            bool: Map swiped.
        """
        if not tolerance:
            tolerance = self.config.MAP_GRID_CENTER_TOLERANCE
        if np.any(np.abs(self.view.center_offset - 0.5) > tolerance):
            logger.info('Re-focus to grid center.')
            self.map_swipe((0, 0))
            return True

        return False

    def _view_init(self):
        if not hasattr(self, 'view'):
            self.view = View(self.config, grid_class=self.grid_class)

    def _update(self, camera=True):
        """Update map image

        Args:
            camera: True to update camera position and perspective data.
        """
        self.device.screenshot()
        if not camera:
            self.view.update(image=self.device.image)
            return True

        self._view_init()
        try:
            if not self.is_in_map() \
                    and not self.is_in_strategy_submarine_move():
                logger.warning('Image to detect is not in_map')
                raise MapDetectionError('Image to detect is not in_map')
            self.view.load(self.device.image)
        except MapDetectionError as e:
            if self.info_bar_count():
                logger.warning('Perspective error caused by info bar')
                self.handle_info_bar()
                return False
            elif self.appear(GET_ITEMS_1):
                logger.warning('Perspective error caused by get_items')
                self.handle_mystery()
                return False
            elif self.handle_story_skip():
                logger.warning('Perspective error caused by story')
                self.ensure_no_story(skip_first_screenshot=False)
                return False
            elif self.is_in_stage():
                logger.warning('Image is in stage')
                raise CampaignEnd('Image is in stage')
            elif self.appear(AUTO_SEARCH_MENU_CONTINUE, offset=self._auto_search_menu_offset):
                logger.warning('Image is in auto search menu')
                self.ensure_auto_search_exit()
                raise CampaignEnd('Image is in auto search menu')
            elif self.appear(GLOBE_GOTO_MAP, offset=(20, 20)):
                logger.warning('Image is in OS globe map')
                self.ui_click(GLOBE_GOTO_MAP, check_button=self.is_in_map, offset=(20, 20),
                              retry_wait=3, skip_first_screenshot=True)
                return False
            elif self.appear(AUTO_SEARCH_REWARD, offset=(50, 50)):
                logger.warning('Perspective error caused by AUTO_SEARCH_REWARD')
                if hasattr(self, 'os_auto_search_quit'):
                    self.os_auto_search_quit()
                    return False
                else:
                    logger.warning('Cannot find method os_auto_search_quit(), use ui_click() instead')
                    self.ui_click(AUTO_SEARCH_REWARD, check_button=self.is_in_map, offset=(50, 50),
                                  retry_wait=3, skip_first_screenshot=True)
                    return False
            elif 'opsi' in self.config.task.command.lower() and self.handle_popup_confirm('OPSI'):
                # Always confirm popups in OpSi, same popups in os_map_goto_globe()
                logger.warning('Perspective error caused by popups')
                return False
            elif not self.is_in_map() \
                    and not self.is_in_strategy_submarine_move():
                if self.appear(GAME_TIPS, offset=(20, 20)):
                    logger.warning('Perspective error caused by game tips')
                    self.device.click(GAME_TIPS)
                    return False
                else:
                    raise e
            elif 'Camera outside map' in str(e):
                string = str(e)
                logger.warning(string)
                x, y = string.split('=')[1].strip('() ').split(',')
                self._map_swipe((-int(x.strip()), -int(y.strip())))
            else:
                raise e

        if self._prev_view is not None and np.linalg.norm(self._prev_swipe) > 0:
            if self.config.MAP_SWIPE_PREDICT:
                swipe = self._prev_view.predict_swipe(
                    self.view,
                    with_current_fleet=self.config.MAP_SWIPE_PREDICT_WITH_CURRENT_FLEET,
                    with_sea_grids=self.config.MAP_SWIPE_PREDICT_WITH_SEA_GRIDS
                )
                if swipe is not None:
                    self._prev_swipe = swipe
            self.camera = tuple(np.add(self.camera, self._prev_swipe))
            self._prev_view = None
            self._prev_swipe = None
            self.show_camera()

        # Set camera position
        if self.view.left_edge:
            x = 0 + self.view.center_loca[0]
        elif self.view.right_edge:
            x = self.map.shape[0] - self.view.shape[0] + self.view.center_loca[0]
        else:
            x = self.camera[0]
        if self.view.upper_edge:
            y = self.map.shape[1] - self.view.shape[1] + self.view.center_loca[1]
        elif self.view.lower_edge:
            y = 0 + self.view.center_loca[1]
        else:
            y = self.camera[1]

        if self.camera != (x, y):
            logger.attr_align('camera_corrected', f'{location2node(self.camera)} -> {location2node((x, y))}')
        self.camera = (x, y)
        self.show_camera()

        self.predict()
        return True

    def update(self, camera=True, allow_error=False):
        """
        Update map image.
        Wraps the original `update()` method to handle random MapDetectionError
        which is usually caused by network issues and mistaken clicks.

        Args:
            camera: True to update camera position and perspective data.
            allow_error: True to exit when encountered detection error
        """
        confirm_timer = Timer(5, count=10).start()
        while 1:
            try:
                success = self._update(camera=camera)
                if success:
                    break
                else:
                    confirm_timer.reset()
                    continue
            except MapDetectionError:
                if allow_error:
                    break
                elif confirm_timer.reached():
                    raise
                else:
                    continue

    def predict(self):
        self.view.predict()
        self.view.show()

    def show_camera(self):
        logger.attr_align('Camera', location2node(self.camera))

    def ensure_edge_insight(self, reverse=False, preset=None, swipe_limit=(3, 2), skip_first_update=True):
        """
        Swipe to bottom left until two edges insight.
        Edges are used to locate camera.

        Args:
            reverse (bool): Reverse swipes.
            preset (tuple(int)): Set in map swipe manually.
            swipe_limit (tuple): (x, y). Limit swipe in (-x, -y, x, y).
            skip_first_update (bool): Usually to be True. Use False if you are calling ensure_edge_insight manually.

        Returns:
            list[tuple]: Swipe record.
        """
        logger.info(f'Ensure edge in sight.')
        record = []
        x_swipe, y_swipe = np.multiply(swipe_limit, random_direction(self.config.MAP_ENSURE_EDGE_INSIGHT_CORNER))

        while 1:
            if len(record) == 0:
                if not skip_first_update:
                    self.update()
                if preset is not None:
                    self.map_swipe(preset)
                    record.append(preset)

            x = 0 if self.view.left_edge or self.view.right_edge else x_swipe
            y = 0 if self.view.lower_edge or self.view.upper_edge else y_swipe

            if len(record) > 0:
                # Swipe even if two edges insight, this will avoid some embarrassing camera position.
                self.map_swipe((x, y))

            record.append((x, y))

            if x == 0 and y == 0:
                break

        if reverse:
            logger.info('Reverse swipes.')
            for vector in record[::-1]:
                x, y = vector
                if x != 0 or y != 0:
                    self.map_swipe((-x, -y))

        return record

    def focus_to(self, location, swipe_limit=(4, 3)):
        """Focus camera on a grid

        Args:
            location: grid
            swipe_limit(tuple): (x, y). Limit swipe in (-x, -y, x, y).
        """
        location = location_ensure(location)
        logger.info('Focus to: %s' % location2node(location))

        while 1:
            vector = np.array(location) - self.camera
            swipe = tuple(np.min([np.abs(vector), swipe_limit], axis=0) * np.sign(vector))
            self.map_swipe(swipe)

            if np.all(np.abs(vector) <= 0):
                break

    def full_scan(self, queue=None, must_scan=None, battle_count=0, mystery_count=0, siren_count=0, carrier_count=0,
                  mode='normal'):
        """Scan the whole map.

        Args:
            queue (SelectedGrids): Grids to focus on. If none, use map.camera_data
            must_scan (SelectedGrids): Must scan these grids
            battle_count:
            mystery_count:
            siren_count:
            carrier_count:
            mode (str): Scan mode, such as 'normal', 'carrier', 'movable'

        """
        logger.info(f'Full scan start, mode={mode}')
        self.map.reset_fleet()

        queue = queue if queue else self.map.camera_data
        if must_scan:
            queue = queue.add(must_scan)

        while len(queue) > 0:
            if self.map.missing_is_none(battle_count, mystery_count, siren_count, carrier_count, mode):
                if must_scan and queue.count != queue.delete(must_scan).count:
                    logger.info('Continue scanning.')
                    pass
                else:
                    logger.info('All spawn found, Early stopped.')
                    break

            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0])
            self.focus_to_grid_center(0.25)
            success = self.map.update(grids=self.view, camera=self.camera, mode=mode)
            if not success:
                self.ensure_edge_insight(skip_first_update=False)
                continue

            queue = queue[1:]

        self.map.missing_predict(battle_count, mystery_count, siren_count, carrier_count, mode)
        self.map.show()

    def in_sight(self, location, sight=None):
        """Make sure location in camera sight

        Args:
            location:
            sight (tuple): Such as (-3, -1, 3, 2).
        """
        location = location_ensure(location)
        logger.info('In sight: %s' % location2node(location))
        if sight is None:
            sight = self.map.camera_sight

        diff = np.array(location) - self.camera
        if diff[1] > sight[3]:
            y = diff[1] - sight[3]
        elif diff[1] < sight[1]:
            y = diff[1] - sight[1]
        else:
            y = 0
        if diff[0] > sight[2]:
            x = diff[0] - sight[2]
        elif diff[0] < sight[0]:
            x = diff[0] - sight[0]
        else:
            x = 0
        self.focus_to((self.camera[0] + x, self.camera[1] + y))

    def convert_global_to_local(self, location):
        """
        If self.grids doesn't contain this location, focus camera on the location and re-convert it.

        Args:
            location: Grid instance in self.map

        Returns:
            Grid: Grid instance in self.view
        """
        location = location_ensure(location)

        local = np.array(location) - self.camera + self.view.center_loca
        logger.info('Global %s (camera=%s) -> Local %s (center=%s)' % (
            location2node(location),
            location2node(self.camera),
            location2node(local),
            location2node(self.view.center_loca)
        ))
        if local in self.view:
            return self.view[local]
        else:
            logger.warning('Convert global to local Failed.')
            self.focus_to(location)
            local = np.array(location) - self.camera + self.view.center_loca
            return self.view[local]

    def convert_local_to_global(self, location):
        """
        If self.map doesn't contain this location, camera might be wrong, correct camera and re-convert it.

        Args:
            location: Grid instance in self.view

        Returns:
            Grid: Grid instance in self.map
        """
        location = location_ensure(location)

        global_ = np.array(location) + self.camera - self.view.center_loca
        logger.info('Global %s (camera=%s) <- Local %s (center=%s)' % (
            location2node(global_),
            location2node(self.camera),
            location2node(location),
            location2node(self.view.center_loca)
        ))

        if global_ in self.map:
            return self.map[global_]
        else:
            logger.warning('Convert local to global Failed.')
            self.ensure_edge_insight(reverse=True)
            global_ = np.array(location) + self.camera - self.view.center_loca
            return self.map[global_]

    def full_scan_find_boss(self):
        logger.info('Full scan find boss.')
        self.map.reset_fleet()

        queue = self.map.select(may_boss=True)
        while len(queue) > 0:
            queue = queue.sort_by_camera_distance(self.camera)
            self.in_sight(queue[0])
            self.predict()
            queue = queue[1:]

            boss = self.map.select(is_boss=True)
            boss = boss.add(self.map.select(may_boss=True, is_enemy=True))
            if boss:
                logger.info(f'Boss found: {boss}')
                self.map.show()
                return True

        logger.warning('No boss found.')
        return False

    def get_swipe_area_opt(self, map_vector):
        """
        Get the whitelist and the blacklist for `random_rectangle_vector_opted()`.

        Args:
            map_vector:

        Returns:
            list, list: whitelist, blacklist
        """
        map_vector = np.array(map_vector)

        def local_to_area(local_grid, pad=0):
            result = []
            for local in local_grid:
                # Predict the position of grid after swipe.
                # Swipe should ends there, to prevent treating swipe as click.
                area = area_offset((0, 0, 1, 1), offset=-map_vector)
                corner = local.grid2screen(area2corner(area))
                area = trapezoid2area(corner, pad=pad)
                result.append(area)
            return result

        def globe_to_local(globe_grids):
            result = []
            for globe in globe_grids:
                location = tuple(np.array(globe.location) - self.camera + self.view.center_loca)
                if location in self.view:
                    local = self.view[location]
                    result.append(local)
            return result

        whitelist = self.map.select(is_land=True) \
            .add(self.map.select(is_current_fleet=True)) \
            .sort_by_camera_distance(self.camera)
        blacklist = self.view.select(is_enemy=True) \
            .add(self.view.select(is_siren=True)) \
            .add(self.view.select(is_boss=True)) \
            .add(self.view.select(is_mystery=True)) \
            .add(self.view.select(is_fleet=True, is_current_fleet=False))

        # self.view.show()
        whitelist = local_to_area(globe_to_local(whitelist), pad=25)
        blacklist = [grid.outer for grid in blacklist] + local_to_area(blacklist, pad=-5)

        return whitelist, blacklist
