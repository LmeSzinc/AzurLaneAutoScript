import re
from datetime import datetime

from module.base.button import Button, ButtonGrid
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import *
from module.exception import ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.map_detection.utils import Points
from module.ocr.ocr import Duration
from module.tactical.assets import *
from module.ui.assets import TACTICAL_CHECK, REWARD_GOTO_TACTICAL
from module.ui.ui import UI, page_tactical, page_reward

BOOKS_GRID = ButtonGrid(origin=(239, 288), delta=(140, 120), button_shape=(98, 98), grid_shape=(6, 2))
BOOK_FILTER = Filter(
    regex=re.compile(
        '(same)?'
        '(red|blue|yellow)?'
        '-?'
        '(t[123])?'
    ),
    attr=('same_str', 'genre_str', 'tier_str'),
    preset=('first',)
)


class Book:
    color_genre = {
        1: (214, 69, 74),  # Offensive, red
        2: (115, 178, 255),  # Defensive, blue
        3: (247, 190, 99),  # Support, yellow
    }
    genre_name = {
        1: 'Red',  # Offensive, red
        2: 'Blue',  # Defensive, blue
        3: 'Yellow',  # Support, yellow
    }
    color_tier = {
        1: (104, 181, 238),  # T1, blue
        2: (151, 129, 203),  # T2, purple
        3: (235, 208, 120),  # T3, gold
        4: (225, 181, 212),  # T4, rainbow
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
        self.genre_str = self.genre_name.get(self.genre, "unknown")
        self.tier_str = f'T{self.tier}' if self.tier else 'Tn'
        self.same_str = 'same' if self.exp else 'unknown'

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
        # Example: Red_T3_Exp
        text = f'{self.genre_str}_{self.tier_str}'
        if self.exp:
            text += '_Exp'
        return text


class RewardTacticalClass(UI):
    books: SelectedGrids
    tactical_finish = []

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

    def _tactical_books_get(self, skip_first_screenshot=True):
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
        prev = SelectedGrids([])
        for n in range(1, 16):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self.handle_info_bar()  # info_bar appears when get ship in Launch Ceremony commissions

            books = SelectedGrids([Book(self.device.image, button) for button in BOOKS_GRID.buttons]).select(valid=True)
            self.books = books
            logger.attr('Book_count', books.count)
            logger.attr('Books', str(books))

            # End
            if books and books.count == prev.count:
                return books
            else:
                prev = books
                if n % 3 == 0:
                    self.device.sleep(3)
                continue

        logger.warning('No book found.')
        raise ScriptError('No book found, after 15 attempts.')

    def _tactical_books_choose(self):
        """
        Choose tactical book according to config.

        Pages:
            in: TACTICAL_CLASS_START
            out: Unknown, may TACTICAL_CLASS_START, page_tactical, or _tactical_animation_running
        """
        self._tactical_books_get()
        BOOK_FILTER.load(self.config.Tactical_TacticalFilter)
        books = BOOK_FILTER.apply(self.books.grids)
        logger.attr('Book_sort', ' > '.join([str(book) for book in books]))

        if len(books):
            book = books[0]
            if str(book) != 'first':
                while 1:
                    self.device.click(book.button)
                    self.device.screenshot()
                    if book.check_selected(self.device.image):
                        break
                self.device.click(TACTICAL_CLASS_START)
            else:
                logger.info('Choose first book')
                self.device.click(books[0].button)
                self.device.sleep((0.3, 0.5))
                self.device.click(TACTICAL_CLASS_START)
        else:
            logger.info('Cancel tactical')
            self.device.click(TACTICAL_CLASS_CANCEL)

    def _tactical_get_finish(self):
        """
        Get the future finish time.
        """
        logger.hr('Tactical get finish')
        grids = ButtonGrid(
            origin=(421, 596), delta=(223, 0), button_shape=(139, 27), grid_shape=(4, 1), name='TACTICAL_REMAIN')
        is_running = [self.image_color_count(button, color=(148, 255, 99), count=50) for button in grids.buttons]
        logger.info(f'Tactical status: {["running" if s else "empty" for s in is_running]}')

        buttons = [b for b, s in zip(grids.buttons, is_running) if s]
        ocr = Duration(buttons, letter=(148, 255, 99), name='TACTICAL_REMAIN')
        remains = ocr.ocr(self.device.image)
        remains = [remains] if not isinstance(remains, list) else remains

        now = datetime.now()
        self.tactical_finish = [(now + remain).replace(microsecond=0) for remain in remains if remain.total_seconds()]
        logger.info(f'Tactical finish: {[str(f) for f in self.tactical_finish]}')

    def _tactical_class_receive(self, skip_first_screenshot=True):
        """
        Receive tactical rewards and fill books.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward, TACTICAL_CLASS_START
            out: page_tactical
        """
        logger.hr('Tactical class receive', level=1)
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
            if self.appear_then_click(REWARD_GOTO_TACTICAL, offset=(20, 20), interval=1):
                tactical_class_timout.reset()
                continue
            if self.handle_popup_confirm():
                tactical_class_timout.reset()
                continue
            if self.handle_urgent_commission():
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

        return True

    def run(self):
        """
        Pages:
            in: Any
            out: page_tactical
        """
        self.ui_ensure(page_reward)

        if self.appear(REWARD_2, offset=(50, 20)):
            self._tactical_class_receive()
            self._tactical_get_finish()
        else:
            logger.info('No tactical class reward.')
            self.ui_goto(page_tactical, skip_first_screenshot=True)
            self._tactical_get_finish()

        # Can't stay in page_tactical
        # There will be popups after tactical finished
        self.ui_goto(page_reward)

        if self.tactical_finish:
            self.config.task_delay(target=self.tactical_finish)
        else:
            logger.info('No tactical running')
            self.config.task_delay(success=False)
