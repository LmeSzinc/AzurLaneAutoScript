"""
Read real emotion values from the dorm ship management panel.

Why this panel
    One-step navigation, just click the pill at the bottom-left of the dorm main
    page, with a fixed 6-slot grid and no ship name recognition required.
    The dock needs 4 steps instead (enter dock, filter, select emotion, confirm)
    and its card order changes with the sort setting.

Recover speed is the ground truth of floor and oath
    The value shown in game matches DIC_RECOVER exactly, floor 1 is 40, floor 2
    is 50 and oath adds 10, so the selected tab gives the floor and the speed
    gives the oath status. Users don't need to register any ship by hand.

Coordinates
    Frozen constants measured on 1280x720 screenshots, they live in
    module.dorm.dorm_emotion_assets, see docs for the raw data. The panel layout
    is fixed and independent of client language, so pure coordinates are used
    here and no template PNG is needed.

Pages:
    in: Any page
    out: Same page as in
"""
import numpy as np

from module.base.timer import Timer
from module.base.utils import crop
from module.dorm.dorm_emotion_assets import (
    DORM_EXP_CONFIRM,
    DORM_SHIP_PANEL_ENTER,
    DORM_SHIP_PANEL_HEADER,
    DORM_SHIP_PANEL_QUIT,
    DORM_SHIP_PANEL_TAB_REST,
    DORM_SHIP_PANEL_TAB_TRAIN,
    DORM_SHIP_SLOT_BACKGROUND,
    MOOD_MAX,
    OCR_DORM_SHIP_MOOD,
    OCR_DORM_SHIP_SPEED,
    RECOVER_SPEEDS,
    SLOT_BACKGROUND_THRESHOLD,
    SLOT_COUNT,
    is_dorm_panel_opened,
)
from module.exception import GamePageUnknownError, RequestHumanTakeover
from module.logger import logger
from module.ui.assets import DORM_GOTO_MAIN
from module.ui.page import page_dorm
from module.ui.ui import UI

class DormShip:
    """
    Emotion snapshot of a ship in one dorm slot.

    Args:
        slot (int): 0 to 5
        floor (str): dormitory_floor_1, dormitory_floor_2
        mood (int): 0 to 150
        speed (int): Recover speed shown in game, 40, 50 or 60
    """

    def __init__(self, slot, floor, mood, speed):
        self.slot = slot
        self.floor = floor
        self.mood = mood
        self.speed = speed

    @property
    def oath(self):
        """
        Whether the ship is oathed, deduced from recover speed.

        Returns:
            bool: True if speed reaches the oathed value of this floor.
        """
        # Imported here to avoid a circular import between
        # module.combat.emotion and module.dorm
        from module.combat.emotion import DIC_RECOVER, OATH_RECOVER
        return self.speed >= DIC_RECOVER[self.floor] + OATH_RECOVER

    def __str__(self):
        return (f'DormShip(slot={self.slot}, floor={self.floor}, '
                f'mood={self.mood}, speed={self.speed}/h, oath={self.oath})')

    __repr__ = __str__


class DormEmotionReader(UI):
    """
    Read emotion values from the dorm ship management panel.

    Navigation is included here instead of assumed done, because the low emotion
    popup handler, which is the next task, will call this while the game is
    stuck on a popup and we can't know which page it is on.
    """

    def dorm_panel_slot_status(self):
        """
        Sample the background of every slot.

        Returns:
            list[int]: Median of slot background, 0 to 255.

        Pages:
            in: DORM_SHIP_PANEL_QUIT
        """
        return [int(np.median(crop(self.device.image, area)))
                for area in DORM_SHIP_SLOT_BACKGROUND]

    def dorm_exp_popup_appear(self, interval=0):
        """
        Whether the dorm exp popup is on screen.

        The popup shows up when the dorm ships have rested for a while, it
        reports the food eaten and the exp gained and waits for a confirm.
        Its background is translucent, which fools both the page detection and
        the slot backgrounds, so it has to be dismissed everywhere.

        Args:
            interval (int): Seconds to wait before detecting it again.

        Returns:
            bool:

        Pages:
            in: Any page
        """
        return self.appear(DORM_EXP_CONFIRM, offset=(30, 30), similarity=0.75, interval=interval)

    def dorm_exp_popup_handle(self):
        """
        Dismiss the dorm exp popup if it is on screen.

        Returns:
            bool: If the popup was found and clicked.

        Pages:
            in: Any page
        """
        # Throttled, the popup needs a moment to close and we don't want to
        # click the same button a dozen times a second
        if not self.dorm_exp_popup_appear(interval=2):
            return False
        logger.info('Dorm exp popup, confirm')
        self.device.click(DORM_EXP_CONFIRM)
        return True

    def dorm_panel_appear(self):
        """
        Whether the ship panel is opened.

        Three checks, all of them have to pass. The exp popup comes first, its
        translucent background lands in the empty slot range and would be read
        as an opened panel. Slot backgrounds alone are not enough either, a page
        that happens to have six grey areas where the slots sit passes them too,
        so the dark panel header is asked for as a second opinion.

        Every check matters because the caller of this is the popup hook of
        ui_goto, a false positive there clicks a close button on an unrelated
        page and throws the navigation away.

        Returns:
            bool:

        Pages:
            in: page_dorm
        """
        if self.dorm_exp_popup_appear():
            return False
        if not is_dorm_panel_opened(self.dorm_panel_slot_status()):
            return False
        return self.appear(DORM_SHIP_PANEL_HEADER, threshold=50)

    def dorm_panel_enter(self):
        """
        Enter dorm and open the ship panel.

        The exp popup can show up right after arriving at the dorm, dismiss it
        before looking for the panel, its background would be read as a panel
        that is already opened and the entrance click would be skipped.

        Returns:
            bool: If panel opened.

        Pages:
            in: Any page
            out: DORM_SHIP_PANEL_QUIT
        """
        logger.hr('Dorm ship panel enter')
        self.ui_goto(page_dorm, skip_first_screenshot=True)
        self.handle_info_bar()

        timeout = Timer(5, count=4).start()
        click = Timer(1, count=2).start()
        while 1:
            self.device.screenshot()

            # Give a fresh window, dismissing the popup costs a second or two
            if self.dorm_exp_popup_handle():
                timeout.reset()
                click.reset()
                continue
            if self.dorm_panel_appear():
                return True
            if timeout.reached():
                logger.warning('Dorm ship panel did not appear')
                return False
            if click.reached():
                self.device.click(DORM_SHIP_PANEL_ENTER)
                click.reset()

    def dorm_panel_tab_switch(self, button):
        """
        Switch to another tab of the panel.

        Clicking the already selected tab has no side effect, so callers can
        simply click both tabs instead of detecting which one is active.

        Args:
            button (Button): DORM_SHIP_PANEL_TAB_TRAIN, DORM_SHIP_PANEL_TAB_REST

        Pages:
            in: DORM_SHIP_PANEL_QUIT
        """
        self.device.click(button)
        self.device.sleep((0.3, 0.5))
        self.device.screenshot()

    def dorm_panel_click_until_closed(self, button, timeout):
        """
        Keep clicking a button until the ship panel is closed.

        The exp popup is handled first on every loop, it may show up on top of
        the panel while it is being read.

        Args:
            button (Button): Button that closes the panel.
            timeout (float): Seconds to keep trying.

        Returns:
            bool: If panel closed.

        Pages:
            in: DORM_SHIP_PANEL_QUIT
        """
        timer = Timer(timeout, count=int(timeout) + 3).start()
        click = Timer(1, count=2).start()
        while 1:
            self.device.screenshot()

            if self.dorm_exp_popup_handle():
                timer.reset()
                click.reset()
                continue
            if not self.dorm_panel_appear():
                return True
            if timer.reached():
                return False
            if click.reached():
                self.device.click(button)
                click.reset()

    def dorm_panel_quit(self):
        """
        Close the ship panel, leaving the game in the dorm main page.

        The close button is the only way out on a normal client. The dorm back
        arrow is a second chance for a client whose panel header is laid out
        elsewhere, it is drawn above the panel and dismisses it as well.

        Returns:
            bool: If panel closed.

        Pages:
            in: DORM_SHIP_PANEL_QUIT
            out: page_dorm
        """
        if self.dorm_panel_click_until_closed(DORM_SHIP_PANEL_QUIT, timeout=4):
            return True

        logger.warning('Dorm ship panel close button missed, try the dorm back arrow')
        if self.dorm_panel_click_until_closed(DORM_GOTO_MAIN, timeout=4):
            return True

        logger.warning('Dorm ship panel close timeout')
        return False

    def ui_additional(self, get_ship=True):
        """
        Extend the Alas hook that handles popups during page switching.

        Alas calls this on every loop of ui_goto, so anything dismissed here
        heals the navigation. Both the exp popup and a ship panel left opened
        are modal, they hide the check button of every page and ui_goto spins
        forever with no log at all. A ship panel is checked here as well
        because the panel closing logic can be fooled by a single frame taken
        while the popup fades in.

        Args:
            get_ship (bool):

        Returns:
            bool: If something was clicked.

        Pages:
            in: Any page
        """
        if self.dorm_exp_popup_handle():
            return True

        if self.dorm_panel_appear():
            logger.info('Dorm ship panel is still opened, close it')
            if self.dorm_panel_quit():
                return True

        return super().ui_additional(get_ship=get_ship)

    def _dorm_panel_parse_slot(self, index, background, mood, speed, floor):
        """
        Convert the OCR results of one slot into a ship.

        Args:
            index (int): Slot index, 0 to 5
            background (int): Median of slot background
            mood (int): OCR result of mood
            speed (int): OCR result of recover speed
            floor (str): Floor of the current tab

        Returns:
            DormShip, None: None if the slot is empty or OCR result is invalid.
        """
        if background > SLOT_BACKGROUND_THRESHOLD:
            return None
        if not 0 <= mood <= MOOD_MAX:
            logger.warning(f'Dorm slot {index} invalid mood: {mood}')
            return None
        # Recover speed can only be 40, 50 or 60, use it to filter misreads
        if speed not in RECOVER_SPEEDS:
            logger.warning(f'Dorm slot {index} invalid recover speed: {speed}')
            return None
        return DormShip(slot=index, floor=floor, mood=mood, speed=speed)

    def _dorm_panel_read(self, floor):
        """
        Read all slots of the current tab.

        Args:
            floor (str): Floor of the current tab.

        Returns:
            list[DormShip]:

        Pages:
            in: DORM_SHIP_PANEL_QUIT
        """
        if not self.dorm_panel_appear():
            logger.warning(f'Dorm panel not appeared when reading {floor}')
            return []

        backgrounds = self.dorm_panel_slot_status()
        moods = OCR_DORM_SHIP_MOOD.ocr(self.device.image)
        speeds = OCR_DORM_SHIP_SPEED.ocr(self.device.image)

        ships = []
        for index in range(SLOT_COUNT):
            ship = self._dorm_panel_parse_slot(
                index, backgrounds[index], moods[index], speeds[index], floor=floor)
            if ship is not None:
                ships.append(ship)

        logger.info(f'Dorm {floor}: {len(ships)} ship(s) ' +
                    ', '.join(f'#{s.slot} mood={s.mood} speed={s.speed}/h' for s in ships))
        return ships

    def dorm_ship_emotion_get(self, origin=None):
        """
        Read every ship in dorm, both floors.

        Errors are swallowed on purpose, callers fall back to the calculated
        value when this returns an empty list.

        The game is always put back on the page it was on, because callers
        continue their own navigation right after this. The ship panel and the
        exp popup are modal, they make every page unknown to Alas, so leaving
        one opened breaks the whole scheduler instead of only this reading.

        Args:
            origin (Page, None): Page to go back to. None to detect it here,
                which requires the game to be on a known page.

        Returns:
            list[DormShip]: Ships in dorm, empty if failed.

        Pages:
            in: Any page
            out: Same page as in
        """
        if origin is None:
            try:
                origin = self.ui_get_current_page()
            except GamePageUnknownError:
                logger.warning('Unknown ui page, skip dorm emotion read')
                return []
        logger.info(f'Dorm emotion read, the game will be put back on {origin}')

        ships = []
        try:
            if self.dorm_panel_enter():
                # Click both tabs so that we don't rely on which one opens by default
                self.dorm_panel_tab_switch(DORM_SHIP_PANEL_TAB_TRAIN)
                ships += self._dorm_panel_read(floor='dormitory_floor_1')
                self.dorm_panel_tab_switch(DORM_SHIP_PANEL_TAB_REST)
                ships += self._dorm_panel_read(floor='dormitory_floor_2')
            else:
                logger.warning('Dorm ship panel did not appear, keep calculated value')
        except Exception as e:
            logger.exception(e)
            logger.warning('Dorm emotion read failed, keep calculated value')

        if not self.dorm_panel_quit():
            logger.critical('Dorm ship panel can not be closed, please close it manually')
            raise RequestHumanTakeover
        self.ui_goto(origin, skip_first_screenshot=True)

        return ships


def read_dorm_emotion(config, device, origin=None):
    """
    Read emotion of every ship in dorm.

    Args:
        config (AzurLaneConfig):
        device (Device):
        origin (Page, None): Page to go back to after reading. None to detect
            it inside, which requires the game to be on a known page.

    Returns:
        list[DormShip]: Ships in dorm, empty if failed.
    """
    return DormEmotionReader(config, device).dorm_ship_emotion_get(origin=origin)
