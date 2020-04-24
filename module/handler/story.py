from module.handler.assets import *
from module.handler.popup import PopupHandler


class StoryHandler(PopupHandler):
    def story_skip(self):
        if self.appear_then_click(STORY_SKIP, offset=True, interval=2):
            return True
        if self.handle_popup_confirm():
            return True
        if self.appear_then_click(STORY_CHOOCE, offset=True, interval=2):
            return True
        if self.appear_then_click(STORY_CHOOCE_2, offset=True, interval=2):
            return True

        return False

    def handle_story_skip(self):
        if not self.config.ENABLE_MAP_CLEAR_MODE:
            return False

        return self.story_skip()