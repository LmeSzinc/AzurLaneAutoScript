from datetime import datetime

from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.exception import GameBugError
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.template.assets import TEMPLATE_OPERATIONS_RED_DOT

GUILD_OPERATIONS_PROGRESS = DigitCounter(OCR_GUILD_OPERATIONS_PROGRESS, letter=(255, 247, 247), threshold=64)


class GuildOperations(GuildBase):
    def _guild_operations_ensure(self, skip_first_screenshot=True):
        """
        Ensure guild operation is loaded
        After entering guild operation, background loaded first, then dispatch/boss
        """
        logger.attr('Guild master/official', self.config.GuildOperation_SelectNewOperation)
        confirm_timer = Timer(1.5, count=3).start()
        click_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if click_count > 5:
                # Info bar showing `none4302`.
                # Probably because guild operation has been started by another guild officer already.
                # Enter guild page again should fix the issue.
                logger.warning(
                    'Unable to start/join guild operation, '
                    'probably because guild operation has been started by another guild officer already')
                raise GameBugError('Unable to start/join guild operation')

            if self._handle_guild_operations_start():
                confirm_timer.reset()
                continue
            if self.appear(GUILD_OPERATIONS_JOIN, interval=3):
                if self.image_color_count(GUILD_OPERATIONS_MONTHLY_COUNT, color=(255, 93, 90), threshold=221, count=20):
                    logger.info('Unable to join operation, no more monthly attempts left')
                    self.device.click(GUILD_OPERATIONS_CLICK_SAFE_AREA)
                else:
                    current, remain, total = GUILD_OPERATIONS_PROGRESS.ocr(self.device.image)
                    threshold = total * self.config.GuildOperation_JoinThreshold
                    if current <= threshold:
                        logger.info('Joining Operation, current progress less than '
                                    f'threshold ({threshold:.2f})')
                        self.device.click(GUILD_OPERATIONS_JOIN)
                    else:
                        logger.info('Refrain from joining operation, current progress exceeds '
                                    f'threshold ({threshold:.2f})')
                        self.device.click(GUILD_OPERATIONS_CLICK_SAFE_AREA)
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('JOIN_OPERATION'):
                click_count += 1
                confirm_timer.reset()
                continue
            if self.handle_popup_single('FLEET_UPDATED'):
                logger.info('Fleet composition altered, may still be dispatch-able. However '
                            'fellow guild members have updated their support line up. '
                            'Suggestion: Enable Boss Recommend')
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_BOSS_ENTER) or self.appear(GUILD_OPERATIONS_ACTIVE_CHECK, offset=(20, 20)):
                if not self.info_bar_count() and confirm_timer.reached():
                    break

    def _handle_guild_operations_start(self):
        """
        Start a new guild operation.
        Current account must be a guild master or officer.

        Starting the third operation of every month is not recommended. Members can only join 2 operations each month,
        most of them can't participate in the dispatch in the third. This will affect the evaluation of the dispatch
        event, resulting in a reduction in the final reward.

        Returns:
            bool: If clicked.
        """
        if not self.config.GuildOperation_SelectNewOperation:
            return False

        today = datetime.now().day
        limit = self.config.GuildOperation_NewOperationMaxDate
        if today >= limit:
            logger.info(f'No new guild operations because, today\'s date {today} >= limit {limit}')
            return False

        # Hard-coded to select The most rewarding operation Solomon Air-Sea Battle.
        if self.appear_then_click(GUILD_OPERATIONS_SOLOMON, offset=(20, 20), interval=3):
            return True
        # Goto the new operation that just started
        # Example page switches:
        # - GUILD_OPERATIONS_SOLOMON
        # - GUILD_OPERATIONS_NEW
        # - handle_popup_confirm(), confirm to consume guild fund.
        # - GUILD_OPERATIONS_JOIN
        # - GUILD_OPERATIONS_ACTIVE_CHECK
        if self.appear_then_click(GUILD_OPERATIONS_NEW, offset=(20, 20), interval=3):
            return True

        return False

    def _guild_operations_get_mode(self):
        """
        Returns:
            int: Determine which operations menu has loaded
                0 - No ongoing operations, Officers/Elites/Leader must select one to begin
                1 - Operations available, displaying a state diagram/web of operations
                2 - Guild Raid Boss active
                Otherwise None if unable to ensure or determine the menu at all

        Pages:
            in: GUILD_OPERATIONS
            out: GUILD_OPERATIONS
        """
        if self.appear(GUILD_OPERATIONS_INACTIVE_CHECK) and self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info(
                'Mode: Operations Inactive, please contact your Elite/Officer/Leader seniors to select '
                'an operation difficulty')
            return 0
        elif self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info('Mode: Operations Active, may proceed to scan and dispatch fleets')
            return 1
        elif self.appear(GUILD_BOSS_ENTER):
            logger.info('Mode: Guild Raid Boss')
            return 2
        else:
            logger.warning('Operations interface is unrecognized')
            return None

    def _guild_operations_get_entrance(self):
        """
        Get 2 entrance button of guild dispatch
        If operation is on the top, after clicking expand button, operation chain moves downward, and enter button
        appears on the top. So we need to detect two buttons in real time.

        Returns:
            list[Button], list[Button]: Expand button, enter button

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        # Where whole operation mission chain is
        detection_area = (152, 135, 1280, 630)
        # Offset inside to avoid clicking on edge
        pad = 5

        list_expand = []
        list_enter = []
        dots = TEMPLATE_OPERATIONS_RED_DOT.match_multi(self.image_crop(detection_area, copy=False), threshold=5)
        logger.info(f'Active operations found: {len(dots)}')
        for button in dots:
            button = button.move(vector=detection_area[:2])
            expand = button.crop(area=(-257, 14, 12, 51), name='DISPATCH_ENTRANCE_1')
            enter = button.crop(area=(-257, -109, 12, -1), name='DISPATCH_ENTRANCE_2')
            for b in [expand, enter]:
                b.area = area_limit(b.area, detection_area)
                b._button = area_pad(b.area, pad)
            list_expand.append(expand)
            list_enter.append(enter)

        return list_expand, list_enter

    def _guild_operations_dispatch_swipe(self, forward=True, skip_first_screenshot=True):
        """
        Although AL will auto focus to active dispatch, but it's bugged.
        It can't reach the operations behind.
        So this method will swipe behind, and focus to active dispatch.
        Force to use minitouch, because uiautomator2 will need longer swipes.

        Args:
            forward (bool): direction of horizontal swipe
            skip_first_screenshot (bool):

        Returns:
            bool: If found active dispatch.
        """
        # Where whole operation mission chain is
        detection_area = (152, 135, 1280, 630)
        direction_vector = (-600, 0) if forward else (600, 0)

        for _ in range(5):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            entrance_1, entrance_2 = self._guild_operations_get_entrance()
            if len(entrance_1):
                return True

            p1, p2 = random_rectangle_vector(
                direction_vector, box=detection_area, random_range=(-50, -50, 50, 50), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
            # self.device.sleep(0.3)

        logger.warning('Failed to find active operation dispatch')
        return False

    def _guild_operations_dispatch_enter(self, skip_first_screenshot=True):
        """
        Returns:
            bool: If entered

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
                After entering guild operation, game will auto located to active operation.
                It is the main operation on chain that will be located to, side operations will be ignored.
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        timer_1 = Timer(2, count=5)
        timer_2 = Timer(2, count=5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK, offset=(20, 20)):
                entrance_1, entrance_2 = self._guild_operations_get_entrance()
                if not len(entrance_1):
                    return False
                if timer_1.reached():
                    self.device.click(entrance_1[0])
                    timer_1.reset()
                    continue
                if timer_2.reached():
                    for button in entrance_2:
                        # Enter button has a black area around Easy/Normal/Hard on the upper right
                        # If operation not expanded, enter button is a background with Gaussian Blur
                        if self.image_color_count(button, color=(0, 0, 0), threshold=235, count=50):
                            self.device.click(button)
                            timer_1.reset()
                            timer_2.reset()
                            break

            if self.appear_then_click(GUILD_DISPATCH_QUICK, offset=(20, 20), interval=2):
                timer_1.reset()
                timer_2.reset()
                continue

            # End
            if self.appear(GUILD_DISPATCH_RECOMMEND, offset=(20, 20)):
                break

        return True

    def _guild_operations_get_dispatch(self):
        """
        Get the button to switch available dispatch
        In previous version, this function detects the red dot on the switch.
        But the red dot may not shows for unknown reason sometimes, so we detect the switch itself.

        Returns:
            Button: Button to switch available dispatch. None if already reach the most right fleet.

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        # Fleet switch, for 4 situation
        #          | 1 |
        #       | 1 | | 2 |
        #    | 1 | | 2 | | 3 |
        # | 1 | | 2 | | 3 | | 4 |
        #   0  1  2  3  4  5  6   buttons in switch_grid
        switch_grid = ButtonGrid(origin=(573.5, 381), delta=(20.5, 0), button_shape=(11, 24), grid_shape=(7, 1))
        # Color of inactive fleet switch
        color_active = (74, 117, 222)
        # Color of current fleet
        color_inactive = (33, 48, 66)

        text = []
        index = 0
        button = None
        for switch in switch_grid.buttons:
            if self.image_color_count(switch, color=color_inactive, threshold=235, count=30):
                index += 1
                text.append(f'| {index} |')
                button = switch
            elif self.image_color_count(switch, color=color_active, threshold=235, count=30):
                index += 1
                text.append(f'[ {index} ]')
                button = switch

        # log example: | 1 | | 2 | [ 3 ]
        text = ' '.join(text)
        logger.attr('Dispatch_fleet', text)
        if text.endswith(']'):
            logger.info('Already at the most right fleet')
            return None
        else:
            return button

    def _guild_operations_dispatch_switch_fleet(self, skip_first_screenshot=True):
        """
        Switch to the fleet on most right

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            button = self._guild_operations_get_dispatch()
            if button is None:
                break
            elif point_in_area((640, 393), button.area):
                logger.info('Dispatching the first fleet, skip switching')
            else:
                self.device.click(button)
                # Wait for the click animation, which will mess up _guild_operations_get_dispatch()
                self.device.sleep((0.5, 0.6))
                continue

    def _guild_operations_dispatch_execute(self, skip_first_screenshot=True):
        """
        Executes the dispatch sequence

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        dispatched = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_DISPATCH_FLEET_UNFILLED, threshold=20, interval=5):
                # Don't use offset here, because GUILD_DISPATCH_FLEET_UNFILLED only has a difference in colors
                # Use long interval because the game needs a few seconds to choose the ships
                self.device.click(GUILD_DISPATCH_RECOMMEND)
                continue
            if not dispatched and self.appear_then_click(GUILD_DISPATCH_FLEET, threshold=20, interval=5):
                # Don't use offset here, because GUILD_DISPATCH_FLEET only has a difference in colors
                continue
            if self.handle_popup_confirm('GUILD_DISPATCH'):
                dispatched = True
                continue

            # End
            if self.appear(GUILD_DISPATCH_IN_PROGRESS):
                # In first dispatch, it will show GUILD_DISPATCH_IN_PROGRESS
                logger.info('Fleet dispatched, dispatch in progress')
                break
            if dispatched and self.appear(GUILD_DISPATCH_FLEET, threshold=20, interval=0):
                # In the rest of the dispatch, it will show GUILD_DISPATCH_FLEET
                # We can't ensure that fleet has dispatched,
                # because GUILD_DISPATCH_FLEET also shows after clicking recommend before dispatching
                # _guild_operations_dispatch() will retry it if haven't dispatched
                logger.info('Fleet dispatched')
                break

    def _guild_operations_dispatch_exit(self, skip_first_screenshot=True):
        """
        Exit to operation map

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_DISPATCH_RECOMMEND, offset=(20, 20), interval=2):
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue
            if self.appear(GUILD_DISPATCH_QUICK, offset=(20, 20), interval=2):
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue
            if self.appear(GUILD_DISPATCH_IN_PROGRESS, interval=2):
                # No offset here, GUILD_DISPATCH_IN_PROGRESS is a colored button
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue

            # End
            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                break

    def _guild_operations_dispatch(self):
        """
        Run guild dispatch

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
            out: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        logger.hr('Guild dispatch')
        success = False
        for _ in reversed(range(2)):
            if self._guild_operations_dispatch_swipe(forward=_):
                success = True
                break
            if _:
                self.guild_side_navbar_ensure(bottom=2)
                self.guild_side_navbar_ensure(bottom=1)
                self._guild_operations_ensure()
        if not success:
            return False

        for _ in range(5):
            if self._guild_operations_dispatch_enter():
                self._guild_operations_dispatch_switch_fleet()
                self._guild_operations_dispatch_execute()
                self._guild_operations_dispatch_exit()
            else:
                return True

        logger.warning('Too many trials on guild operation dispatch')
        return False

    def _guild_operations_boss_preparation(self, az, skip_first_screenshot=True):
        """
        Execute preparation sequence for guild raid boss

        az is a GuildCombat instance to handle combat various
        interfaces. Independently created to avoid conflicts
        or override methods of parent/child objects

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: IN_BATTLE
        """
        is_loading = False
        dispatch_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_BOSS_ENTER, interval=3):
                continue

            if self.appear(GUILD_DISPATCH_FLEET, threshold=20, interval=3):
                # Button does not appear greyed out even
                # when empty fleet composition
                if dispatch_count < 5:
                    self.device.click(GUILD_DISPATCH_FLEET)
                    dispatch_count += 1
                else:
                    logger.warning('Fleet composition error. Preloaded guild support selection may be '
                                   'preventing dispatch. Suggestion: Enable Boss Recommend')
                    return False
                continue

            if self.config.GuildOperation_BossFleetRecommend:
                if self.info_bar_count() and self.appear_then_click(GUILD_DISPATCH_RECOMMEND_2, interval=3):
                    continue

            # Only print once when detected
            if not is_loading:
                if az.is_combat_loading():
                    self.device.screenshot_interval_set('combat')
                    is_loading = True
                    continue

            if az.handle_combat_automation_confirm():
                continue

            # End
            pause = az.is_combat_executing()
            if pause:
                logger.attr('BattleUI', pause)
                return True

    def _guild_operations_boss_combat(self):
        """
        Execute combat sequence
        If battle could not be prepared, exit

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: GUILD_OPERATIONS_BOSS
        """
        from module.guild.guild_combat import GuildCombat
        az = GuildCombat(self.config, device=self.device)

        if not self._guild_operations_boss_preparation(az):
            return False
        az.combat_execute(auto='combat_auto', submarine='every_combat')
        az.combat_status(expected_end='in_ui')
        logger.info('Guild Raid Boss has been repelled')
        return True

    def _guild_operations_boss_available(self):
        """
        Returns:
            bool:
        """
        appear = self.image_color_count(GUILD_BOSS_AVAILABLE, color=(140, 243, 99), threshold=221, count=10)
        if appear:
            logger.info('Guild boss available')
        else:
            logger.info('Guild boss not available')
        return appear

    def guild_operations(self):
        logger.hr('Guild operations', level=1)
        self.guild_side_navbar_ensure(bottom=1)
        self._guild_operations_ensure()
        # Determine the mode of operations, currently 3 are available
        operations_mode = self._guild_operations_get_mode()

        # Execute actions based on the detected mode
        result = True
        if operations_mode == 0:
            pass
        elif operations_mode == 1:
            self._guild_operations_dispatch()
        elif operations_mode == 2:
            if self._guild_operations_boss_available():
                if self.config.GuildOperation_AttackBoss:
                    result = self._guild_operations_boss_combat()
                else:
                    logger.info('Auto-battle disabled, play manually to complete this Guild Task')
        else:
            result = False

        logger.info(f'Guild operation run success: {result}')
        return result
