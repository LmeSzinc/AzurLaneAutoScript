from module.base.button import ClickButton
from module.base.utils import area_limit
from module.logger import logger
from tasks.rogue.assets.assets_rogue_event import CHOOSE_OPTION, CHOOSE_OPTION_CONFIRM, CHOOSE_STORY, OCR_EVENT
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM, PAGE_EVENT
from tasks.rogue.bleesing.ui import RogueUI


class RogueEvent(RogueUI):
    def handle_event_continue(self):
        if self.appear(PAGE_EVENT, interval=0.6):
            logger.info(f'{PAGE_EVENT} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        if self.appear_then_click(CHOOSE_STORY, interval=2):
            return True
        if self.appear_then_click(CHOOSE_OPTION_CONFIRM, interval=2):
            self.interval_reset([
                PAGE_EVENT,
                CHOOSE_STORY,
                CHOOSE_OPTION,
            ])
            return True

        return False

    def handle_event_option(self):
        options = CHOOSE_OPTION.match_multi_template(self.device.image)
        count = len(options)
        if count == 0:
            return False

        logger.attr('EventOption', count)
        for button in options:
            button.button = area_limit(button.button, OCR_EVENT.area)
        # Only one option, click directly
        if count == 1:
            if self.interval_is_reached(CHOOSE_OPTION, interval=2):
                self.device.click(options[0])
                self.interval_reset(CHOOSE_OPTION)
                return True

        if self.interval_is_reached(CHOOSE_OPTION, interval=2):
            option = self._event_option_filter(options)
            self.device.click(option)
            self.interval_reset(CHOOSE_OPTION)
            return True

        return False

    def _event_option_filter(self, options: list[ClickButton]) -> ClickButton:
        # TODO: OCR options instead of choosing the last one
        return options[-1]
