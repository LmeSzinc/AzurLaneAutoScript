from datetime import datetime

import module.config.server as server
from module.base.button import Button, ButtonGrid
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import *
from module.combat.level import LevelOcr
from module.config.utils import get_server_next_update
from module.exception import ScriptError
from module.handler.assets import GET_MISSION, MISSION_POPUP_ACK, MISSION_POPUP_GO, POPUP_CANCEL, POPUP_CONFIRM
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import DigitCounter, Duration, Ocr
from module.retire.assets import DOCK_CHECK, DOCK_EMPTY, SHIP_CONFIRM
from module.retire.dock import CARD_GRIDS, CARD_LEVEL_GRIDS, Dock
from module.tactical.assets import *
from module.ui.assets import (BACK_ARROW, REWARD_CHECK, REWARD_GOTO_TACTICAL, TACTICAL_CHECK)
from module.ui.page import page_reward
from module.ui_white.assets import REWARD_2_WHITE, REWARD_GOTO_TACTICAL_WHITE

SKILL_GRIDS = ButtonGrid(origin=(315, 140), delta=(621, 132), button_shape=(621, 119), grid_shape=(1, 3), name='SKILL')
if server.server != 'jp':
    SKILL_LEVEL_GRIDS = SKILL_GRIDS.crop(area=(406, 98, 618, 116), name='EXP')
else:
    SKILL_LEVEL_GRIDS = SKILL_GRIDS.crop(area=(406, 98, 621, 118), name='EXP')


class ExpOnBookSelect(DigitCounter):
    def pre_process(self, image):
        # Image is like `NEXT:1900+500/5800`, 500 is green and others are in white

        # Find green letters
        hsv = rgb2hsv(image)
        h = (60, 180)
        s = (50, 100)
        v = (50, 100)
        lower = (h[0], s[0], v[0])
        upper = (h[1], s[1], v[1])
        green = np.mean(cv2.inRange(hsv, lower, upper), axis=0)
        # Convert to gray scale
        r, g, b = cv2.split(image)
        image = cv2.max(cv2.max(r, g), b)
        # Paint `+500` to white
        matched = np.where(green > 0.5)[0]
        if len(matched):
            image[:, matched[0] - 8:matched[-1] + 2] = 0

        image = 255 - image

        # Strip `Next:`
        if server.server == 'en':
            # Bold `Next:`
            image = image_left_strip(image, threshold=105, length=46)
        elif server.server == 'jp':
            # Wide `Next:`
            image = image_left_strip(image, threshold=105, length=55)
        else:
            image = image_left_strip(image, threshold=105, length=42)
        return image

    def after_process(self, result):
        result = super().after_process(result)

        if '/' not in result:
            for exp in [5800, 4400, 3200, 2200, 1400, 800, 400, 200, 100]:
                res = re.match(rf'^(\d+){exp}$', result)
                if res:
                    # 10005800 -> 1000/5800
                    new = f'{res.group(1)}/{exp}'
                    logger.info(f'ExpOnBookSelect result {result} is revised to {new}')
                    result = new
                    break

        return result


class ExpOnSkillSelect(Ocr):
    def pre_process(self, image):
        # Convert to gray scale
        r, g, b = cv2.split(image)
        image = cv2.max(cv2.max(r, g), b)

        image = 255 - image

        # Strip `Next:`
        if server.server == 'en':
            # Bold `Next:`
            image = image_left_strip(image, threshold=105, length=46)
        elif server.server == 'jp':
            # Wide `Next:`
            image = image_left_strip(image, threshold=105, length=53)
        else:
            image = image_left_strip(image, threshold=105, length=42)
        return image


SKILL_EXP = ExpOnBookSelect(buttons=OCR_SKILL_EXP)
BOOKS_GRID = ButtonGrid(origin=(213, 292), delta=(147, 117), button_shape=(98, 98), grid_shape=(6, 2))
BOOK_FILTER = Filter(
    regex=re.compile(
        '(same)?'
        '(red|blue|yellow)?'
        '-?'
        '(t[1234])?'
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
    exp_tier = {
        0: 0,
        1: 100,
        2: 300,
        3: 800,
        4: 1500,
    }

    def __init__(self, image, button):
        """
        Args:
            image (np.ndarray):
            button (Button):
        """
        image = crop(image, button.area, copy=False)
        self.button = button

        # During the test of 40 random screenshots,
        # when the threshold range is 50-70, the test can all pass,
        # but it must not exceed 75, otherwise the rainbow will be recognized as purple
        self.genre = 0
        color = get_color(image, (65, 35, 72, 42))
        for key, value in self.color_genre.items():
            if color_similar(color1=color, color2=value, threshold=50):
                self.genre = key

        self.tier = 0
        color = get_color(image, (83, 61, 92, 70))
        for key, value in self.color_tier.items():
            if color_similar(color1=color, color2=value, threshold=50):
                self.tier = key

        color = color_similarity_2d(crop(image, (15, 0, 97, 13), copy=False), color=(148, 251, 99))
        self.exp = bool(np.sum(color > 221) > 50)

        self.valid = bool(self.genre and self.tier)
        self.genre_str = self.genre_name.get(self.genre, "unknown")
        self.tier_str = f'T{self.tier}' if self.tier else 'Tn'
        self.same_str = 'same' if self.exp else 'unknown'

        factor = 1 if not self.exp else 1.5 if self.tier < 4 else 2
        self.exp_value = self.exp_tier[self.tier] * factor

    def check_selected(self, image):
        """
        Args:
            image (np.ndarray): Screenshot
        """
        area = self.button.area
        check_area = tuple([area[0], area[3] + 2, area[2], area[3] + 4])
        im = rgb2gray(crop(image, check_area, copy=False))
        return True if np.mean(im) > 127 else False

    def __str__(self):
        # Example: Red_T3_Exp
        text = f'{self.genre_str}_{self.tier_str}'
        if self.exp:
            text += '_Exp'
        return text


class RewardTacticalClass(Dock):
    books: SelectedGrids
    tactical_finish = []
    dock_select_index = 0

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
            if not self.appear(TACTICAL_CLASS_START, offset=(30, 30)):
                logger.info('Not in TACTICAL_CLASS_START anymore, exit')
                return False

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

    def _tactical_book_select(self, book, skip_first_screenshot=True):
        """
        Select the target book onscreen
        Updates current image if needed

        Args:
            book (Book):
            skip_first_screenshot (bool):
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not book.check_selected(self.device.image):
                self.device.click(book.button)
                self.device.sleep((0.3, 0.5))
            else:
                break

    def _tactical_books_filter_exp(self):
        """
        Complex filter to remove specific grade
        books from self.books based on current
        progress of the tactical skill.
        """
        # Read 'current' and 'remain' will be inaccurate
        # since first exp_value is factored into it
        current, remain, total = SKILL_EXP.ocr(self.device.image)

        # Max level in progress; so selective books
        # should be removed to prevent waste
        if total == 5800:
            logger.info('About to reach level 10; will remove '
                        'detected books based on actual '
                        f'progress: {current}/{total}; {remain}')

            def filter_exp_func(book):
                # Retain at least non-T1 bonus books if nothing else
                if book.exp_value == 100:
                    return True

                # Acquire 'overflow' for respective tier book if enabled
                overflow = 0
                if self.config.ControlExpOverflow_Enable:
                    overflow = getattr(self.config, f'ControlExpOverflow_T{book.tier}Allow')

                # Remove book if sum to be gained exceeds total (+ overflow)
                if (current + book.exp_value) > (total + overflow):
                    return False
                return True

            before = self.books.count
            self.books = SelectedGrids([book for book in self.books if filter_exp_func(book)])
            logger.attr('Filtered', before - self.books.count)
            logger.attr('Books', str(self.books))

    def _tactical_books_choose(self):
        """
        Choose tactical book according to config.

        Returns:
            int: If success

        Pages:
            in: TACTICAL_CLASS_START
            out: Unknown, may TACTICAL_CLASS_START, page_tactical, or _tactical_animation_running
        """
        logger.hr('Tactical books choose', level=2)
        if not self._tactical_books_get():
            return False

        self.device.click_record_clear()
        # Ensure first book is focused
        # For slow PCs, selection may have changed
        first = self.books[0]
        self._tactical_book_select(first)

        # Apply complex filter, modifies self.books
        self._tactical_books_filter_exp()

        # Apply configuration filter, does not modify self.books
        BOOK_FILTER.load(self.config.Tactical_TacticalFilter)
        books = BOOK_FILTER.apply(self.books.grids)
        logger.attr('Book_sort', ' > '.join([str(book) for book in books]))

        # Choose applicable book if any
        # Otherwise cancel altogether
        if len(books):
            book = books[0]
            if str(book) != 'first':
                self._tactical_book_select(book)
            else:
                logger.info('Choose first book')
                self._tactical_book_select(first)
            self.device.click(TACTICAL_CLASS_START)
        else:
            logger.info('Cancel tactical')
            self.device.click(TACTICAL_CLASS_CANCEL)
        return True

    def handle_rapid_training(self):
        """
        Returns:
            bool: If handled
        """
        slot = self.config.Tactical_RapidTrainingSlot
        if slot == 'slot_1':
            slot = 0
        elif slot == 'slot_2':
            slot = 1
        elif slot == 'slot_3':
            slot = 2
        elif slot == 'slot_4':
            slot = 3
        else:
            # do_not_use
            return False

        offset = (slot * 220 - 20, -20, slot * 220 + 20, 20)
        if self.appear(RAPID_TRAINING, offset=offset, interval=1):
            self.device.click(RAPID_TRAINING)
            return True

        return False

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
        return self.tactical_finish

    def tactical_class_receive(self, skip_first_screenshot=True):
        """
        Receive tactical rewards and fill books.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward, TACTICAL_CLASS_START
            out: page_reward
        """
        logger.hr('Tactical class receive', level=1)
        received = False
        study_finished = not self.config.AddNewStudent_Enable
        book_empty = False
        # tactical cards can't be loaded that fast, confirm if it's empty.
        empty_confirm = Timer(0.6, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if received and self.appear(REWARD_CHECK, offset=(20, 20)):
                break

            # Learn new skills
            if not study_finished and self.appear(TACTICAL_CHECK, offset=(20, 20)):
                # Tactical page, has empty position
                if self.appear_then_click(ADD_NEW_STUDENT, offset=(800, 20), interval=1):
                    self.interval_reset([TACTICAL_CHECK, RAPID_TRAINING])
                    self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_MISSION])
                    continue
            if self.handle_rapid_training():
                self.interval_reset(TACTICAL_CHECK)
                self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_MISSION])
                continue

            # Get finish time
            if self.appear(TACTICAL_CHECK, offset=(20, 20), interval=2):
                self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_MISSION])
                if book_empty:
                    self.device.click(BACK_ARROW)
                    self.interval_reset(TACTICAL_CHECK)
                    continue
                if self._tactical_get_finish():
                    self.device.click(BACK_ARROW)
                    self.interval_reset(TACTICAL_CHECK)
                    empty_confirm.reset()
                    received = True
                    continue
                else:
                    self.interval_clear(TACTICAL_CHECK)
                    if empty_confirm.reached():
                        self.device.click(BACK_ARROW)
                        empty_confirm.reset()
                        received = True
                        continue
            else:
                empty_confirm.reset()

            # Popups
            if self.appear_then_click(REWARD_2, offset=(20, 20), interval=3):
                self.interval_reset(REWARD_2_WHITE)
                continue
            if self.appear_then_click(REWARD_2_WHITE, offset=(20, 20), interval=3):
                self.interval_reset(REWARD_2)
                continue
            if self.appear_then_click(REWARD_GOTO_TACTICAL, offset=(20, 20), interval=3):
                self.interval_reset(REWARD_GOTO_TACTICAL_WHITE)
                continue
            if self.appear_then_click(REWARD_GOTO_TACTICAL_WHITE, offset=(20, 20), interval=3):
                self.interval_reset(REWARD_GOTO_TACTICAL)
                continue
            if self.ui_main_appear_then_click(page_reward, interval=3):
                continue
            if self.handle_popup_confirm('TACTICAL'):
                self.interval_reset([BOOK_EMPTY_POPUP])
                continue
            if self.handle_urgent_commission():
                # Only one button in the middle, when skill reach max level.
                continue
            if self.ui_page_main_popups():
                self.interval_reset([BOOK_EMPTY_POPUP])
                continue
            # Similar to handle_mission_popup_ack, but battle pass item expire popup has a different ACK button
            if self.appear(MISSION_POPUP_GO, offset=self._popup_offset, interval=2):
                self.device.click(MISSION_POPUP_ACK)
                continue
            if self.appear(TACTICAL_CLASS_CANCEL, offset=(30, 30), interval=2) \
                    and self.appear(TACTICAL_CLASS_START, offset=(30, 30)):
                if self._tactical_books_choose():
                    self.dock_select_index = 0
                    self.interval_reset([TACTICAL_CLASS_CANCEL, BOOK_EMPTY_POPUP])
                    self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_MISSION])
                else:
                    study_finished = True
                continue
            if self.appear(DOCK_CHECK, offset=(20, 20), interval=3):
                if self.dock_selected():
                    # When you click a ship from page_main -> dock,
                    # this ship will be selected default in tactical dock,
                    # so we need click BACK_ARROW to clear selected state
                    logger.info('Having pre-selected ship in dock, re-enter')
                    self.device.click(BACK_ARROW)
                    continue
                # If not enable or can not fina a suitable ship
                if self.config.AddNewStudent_Enable:
                    if self.select_suitable_ship():
                        pass
                    else:
                        study_finished = True
                        self.device.click(BACK_ARROW)
                else:
                    logger.info('Not going to learn skill but in dock, close it')
                    study_finished = True
                    self.device.click(BACK_ARROW)
                self.interval_reset([BOOK_EMPTY_POPUP])
                continue
            if self.appear(SKILL_CONFIRM, offset=(20, 20), interval=3):
                # If not enable or can not find a skill
                if self.config.AddNewStudent_Enable:
                    if self._tactical_skill_choose():
                        pass
                    else:
                        study_finished = True
                        self.device.click(BACK_ARROW)
                else:
                    logger.info('Not going to learn skill but having SKILL_CONFIRM, close it')
                    study_finished = True
                    self.device.click(BACK_ARROW)
                self.interval_reset([BOOK_EMPTY_POPUP])
                continue
            if self.appear(TACTICAL_META, offset=(200, 20), interval=3):
                # If meta's skill page, it's inappropriate
                logger.info('META skill found, exit')
                self.device.click(BACK_ARROW)
                # Select the next ship in `select_suitable_ship()`
                self.dock_select_index += 1
                # Avoid exit tactical between exiting meta skill to select new ship
                self.interval_reset([TACTICAL_CHECK, BOOK_EMPTY_POPUP])
                self.interval_clear(ADD_NEW_STUDENT)
                continue
            # No books
            if self.appear(BOOK_EMPTY_POPUP, offset=(20, 20), interval=3):
                self.device.click(BOOK_EMPTY_POPUP)
                study_finished = True
                received = True
                book_empty = True
                continue

        if book_empty:
            logger.warning('Tactical books empty, delay to tomorrow')
            self.tactical_finish = get_server_next_update(self.config.Scheduler_ServerUpdate)
            logger.info(f'Tactical finish: {self.tactical_finish}')
        return True

    def _tactical_skill_select(self, selected_skill, skip_first_screenshot=True):
        """
        Select the target skill onscreen
        Updates current image if needed

        Args:
            selected_skill: button
            skip_first_screenshot (bool):
        """
        logger.info('Tactical skill select')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not self.check_skill_selected(selected_skill, self.device.image):
                self.device.click(selected_skill)
                self.device.sleep((0.3, 0.5))
            else:
                break

    @staticmethod
    def check_skill_selected(button, image):
        area = button.area
        check_area = tuple([area[0], area[3] + 2, area[2], area[3] + 4])
        im = rgb2gray(crop(image, check_area, copy=False))
        return True if np.mean(im) > 127 else False

    def _tactical_skill_choose(self):
        """
        Choose a not full level skill.

        Returns:
            bool: Find or not

        Pages:
            in: SKILL_CONFIRM
            out: Unknown, may TACTICAL_CLASS_START, page_tactical
        """
        logger.hr('Tactical skill choose')
        selected_skill = self.find_not_full_level_skill()

        # If can't select a skill, think this ship no need study
        if selected_skill is None:
            logger.info('No available skill to learn')
            return False

        # If select a skill, think it not full level and should start or continue
        # Here should check selected or not
        self._tactical_skill_select(selected_skill)
        self.device.click(SKILL_CONFIRM)

        return True

    def select_suitable_ship(self):
        logger.hr(f'Select suitable ship')

        # reset filter
        self.dock_filter_set()

        # Set if favorite from config
        self.dock_favourite_set(enable=self.config.AddNewStudent_Favorite)

        # No ship in dock
        if self.appear(DOCK_EMPTY, offset=(30, 30)):
            logger.info('Dock is empty or favorite ships is empty')
            return False

        # Ship cards may slow to show, like:
        # [0, 0, 120, 120, 120, 120, 0, 0, 0, 0, 0, 0, 0, 0]
        # [12, 0, 0, 120, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # Wait until they turn into
        # [120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120]
        level_ocr = LevelOcr(CARD_LEVEL_GRIDS.buttons, name='DOCK_LEVEL_OCR', threshold=64)
        timeout = Timer(1, count=1).start()
        while 1:
            list_level = level_ocr.ocr(self.device.image)
            first_ship = next((i for i, x in enumerate(list_level) if x > 0), len(list_level))
            first_empty = next((i for i, x in enumerate(list_level) if x == 0), len(list_level))
            if timeout.reached():
                logger.warning('Wait ship cards timeout')
                break
            if first_empty >= first_ship:
                break
            self.device.screenshot()

        should_select_button = None
        for button, level in list(zip(CARD_GRIDS.buttons, list_level))[self.dock_select_index:]:
            # Select ship LV > 1 only
            if level > 1:
                should_select_button = button
                break

        if should_select_button is None:
            logger.info('No ships with level > 1 in dock')
            return False

        # select a ship
        self.dock_select_one(should_select_button, skip_first_screenshot=True)
        # Confirm selected ship
        # Clear interval if alas have just selected and exited from a meta skill
        self.interval_clear(SHIP_CONFIRM)

        # Removed the use of TACTICAL_SKILL_LIST, cause EN uses "Select skills"
        # in normal skill list but "Choose skills" in META skill list
        def check_button():
            if self.appear(SKILL_CONFIRM, offset=(30, 30)):
                return True
            if self.appear(TACTICAL_META, offset=(200, 30)):
                return True

        self.dock_select_confirm(check_button=check_button)

        return True

    def find_not_full_level_skill(self, skip_first_screenshot=True):
        """
        Check up to three skills in the list, find a skill whose level is not max

        Returns:
            Selected skill's button

        Pages:
            in: SKILL_CONFIRM
            out: SKILL_CONFIRM
        """

        if not skip_first_screenshot:
            self.device.screenshot()

        skill_level_ocr = ExpOnSkillSelect(buttons=SKILL_LEVEL_GRIDS.buttons, lang='cnocr', name='SKILL_LEVEL')
        skill_level_list = skill_level_ocr.ocr(self.device.image)
        for skill_button, skill_level in list(zip(SKILL_GRIDS.buttons, skill_level_list)):
            level = skill_level.upper().replace(' ', '')
            # Empty skill slot
            # Probably because all favourite ships have their skill leveled max.
            # '———l', '—l'
            if not level:
                continue
            if re.search(r'[—\-一]{2,}', level):
                continue
            if re.search(r'[—一]+', level):
                continue
            # Use 'MA' as a part of `MAX`.
            # SKILL_LEVEL_GRIDS may move a little lower for unknown reason, OCR results are like:
            # ['NEXT:MA', 'NEXT:/1D]', 'NEXT:MA'] (Actually: `NEXT:MAX, NEXT:0/100, NEXT:MAX`)
            # ['NEXT:MA', 'NEX T:/ 14[]]', 'NEXT:MA']  (Actually: `NEXT:MAX, NEXT:150/1400, NEXT:MAX`)
            if 'MA' not in level:
                logger.attr('LEVEL', 'EMPTY' if len(level) == 0 else level)
                return skill_button

        return None

    def run(self):
        """
        Pages:
            in: Any
            out: page_tactical
        """
        self.ui_ensure(page_reward)

        self.tactical_class_receive()

        if self.tactical_finish:
            self.config.task_delay(target=self.tactical_finish)
        else:
            logger.info('No tactical running')
            self.config.task_delay(success=False)
