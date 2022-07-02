from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.config.utils import get_server_next_update
from module.logger import logger
from module.meowfficer.assets import *
from module.ui.assets import MEOWFFICER_CHECK, MEOWFFICER_INFO
from module.ui.ui import UI


class MeowfficerBase(UI):
    def meow_additional(self):
        """
        Handle additional clauses
        that may occur in between screens

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=3):
            return True

        return False

    def meow_menu_close(self, skip_first_screenshot=True):
        """
        Exit from any meowfficer menu popups

        Pages:
            in: MEOWFFICER_FORT_CHECK, MEOWFFICER_BUY, MEOWFFICER_TRAIN_START, etc
            out: page_meowfficer
        """
        logger.hr('Meowfficer menu close')
        click_timer = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(MEOWFFICER_CHECK, offset=(20, 20)) \
                    and MEOWFFICER_CHECK.match_appear_on(self.device.image):
                break
            else:
                if click_timer.reached():
                    # MEOWFFICER_CHECK is safe to click
                    self.device.click(MEOWFFICER_CHECK)
                    click_timer.reset()
                    continue

            # Fort
            if self.appear(MEOWFFICER_FORT_CHECK, offset=(20, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            # Buy
            if self.appear(MEOWFFICER_BUY, offset=(20, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            # Train
            if self.appear(MEOWFFICER_TRAIN_FILL_QUEUE, offset=(20, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            if self.appear(MEOWFFICER_TRAIN_FINISH_ALL, offset=(20, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            # Popups
            if self.appear(MEOWFFICER_CONFIRM, offset=(40, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            if self.appear(MEOWFFICER_CANCEL, offset=(40, 20), interval=3):
                self.device.click(MEOWFFICER_CHECK)
                click_timer.reset()
                continue
            if self.appear_then_click(GET_ITEMS_1, offset=5, interval=3):
                click_timer.reset()
                continue
            if self.meow_additional():
                click_timer.reset()
                continue

    def handle_meow_popup_confirm(self):
        """
        Confirm the popup; can mean close
        the popup and allow the action

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            return True
        else:
            return False

    def handle_meow_popup_cancel(self):
        """
        Cancel the popup; can mean close
        the popup or to not allow the action

        Returns:
            bool:
        """
        if self.appear_then_click(MEOWFFICER_CANCEL, offset=(40, 20), interval=5):
            return True
        else:
            return False

    def handle_meow_popup_dismiss(self):
        """
        Dismiss the popup; neither confirm
        or cancel the action

        Returns:
            bool:
        """
        if self.appear(MEOWFFICER_CONFIRM, offset=(40, 20), interval=5):
            self.device.click(MEOWFFICER_CHECK)
            return True
        elif self.appear(MEOWFFICER_CANCEL, offset=(40, 20), interval=5):
            self.device.click(MEOWFFICER_CHECK)
            return True
        else:
            return False

    def meow_is_sunday(self):
        """
        datetime argument is the next server update of,
        today's run. So check for Monday's weekday value
        (0) rather than Sunday's weekday value (6)

        Returns:
            bool:
        """
        return get_server_next_update(self.config.Scheduler_ServerUpdate).weekday() == 0
