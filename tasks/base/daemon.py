from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_daemon import *
from tasks.base.main_page import MainPage
from tasks.base.page import page_main, page_rogue
from tasks.daily.assets.assets_daily_camera import PICTURE_TAKEN
from tasks.map.assets.assets_map_bigmap import TELEPORT_RIGHT
from tasks.rogue.route.base import RouteBase


class Daemon(RouteBase):
    def run(self):
        # Rebind daemon settings along with rogue settings
        self.config.bind('Daemon', func_list=['Rogue'])
        self.device.disable_stuck_detection()

        teleport_confirm = Timer(1, count=5)
        while 1:
            self.device.screenshot()

            # Check lang
            if not MainPage._lang_checked and self.ui_page_appear(page_main, interval=5):
                self.handle_lang_check(page=page_main)
                # Check again
                if not MainPage._lang_check_success:
                    MainPage._lang_checked = False
            # Story
            if self.appear_then_click(STORY_NEXT, interval=0.7):
                self.interval_reset(STORY_OPTION)
                # self.interval_reset(INTERACT_INVESTIGATE)
                continue
            if self.appear_then_click(STORY_OPTION, interval=1):
                # self.interval_reset(INTERACT_INVESTIGATE)
                continue
            # Map interact
            if self.appear_then_click(INTERACT_TREASURE, interval=1):
                continue
            # if self.appear_then_click(INTERACT_INVESTIGATE, interval=2):
            #     continue
            if self.appear_then_click(INTERACT_COLLECT, interval=1):
                continue
            # Story teleport
            if self.appear_then_click(TELEPORT_RIGHT, interval=3):
                teleport_confirm.reset()
                continue
            if teleport_confirm.started() and not teleport_confirm.reached():
                if self.handle_popup_confirm():
                    logger.info(f'{TELEPORT_RIGHT} -> popup')
                    continue
            # Chat
            if self.appear_then_click(CHAT_OPTION, interval=3):
                continue
            if self.appear_then_click(CHAT_CLOSE, interval=3):
                continue
            # Popup
            if self.handle_reward(interval=1.5):
                continue
            if self.handle_ui_close(PICTURE_TAKEN, interval=1):
                continue
            # Rogue
            if self.handle_blessing():
                continue
            if self.ui_page_appear(page_rogue):
                if self.handle_event_continue():
                    continue
                if self.handle_event_option():
                    continue
