import re

import numpy as np

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import crop, rgb2gray
from module.combat.assets import *
from module.logger import logger
from module.mail.assets import *
from module.statistics.item import ItemGrid
from module.ui.page import *
from module.ui.ui import UI

MAIL_BUTTON_GRID = ButtonGrid(
    origin=(137, 207), delta=(0, 97),
    button_shape=(64, 64), grid_shape=(1, 3),
    name='MAIL_BUTTON_GRID')
FILTER_REGEX = re.compile(
    '^(cube|coin|oil|merit|gem)$',
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
        """
        btn = MAIL_BUTTON_GRID.buttons[0].move((350, 0))
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(page_main.check_button, offset=(30, 30), interval=3):
                self.device.click(MAIL_ENTER)
                continue
            if delete:
                if self.appear_then_click(MAIL_DELETE, offset=(350, 20), interval=3):
                    continue
                if self.handle_popup_confirm('MAIL_DELETE'):
                    delete = False
                    continue
            else:
                if self.appear(MAIL_DELETE, offset=(350, 20), interval=3):
                    self.device.click(btn)
                    continue
            if self.handle_info_bar():
                continue

            # End
            if not delete and self.appear(MAIL_COLLECT, offset=(20, 20)):
                break

    def _mail_exit(self, skip_first_screenshot=True):
        """
        Exits from mail page back into page_main

        Args:
            skip_first_screenshot (bool):
        """
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
            if self.appear(page_main.check_button, offset=(30, 30)):
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

    def _mail_selected(self, button, image):
        """
        Check if mail (button) is selected i.e.
        has bottom yellow border

        Args:
            button (Button):
            image (np.ndarray): Screenshot

        Returns:
            bool
        """
        area = button.area
        check_area = tuple([area[0], area[3] + 3, area[2], area[3] + 5])
        im = rgb2gray(crop(image, check_area))
        return True if np.mean(im) < 182 else False

    def _mail_collect_one(self, item, skip_first_screenshot=True):
        """
        Executes the collecting sequence on
        one mail item

        Args:
            item (Item):
            skip_first_screenshot (bool):
        """
        btn = item._button
        click_timer = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if click_timer.reached():
                if not self._mail_selected(btn, self.device.image):
                    self.device.click(btn.move((350, 0)))
                    click_timer.reset()
                    continue
                click_timer.reset()
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

    def mail_run(self, collect=True, delete=False):
        """
        Collects mail rewards

        Args:
            collect (bool):
            delete (bool):
        """
        if not collect:
            return False
        logger.info('Mail run')

        self._mail_enter(delete)
        self._mail_collect()
        self._mail_exit()

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        self.ui_goto(page_main)
        self.mail_run(collect=self.config.Mail_Collect,
                      delete=self.config.Mail_Delete)
        self.config.task_delay(success=True)
