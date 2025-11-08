from module.base.timer import Timer
from module.base.utils import *
from module.exception import GameStuckError
from module.logger import logger
from module.os.assets import *
from module.os.globe_detection import GLOBE_MAP_SHAPE, GlobeDetection
from module.os.globe_operation import GlobeOperation
from module.os.globe_zone import Zone, ZoneManager
from module.os_ash.assets import ASH_QUIT, ASH_SHOWDOWN
from module.os_handler.assets import ACTION_POINT_CANCEL, ACTION_POINT_USE, AUTO_SEARCH_REWARD


class GlobeCamera(GlobeOperation, ZoneManager):
    globe: GlobeDetection
    globe_camera: tuple

    def _globe_init(self):
        """
        Call this method before doing anything.
        """
        if not hasattr(self, 'globe'):
            self.globe = GlobeDetection(self.config)
            self.globe.load_globe_map()

    def globe_update(self):
        # Handle random black screenshots
        timeout = Timer(5, count=10).start()
        while 1:
            if timeout.reached():
                raise GameStuckError

            self.device.screenshot()

            # End
            if self.is_in_globe():
                break

            # A copy of os_map_goto_globe()
            # May accidentally enter map
            if self.appear_then_click(MAP_GOTO_GLOBE, offset=(200, 5), interval=3):
                # Just to initialize interval timer of MAP_GOTO_GLOBE_FOG
                self.appear(MAP_GOTO_GLOBE_FOG, interval=3)
                timeout.reset()
                continue
            # Encountered only in strongholds; AL will not prevent
            # zone exit even with left over exploration rewards in map
            if self.appear_then_click(MAP_GOTO_GLOBE_FOG, interval=3):
                self.interval_reset(MAP_GOTO_GLOBE)
                timeout.reset()
                continue
            if self.handle_map_event():
                timeout.reset()
                continue
            # Popup: AUTO_SEARCH_REWARD appears slowly
            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50), interval=3):
                timeout.reset()
                continue
            # Popup: Leaving current zone will terminate meowfficer searching.
            # Popup: Leaving current zone will retreat submarines
            # Searching reward will be shown after entering another zone.
            if self.handle_popup_confirm('GOTO_GLOBE'):
                timeout.reset()
                continue
            # Don't know why but AL just entered META page
            if self.appear(ASH_SHOWDOWN, offset=(20, 20), interval=3):
                self.device.click(ASH_QUIT)
                timeout.reset()
                continue
            # Action point popup
            if self.appear(ACTION_POINT_USE, offset=(20, 20), interval=3):
                self.device.click(ACTION_POINT_CANCEL)
                timeout.reset()
                continue

            logger.warning('Trying to do globe_update(), but not in os globe map')
            continue

        self._globe_init()
        self.globe.load(self.device.image)
        self.globe_camera = self.globe.center_loca
        center = self.camera_to_zone(self.globe.center_loca)
        logger.attr('Globe_center', center.zone_id)

    def globe_swipe(self, vector, box=(20, 220, 980, 620)):
        """
        Args:
            vector (tuple, np.ndarray): float
            box (tuple): Area that allows to swipe.

        Returns:
            bool: if camera moved.
        """
        name = 'GLOBE_SWIPE_' + '_'.join([str(int(round(x))) for x in vector])
        if np.linalg.norm(vector) <= 25:
            logger.warning(f'Globe swipe to short: {vector}')
            vector = np.sign(vector) * 25

        if self.config.DEVICE_CONTROL_METHOD == 'minitouch':
            distance = self.config.MAP_SWIPE_MULTIPLY_MINITOUCH
        elif self.config.DEVICE_CONTROL_METHOD == 'MaaTouch':
            distance = self.config.MAP_SWIPE_MULTIPLY_MAATOUCH
        else:
            distance = self.config.MAP_SWIPE_MULTIPLY
        vector = np.array(distance) * vector

        vector = -vector
        self.device.swipe_vector(vector, name=name, box=box)
        self.device.sleep(0.3)

        self.globe_update()

    def globe_wait_until_stable(self):
        prev = self.globe_camera
        interval = Timer(1)
        confirm = Timer(0.5, count=1).start()
        for n in range(10):
            if not interval.reached():
                interval.wait()
            interval.reset()

            self.globe_update()

            # End
            if np.linalg.norm(np.subtract(self.globe_camera, prev)) < 10:
                if confirm.reached():
                    logger.info('Globe map stabled')
                    break
            else:
                confirm.reset()

            if self.handle_zone_pinned():
                continue

            prev = self.globe_camera

    def globe2screen(self, points):
        points = np.array(points) - self.globe_camera + self.globe.homo_center
        return self.globe.globe2screen(points).round()

    def screen2globe(self, points):
        points = self.globe.screen2globe(points).round()
        return points - self.globe.homo_center + self.globe_camera

    def zone_to_button(self, zone):
        """
        Args:
            zone (Zone):

        Returns:
            Button:
        """
        pinned = self.globe2screen([zone.location])[0]
        # pinned is the bottom left corner of where its actually pinned.
        area = area_offset((0, -10, 16, 0), offset=pinned)
        button = Button(area=area, color=(), button=area, name=f'ZONE_{zone.zone_id}')
        return button

    def globe_in_sight(self, zone, swipe_limit=(620, 340), sight=(20, 220, 980, 620)):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.
            swipe_limit (tuple):
            sight (tuple):
        """
        zone = self.name_to_zone(zone)
        # logger.info(f'Globe in_sight: {zone}')

        while 1:
            if point_in_area(self.globe2screen([zone.location])[0], area=sight):
                break

            area = (400, 200, GLOBE_MAP_SHAPE[0] - 400, GLOBE_MAP_SHAPE[1] - 250)
            loca = point_limit(zone.location, area=area)
            vector = np.array(loca) - self.globe_camera
            vector = vector / self.config.OS_GLOBE_SWIPE_MULTIPLY
            swipe = tuple(np.min([np.abs(vector), swipe_limit], axis=0) * np.sign(vector))
            self.globe_swipe(swipe)

    def get_globe_pinned_zone(self):
        """
        Returns:
            Zone:
        """
        location = self.screen2globe([ZONE_PINNED.button[:2]])[0] + (0, 5)
        return self.camera_to_zone(location)

    def globe_wait_until_zone_pinned(self, zone, skip_first_screenshot=True):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.
            skip_first_screenshot:

        Returns:
            bool: True if zone pinned, False if timeout
        """
        zone = self.name_to_zone(zone)
        timeout = Timer(5, count=5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
                self.globe_update()

            if self.is_zone_pinned():
                if self.get_globe_pinned_zone() == zone:
                    logger.attr('Globe_pinned', zone)
                    return True
            if timeout.reached():
                logger.warning('Wait until zone pinned timeout')
                return False

    def globe_focus_to(self, zone):
        """
        Focus to a zone in globe view
        self.globe_update() needs to be called first

        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.

        Pages:
            in: IN_GLOBE
            out: IN_GLOBE, zone selected, ZONE_ENTRANCE
        """
        zone = self.name_to_zone(zone)
        logger.info(f'Globe focus_to: {zone.zone_id}')

        while 1:
            if self.handle_zone_pinned():
                self.globe_update()
                continue

            # Insight
            self.globe_in_sight(zone)
            # Click zone
            button = self.zone_to_button(zone)
            self.device.click(button)
            # Wait until zone pinned
            if self.globe_wait_until_zone_pinned(zone):
                break

    def _globe_predict_stronghold(self, zone):
        """
        Predict if this zone has siren stronghold.
        `self.globe_in_sight(zone)` must be called before calling this method.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.

        Returns:
            bool:
        """
        zone = self.name_to_zone(zone)
        # The center of red whirlpool, on 2D map.
        location = zone.location + (-9.5, -12.5)
        # Area around the center, on 2D map.
        location = [location - (4, 4), location + (4, 4)]
        # Area around the center, on screen.
        screen = self.globe2screen(location).flatten().round()
        screen = np.round(screen).astype(int).tolist()
        # Average color of whirlpool center
        center = self.image_crop(screen, copy=False)
        center = np.array([[cv2.mean(center), ], ]).astype(np.uint8)
        h, s, v = rgb2hsv(center)[0][0]
        # hsv usually to be (338, 74.9, 100)
        if 285 < h <= 360 and s > 45 and v > 45:
            return True
        else:
            return False

    def _find_siren_stronghold(self, zones):
        """
        self.globe_update() needs to be called first

        Args:
            zones (SelectGrids): A group of zones to search from.

        Returns:
            zone: Zone that has siren stronghold, or None if not found.

        Pages:
            in: in_globe
            out: in_globe, is_zone_pinned() if found.
        """
        sight = (20, 220, 980, 620)
        while zones:
            prev = self.camera_to_zone(self.globe_camera)
            zone = zones.sort_by_camera_distance(prev.location)[0]
            logger.info(f'Find siren stronghold around {zone}')
            self.globe_in_sight(zone, sight=sight)

            to_check = zones.filter(lambda z: point_in_area(self.globe2screen([z.location])[0], area=sight))
            for zone in to_check:
                if self._globe_predict_stronghold(zone):
                    logger.info(f'Zone {zone.zone_id} is a siren stronghold')
                    self.globe_focus_to(zone)
                    if self.get_zone_pinned_name() == 'STRONGHOLD':
                        logger.info('Confirm it is a siren stronghold')
                        return zone
                    else:
                        logger.warning('Not a siren stronghold, continue searching')
                        self.ensure_no_zone_pinned()
                else:
                    logger.info(f'Zone {zone.zone_id} is not a siren stronghold')

            zones = zones.delete(to_check)

        logger.info('Find siren stronghold finished')
        return None

    def find_siren_stronghold(self):
        """
        Returns:
            zone: Zone that has siren stronghold, or None if not found.

        Pages:
            in: in_globe
            out: in_globe, is_zone_pinned() if found.
        """
        logger.hr(f'Find siren stronghold', level=1)
        region = self.camera_to_zone(self.globe_camera).region
        order = [1, 2, 4, 3]
        if region not in order:
            # Camera may focus on region 5, select the nearest non-region-5 zone
            zones = self.zones.delete(self.zones.select(region=5)) \
                .delete(self.zones.select(is_port=True)) \
                .sort_by_camera_distance(self.globe_camera)
            region = zones[0].region

        index = order.index(region)
        order = order * 2
        order = order[index:index + 4]
        for region in order:
            logger.hr(f'Find siren stronghold in region {region}', level=2)
            zones = self.zones.select(region=region, is_port=False)
            result = self._find_siren_stronghold(zones)
            if result is not None:
                return result

        logger.info('No more siren stronghold')
        return None
