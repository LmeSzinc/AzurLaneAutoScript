from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.exception import ScriptError
from module.logger import logger
from module.map_detection.utils import Points
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

    def check_selected(self, image):
        """
        Args:
            image (PIL.Image.Image): Screenshot
        """
        area = self.button.area
        check_area = tuple([area[0], area[3] + 2, area[2], area[3] + 4])
        im = np.array(image.crop(check_area).convert('L'))
        return True if np.mean(im) > 127 else False
        
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

    def choose(self, tier_max, tier_min, exp=True):
        """
        Args:
            tier_max (int): Max tier to choose, 1 to 3.
            tier_min (int): Min tier to choose, 1 to 3.
            exp (bool): True to choose books with exp bonus, False to choose other books in the same tier.

        Returns:
            Book:
        """
        tier = tier_max
        while tier >= tier_min:
            books = self.select(tier=tier)
            books_with_exp = books.select(exp=True)
            tier -= 1

            if exp and not books_with_exp:
                continue
            if books_with_exp:
                books = books_with_exp
            if books:
                logger.attr('Book_choose', books[0])
                return books[0]

        logger.info('No book choose')
        return None


class RewardTacticalClass(UI):
    def _tactical_animation_running(self):
        """
        Detect the white dash line under student cards.
        If student learning in progress or position haven't been unlocked, there will be a white line under the card.
        The card with animation running, white line become gray.

        Returns:
            bool: If showing skill points increasing animation.
        """
        # Area of the white line under student cards.
        area = (360, 680, 1280, 700)
        mask = color_similarity_2d(self.image_area(area), color=(255, 255, 255)) > 235
        points = np.array(np.where(mask)).T
        # Width of card is 200 px
        points = Points(points).group(threshold=210)
        card = len(points)
        if card == 0:
            logger.warning('No student card found.')
            return False
        elif card == 3:
            return True
        elif card == 4:
            return False
        else:
            logger.warning(f'Unexpected amount of student cards: {card}')
            return False

    def _tactical_books_get(self):
        """
        Get books. Handle loadings, wait 10 times at max.
        When TACTICAL_CLASS_START appears, game may stuck in loading, wait and retry detection.
        If loading still exists, raise ScriptError.

        Returns:
            BookGroup:

        Pages:
            in: TACTICAL_CLASS_START
            out: TACTICAL_CLASS_START
        """
        for n in range(10):
            self.device.screenshot()
            self.handle_info_bar()  # info_bar appears when get ship in Launch Ceremony commissions
            books = BookGroup([Book(self.device.image, button) for button in BOOKS_GRID.buttons]).select(valid=True)
            logger.attr('Book_count', len(books))
            for index in range(1, 4):
                logger.info(f'Book_T{index}: {books.select(tier=index)}')

            # End
            if books:
                return books
            else:
                self.device.sleep(3)
                continue

        logger.warning('No book found.')
        raise ScriptError('No book found, after 10 attempts.')

    def _tactical_books_choose(self):
        """
        Choose tactical book according to config.
        """
        books = self._tactical_books_get()
        book = books.choose(tier_max=self.config.TACTICAL_BOOK_TIER_MAX,
                            tier_min=self.config.TACTICAL_BOOK_TIER_MIN,
                            exp=self.config.TACTICAL_EXP_FIRST)

        if book is not None:
            while 1:
                self.device.click(book.button)
                self.device.screenshot()
                if book.check_selected(self.device.image):
                    break
            self.device.click(TACTICAL_CLASS_START)
        else:
            # cancel_tactical, use_the_first_book
            if self.config.TACTICAL_IF_NO_BOOK_SATISFIED == 'use_the_first_book':
                logger.info('Choose first book')
                self.device.click(books[0].button)
                self.device.sleep((0.3, 0.5))
                self.device.click(TACTICAL_CLASS_START)
            else:
                logger.info('Cancel tactical')
                self.device.click(TACTICAL_CLASS_CANCEL)

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
        tactical_class_timout = Timer(10, count=10).start()
        tactical_animation_timer = Timer(2, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REWARD_2, interval=1):
                tactical_class_timout.reset()
                continue
            if self.handle_popup_confirm():
                tactical_class_timout.reset()
                continue
            if self.handle_urgent_commission(save_get_items=False):
                # Only one button in the middle, when skill reach max level.
                tactical_class_timout.reset()
                continue
            if self.appear(TACTICAL_CLASS_CANCEL, offset=(30, 30), interval=2) \
                    and self.appear(TACTICAL_CLASS_START, offset=(30, 30)):
                self.device.sleep(0.3)
                self._tactical_books_choose()
                self.interval_reset(TACTICAL_CLASS_CANCEL)
                tactical_class_timout.reset()
                continue

            # End
            if self.appear(TACTICAL_CHECK, offset=(20, 20)):
                self.ui_current = page_tactical
                if not self._tactical_animation_running():
                    if tactical_animation_timer.reached():
                        logger.info('Tactical reward end.')
                        break
                else:
                    tactical_animation_timer.reset()
            if tactical_class_timout.reached():
                logger.info('Tactical reward timeout.')
                break

        self.ui_goto(page_reward, skip_first_screenshot=True)
        return True

    def handle_tactical_class(self):
        """
        Returns:
            bool: If rewarded.
        """
        if not self.config.ENABLE_TACTICAL_REWARD:
            return False

        return self._tactical_class_receive()
