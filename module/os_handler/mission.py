from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map_detection.utils import fit_points
from module.os.globe_detection import GLOBE_MAP_SHAPE
from module.os.globe_operation import GlobeOperation
from module.os.globe_zone import Zone, ZoneManager
from module.os_handler.assets import *


class MissionAtCurrentZone(Exception):
    pass


class MissionHandler(GlobeOperation, ZoneManager):
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
        """
        Enter mission list and claim mission reward.

        Pages:
            in: MISSION_ENTER
            out: MISSION_CHECK
        """
        logger.info('OS mission enter')
        confirm_timer = Timer(2, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MISSION_ENTER, offset=(200, 5), interval=5):
                confirm_timer.reset()
                continue
            if self.appear_then_click(MISSION_FINISH, offset=(20, 20), interval=2):
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('MISSION_FINISH'):
                confirm_timer.reset()
                continue
            if self.handle_map_get_items():
                confirm_timer.reset()
                continue
            if self.handle_info_bar():
                confirm_timer.reset()
                continue

            # End
            if self.appear(MISSION_CHECK, offset=(20, 20)) \
                    and not self.appear(MISSION_FINISH, offset=(20, 20)) \
                    and not (self.appear(MISSION_CHECKOUT, offset=(20, 20))
                             and MISSION_CHECKOUT.match_appear_on(self.device.image)):
                # No mission found, wait to confirm. Missions might not be loaded so fast.
                if confirm_timer.reached():
                    logger.info('No OS mission found.')
                    break
            elif self.appear(MISSION_CHECK, offset=(20, 20)) \
                    and (self.appear(MISSION_CHECKOUT, offset=(20, 20))
                         and MISSION_CHECKOUT.match_appear_on(self.device.image)):
                # Found one mission.
                logger.info('Found at least one OS missions.')
                break
            else:
                confirm_timer.reset()

    def os_mission_quit(self, skip_first_screenshot=True):
        logger.info('OS mission quit')
        self.ui_click(MISSION_QUIT, check_button=self.is_in_map, offset=(200, 5),
                      skip_first_screenshot=skip_first_screenshot)

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

    def os_get_next_mission2(self):
        """
        Another method to get os mission. The old one is outdated.
        After clicking MISSION_CHECKOUT, AL switch to target zone directly instead of showing a meaningless map.
        If already at target zone, show info bar and close mission list.

        Returns:
            bool: If has entered mission zone.
        """
        self.os_mission_enter()

        if not (self.appear(MISSION_CHECKOUT, offset=(20, 20)) and MISSION_CHECKOUT.match_appear_on(self.device.image)):
            # If not having enough items to claim a mission,
            # there will still be MISSION_CHECKOUT, but button is transparent.
            # So here needs to use both template matching and color detection.
            self.os_mission_quit()
            return False

        logger.info('Checkout os mission')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MISSION_CHECKOUT, offset=(20, 20), interval=2):
                continue
            if self.handle_popup_confirm('OS_MISSION_CHECKOUT'):
                # Popup: Submarine will retreat after exiting current zone.
                continue

            # End
            if self.is_zone_pinned():
                logger.info('Pinned at mission zone')
                self.globe_enter(zone=self.name_to_zone(72))
                return True
            if self.is_in_map() and self.info_bar_count():
                logger.info('Already at mission zone')
                return True
