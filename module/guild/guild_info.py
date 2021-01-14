from module.base.timer import Timer
from module.guild.assets import GUILD_HANDLE_CONFIRM, GUILD_BOSS_CHECK, GUILD_OPERATIONS_ACTIVE_CHECK
from module.guild.logistics import GuildLogistics
from module.guild.operations import GuildOperations
from module.logger import logger
from module.ui.assets import GUILD_CHECK

class InfoGuild(GuildLogistics, GuildOperations):
    def guild_info_appear(self):
        """
        Helper function to check whether the guild
        info window has appeared

        Pages:
            in: ANY
            out: ANY
        """
        return self.appear(GUILD_HANDLE_CONFIRM, offset=30)

    def _guild_quit_check_func(self):
        """
        Helper function to check whether having
        exited the guild page

        Pages:
            in: ANY
            out: ANY
        """
        return not self.appear(GUILD_CHECK)

    def _guild_quit(self):
        """
        Handle returning back to page where
        info window had appeared

        Pages:
            in: GUILD_LOGISTICS or GUILD_OPERATIONS
            out: ANY
        """
        self.ui_back(check_button=self._guild_quit_check_func, skip_first_screenshot=True)

    def _guild_info_ensure(self):
        """
        Ensure guild page being dealt with using
        expected assets, if timed out then assume
        other page

        Pages:
            in: GUILD_LOGISTICS or GUILD_OPERATIONS
            out: GUILD_LOGISTICS or GUILD_OPERATIONS
        """
        confirm_timer = Timer(1.5, count=3).start()
        verify_timeout = Timer(3, count=6)
        while 1:
            self.device.screenshot()

            # End
            if self.appear(GUILD_BOSS_CHECK) or self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                if confirm_timer.reached():
                    logger.info('Detected handle operations')
                    return True
            else:
                confirm_timer.reset()
                if not verify_timeout.started():
                    verify_timeout.reset()
                elif verify_timeout.reached():
                    logger.info('Detected handle logistics')
                    return False

    def _guild_info_handler(self):
        """
        Enters into Guild and scans the current image
        to determine approriate action

        Pages:
            in: ANY
            out: GUILD_LOGISTICS or GUILD_OPERATIONS
        """
        self.ui_click(GUILD_HANDLE_CONFIRM, check_button=GUILD_CHECK, skip_first_screenshot=True)

        # Determine which guild info is being dealt with
        # Execute if it's corresponding flag is enabled
        # Else just go back and info window will self
        # close upon returning to last page
        if self._guild_info_ensure():
            if self.config.ENABLE_GUILD_OPERATIONS:
                self.guild_operations()
        else:
            if self.config.ENABLE_GUILD_LOGISTICS:
                self.guild_logistics()

        self._guild_quit()

    def handle_guild_info(self):
        """
        Handle cases when the guild
        info window appears

        Pages:
            in: ANY
            out: ANY
        """
        if not self.guild_info_appear():
            return False

        self._guild_info_handler()

        return True