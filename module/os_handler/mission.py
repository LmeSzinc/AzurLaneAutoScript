from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map_detection.utils import fit_points
from module.os.globe_detection import GLOBE_MAP_SHAPE
from module.os.globe_zone import Zone, ZoneManager
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.ui.ui import UI


class MissionAtCurrentZone(Exception):
    pass


class MissionHandler(UI, MapEventHandler, ZoneManager):
    _os_mission_submitted = False

    def get_mission_zone(self):
        """
        Returns:
            Zone:
        """
        area = (341, 72, 1217, 648)
        # Points of the yellow `!`
        image = color_similarity_2d(self.image_area(area), color=(255, 207, 66))
        points = np.array(np.where(image > 235)).T[:, ::-1]
        if not len(points):
            logger.warning('Unable to find mission on OS mission map')

        point = fit_points(points, mod=(1000, 1000), encourage=5) + (0, 11)
        # Location of zone.
        # (2570, 1694) is the shape of os_globe_map.png
        point *= np.array(GLOBE_MAP_SHAPE) / np.subtract(area[2:], area[:2])

        zone = self.camera_to_zone(tuple(point))
        return zone

    def os_mission_enter(self, skip_first_screenshot=True):
        self.ui_click(MISSION_ENTER, check_button=MISSION_CHECK, offset=(200, 5),
                      skip_first_screenshot=skip_first_screenshot)

    def os_mission_quit(self, skip_first_screenshot=True):
        self.ui_click(MISSION_QUIT, check_button=self.is_in_map, offset=(200, 5),
                      skip_first_screenshot=skip_first_screenshot)

    def os_mission_submit(self, skip_first_screenshot=True):
        """
        Submit items and finish missions.

        Pages:
            in: MISSION_CHECK
            out: MISSION_CHECK
        """
        confirm_timer = Timer(2, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(MISSION_CHECK, offset=(20, 20)) and not self.appear(MISSION_FINISH, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            if self.appear_then_click(MISSION_FINISH, offset=(20, 20), interval=1):
                continue
            if self.handle_popup_confirm('MISSION_FINISH'):
                continue
            if self.handle_map_get_items():
                continue

    def os_get_next_mission(self):
        """
        Returns:
            Zone: Zone instance of next daily mission. Return None if no more missions.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        def handle_mission_at_current_zone():
            if self.info_bar_count():
                raise MissionAtCurrentZone

        self.os_mission_enter()
        if not self._os_mission_submitted:
            self.os_mission_submit()
            self._os_mission_submitted = True

        if self.appear(MISSION_CHECKOUT, offset=(20, 20)):
            try:
                self.ui_click(MISSION_CHECKOUT, check_button=MISSION_MAP_CHECK,
                              additional=handle_mission_at_current_zone, skip_first_screenshot=True)
            except MissionAtCurrentZone:
                logger.info('Mission at current zone')
                self.os_mission_quit()
                return self.zone

            self.device.sleep(0.5)
            self.device.screenshot()
            zone = self.get_mission_zone()
            if zone.zone_id == 154:
                # Reconfirm if zone is [154|NA海域中心|NA OCEAN CENTRAL SECTOR|NA海域中心]
                self.device.sleep(1)
                self.device.screenshot()
                zone = self.get_mission_zone()
            self.ui_click(MISSION_CHECKOUT, appear_button=MISSION_MAP_CHECK, check_button=MISSION_CHECK,
                          skip_first_screenshot=True)
            logger.info(f'OS mission in {zone}')
        else:
            zone = None
            logger.info('No more OS mission')

        self.os_mission_quit()
        return zone
