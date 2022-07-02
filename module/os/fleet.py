import re

import inflection
import numpy as np

from module.base.button import Button, ButtonGrid
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import point_limit
from module.exception import MapWalkError
from module.logger import logger
from module.map.fleet import Fleet
from module.map.map_grids import SelectedGrids
from module.map.utils import location_ensure
from module.map_detection.utils import area2corner, corner2inner
from module.ocr.ocr import Ocr
from module.os.assets import MAP_GOTO_GLOBE, STRONGHOLD_PERCENTAGE, TEMPLATE_EMPTY_HP, FLEET_EMP_DEBUFF
from module.os.camera import OSCamera
from module.os.map_base import OSCampaignMap
from module.os_ash.ash import OSAsh
from module.os_combat.combat import Combat
from module.os_handler.assets import CLICK_SAFE_AREA, IN_MAP, PORT_ENTER, PORT_SUPPLY_CHECK

FLEET_FILTER = Filter(regex=re.compile('fleet-?(\d)'), attr=('fleet',), preset=('callsubmarine',))


def limit_walk(location, step=3):
    x, y = location
    if abs(x) > 0:
        x = min(abs(x), step - abs(y)) * x // abs(x)
    return x, y


class BossFleet:
    def __init__(self, fleet_index):
        self.fleet_index = fleet_index
        self.fleet = str(fleet_index)
        self.standby_loca = (0, 0)

    def __str__(self):
        return f'Fleet-{self.fleet}'

    __repr__ = __str__


class PercentageOcr(Ocr):
    def __init__(self, *args, **kwargs):
        kwargs['lang'] = 'azur_lane'
        super().__init__(*args, **kwargs)

    def pre_process(self, image):
        image = super().pre_process(image)
        image = np.pad(image, ((2, 2), (0, 0)), mode='constant', constant_values=255)
        return image


class OSFleet(OSCamera, Combat, Fleet, OSAsh):
    def _goto(self, location, expected=''):
        super()._goto(location, expected)
        self.predict_radar()
        self.map.show()

        if self.handle_ash_beacon_attack():
            # After ash attack, camera refocus to current fleet.
            self.camera = location
            self.update()

    def map_data_init(self, map_=None):
        """
        Create new map object, and use the shape of current zone
        """
        map_ = OSCampaignMap()
        map_.shape = self.zone.shape
        super().map_data_init(map_)

    def map_control_init(self):
        """
        Remove non-exist things like strategy, round.
        """
        # self.handle_strategy(index=1 if not self.fleets_reversed() else 2)
        self.update()
        # if self.handle_fleet_reverse():
        #     self.handle_strategy(index=1)
        self.hp_reset()
        self.hp_get()
        self.lv_reset()
        self.lv_get()
        self.ensure_edge_insight(preset=self.map.in_map_swipe_preset_data, swipe_limit=(6, 5))
        # self.full_scan(must_scan=self.map.camera_data_spawn_point)
        # self.find_current_fleet()
        # self.find_path_initial()
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

    def hp_retreat_triggered(self):
        return False

    need_repair = [False, False, False, False, False, False]

    def hp_get(self):
        """
        Calculate current HP, also detects the wrench (Ship died, need to repair)
        """
        super().hp_get()
        ship_icon = self._hp_grid().crop((0, -67, 67, 0))
        need_repair = [TEMPLATE_EMPTY_HP.match(self.image_crop(button)) for button in ship_icon.buttons]
        self.need_repair = need_repair
        logger.attr('Repair icon', need_repair)

        if any(need_repair):
            for index, repair in enumerate(need_repair):
                if repair:
                    self._hp_has_ship[self.fleet_current_index][index] = True
                    self._hp[self.fleet_current_index][index] = 0

            logger.attr('HP', ' '.join(
                [str(int(data * 100)).rjust(3) + '%' if use else '____'
                 for data, use in zip(self.hp, self.hp_has_ship)]))

        return self.hp

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

    def wait_until_camera_stable(self, skip_first_screenshot=True):
        """
        Wait until homo_loca stabled.
        DETECTION_BACKEND must be 'homography'.
        """
        logger.hr('Wait until camera stable')
        record = None
        confirm_timer = Timer(0.6, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self.update_os()
            current = self.view.backend.homo_loca
            logger.attr('homo_loca', current)
            if record is None or (current is not None and np.linalg.norm(np.subtract(current, record)) < 3):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            record = current

        logger.info('Camera stabled')

    def wait_until_walk_stable(self, confirm_timer=None, skip_first_screenshot=False, walk_out_of_step=True, drop=None):
        """
        Wait until homo_loca stabled.
        DETECTION_BACKEND must be 'homography'.

        Args:
            confirm_timer (Timer):
            skip_first_screenshot (bool):
            walk_out_of_step (bool): If catch walk_out_of_step error.
                Default to True, use False in abyssal zones.
            drop (DropImage):

        Returns：
            str: Things that fleet met on its way,
                'event', 'search', 'akashi', 'combat',
                or their combinations like 'event_akashi', 'event_combat',
                or an empty string '' if nothing met.

        Raises:
            MapWalkError: If unable to goto such grid.
        """
        logger.hr('Wait until walk stable')
        record = None
        enemy_searching_appear = False
        self.device.screenshot_interval_set(0.35)
        if confirm_timer is None:
            confirm_timer = Timer(0.8, count=2)
        result = set()

        confirm_timer.reset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Map event
            if self.handle_map_event(drop=drop):
                confirm_timer.reset()
                result.add('event')
                continue
            if self.handle_retirement():
                confirm_timer.reset()
                continue
            if self.handle_walk_out_of_step():
                if walk_out_of_step:
                    raise MapWalkError('walk_out_of_step')
                else:
                    continue

            # Accident click
            if self.is_in_globe():
                self.os_globe_goto_map()
                confirm_timer.reset()
                continue
            if self.is_in_storage():
                self.storage_quit()
                confirm_timer.reset()
                continue
            if self.is_in_os_mission():
                self.os_mission_quit()
                confirm_timer.reset()
                continue
            if self.handle_os_game_tips():
                confirm_timer.reset()
                continue

            # Enemy searching
            if not enemy_searching_appear and self.enemy_searching_appear():
                enemy_searching_appear = True
                confirm_timer.reset()
                continue
            else:
                if enemy_searching_appear:
                    self.handle_enemy_flashing()
                    self.device.sleep(0.3)
                    logger.info('Enemy searching appeared.')
                    enemy_searching_appear = False
                    result.add('search')
                if self.is_in_map():
                    self.enemy_searching_color_initial()

            # Combat
            if self.combat_appear():
                # Use ui_back() for testing, because there are too few abyssal loggers every month.
                # self.ui_back(check_button=self.is_in_map)
                self.combat(expected_end=self.is_in_map, fleet_index=self.fleet_show_index, save_get_items=drop)
                confirm_timer.reset()
                result.add('event')
                continue

            # Akashi shop
            if self.appear(PORT_SUPPLY_CHECK, offset=(20, 20)):
                self.interval_clear(PORT_SUPPLY_CHECK)
                self.handle_akashi_supply_buy(CLICK_SAFE_AREA)
                confirm_timer.reset()
                result.add('akashi')
                continue

            # Arrive
            # Check colors, because screen goes black when something is unlocking.
            if self.is_in_map() and IN_MAP.match_appear_on(self.device.image):
                self.update_os()
                current = self.view.backend.homo_loca
                logger.attr('homo_loca', current)
                if record is None or (current is not None and np.linalg.norm(np.subtract(current, record)) < 3):
                    if confirm_timer.reached():
                        break
                else:
                    confirm_timer.reset()
                record = current
            else:
                confirm_timer.reset()

        result = '_'.join(result)
        logger.info(f'Walk stabled, result: {result}')
        self.device.screenshot_interval_set()
        return result

    def port_goto(self):
        """
        A simple and poor implement to goto port. Searching port on radar.

        In OpSi, camera always focus to fleet when fleet is moving which mess up `self.goto()`.
        In most situation, we use auto search to clear a map in OpSi, and classic methods are deprecated.
        But we still need to move fleet toward port, this method is for this situation.

        Raises:
            MapWalkError: If unable to goto such grid.
                Probably clicking at land, center of port, or fleet itself.
        """
        confirm_timer = Timer(3, count=6).start()
        while 1:
            # Calculate destination
            grid = self.radar.port_predict(self.device.image)
            logger.info(f'Port route at {grid}')
            radar_arrive = np.linalg.norm(grid) == 0
            port_arrive = self.appear(PORT_ENTER, offset=(20, 20))
            if port_arrive:
                logger.info('Arrive port')
                break
            elif not port_arrive and radar_arrive:
                if confirm_timer.reached():
                    logger.warning('Arrive port on radar but port entrance not appear')
                    raise MapWalkError
                else:
                    logger.info('Arrive port on radar but port entrance not appear, confirming')
                    self.device.screenshot()
                    continue
            else:
                confirm_timer.reset()

            # Update local view
            self.update_os()
            self.predict()

            # Click way point
            grid = point_limit(grid, area=(-4, -2, 3, 2))
            grid = self.convert_radar_to_local(grid)
            self.device.click(grid)

            # Wait until arrived
            self.wait_until_walk_stable()

    def fleet_set(self, index=1, skip_first_screenshot=True):
        """
        Args:
            index (int): Target fleet_current_index
            skip_first_screenshot (bool):

        Returns:
            bool: If switched.
        """
        logger.hr(f'Fleet set to {index}')
        if self.fleet_selector.ensure_to_be(index):
            self.wait_until_camera_stable()
            return True
        else:
            return False

    def parse_fleet_filter(self):
        """
        Returns:
            list: List of BossFleet or str. Such as [Fleet-4, 'CallSubmarine', Fleet-2, Fleet-3, Fleet-1].
        """
        FLEET_FILTER.load(self.config.OpsiFleetFilter_Filter)
        fleets = FLEET_FILTER.apply([BossFleet(f) for f in [1, 2, 3, 4]])

        # Set standby location
        standby_list = [(-1, -1), (0, -1), (1, -1)]
        index = 0
        for fleet in fleets:
            if isinstance(fleet, BossFleet) and index < len(standby_list):
                fleet.standby_loca = standby_list[index]
                index += 1

        return fleets

    def question_goto(self, has_fleet_step=False):
        logger.hr('Question goto')
        while 1:
            # Update local view
            # Not screenshots taking, reuse the old one
            self.update_os()
            self.predict()
            self.predict_radar()

            # Calculate destination
            grids = self.radar.select(is_question=True)
            if grids:
                # Click way point
                grid = location_ensure(grids[0])
                grid = point_limit(grid, area=(-4, -2, 3, 2))
                if has_fleet_step:
                    grid = limit_walk(grid)
                grid = self.convert_radar_to_local(grid)
                self.device.click(grid)
            else:
                logger.info('No question mark to goto, stop')
                break

            # Wait until arrived
            # Having new screenshots
            self.wait_until_walk_stable(confirm_timer=Timer(1.5, count=4), walk_out_of_step=False)

    def boss_goto(self, location=(0, 0), has_fleet_step=False, drop=None):
        logger.hr('BOSS goto')
        while 1:
            # Update local view
            # Not screenshots taking, reuse the old one
            self.update_os()
            self.predict()
            self.predict_radar()

            # Calculate destination
            grids = self.radar.select(is_enemy=True)
            if grids:
                # Click way point
                grid = np.add(location_ensure(grids[0]), location)
                grid = point_limit(grid, area=(-4, -2, 3, 2))
                if has_fleet_step:
                    grid = limit_walk(grid)
                if grid == (0, 0):
                    logger.info(f'Arrive destination: boss {location}')
                    break
                grid = self.convert_radar_to_local(grid)
                self.device.click(grid)
            else:
                logger.info('No boss to goto, stop')
                break

            # Wait until arrived
            # Having new screenshots
            self.wait_until_walk_stable(confirm_timer=Timer(1.5, count=4), walk_out_of_step=False, drop=drop)

    def get_boss_leave_button(self):
        for grid in self.view:
            if grid.predict_current_fleet():
                return None

        grids = [grid for grid in self.view if grid.predict_caught_by_siren()]
        if len(grids) == 1:
            center = grids[0]
        elif len(grids) > 1:
            logger.warning(f'Found multiple fleets in boss ({grids}), use the center one')
            center = SelectedGrids(grids).sort_by_camera_distance(self.view.center_loca)[0]
        else:
            logger.warning('No fleet in boss, use camera center instead')
            center = self.view[self.view.center_loca]

        logger.info(f'Fleet in boss: {center}')
        # The left half grid next to the center grid.
        area = corner2inner(center.grid2screen(area2corner((1, 0.25, 1.5, 0.75))))
        button = Button(area=area, color=(), button=area, name='BOSS_LEAVE')
        return button

    def boss_leave(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_map(), or combat_appear()
            out: is_in_map(), fleet not in boss.
        """
        logger.hr('BOSS leave')
        # Update local view
        self.update_os()

        click_timer = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_map():
                self.predict_radar()
                if self.radar.select(is_enemy=True):
                    logger.info('Fleet left boss, boss found')
                    break

            # Re-enter boss accidentally
            if self.combat_appear():
                self.ui_back(check_button=self.is_in_map)

            # Click leave button
            if self.is_in_map() and click_timer.reached():
                button = self.get_boss_leave_button()
                if button is not None:
                    self.device.click(button)
                    click_timer.reset()
                    continue
                else:
                    logger.info('Fleet left boss, current fleet found')
                    break

    def boss_clear(self, has_fleet_step=True):
        """
        All fleets take turns in attacking the boss.

        Args:
            has_fleet_step (bool):

        Returns:
            bool: If success to clear.

        Pages:
            in: Siren logger (abyssal), boss appeared.
            out: If success, dangerous or safe zone.
                If failed, still in abyssal.
        """
        logger.hr(f'BOSS clear', level=1)
        fleets = self.parse_fleet_filter()
        with self.stat.new(
                genre=inflection.underscore(self.config.task.command),
                method=self.config.DropRecord_OpsiRecord
        ) as drop:
            for fleet in fleets:
                logger.hr(f'Turn: {fleet}', level=2)
                if not isinstance(fleet, BossFleet):
                    self.os_order_execute(recon_scan=False, submarine_call=True)
                    continue

                # Attack
                self.fleet_set(fleet.fleet_index)
                self.handle_os_map_fleet_lock(enable=False)
                self.boss_goto(location=(0, 0), has_fleet_step=has_fleet_step, drop=drop)

                # End
                self.predict_radar()
                if self.radar.select(is_question=True):
                    logger.info('BOSS clear')
                    if drop.count:
                        drop.add(self.device.image)
                    self.map_exit()
                    return True

                # Standby
                self.boss_leave()
                if fleet.standby_loca != (0, 0):
                    self.boss_goto(location=fleet.standby_loca, has_fleet_step=has_fleet_step, drop=drop)
                else:
                    if drop.count:
                        drop.add(self.device.image)
                    break

        logger.critical('Unable to clear boss, fleets exhausted')
        return False

    def run_abyssal(self):
        """
        Handle double confirms and attack abyssal (siren logger) boss.

        Returns:
            bool: If success to clear.

        Pages:
            in: Siren logger (abyssal).
            out: If success, in a dangerous or safe zone.
                If failed, still in abyssal.
        """
        self.handle_os_map_fleet_lock(enable=False)

        def is_at_front(grid):
            # Grid location is usually to be (0, -2)
            x, y = grid.location
            return (abs(x) <= abs(y)) and (y < 0)

        while 1:
            self.device.screenshot()
            self.question_goto(has_fleet_step=True)

            if self.radar.select(is_enemy=True).filter(is_at_front):
                logger.info('Found boss at front')
                break
            else:
                logger.info('No boss at front, retry question_goto')
                continue

        result = self.boss_clear(has_fleet_step=True)
        return result

    def get_stronghold_percentage(self):
        """
        Get the clear status in siren stronghold.

        Returns:
            str: Usually in ['100', '80', '60', '40', '20', '0']
        """
        ocr = PercentageOcr(STRONGHOLD_PERCENTAGE, letter=(255, 255, 255), threshold=128, name='STRONGHOLD_PERCENTAGE')
        result = ocr.ocr(self.device.image)
        result = result.rstrip('7Kk')
        for starter in ['100', '80', '60', '40', '20', '0']:
            if result.startswith(starter):
                result = starter
                logger.attr('STRONGHOLD_PERCENTAGE', result)
                return result

        logger.warning(f'Unexpected STRONGHOLD_PERCENTAGE: {result}')
        return result

    def get_second_fleet(self):
        """
        Get a second fleet to unlock fleet mechanism that requires 2 fleets.

        Returns:
            int:
        """
        current = self.fleet_selector.get()
        if current == 1:
            second = 2
        else:
            second = 1
        logger.attr('Second_fleet', second)
        return second

    @staticmethod
    def fleet_walk_limit(outside, step=3):
        if np.linalg.norm(outside) <= 3:
            return outside
        if step == 1:
            grids = np.array([
                (0, -1), (0, 1), (-1, 0), (1, 0),
            ])
        else:
            grids = np.array([
                (0, -3), (0, 3), (-3, 0), (3, 0),
                (2, -2), (2, 2), (-2, 2), (2, 2),
            ])
        degree = np.sum(grids * outside, axis=1) / np.linalg.norm(grids, axis=1) / np.linalg.norm(outside)
        return grids[np.argmax(degree)]

    _nearest_object_click_timer = Timer(2)

    def click_nearest_object(self):
        if not self._nearest_object_click_timer.reached():
            return False
        if not self.appear(MAP_GOTO_GLOBE, offset=(200, 20)):
            return False
        if self.appear(PORT_ENTER, offset=(20, 20)):
            return False

        self.update_os()
        self.view.predict()
        self.radar.predict(self.device.image)
        self.radar.show()
        nearest = self.radar.nearest_object()
        if nearest is None:
            self._nearest_object_click_timer.reset()
            return False

        step = 1 if self.appear(FLEET_EMP_DEBUFF, offset=(50, 20)) else 3
        nearest = self.fleet_walk_limit(nearest.location, step=step)
        try:
            nearest = self.convert_radar_to_local(nearest)
        except KeyError:
            logger.info('Radar grid not on local map')
            self._nearest_object_click_timer.reset()
            return False
        self.device.click(nearest)
        self._nearest_object_click_timer.reset()
