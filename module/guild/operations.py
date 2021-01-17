from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.template.assets import TEMPLATE_OPERATIONS_RED_DOT, TEMPLATE_OPERATIONS_ADD

RECORD_OPTION_DISPATCH = ('RewardRecord', 'operations_dispatch')
RECORD_SINCE_DISPATCH = (6, 12, 18, 21,)
RECORD_OPTION_BOSS = ('RewardRecord', 'operations_boss')
RECORD_SINCE_BOSS = (0,)

MASK_OPERATIONS = Mask(file='./assets/mask/MASK_OPERATIONS.png')
MASK_SIDEBAR_RED_DOT = Mask(file='./assets/mask/MASK_SIDEBAR_RED_DOT.png')


class GuildOperations(GuildBase):
    def _guild_operations_mode_ensure(self, skip_first_screenshot=True):
        """
        Determine which operations menu has loaded
            0 - No ongoing operations, Officers/Elites/Leader must select one to begin
            1 - Operations available, displaying a state diagram/web of operations
            2 - Guild Raid Boss active
            Otherwise None if unable to ensure or determine the menu at all

        Pages:
            in: GUILD_OPERATIONS_ANY
            out: GUILD_OPERATIONS_ANY
        """
        if not self.guild_sidebar_ensure(1):
            logger.info('Operations sidebar not ensured, try again on next reward loop')
            return None

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_OPERATIONS_JOIN, interval=3):
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_BOSS_CHECK) or self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                if not self.info_bar_count() and confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        if self.appear(GUILD_OPERATIONS_INACTIVE_CHECK) and self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info(
                'Mode: Operations Inactive, please contact your Elite/Officer/Leader seniors to select '
                'an operation difficulty')
            return 0
        elif self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info('Mode: Operations Active, may proceed to scan and dispatch fleets')
            return 1
        elif self.appear(GUILD_BOSS_CHECK):
            logger.info('Mode: Guild Raid Boss')
            return 2
        else:
            logger.warning('Operations interface is unrecognized')
            return None

    def _guild_operations_red_dot_present(self):
        """
        Helper function to perform an isolated scan
        for the lower bottom left sidebar whether
        a red dot is present.
        The red dot could either be Tech
        or Operations (Guild Master vs Member).

        Pages:
            in: GUILD_ANY
            out: GUILD_ANY
        """
        # Apply mask to cover potential RED_DOTs that are operations or
        # anywhere else for that matter
        image = MASK_SIDEBAR_RED_DOT.apply(np.array(self.device.image))

        # Scan image and must have similarity greater than 0.85
        sim, point = TEMPLATE_OPERATIONS_RED_DOT.match_result(image)
        if sim < 0.85:
            return False

        # Unsure whether this red dot is from the Tech or Operations
        # sidebar. But for safety will check Operations anyway
        return True

    def _guild_operations_enter_ensure(self):
        """
        Specific helper to ensure operation has
        been opened. This occurs due to expansion,
        this may shift the map far from how it was
        originally

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_MAP
        """
        confirm_timer = Timer(1.5, count=3).start()
        verify_timeout = Timer(3, count=6)
        while 1:
            self.device.screenshot()

            # End
            if self.appear(GUILD_DISPATCH_QUICK):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()
                if not verify_timeout.started():
                    verify_timeout.reset()
                elif verify_timeout.reached():
                    logger.info('Map shift detected, will commence rescan for operation')
                    return False

    def _guild_operations_enter(self):
        """
        Mask and then scan the current image to look
        for active operations, noted by a red dot icon
            0 - Red dot not found at all
            1 - Red dot found and entered into operation successfully
            2 - Red dot found however due to map shift, operation could
                not be entered, allow re-try next loop

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_DISPATCH
        """
        # Apply mask to cover potential RED_DOTs that are not operations
        image = MASK_OPERATIONS.apply(np.array(self.device.image))

        # Scan image and must have similarity greater than 0.85
        sim, point = TEMPLATE_OPERATIONS_RED_DOT.match_result(image)
        if sim < 0.85:
            logger.info('No active operations found in this area')
            return 0

        # Target RED_DOT found, adjust the found point location
        # for 2 separate clicks
        # First, Expand operation for details click area
        # Second, Open operation enter into dispatch GUI
        expand_point = tuple(sum(x) for x in zip(point, (0, 25)))
        open_point = tuple(sum(x) for x in zip(point, (-55, -55)))

        # Use small area to reduce random click point
        expand_button = area_offset(area=(-4, -4, 4, 4), offset=expand_point)
        open_button = area_offset(area=(-4, -4, 4, 4), offset=open_point)

        expand_click = Button(area=expand_button, color=(), button=expand_button, name='EXPAND_OPERATION')
        open_click = Button(area=open_button, color=(), button=open_button, name='OPEN_OPERATION')

        logger.info('Active operation found in this area, attempting to enter')
        self.device.click(expand_click)
        self.device.sleep((0.5, 0.8))
        self.device.click(open_click)

        if self._guild_operations_enter_ensure():
            return 1
        else:
            return 2

    def _guild_operations_dispatch(self, skip_first_screenshot=True):
        """
        Executes the dispatch sequence

        Pages:
            in: GUILD_OPERATIONS_DISPATCH
            out: GUILD_OPERATIONS_MAP
        """
        confirm_timer = Timer(1.5, count=3).start()
        add_timer = Timer(1.5, count=3)
        close_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_DISPATCH_QUICK, interval=5):
                confirm_timer.reset()
                close_timer.reset()
                continue

            if self.appear(GUILD_DISPATCH_EMPTY, interval=5):
                self.device.click(GUILD_DISPATCH_RECOMMEND)
                self.device.sleep((0.5, 0.8))
                self.device.click(GUILD_DISPATCH_FLEET)
                confirm_timer.reset()
                close_timer.reset()
                continue

            # Pseudo interval timer for template match_result calls
            if not add_timer.started() or add_timer.reached():
                sim, point = TEMPLATE_OPERATIONS_ADD.match_result(self.device.image)
                if sim > 0.85:
                    # Use small area to reduce random click point
                    button = area_offset(area=(-2, -2, 24, 12), offset=point)
                    dispatch_add = Button(area=button, color=(), button=button, name='GUILD_DISPATCH_ADD')
                    self.device.click(dispatch_add)
                    confirm_timer.reset()
                    add_timer.reset()
                    close_timer.reset()
                    continue
                add_timer.reset()

            if self.handle_popup_confirm('GUILD_DISPATCH'):
                # Explicit click since GUILD_DISPATCH_FLEET
                # does not automatically turn into
                # GUILD_DISPATCH_IN_PROGRESS after confirm
                self.device.sleep((0.5, 0.8))
                self.device.click(GUILD_DISPATCH_CLOSE)
                confirm_timer.reset()
                close_timer.reset()
                continue

            if self.appear(GUILD_DISPATCH_IN_PROGRESS):
                # Independent timer used instead of interval
                # Since can appear if at least 1 fleet already
                # dispatched, don't want to exit prematurely
                if close_timer.reached_and_reset():
                    self.device.click(GUILD_DISPATCH_CLOSE)
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                if not self.info_bar_count() and confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()
                close_timer.reset()

    def _guild_operations_scan(self, skip_first_screenshot=True):
        """
        Executes the scan operations map sequence
        and additional events
        Scanning for active operations
        if found enters and dispatch fleet
        otherwise exits upon reaching timeout

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_MAP
        """
        scan_timeout = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Scan location for any active operations
            entered = self._guild_operations_enter()
            if entered:
                if entered == 1:
                    self._guild_operations_dispatch()
                scan_timeout.reset()
                continue

            # if not self.guild_view_forward():
            #     break
            if not scan_timeout.started():
                scan_timeout.reset()
            elif scan_timeout.reached():
                break

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

            if self.appear(GUILD_DISPATCH_FLEET, interval=3):
                # Button does not appear greyed out even
                # when empty fleet composition
                if dispatch_count < 3:
                    self.device.click(GUILD_DISPATCH_FLEET)
                    dispatch_count += 1
                else:
                    logger.warning('Fleet composition error. Preloaded guild support selection may be '
                                   'preventing dispatch. Suggestion: Enable Boss Recommend')
                    return False
                continue

            if self.config.ENABLE_GUILD_OPERATIONS_BOSS_RECOMMEND:
                if self.info_bar_count() and self.appear_then_click(GUILD_DISPATCH_RECOMMEND_2, interval=3):
                    continue

            # Only print once when detected
            if not is_loading:
                if az.is_combat_loading():
                    is_loading = True
                    continue

            if az.handle_combat_automation_confirm():
                continue

            # End
            if az.is_combat_executing():
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
        az.combat_execute(auto='combat_auto')
        az.combat_status(expected_end='in_ui')
        logger.info('Guild Raid Boss has been repelled')
        return True

    def guild_operations(self):
        # Determine the mode of operations, currently 3 are available
        operations_mode = self._guild_operations_mode_ensure()
        if operations_mode is None:
            return

        # Execute actions based on the detected mode
        if operations_mode == 0:
            return
        elif operations_mode == 1:
            # Limit check for scanning operations to 4 times a day i.e. 6-hour intervals, 4th time reduced to 3-hour
            if not self.config.record_executed_since(option=RECORD_OPTION_DISPATCH,
                                                     since=RECORD_SINCE_DISPATCH) or \
                    self._guild_operations_red_dot_present():
                self._guild_operations_scan()
                self.config.record_save(option=RECORD_OPTION_DISPATCH)
        else:
            # Limit check for Guild Raid Boss to once a day
            if not self.config.record_executed_since(option=RECORD_OPTION_BOSS,
                                                     since=RECORD_SINCE_BOSS) or \
                    self._guild_operations_red_dot_present():
                skip_record = False
                if self.appear(GUILD_BOSS_AVAILABLE):
                    if self.config.ENABLE_GUILD_OPERATIONS_BOSS_AUTO:
                        if not self._guild_operations_boss_combat():
                            skip_record = True
                    else:
                        logger.info('Auto-battle disabled, play manually to complete this Guild Task')

                if not skip_record:
                    self.config.record_save(option=RECORD_OPTION_BOSS)
