from datetime import timedelta

from module.base.timer import Timer
from module.base.utils import *
from module.config.utils import get_os_next_reset, DEFAULT_TIME
from module.logger import logger
from module.map_detection.utils import fit_points
from module.os.assets import GLOBE_GOTO_MAP
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
        image = color_similarity_2d(self.image_crop(area, copy=False), color=(255, 207, 66))
        points = np.array(np.where(image > 235)).T[:, ::-1]
        if not len(points):
            logger.warning('Unable to find mission on OS mission map')

        point = fit_points(points, mod=(1000, 1000), encourage=5) + (0, 11)
        # Location of zone.
        # (2570, 1694) is the shape of os_globe_map.png
        point *= np.array(GLOBE_MAP_SHAPE) / np.subtract(area[2:], area[:2])

        zone = self.camera_to_zone(tuple(point))
        return zone

    def is_in_os_mission(self):
        return self.appear(MISSION_CHECK, offset=(20, 20))

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

            # End
            if self.is_in_os_mission() \
                    and not self.appear(MISSION_FINISH, offset=(20, 20)) \
                    and not self.match_template_color(MISSION_CHECKOUT, offset=(20, 20)):
                # No mission found, wait to confirm. Missions might not be loaded so fast.
                if confirm_timer.reached():
                    logger.info('No OS mission found.')
                    break
            elif self.is_in_os_mission() \
                    and self.match_template_color(MISSION_CHECKOUT, offset=(20, 20)):
                # Found one mission.
                logger.info('Found at least one OS missions.')
                break
            else:
                confirm_timer.reset()

            # Click
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
            if self.appear_then_click(GLOBE_GOTO_MAP, offset=(20, 20), interval=2):
                # Accidentally entered globe
                confirm_timer.reset()
                continue

    def os_mission_quit(self, skip_first_screenshot=True):
        logger.info('OS mission quit')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            # sometimes you have os mission popup without black-blurred background
            # MISSION_QUIT and is_in_map appears
            if not self.appear(MISSION_QUIT, offset=(20, 20)):
                if self.is_in_map():
                    break
            # Click
            if self.appear_then_click(MISSION_QUIT, offset=(20, 20), interval=3):
                continue

    def os_get_next_mission(self):
        """
        Another method to get os mission. The old one is outdated.
        After clicking MISSION_CHECKOUT, AL switch to target zone directly instead of showing a meaningless map.
        If already at target zone, show info bar and close mission list.

        Returns:
            str: pinned_at_mission_zone, already_at_mission_zone, pinned_at_archive_zone,
                or False if no more mission.
        """
        self.os_mission_enter()

        checkout_offset = (20, 20)
        if self.appear(MISSION_MONTHLY_BOSS, offset=(20, 20)):
            # If monthly BOSS hasn't been killed, there is always a task.
            logger.info('Monthly BOSS mission found, checking missions bellow it')
            checkout_offset = (-20, 100, 20, 150)

        if not self.match_template_color(MISSION_CHECKOUT, offset=checkout_offset):
            # If not having enough items to claim a mission,
            # there will still be MISSION_CHECKOUT, but button is transparent.
            # So here needs to use both template matching and color detection.
            logger.info('No more OS missions')
            self.os_mission_quit()
            return False

        if self.is_in_opsi_explore():
            logger.info('OpsiExplore is under scheduling, accept missions and receive rewards only')
            self.os_mission_quit()
            return False

        logger.info('Checkout os mission')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_zone_pinned():
                if self.get_zone_pinned_name() == 'ARCHIVE':
                    logger.info('Pinned at archive zone')
                    self.globe_enter(zone=self.name_to_zone(72))
                    return 'pinned_at_archive_zone'
                else:
                    logger.info('Pinned at mission zone')
                    self.globe_enter(zone=self.name_to_zone(72))
                    return 'pinned_at_mission_zone'
            if self.is_in_map() and self.info_bar_count():
                logger.info('Already at mission zone')
                return 'already_at_mission_zone'

            if self.appear_then_click(MISSION_CHECKOUT, offset=checkout_offset, interval=2):
                continue
            if self.handle_popup_confirm('OS_MISSION_CHECKOUT'):
                # Popup: Submarine will retreat after exiting current zone.
                continue

    def os_mission_overview_accept(self):
        """
        Accept all missions in mission overview.

        Returns:
            bool: True if all missions accepted or no mission found.
                  False if unable to accept more missions.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        logger.hr('OS mission overview accept', level=1)
        # is_in_map
        self.os_map_goto_globe(unpin=False)
        # is_in_globe
        self.ui_click(MISSION_OVERVIEW_ENTER, check_button=MISSION_OVERVIEW_CHECK,
                      offset=(200, 20), retry_wait=3, skip_first_screenshot=True)

        # MISSION_OVERVIEW_CHECK
        confirm_timer = Timer(1, count=3).start()
        skip_first_screenshot = True
        success = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.info_bar_count():
                logger.info('Unable to accept missions, because reached the maximum number of missions')
                success = False
                break
            if self.appear_then_click(MISSION_OVERVIEW_ACCEPT, offset=(20, 20), interval=0.2):
                confirm_timer.reset()
                continue
            else:
                # End
                if confirm_timer.reached():
                    success = True
                    break
            if self.appear_then_click(MISSION_OVERVIEW_ACCEPT_SINGLE, offset=(20, 20), interval=0.2):
                confirm_timer.reset()
                continue

        # is_in_globe
        self.ui_back(appear_button=MISSION_OVERVIEW_CHECK, check_button=self.is_in_globe,
                     skip_first_screenshot=True)
        # is_in_map
        self.os_globe_goto_map()
        return success

    def is_in_opsi_explore(self):
        """
        Returns:
            bool: If task OpsiExplore is under scheduling.
        """
        enable = self.config.is_task_enabled('OpsiExplore')
        next_run = self.config.cross_get(keys='OpsiExplore.Scheduler.NextRun', default=DEFAULT_TIME)
        next_reset = get_os_next_reset()
        logger.attr('OpsiNextReset', next_reset)
        logger.attr('OpsiExplore', (enable, next_run))
        # -12 hours to handle DST
        # `next_run` might be calculated before DST but it's DST now
        # 2023-03-14 11:15:28.423 | INFO | [OpsiNextReset] 2023-04-01 03:00:00
        # 2023-03-14 11:15:28.425 | INFO | [OpsiExplore] (True, datetime.datetime(2023, 4, 1, 2, 0))
        # 2023-03-14 11:15:28.426 | INFO | OpsiExplore is still running, accept missions only...
        if enable and next_run < next_reset - timedelta(hours=12):
            logger.info('OpsiExplore is still running, accept missions only. '
                        'Missions will be finished when OpsiExplore visits every zones, '
                        'no need to worry they are left behind.')
            return True
        else:
            logger.info('Not in OpsiExplore, able to do OpsiDaily')
            return False
