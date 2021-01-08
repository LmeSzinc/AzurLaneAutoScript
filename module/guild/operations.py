import numpy as np

from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.template.assets import TEMPLATE_OPERATIONS_RED_DOT, TEMPLATE_OPERATIONS_ADD

MASK_OPERATIONS = Mask(file='./assets/mask/MASK_OPERATIONS.png')

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
            logger.info('Operations ensurance failed, try again on next reward loop')
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
            logger.info('Mode: Operations Inactive, please contact your Elite/Officer/Leader seniors to select an operation difficulty')
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

        expand = Button(area=expand_button, color=(), button=expand_button, name='EXPAND_OPERATION')
        open = Button(area=open_button, color=(), button=open_button, name='OPEN_OPERATION')

        logger.info('Active operation found in this area, attempting to enter')
        self.device.click(expand)
        self.device.sleep((0.5, 0.8))
        self.device.click(open)

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
        otherwise swipes forward until
        reached end of map

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_MAP
        """
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
                continue

            if not self.view_forward():
                break

    def _guild_operations_boss_preparation(self, skip_first_screenshot=True):
        """
        Execute preperation sequence for guild raid boss

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: IN_BATTLE
        """
        is_loading = False
        empty_timer = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_BOSS_ENTER, interval=3):
                continue

            if self.appear(GUILD_DISPATCH_EMPTY_2):
                # Account for loading lag especially if using
                # guild support
                if not empty_timer.started():
                    empty_timer.reset()
                    continue
                elif empty_timer.reached():
                    logger.warning('Fleet composition empty, cannot auto-battle Guild Raid Boss')
                    return False

            if self.appear(GUILD_DISPATCH_FLEET, interval=3):
                # Button does not appear greyed out even
                # when empty fleet composition
                if not self.appear(GUILD_DISPATCH_EMPTY_2):
                    self.device.click(GUILD_DISPATCH_FLEET)

            # Only print once when detected
            if not is_loading:
                if self.is_combat_loading():
                    is_loading = True
                continue

            if self.handle_combat_automation_confirm():
                continue

            # End
            if self.is_combat_executing():
                return True

    def _guild_operations_boss_combat(self):
        """
        Execute combat sequence
        If battle could not be prepared, exit

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: GUILD_OPERATIONS_BOSS
        """
        if not self._guild_operations_boss_preparation():
            return
        self.combat_execute(auto='combat_auto')
        self.combat_status(expected_end='in_ui')
        logger.info('Guild Raid Boss has been repelled')

    def guild_operations(self):
        # Determine the mode of operations, currently 3 are available
        operations_mode = self._guild_operations_mode_ensure()
        if operations_mode is None:
            return

        # Execute actions based on the detected mode
        if operations_mode == 0:
            return
        elif operations_mode == 1:
            self._guild_operations_scan()
        else:
            if self.appear(GUILD_BOSS_AVAILABLE):
                if self.config.ENABLE_GUILD_OPERATIONS_BOSS_AUTO:
                    self._guild_operations_boss_combat()
                else:
                    logger.info('Auto-battle disabled, play manually to complete this Guild Task')