from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.os.assets import *
from module.os.globe_detection import GlobeDetection, GLOBE_MAP_SHAPE
from module.os.globe_operation import GlobeOperation
from module.os.globe_zone import Zone, ZoneManager


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
        self.device.screenshot()

        self._globe_init()
        self.globe.load(self.device.image)
        self.globe_camera = self.globe.center_loca
        center = self.camera_to_zone(self.globe.center_loca)
        logger.attr('Globe_center', center)

    def globe_swipe(self, vector, box=(0, 220, 980, 620)):
        """
        Args:
            vector (tuple, np.ndarray): float
            box (tuple): Area that allows to swipe.

        Returns:
            bool: if camera moved.
        """
        name = 'GLOBE_SWIPE_' + '_'.join([str(int(round(x))) for x in vector])
        if np.any(np.abs(vector) > 25):
            if self.config.DEVICE_CONTROL_METHOD == 'minitouch':
                distance = self.config.MAP_SWIPE_MULTIPLY_MINITOUCH
            else:
                distance = self.config.MAP_SWIPE_MULTIPLY
            vector = np.array(distance) * vector

            vector = -vector
            self.device.swipe(vector, name=name, box=box)
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
        return self.globe.globe2screen(points)

    def screen2globe(self, points):
        points = self.globe.screen2globe(points)
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

    def globe_in_sight(self, zone, swipe_limit=(620, 340), sight=(0, 220, 980, 620)):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.
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
            swipe = tuple(np.min([np.abs(vector), swipe_limit], axis=0) * np.sign(vector))
            self.globe_swipe(swipe)

    def globe_focus_to(self, zone):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.

        Pages:
            in: IN_GLOBE
            out: IN_GLOBE, zone selected, ZONE_ENTRANCE
        """
        zone = self.name_to_zone(zone)
        logger.info(f'Globe focus_to: {zone}')

        interval = Timer(2, count=2)
        while 1:
            if self.handle_zone_pinned():
                self.globe_update()
                continue

            self.globe_in_sight(zone)
            if interval.reached_and_reset():
                self.device.click(self.zone_to_button(zone))
                self.device.sleep(0.3)

            self.globe_update()

            if self.is_zone_pinned():
                location = self.screen2globe([ZONE_PINNED.button[:2]])[0] + (0, 5)
                pinned_zone = self.camera_to_zone(location)
                if pinned_zone == zone:
                    logger.attr('Globe_pinned', pinned_zone)
                    break
