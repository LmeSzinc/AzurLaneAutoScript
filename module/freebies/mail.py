import re

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.timer import Timer
from module.combat.assets import *
from module.freebies.assets import *
from module.logger import logger
from module.statistics.item import ItemGrid
from module.ui.page import page_main, page_main_white
from module.ui.ui import UI
from module.ui_white.assets import MAIL_ENTER_WHITE

MAIL_BUTTON_GRID = ButtonGrid(
    origin=(137, 207), delta=(0, 97),
    button_shape=(64, 64), grid_shape=(1, 3),
    name='MAIL_BUTTON_GRID')
FILTER_REGEX = re.compile(
    '^(cube|coin|coolant|decorcoin|oil|merit|gem)$',
    flags=re.IGNORECASE)
FILTER_ATTR = ['name']
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


class Mail(UI):
    def _mail_enter(self, delete=False, skip_first_screenshot=True):
        """
        Goes to mail page
        Also deletes viewed mails to ensure the relevant
        row entries are in view

        Args:
            delete (bool):
                Enable extra step to delete old
                already collected mail entries
            skip_first_screenshot (bool):

        Returns:
            bool: False if mail list empty
        """
        logger.hr('Mail enter')
        btn_expanded = MAIL_BUTTON_GRID.buttons[0]
        btn_collapsed = btn_expanded.move((350, 0))
        self.interval_clear([page_main.check_button, page_main_white.check_button, MAIL_DELETE])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(MAIL_EMPTY, offset=(20, 20)):
                logger.info('Mail list empty')
                return False
            if self.appear(MAIL_GUILD_MESSAGE, offset=(20, 20)):
                logger.info('Guild mail found, exit')
                return False
            if not delete and self._mail_selected(btn_expanded):
                if self.appear(MAIL_COLLECT, offset=(20, 20)):
                    return True
                if self.appear(MAIL_COLLECTED, offset=(20, 20)):
                    return True

            if self.appear(page_main.check_button, offset=(30, 30), interval=3):
                self.device.click(MAIL_ENTER)
                continue
            if self.appear(page_main_white.check_button, offset=(30, 30), interval=3):
                self.device.click(MAIL_ENTER_WHITE)
                continue
            if delete:
                if self.appear_then_click(MAIL_DELETE, offset=(350, 20), interval=3):
                    continue
                if self.handle_popup_confirm('MAIL_DELETE'):
                    delete = False
                    continue
            else:
                if self.appear(MAIL_DELETE, offset=(350, 20), interval=3):
                    self.device.click(btn_collapsed)
                    continue
            if self.handle_info_bar():
                continue

    def _mail_exit(self, skip_first_screenshot=True):
        """
        Exits from mail page back into page_main

        Args:
            skip_first_screenshot (bool):
        """
        logger.hr('Mail exit')
        self.interval_clear([MAIL_DELETE, GET_ITEMS_1, GET_ITEMS_2])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_ITEMS_1, offset=(30, 30), interval=1):
                self.device.click(MAIL_COLLECT)
                continue
            if self.appear(GET_ITEMS_2, offset=(30, 30), interval=1):
                self.device.click(MAIL_COLLECT)
                continue
            if self.appear(MAIL_DELETE, offset=(350, 20), interval=3):
                self.device.click(MAIL_ENTER)
                continue
            if self.handle_info_bar():
                continue

            # End
            if self.is_in_main():
                break

    @cached_property
    def _mail_grid(self):
        """
        This grid only comprises the top 3 mail rows

        Returns:
            ItemGrid
        """
        mail_item_grid = ItemGrid(MAIL_BUTTON_GRID, templates={},
                                  amount_area=(60, 74, 96, 95))
        mail_item_grid.load_template_folder('./assets/stats_basic')
        mail_item_grid.similarity = 0.85
        return mail_item_grid

    def _mail_get_collectable(self):
        """
        Loads filter and scans the items in the mail grid
        then returns a subset of those that are collectable

        Returns:
            list[Item]
        """
        FILTER.load(self.config.Mail_Filter.strip())
        items = self._mail_grid.predict(
            self.device.image,
            name=True,
            amount=False,
            cost=False,
            price=False,
            tag=False
        )
        filtered = FILTER.apply(items, None)
        logger.attr('Item_sort', ' > '.join([str(item) for item in filtered]))
        return filtered

    def _mail_selected(self, button):
        """
        Check if mail (button) is selected i.e.
        has bottom yellow border

        Args:
            button (Button):

        Returns:
            bool
        """
        area = button.area
        check_area = tuple([area[0], area[3] + 3, area[2], area[3] + 10])
        return self.image_color_count(check_area, color=(255, 223, 66), threshold=180, count=25)

    def _mail_collect_one(self, item, skip_first_screenshot=True):
        """
        Executes the collecting sequence on
        one mail item

        Args:
            item (Item):
            skip_first_screenshot (bool):
        """
        logger.hr('Mail collect one')
        btn = item._button
        click_timer = Timer(1.5, count=3)
        self.interval_clear([MAIL_COLLECT, GET_ITEMS_1, GET_ITEMS_2])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if click_timer.reached():
                if not self._mail_selected(btn):
                    self.device.click(btn.move((350, 0)))
                    click_timer.reset()
                    continue
            if self.appear_then_click(MAIL_COLLECT, offset=(20, 20), interval=3):
                click_timer.reset()
                continue
            if self.appear(GET_ITEMS_1, offset=(30, 30), interval=1):
                self.device.click(MAIL_COLLECT)
                click_timer.reset()
                continue
            if self.appear(GET_ITEMS_2, offset=(30, 30), interval=1):
                self.device.click(MAIL_COLLECT)
                click_timer.reset()
                continue
            if self.handle_info_bar():
                click_timer.reset()
                continue

            # End
            if self.appear(MAIL_COLLECTED, offset=(20, 20)):
                break

    def _mail_collect(self, skip_first_screenshot=True):
        """
        Executes the collecting sequence to
        applicable mail items

        Args:
            skip_first_screenshot (bool):
        """
        logger.hr('Mail collect', level=2)
        for _ in range(5):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            collectable = self._mail_get_collectable()
            if not collectable:
                break

            self._mail_collect_one(collectable[0])

        logger.info('Finished collecting all applicable mail')

    def mail_run(self, delete=False):
        """
        Collects mail rewards

        Args:
            delete (bool):
        """
        logger.info('Mail run')

        if self._mail_enter(delete):
            self._mail_collect()
            self._mail_exit()
        else:
            self._mail_exit()

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        self.ui_goto(page_main)
        self.mail_run(delete=self.config.Mail_Delete)
