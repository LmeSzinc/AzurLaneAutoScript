from module.base.timer import Timer
from module.daemon.daemon_base import DaemonBase
from module.device.method import maatouch
from module.logger import logger
from tasks.base.assets.assets_base_daemon import *
from tasks.base.main_page import MainPage
from tasks.base.page import page_main, page_rogue
from tasks.daily.assets.assets_daily_camera import PICTURE_TAKEN
from tasks.map.assets.assets_map_bigmap import TELEPORT_RIGHT
from tasks.map.interact.aim import AimDetectorMixin
from tasks.rogue.route.base import RouteBase


class SecondaryMaatouchBuilder(maatouch.MaatouchBuilder):
    def __init__(self, device, contact=0, handle_orientation=False):
        """
        Click on secondary contact to avoid interruption of real-person contact
        """
        super().__init__(device, contact=1, handle_orientation=handle_orientation)


maatouch.MaatouchBuilder = SecondaryMaatouchBuilder


class Daemon(RouteBase, DaemonBase, AimDetectorMixin):
    aim_interval = Timer(0.3, count=1)

    def handle_aim_click(self, item=True, enemy=True):
        """
        Args:
            item:
            enemy:

        Returns:
            bool: If clicked
        """
        if not item and not enemy:
            return False
        if not self.is_in_main():
            return False

        if self.aim_interval.reached_and_reset():
            self.aim.predict(self.device.image, item=item, enemy=enemy)
        if self.aim.aimed_enemy:
            if self.handle_map_A():
                return True
        if self.aim.aimed_item:
            if self.handle_map_A():
                return True
        return False

    def run(self):
        # Rebind daemon settings along with rogue settings
        self.config.bind('Daemon', func_list=['Rogue'])
        # Check contact
        builder = self.device.maatouch_builder
        if builder.contact >= 1:
            logger.info(f'Maatouch contact on {builder.contact}')
        else:
            logger.warning(f'Maatouch contact on {builder.contact}, may cause interruptions')

        STORY_OPTION.set_search_offset((-5, -10, 32, 5))
        INTERACT_COLLECT.set_search_offset((-5, -5, 32, 5))
        INTERACT_INVESTIGATE.set_search_offset((-5, -5, 32, 5))
        INTERACT_TREASURE.set_search_offset((-5, -5, 32, 5))

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
            if self.appear_then_click(DUNGEON_EXIT, interval=1.5):
                continue
            # Tutorial popup
            if self.appear(TUTORIAL_CHECK, interval=0.2):
                if self.image_color_count(TUTORIAL_CLOSE, color=(255, 255, 255), threshold=180, count=400):
                    self.device.click(TUTORIAL_CLOSE)
                    continue
                if self.image_color_count(TUTORIAL_NEXT, color=(255, 255, 255), threshold=180, count=50):
                    self.device.click(TUTORIAL_NEXT)
                    continue
            # Rogue
            if self.handle_blessing():
                continue
            if self.ui_page_appear(page_rogue):
                if self.handle_event_continue():
                    continue
                if self.handle_event_option():
                    continue
            # Aim click
            if self.handle_aim_click(
                    item='item' in self.config.Daemon_AimClicker,
                    enemy='enemy' in self.config.Daemon_AimClicker,
            ):
                continue
