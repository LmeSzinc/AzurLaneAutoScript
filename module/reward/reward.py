import numpy as np
import re

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import crop, rgb2gray
from module.combat.assets import *
from module.logger import logger
from module.reward.assets import *
from module.statistics.item import ItemGrid
from module.ui.navbar import Navbar
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

class Reward(UI):
    def reward_receive(self, oil, coin, exp, skip_first_screenshot=True):
        """
        Args:
            oil (bool):
            coin (bool):
            exp (bool):
            skip_first_screenshot (bool):

        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward
            out: page_reward, with info_bar if received
        """
        if not oil and not coin and not exp:
            return False

        logger.hr('Reward receive')
        logger.info(f'oil={oil}, coin={coin}, exp={exp}')
        confirm_timer = Timer(1, count=3).start()
        # Set click interval to 0.3, because game can't respond that fast.
        click_timer = Timer(0.3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if oil and click_timer.reached() and self.appear_then_click(OIL, interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue
            if coin and click_timer.reached() and self.appear_then_click(COIN, interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue
            if exp and click_timer.reached() and self.appear_then_click(EXP, interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue

            # End
            if confirm_timer.reached():
                break

        logger.info('Reward receive end')
        return True

    def _reward_mission_collect(self, interval=1):
        """
        Streamline handling of mission rewards for
        both 'all' and 'weekly' pages

        Args:
            interval (int): Configure the interval for
                            assets involved

        Returns:
            bool, if encountered at least 1 GET_ITEMS_*
        """
        # Reset any existing interval for the following assets
        self.interval_clear([GET_ITEMS_1, GET_ITEMS_2,
                             MISSION_MULTI, MISSION_SINGLE,
                             GET_SHIP])

        # Basic timers for certain scenarios
        exit_timer = Timer(2)
        click_timer = Timer(1)
        timeout = Timer(10)
        exit_timer.start()
        timeout.start()

        reward = False
        while 1:
            self.device.screenshot()

            for button in [GET_ITEMS_1, GET_ITEMS_2]:
                if self.appear_then_click(button, offset=(30, 30), interval=interval):
                    exit_timer.reset()
                    timeout.reset()
                    reward = True
                    continue

            for button in [MISSION_MULTI, MISSION_SINGLE]:
                if not click_timer.reached():
                    continue
                if self.appear(button, offset=(0, 200), interval=interval) \
                        and button.match_appear_on(self.device.image):
                    self.device.click(button)
                    exit_timer.reset()
                    click_timer.reset()
                    timeout.reset()
                    continue

            if not self.appear(MISSION_CHECK):
                if self.appear_then_click(GET_SHIP, interval=interval):
                    exit_timer.reset()
                    click_timer.reset()
                    timeout.reset()
                    continue

            if self.handle_mission_popup_ack():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            # Story
            if self.handle_vote_popup():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue
            if self.story_skip():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            if self.handle_popup_confirm('MISSION_REWARD'):
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            # End
            if reward and exit_timer.reached():
                break
            if timeout.reached():
                logger.warning('Wait get items timeout.')
                break

        return reward

    def _reward_mission_all(self):
        """
        Collects all page mission rewards

        Returns:
            bool, if handled
        """
        self.reward_side_navbar_ensure(upper=1)

        if not self.appear(MISSION_MULTI) and \
                not self.appear(MISSION_SINGLE):
            return False

        # Uses default interval to account for
        # behavior differences and avoid
        # premature exit
        return self._reward_mission_collect()

    def _reward_mission_weekly(self):
        """
        Collects weekly page mission rewards

        Returns:
            bool, if handled
        """
        if not self.appear(MISSION_WEEKLY_RED_DOT):
            return False

        self.reward_side_navbar_ensure(upper=5)

        # Uses no interval to account for
        # behavior differences and avoid
        # premature exit
        return self._reward_mission_collect(interval=0)

    def reward_mission(self, daily=True, weekly=True):
        """
        Collects mission rewards

        Args:
            daily (bool): If collect daily rewards
            weekly (bool): If collect weekly rewards

        Returns:
            bool: If rewarded.

        Pages:
            in: page_main
            out: page_mission
        """
        if not daily and not weekly:
            return False
        logger.hr('Mission reward')
        if not self.appear(MISSION_NOTICE):
            logger.info('No mission reward')
            return False
        else:
            logger.info('Found mission reward notice')

        self.ui_goto(page_mission, skip_first_screenshot=True)

        reward = False
        if daily:
            reward |= self._reward_mission_all()
        if weekly:
            reward |= self._reward_mission_weekly()

        return reward

    def _reward_mail_enter(self, skip_first_screenshot=True):
        """
        Goes to mail page
        Also deletes viewed mails to ensure the relevant
        row entries are in view

        Args:
            skip_first_screenshot (bool):
        """
        deleted = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(page_main.check_button, offset=(30, 30), interval=3):
                self.device.click(MAIL_ENTER)
                continue
            if not deleted:
                if self.appear_then_click(MAIL_DELETE, offset=(350, 20), interval=3):
                    continue
                if self.handle_popup_confirm('MAIL_DELETE'):
                    deleted = True
                    continue
            else:
                if self.appear(MAIL_DELETE, offset=(350, 20), interval=3):
                    btn = MAIL_BUTTON_GRID.buttons[0].move((350, 0))
                    self.device.click(btn)
                    continue
            if self.handle_info_bar():
                continue

            # End
            if deleted and self.appear(MAIL_COLLECT, offset=(20, 20)):
                break

    def _reward_mail_exit(self, skip_first_screenshot=True):
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

            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                continue
            if self.appear_then_click(GET_ITEMS_2, offset=(30, 30), interval=1):
                continue
            if self.appear(MAIL_DELETE, offset=(350, 20), interval=3):
                self.device.click(MAIL_ENTER)
                continue

            # End
            if self.appear(page_main.check_button, offset=(30, 30)):
                break

    @cached_property
    def _reward_mail_grid(self):
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

    def _reward_mail_get_collectable(self):
        """
        Loads filter and scans the items in the mail grid
        then returns a subset of those that are collectable

        Returns:
            list[Item]
        """
        FILTER.load(self.config.Reward_MailFilter.strip())
        items = self._reward_mail_grid.predict(
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

    def _reward_mail_selected(self, button, image):
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

    def _reward_mail_collect_one(self, item, skip_first_screenshot=True):
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
                if not self._reward_mail_selected(btn, self.device.image):
                    self.device.click(btn.move((350, 0)))
                    self.device.sleep((0.3, 0.5))
                    click_timer.reset()
                    continue
                click_timer.reset()
            if self.appear_then_click(MAIL_COLLECT, offset=(20, 20), interval=3):
                click_timer.reset()
                continue
            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                click_timer.reset()
                continue
            if self.appear_then_click(GET_ITEMS_2, offset=(30, 30), interval=1):
                click_timer.reset()
                continue

            # End
            if self.appear(MAIL_COLLECTED, offset=(20, 20)):
                break

        return True

    def _reward_mail_collect(self, skip_first_screenshot=True):
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

            collectable = self._reward_mail_get_collectable()
            if not collectable:
                break

            self._reward_mail_collect_one(collectable[0])

        logger.info('Finished collecting all applicable mail')

    def reward_mail(self, collect):
        """
        Collects mail rewards

        Args:
            collect (bool):

        Returns:
            bool
        """
        if not collect:
            return False
        logger.info('Mail reward')

        self._reward_mail_enter()
        result = self._reward_mail_collect()
        self._reward_mail_exit()
        return result


    @cached_property
    def _reward_side_navbar(self):
        """
        side_navbar options:
           all.
           main.
           side.
           daily.
           weekly.
           event.
        """
        reward_side_navbar = ButtonGrid(
            origin=(21, 118), delta=(0, 94.5),
            button_shape=(60, 75), grid_shape=(1, 6),
            name='REWARD_SIDE_NAVBAR')

        return Navbar(grids=reward_side_navbar,
                      active_color=(247, 255, 173),
                      inactive_color=(140, 162, 181))

    def reward_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page
        Whether page has completely loaded is handled
        separately and optionally

        Args:
            upper (int):
                1  for all.
                2  for main.
                3  for side.
                4  for daily.
                5  for weekly.
                6  for event.
            bottom (int):
                6  for all.
                5  for main.
                4  for side.
                3  for daily.
                2  for weekly.
                1  for event.

        Returns:
            bool: if side_navbar set ensured
        """
        if self._reward_side_navbar.set(self, upper=upper, bottom=bottom):
            return True
        return False

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main or page_mission, may have info_bar
        """
        self.ui_ensure(page_reward)
        self.reward_receive(
            oil=self.config.Reward_CollectOil,
            coin=self.config.Reward_CollectCoin,
            exp=self.config.Reward_CollectExp)
        self.ui_goto(page_main)
        self.reward_mission(daily=self.config.Reward_CollectMission,
                            weekly=self.config.Reward_CollectWeeklyMission)
        self.ui_goto(page_main)
        self.reward_mail(collect=self.config.Reward_CollectMail)
        self.config.task_delay(success=True)
