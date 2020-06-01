import numpy as np
from scipy import signal

from module.base.button import Button, ButtonGrid
from module.base.timer import Timer, time_range_active
from module.base.utils import area_offset, get_color, color_similar, color_similarity_2d
from module.exception import ScriptError
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.reward.assets import *
from module.ui.assets import TACTICAL_CHECK
from module.ui.ui import UI, page_tactical, page_reward

GENRE_NAME_DICT = {
    1: 'Offensive',  # red
    2: 'Defensive',  # blue
    3: 'Support',  # yellow
}
BOOKS_GRID = ButtonGrid(origin=(239, 288), delta=(140, 120), button_shape=(98, 98), grid_shape=(6, 2))


class Book:
    color_genre = {
        1: (214, 69, 74),  # Offensive, red
        2: (115, 178, 255),  # Defensive, blue
        3: (247, 190, 99),  # Support, yellow
    }
    color_tier = {
        1: (104, 181, 238),  # T1, blue
        2: (151, 129, 203),  # T2, purple
        3: (235, 208, 120),  # T3, gold
    }

    def __init__(self, image, button):
        """
        Args:
            image (PIL.Image.Image):
            button (Button):
        """
        image = image.crop(button.area)
        self.button = button

        self.genre = 0
        color = get_color(image, (65, 35, 72, 42))
        for key, value in self.color_genre.items():
            if color_similar(color1=color, color2=value, threshold=30):
                self.genre = key

        self.tier = 0
        color = get_color(image, (83, 61, 92, 70))
        for key, value in self.color_tier.items():
            if color_similar(color1=color, color2=value, threshold=30):
                self.tier = key

        color = color_similarity_2d(image.crop((15, 0, 97, 13)), color=(148, 251, 99))
        self.exp = bool(np.sum(color > 221) > 50)

        self.valid = bool(self.genre and self.tier)

    def __str__(self):
        # Example: Defensive_T3_Exp
        text = f'{GENRE_NAME_DICT.get(self.genre, "Unknown")}_T{self.tier}'
        if self.exp:
            text += '_Exp'
        return text


class BookGroup:
    def __init__(self, books):
        """
        Args:
            books (list[Book]):
        """
        self.books = books

    def __iter__(self):
        return iter(self.books)

    def __len__(self):
        return len(self.books)

    def __bool__(self):
        return len(self.books) > 0

    def __getitem__(self, item):
        return self.books[item]

    def __str__(self):
        # return str([str(grid) for grid in self])
        return '[' + ', '.join([str(grid) for grid in self]) + ']'

    def select(self, **kwargs):
        """
        Args:
            **kwargs: Attributes of Grid.

        Returns:
            SelectedGrids:
        """
        result = []
        for grid in self.books:
            flag = True
            for k, v in kwargs.items():
                if grid.__getattribute__(k) != v:
                    flag = False
            if flag:
                result.append(grid)

        return BookGroup(result)

    def add(self, books):
        """
        Args:
            books(BookGroup):

        Returns:
            BookGroup:
        """
        return BookGroup(self.books + books.books)

    def choose(self, tier, exp=True):
        """
        Args:
            tier (int): Max tier to choose.
            exp (bool): True to choose books with exp bonus, False to choose other books in the same tier.

        Returns:
            Book:
        """
        while 1:
            books = self.select(tier=tier)
            tier -= 1
            books_with_exp = books.select(exp=True)
            if exp and not books_with_exp:
                continue
            if books_with_exp:
                books = books_with_exp
            if books:
                logger.attr('Book_choose', books[0])
                return books[0]

            # End
            if tier <= 0:
                break

        logger.warning('No book choose, return first book.')
        return self[0]


class RewardTacticalClass(UI, InfoHandler):
    tactical_animation_timer = Timer(2, count=3)

    def _tactical_animation_running(self):
        """
        Returns:
            bool: If showing skill points increasing animation.
        """
        color_height = np.mean(self.device.image.crop((922, 0, 1036, 720)).convert('L'), axis=1)
        parameters = {'height': 200}
        peaks, _ = signal.find_peaks(color_height, **parameters)
        peaks = [y for y in peaks if y > 67 + 243]

        if not len(peaks):
            logger.warning('No student card found.')
        for y in peaks:
            student_area = (447, y - 243, 1244, y)
            area = area_offset((677, 172, 761, 183), student_area[0:2])
            # Normal: 160, In skill-increasing animation: 109
            if np.mean(get_color(self.device.image, area)) < 135:
                return True

        return False

    def _tactical_books_choose(self):
        """
        Choose tactical book according to config.
        """
        books = BookGroup([Book(self.device.image, button) for button in BOOKS_GRID.buttons()]).select(valid=True)
        logger.attr('Book_count', len(books))
        for index in range(1, 4):
            logger.info(f'Book_T{index}: {books.select(tier=index)}')
        if not books:
            logger.warning('No book found.')
            raise ScriptError('No book found.')

        if not time_range_active(self.config.TACTICAL_NIGHT_RANGE):
            tier = self.config.TACTICAL_BOOK_TIER
            exp = self.config.TACTICAL_EXP_FIRST
        else:
            tier = self.config.TACTICAL_BOOK_TIER_NIGHT
            exp = self.config.TACTICAL_EXP_FIRST_NIGHT
        book = books.choose(tier=tier, exp=exp)

        self.device.click(book.button)
        self.device.sleep((0.3, 0.5))

    def _tactical_class_receive(self, skip_first_screenshot=True):
        """Remember to make sure current page is page_reward before calls.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: If rewarded.
        """
        if not self.appear(REWARD_2):
            logger.info('No tactical class reward.')
            return False

        logger.hr('Tactical class receive')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REWARD_2, interval=1):
                continue
            if self.handle_popup_confirm():
                continue
            if self.handle_urgent_commission(save_get_items=False):
                # Only one button in the middle, when skill reach max level.
                continue
            if self.appear(TACTICAL_CLASS_CANCEL, offset=(30, 30), interval=2) \
                    and self.appear(TACTICAL_CLASS_START, offset=(30, 30)):
                self.device.sleep(0.3)
                self.device.screenshot()
                self._tactical_books_choose()
                self.device.click(TACTICAL_CLASS_START)
                self.interval_reset(TACTICAL_CLASS_CANCEL)
                continue

            # End
            if self.appear(TACTICAL_CHECK, offset=(20, 20)):
                self.ui_current = page_tactical
                if not self._tactical_animation_running():
                    if self.tactical_animation_timer.reached():
                        logger.info('Tactical reward end.')
                        break
                else:
                    self.tactical_animation_timer.reset()

        self.ui_goto(page_reward, skip_first_screenshot=True)
        return True

    def handle_tactical_class(self):
        """
        Returns:
            bool: If rewarded.
        """
        if not self.config.ENABLE_TACTICAL_REWARD:
            return False

        self._tactical_class_receive()

        return True
