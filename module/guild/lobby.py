import numpy as np

from module.base.button import Button
from module.base.timer import Timer
from module.base.utils import area_offset, color_similarity_2d
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.map_detection.utils import Points
from module.ui.assets import GUILD_CHECK


class GuildLobby(GuildBase):
    def guild_lobby_get_report(self):
        """
        Returns:
            Button: Button to enter guild report.
        """
        # Find red color in the area of GUILD_REPORT_AVAILABLE
        image = color_similarity_2d(self.image_crop(GUILD_REPORT_AVAILABLE), color=(255, 8, 8))
        points = np.array(np.where(image > 221)).T[:, ::-1]
        if len(points):
            # The center of red dot
            points = Points(points).group(threshold=40) + GUILD_REPORT_AVAILABLE.area[:2]
            # Shift to the center of report icon
            area = area_offset((-51, -45, -13, 0), offset=points[0])
            return Button(area=area, color=(255, 255, 255), button=area, name='GUILD_REPORT')
        else:
            return None

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
        click_timer = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if click_timer.reached() and self.appear(GUILD_CHECK):
                button = self.guild_lobby_get_report()
                if button is not None:
                    self.device.click(button)
                    click_timer.reset()

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
        logger.hr('Guild lobby', level=1)
        self._guild_lobby_collect()
        logger.info('Guild lobby collect finished')
