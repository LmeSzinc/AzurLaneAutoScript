from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from tasks.rogue.assets.assets_rogue_path import *
from tasks.rogue.assets.assets_rogue_ui import ROGUE_LAUNCH
from tasks.rogue.blessing.ui import RogueUI
from tasks.rogue.exception import RogueTeamNotPrepared
from tasks.rogue.keywords import KEYWORDS_ROGUE_PATH, RoguePath


def area_pad_around(area, pad):
    """
    Inner offset an area.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        pad (tuple):

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    upper_left_x, upper_left_y, bottom_right_x, bottom_right_y = area
    upper_left_x_pad, upper_left_y_pad, bottom_right_x_pad, bottom_right_y_pad = pad
    return upper_left_x + upper_left_x_pad, \
           upper_left_y + upper_left_y_pad, \
           bottom_right_x - bottom_right_x_pad, \
           bottom_right_y - bottom_right_y_pad


class RoguePathHandler(RogueUI):
    @cached_property
    def _rogue_path_checks(self) -> dict[RoguePath, ButtonWrapper]:
        buttons = {
            KEYWORDS_ROGUE_PATH.Preservation: CHECK_PRESERVATION,
            KEYWORDS_ROGUE_PATH.Remembrance: CHECK_REMEMBRANCE,
            KEYWORDS_ROGUE_PATH.Nihility: CHECK_NIHILITY,
            KEYWORDS_ROGUE_PATH.Abundance: CHECK_ABUNDANCE,
            KEYWORDS_ROGUE_PATH.The_Hunt: CHECK_THE_HUNT,
            KEYWORDS_ROGUE_PATH.Destruction: CHECK_DESTRUCTION,
            KEYWORDS_ROGUE_PATH.Elation: CHECK_ELATION,
            KEYWORDS_ROGUE_PATH.Propagation: CHECK_PROPAGATION
        }
        return buttons

    @cached_property
    def _rogue_path_clicks(self) -> dict[RoguePath, ButtonWrapper]:
        buttons = {
            KEYWORDS_ROGUE_PATH.Preservation: CLICK_PRESERVATION,
            KEYWORDS_ROGUE_PATH.Remembrance: CLICK_REMEMBRANCE,
            KEYWORDS_ROGUE_PATH.Nihility: CLICK_NIHILITY,
            KEYWORDS_ROGUE_PATH.Abundance: CLICK_ABUNDANCE,
            KEYWORDS_ROGUE_PATH.The_Hunt: CLICK_THE_HUNT,
            KEYWORDS_ROGUE_PATH.Destruction: CLICK_DESTRUCTION,
            KEYWORDS_ROGUE_PATH.Elation: CLICK_ELATION,
        }
        # Path list is sliding, expand search area
        for b in buttons.values():
            b.load_search(area_pad_around(b.area, pad=(-100, -5, -100, -5)))
        return buttons

    def _get_path_click(self, path: RoguePath) -> ButtonWrapper:
        buttons = self._rogue_path_clicks
        if ret := buttons.get(path):
            return ret
        else:
            # choose the closest path
            paths = list(buttons.keys())
            path_click = min(paths, key=lambda p: abs(self._calculate_distance(p, path)))
            return buttons.get(path_click)

    @staticmethod
    def _calculate_distance(path_1: RoguePath, path_2: RoguePath):
        """
        click times from path1 to path2

        Returns:
            int: Positive value to click right,
                negative value to click left,
                0 to be the same.
        """
        length = len(path_1.instances)
        distance = path_1.id - path_2.id
        left_times = distance % length
        right_times = -distance % length
        if right_times <= left_times:
            return right_times
        else:
            return -left_times

    def _get_selected_path(self) -> RoguePath | None:
        for path, button in self._rogue_path_checks.items():
            # Check colors to wait appear animation
            if self.match_template_color(button):
                logger.attr('SelectedPath', path)
                return path
        logger.attr('SelectedPath', None)
        return None

    def _is_page_rogue_path(self) -> bool:
        appear = self.appear(PAGE_ROGUE_PATH)
        return appear

    def _is_team_prepared(self) -> bool:
        """
        Pages:
            in: is_page_rogue_launch()
        """
        slots = CHARACTER_EMPTY.match_multi_template(self.device.image)
        slots = 4 - len(slots)
        logger.attr('TeamSlotsPrepared', slots)
        return slots > 0

    def _change_confirm_path(self, path: RoguePath, skip_first_screenshot=True) -> bool:
        """
        Pages:
            in: CONFIRM_PATH
        """
        logger.info('Change confirm path')
        interval = Timer(2)
        timeout = Timer(10, count=20).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            selected_path = self._get_selected_path()
            # End
            if selected_path == path:
                logger.info('Selected to the right path')
                return True
            if timeout.reached():
                logger.warning(f'Unable to switch to path {path}, probably locked')
                return False
            # Click
            if selected_path is not None and interval.reached():
                diff = self._calculate_distance(selected_path, path)
                if diff > 0:
                    self.device.multi_click(CHOOSE_RIGHT, n=diff)
                    interval.reset()
                elif diff < 0:
                    self.device.multi_click(CHOOSE_LEFT, n=abs(diff))
                    interval.reset()
                else:
                    logger.warning(f'Invalid path distance: {diff}')

    def rogue_path_select(self, path: str | RoguePath, skip_first_screenshot=True):
        """
        Raises:
            RogueTeamNotPrepared:

        Pages:
            in: LAUNCH_ROGUE
            out: is_page_choose_bonus()
                or page_main if previous rogue run had bonus selected but didn't finish any domain
        """
        logger.hr('Rogue path select', level=2)
        path: RoguePath = RoguePath.find_name(path)
        logger.info(f'Select path: {path}')
        entry = self._get_path_click(path)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_page_choose_bonus():
                logger.info('rogue_path_select ended at is_page_choose_bonus')
                break
            if self.is_in_main():
                logger.info('rogue_path_select ended at page_main')
                break

            if self.appear(ROGUE_LAUNCH, interval=2):
                if not self._is_team_prepared():
                    raise RogueTeamNotPrepared
                self.device.click(ROGUE_LAUNCH)
                continue
            # The average level of your team is lower than the recommended level.
            # Continue anyway?
            if self.handle_popup_confirm():
                continue
            # Select path
            if self.interval_is_reached(entry, interval=2) and self._is_page_rogue_path():
                if self.appear_then_click(entry, interval=2):
                    self.interval_reset(entry, interval=2)
                    continue
            # Confirm path
            if self.appear(CONFIRM_PATH, interval=2):
                if self._change_confirm_path(path):
                    self.device.click(CONFIRM_PATH)
                    continue
