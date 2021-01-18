from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.guild.assets import *
from module.guild.base import GuildBase
from module.ui.assets import GUILD_CHECK


class GuildLobby(GuildBase):
    def _guild_lobby_collect(self, skip_first_screenshot=True):
        """
        Performs collect actions if report rewards
        are present in lobby
        If already in page_guild but not lobby,
        this will timeout check and collect next time
        These rewards are queued and do not need to be
        collected immediately

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_REPORT_AVAILABLE, interval=3):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GUILD_REPORT_CLAIM, interval=3):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=2):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_2, offset=(30, 30), interval=2):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_3, offset=(30, 30), interval=2):
                confirm_timer.reset()
                continue

            if self.appear(GUILD_REPORT_CLAIMED, interval=3):
                self.device.click(GUILD_REPORT_CLOSE)
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_CHECK):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def guild_lobby(self):
        """
        Execute all actions in lobby

        Pages:
            in: GUILD_LOBBY
            out: GUILD_LOBBY
        """
        self._guild_lobby_collect()
