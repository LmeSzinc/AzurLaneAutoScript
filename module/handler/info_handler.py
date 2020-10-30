from module.base.base import ModuleBase
from module.base.timer import Timer
from module.handler.assets import *
from module.logger import logger


class InfoHandler(ModuleBase):
    """
    Class to handle all kinds of message.
    """
    """
    Info bar
    """
    def info_bar_count(self):
        if self.appear(INFO_BAR_3):
            return 3
        elif self.appear(INFO_BAR_2):
            return 2
        elif self.appear(INFO_BAR_1):
            return 1
        else:
            return 0

    def handle_info_bar(self):
        if self.info_bar_count():
            self.wait_until_disappear(INFO_BAR_1)
            return True
        else:
            return False

    def ensure_no_info_bar(self, timeout=0.6):
        timeout = Timer(timeout)
        timeout.start()
        while 1:
            self.device.screenshot()
            self.handle_info_bar()

            if timeout.reached():
                break

    """
    Popup info
    """
    _popup_offset = (3, 30)

    def handle_popup_confirm(self, name=''):
        if self.appear(POPUP_CANCEL, offset=self._popup_offset) \
                and self.appear(POPUP_CONFIRM, offset=self._popup_offset, interval=2):
            POPUP_CONFIRM.name = POPUP_CONFIRM.name + '_' + name
            self.device.click(POPUP_CONFIRM)
            POPUP_CONFIRM.name = POPUP_CONFIRM.name[:-len(name) - 1]
            return True
        else:
            return False

    def handle_popup_cancel(self, name=''):
        if self.appear(POPUP_CONFIRM, offset=self._popup_offset) \
                and self.appear(POPUP_CANCEL, offset=self._popup_offset, interval=2):
            POPUP_CANCEL.name = POPUP_CANCEL.name + '_' + name
            self.device.click(POPUP_CANCEL)
            POPUP_CANCEL.name = POPUP_CANCEL.name[:-len(name) - 1]
            return True
        else:
            return False

    def handle_urgent_commission(self, save_get_items=None):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if save_get_items is None:
            save_get_items = self.config.ENABLE_SAVE_GET_ITEMS

        appear = self.appear(GET_MISSION, offset=True, interval=2)
        if appear:
            logger.info('Get urgent commission')
            if save_get_items:
                self.handle_info_bar()
                self.device.save_screenshot('get_mission')
            self.device.click(GET_MISSION)
        return appear

    def handle_combat_low_emotion(self):
        if not self.config.IGNORE_LOW_EMOTION_WARN:
            return False

        return self.handle_popup_confirm('IGNORE_LOW_EMOTION')

    """
    Story
    """
    story_popup_timout = Timer(10, count=20)
    map_has_fast_forward = False  # Will be override in fast_forward.py

    def story_skip(self):
        if self.story_popup_timout.started() and not self.story_popup_timout.reached():
            if self.handle_popup_confirm('STORY_SKIP'):
                self.story_popup_timout = Timer(10)
                self.interval_reset(STORY_SKIP)
                self.interval_reset(STORY_LETTERS_ONLY)
                return True
        if self.appear_then_click(STORY_SKIP, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self.appear(STORY_LETTER_BLACK) and self.appear_then_click(STORY_LETTERS_ONLY, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self.appear_then_click(STORY_CHOOSE, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self.appear_then_click(STORY_CHOOSE_2, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self.appear_then_click(GAME_TIPS, offset=(20, 20), interval=2):
            self.story_popup_timout.reset()
            return True

        return False

    def handle_story_skip(self):
        if self.map_has_fast_forward:
            return False

        return self.story_skip()

    def ensure_no_story(self, skip_first_screenshot=True):
        logger.info('Ensure no story')
        story_timer = Timer(5, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.story_skip():
                story_timer.reset()

            if story_timer.reached():
                break

    def handle_map_after_combat_story(self):
        if not self.config.MAP_HAS_MAP_STORY:
            return False

        self.ensure_no_story()
