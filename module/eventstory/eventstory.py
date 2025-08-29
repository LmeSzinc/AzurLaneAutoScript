from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.campaign.campaign_ui import CampaignUI
from module.combat.combat import Combat
from module.eventstory.assets import *
from module.handler.login import LoginHandler
from module.logger import logger
from module.ui.page import page_event


class EventStory(CampaignUI, Combat, LoginHandler):
    def ui_goto_event_story(self):
        """
        Returns:
            str: 'finish', 'story', 'unknown'
        """
        self.ui_ensure(page_event)
        self.campaign_ensure_mode_20241219('story')

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
                self.campaign_ensure_mode_20241219('combat')
                self.campaign_ensure_mode_20241219('story')
                continue
            else:
                break

        return state

    def get_event_20250724_button(self):
        """
        Returns:
            Button | None:
        """
        area = (0, 72, 1280, 560)
        image = self.image_crop(area, copy=False)
        image = rgb2gray(image)
        sim, button = TEMPLATE_ALCHEMIST_STORY.match_result(image)
        if sim >= 0.85:
            button = button.move(area[:2])
            # move down to click the text
            button = button.move((0, 44))
            return button
        sim, button = TEMPLATE_ALCHEMIST_BATTLE.match_result(image)
        if sim >= 0.85:
            button = button.move(area[:2])
            # move down to click the text
            button = button.move((0, 44))
            return button
        return None

    def handle_event_20250724(self, interval=2):
        """
        In Alchemist collab 2, story button just appear everywhere

        Returns:
            bool: If clicked
        """
        interval = self.get_interval_timer(TEMPLATE_ALCHEMIST_STORY, interval=interval)
        if not interval.reached():
            return False
        button = self.get_event_20250724_button()
        if button:
            self.device.click(button)
            interval.reset()
            return True
        else:
            return False

    def event_story(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            str: 'battle' or 'finish'
        """
        logger.hr('Event story', level=1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_combat_executing() or self.is_combat_loading():
                logger.info('run_story end at battle')
                return 'battle'
            if self.match_template_color(STORY_FINISHED, offset=(20, 20), interval=3):
                logger.info('run_story end at STORY_FINISHED')
                return 'finish'
            if self.appear(REWARD_GOT, offset=(50, 30)):
                logger.info('run_story end at REWARD_GOT')
                return 'finish'

            # Story skip
            if self.handle_story_skip():
                self.interval_clear([STORY_MIDDLE, BATTLE_MIDDLE])
                continue
            if self.handle_get_items():
                continue

            # Clicks
            if self.appear_then_click(STORY_FIRST, offset=(20, 20), interval=3):
                self.story_skip_interval_clear()
                self.popup_interval_clear()
                self.device.click_record_clear()
                continue
            if self.match_template_color(STORY_LAST, offset=(20, 20), interval=3):
                self.device.click(STORY_LAST)
                self.story_skip_interval_clear()
                self.popup_interval_clear()
                self.device.click_record_clear()
                continue
            if self.appear_then_click(STORY_MIDDLE, offset=(20, 200), interval=3):
                self.story_skip_interval_clear()
                self.popup_interval_clear()
                self.device.click_record_clear()
                continue
            if self.appear_then_click(BATTLE_MIDDLE, offset=(20, 200), interval=3):
                self.story_skip_interval_clear()
                self.popup_interval_clear()
                self.device.click_record_clear()
                continue
            if self.handle_event_20250724():
                self.story_skip_interval_clear()
                self.popup_interval_clear()
                self.device.click_record_clear()
                continue
            # Secrets of the Abyss (event_20250814_cn)
            # popup after all story finished
            if self.appear_then_click(POPUP_RPG_STATUS, offset=(20, 20), interval=3):
                continue

    def run_event_story(self):
        """
        Loop until event story finished
        Handle story battles
        """
        while 1:
            state = self.ui_goto_event_story()
            if state == 'finish':
                break
            result = self.event_story()
            if result == 'battle':
                # Kill game is considered cleared battles
                # It's much faster than waiting event battles
                logger.hr('Event Story Battle', level=2)
                self.config.override(Error_HandleError=True)
                self.app_stop()
                self.app_start()
                continue
            if result == 'finish':
                # Run after finished event story, in order to close GET_ITEMS
                logger.hr('Event story finish', level=2)
                self.ui_goto_main()
                self.ui_goto_event_story()

    def get_event_story_state(self):
        """
        Returns:
            str: 'finish', 'story', 'unknown'
        """
        if self.match_template_color(STORY_FINISHED, offset=(20, 20)):
            return 'finish'
        if self.appear(REWARD_GOT, offset=(50, 30)):
            return 'finish'

        if self.appear_then_click(STORY_FIRST, offset=(20, 20)):
            return 'story'
        if self.match_template_color(STORY_LAST, offset=(20, 20)):
            return 'story'
        if self.appear_then_click(STORY_MIDDLE, offset=(20, 200)):
            return 'story'
        if self.appear_then_click(BATTLE_MIDDLE, offset=(20, 200)):
            return 'story'
        if self.get_event_20250724_button():
            return 'story_alchemist'

        return 'unknown'

    def run(self):
        if not self.device.app_is_running():
            logger.warning('Game is not running, start it')
            self.app_start()

        self.run_event_story()

        # Scheduler
        pass


if __name__ == '__main__':
    self = EventStory('alas')
    self.run()
