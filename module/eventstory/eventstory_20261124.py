import cv2

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_similar, get_color
from module.coalition.ui import CoalitionUI
from module.eventstory.assets import *
from module.eventstory.eventstory_base import EventStoryBase
from module.logger import logger
from module.ui.page import page_coalition


class EventStory20261124(EventStoryBase, CoalitionUI):
    def ui_goto_event_story(self):
        self.ui_ensure(page_coalition)
        self.coalition_ensure_mode(event='coalition_20261124', mode='story')

        state = 'unknown'
        for _ in range(3):
            # wait any story state
            timeout = Timer(2, count=6).start()
            for _ in self.loop():
                state = self.get_event_story_state()
                logger.attr('EventStoryState', state)
                if state != 'unknown':
                    break
                if timeout.reached():
                    logger.warning('Wait EventStoryState timeout')
                    break
            if state == 'unknown':
                # Story page get swiped, can't find story entrance
                # Reset mode to reset swipe
                self.coalition_ensure_mode(event='coalition_20261124', mode='battle')
                self.coalition_ensure_mode(event='coalition_20261124', mode='story')
                continue
            else:
                break

        return state

    def get_event_story_button(self):
        area = (0, 160, 880, 530)
        image = self.image_crop(area, copy=False)
        buttons = TEMPLATE_VERITAS_STORY_MIDDLE.match_multi(image)
        color = cv2.mean(TEMPLATE_VERITAS_STORY_MIDDLE.image)[:3]
        # click buttons on the left first
        buttons = sorted(buttons, key=lambda b: b.area[0])
        for button in buttons:
            button = button.move(area[:2])
            color_t = get_color(self.device.image, button.area)
            if color_similar(color_t, color, threshold=20):
                return button

        buttons = TEMPLATE_VERITAS_BATTLE.match_multi(image)
        color = cv2.mean(TEMPLATE_VERITAS_BATTLE.image)[:3]
        for button in buttons:
            button = button.move(area[:2])
            color_t = get_color(self.device.image, button.area)
            if color_similar(color_t, color, threshold=20):
                return button

        buttons = TEMPLATE_VERITAS_FINAL.match_multi(image)
        color = cv2.mean(TEMPLATE_VERITAS_FINAL.image)[:3]
        for button in buttons:
            button = button.move(area[:2])
            color_t = get_color(self.device.image, button.area)
            if color_similar(color_t, color, threshold=20):
                return button
        return None

    def get_event_story_state(self):
        """
        Returns:
            str: 'finish', 'story', 'unknown'
        """
        if self.appear(VERITAS_FINISHED, offset=(20, 20)):
            return 'finish'
        button = self.get_event_story_button()
        if button:
            return 'story'
        return 'unknown'

    def handle_event_story(self, interval=2):
        # TODO: FIX THAT match_template_color cannot return the correct result
        #  if the best result of template match is not within color threshold
        interval = self.get_interval_timer(TEMPLATE_VERITAS_STORY_MIDDLE, interval=interval)
        if not interval.reached():
            return False
        button = self.get_event_story_button()
        if button:
            self.device.click(button)
            interval.reset()
            return True

        return False

    @cached_property
    def allow_event_battle_kill_game(self):
        return False

    def combat_expected_end(self):
        if self.ui_page_appear(page_coalition):
            return True
        return False
