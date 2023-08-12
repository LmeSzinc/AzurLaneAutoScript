import re

import numpy as np

from module.base.filter import MultiLangFilter
from module.base.timer import Timer
from module.base.utils import area_offset, get_color
from module.logger import logger
from module.ocr.keyword import Keyword
from module.ocr.ocr import Ocr, OcrResultButton, DigitCounter
from tasks.rogue.assets.assets_rogue_blessing import *
from tasks.rogue.assets.assets_rogue_ui import CONFIRM
from tasks.rogue.keywords import *
from tasks.rogue.preset import *
from tasks.rogue.ui import RogueUI
from tasks.rogue.utils import get_regex_from_keyword_name, parse_name

# normal blessing
pattern = ""
BLESSING_FILTER_ATTR = tuple()
PATH_ATTR_NAME = 'path_name'
path_regex = get_regex_from_keyword_name(RoguePath, PATH_ATTR_NAME)
pattern += path_regex
BLESSING_FILTER_ATTR += (PATH_ATTR_NAME,)

pattern += "([123])?-?"
BLESSING_FILTER_ATTR += ("rarity",)
BLESSING_ATTR_NAME = 'blessing_name'
blessing_regex = get_regex_from_keyword_name(RogueBlessing, BLESSING_ATTR_NAME)
pattern += blessing_regex
BLESSING_FILTER_ATTR += (BLESSING_ATTR_NAME,)

FILETER_REGEX = re.compile(pattern)
BLESSING_FILTER_PRESET = ("reset", "random")
BLESSING_FILTER = MultiLangFilter(FILETER_REGEX, BLESSING_FILTER_ATTR, BLESSING_FILTER_PRESET)

# resonance
RESONANCE_ATTR_NAME = 'resonance_name'
pattern = get_regex_from_keyword_name(RogueResonance, RESONANCE_ATTR_NAME)

FILETER_REGEX = re.compile(pattern)
RESONANCE_FILTER_PRESET = ("random",)
RESONANCE_FILTER = MultiLangFilter(FILETER_REGEX, (RESONANCE_ATTR_NAME,), RESONANCE_FILTER_PRESET)


class RogueBuffOcr(Ocr):
    merge_thres_x = 40

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            replace_pattern_dict = {
                "蓬失": "蓬矢",
                "柘弓危失": "柘弓危矢",
                "飞虹凿齿": "飞虹诛凿齿",
                "天培步危": "天棓步危",
                "云[摘销]": "云镝",
                "制桑": "制穹桑",
                "乌号基": "乌号綦",
                "追摩物": "追孽物",
                "特月": "狩月",
                "彤弓素增": "彤弓素矰",
                "白决射御": "白矢决射御",
                "苦表": "苦衷",
                "[沦沧]肌髓": "沦浃肌髓",
                "进发": "迸发",
                "永缩体": "永坍缩体",
                "完美体验：绒默": "完美体验：缄默",
                r"\w*灾$": "禳灾",
            }
            for pattern, replace in replace_pattern_dict.items():
                result = re.sub(pattern, replace, result)
        return result


class RogueBlessingUI(RogueUI):
    def get_blessing_count(self) -> int:
        """
        Returns: The number of blessing
        """
        color = get_color(self.device.image, BOTTOM_WHITE_BAR.area)
        mean = np.mean(color)
        return int(mean // 60)  # the magic number that maps blessing num with mean_color

    def buffs_recognition(self):
        self.wait_until_blessing_loaded()
        ocr = RogueBuffOcr(OCR_ROGUE_BUFF)
        results = ocr.matched_ocr(self.device.image, [RogueBlessing, RogueResonance])
        blessing_count = self.get_blessing_count()
        if blessing_count != len(results):
            logger.warning(f"The OCR result does not match the blessing count. "
                           f"Expect {blessing_count}, but recognized {len(results)} only.")
        self.blessings = results
        return results

    def ui_select_blessing(self, blessing: OcrResultButton | None, skip_first_screenshot=True, enforce=False):
        """
        Select buff once. Multiple calls needed if there's more than one time to choose
        It might occur that all listed blessings are not recognized
        So this method provides a hard code way to choose one, which fit in case when blessing num is 1-3
        """

        def is_blessing_selected():
            """
            There is a white border if a blessing is selected.
            """
            top_border = area_offset(blessing.area, (0, -180))
            return self.image_color_count(top_border, (255, 255, 255))

        def is_select_blessing_complete():
            """
                Case 1: back to main page
                Case 2: choose curio
                Case 3: another choose blessings, but no blessing is selected when the new selection page loaded
            """
            return (self.is_in_main() or self.is_page_choose_curio()
                    or (self.is_page_choose_blessing() and not is_blessing_selected()))

        interval = Timer(1)
        if not blessing:
            enforce = True

        # start -> selected
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if is_blessing_selected():
                if enforce:
                    logger.info("Buff selected (enforce)")
                else:
                    logger.info(f"Buff {blessing} selected")
                break
            if interval.reached():
                if enforce:
                    self.device.click(BLESSING_ENFORCE)
                else:
                    self.device.click(blessing)
                interval.reset()

        skip_first_screenshot = True
        # selected -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if is_select_blessing_complete():
                break
            if interval.reached():
                self.device.click(CONFIRM)
                interval.reset()

    def get_reset_count(self):
        current, _, _ = DigitCounter(OCR_RESET_COUNT).ocr_single_line(self.device.image)
        return current

    def wait_until_blessing_loaded(self, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        timer.reset()
        timeout.reset()
        previous_count = self.get_blessing_count()
        while 1:
            self.device.screenshot()
            blessing_count = self.get_blessing_count()

            if timeout.reached():
                logger.warning('Wait blessing page loaded timeout')
                break

            if previous_count and previous_count == blessing_count:
                if timer.reached():
                    logger.info('Blessing page stabled')
                    break
            else:
                previous_count = blessing_count
                timer.reset()

    def reset_blessing_list(self, skip_first_screenshot=True):
        if not self.is_page_choose_blessing():
            return False

        reset_count = self.get_reset_count()
        if not reset_count:
            return False

        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            new_count = self.get_reset_count()

            if reset_count - new_count == 1:
                logger.info("Reset once")
                break
            if interval.reached():
                self.device.click(BLESSING_RESET)
                interval.reset()
        return True


class RogueBlessingSelector(RogueBlessingUI):
    """
    Usage:
        self = RogueBlessingSelector('alas')
        self.device.screenshot()
        self.buff_recognition()
        self.select_blessing(self.)
    """

    def load_filter(self) -> MultiLangFilter:
        filter_ = None
        keyword = self.blessings[0].matched_keyword
        if isinstance(keyword, RogueBlessing):
            filter_ = BLESSING_FILTER
            if self.config.Rogue_PresetBlessingFilter == 'preset-1':
                filter_.load(parse_name(BLESSING_PRESET_1))
            if self.config.Rogue_PresetBlessingFilter == 'custom':
                filter_.load(parse_name(self.config.Rogue_CustomBlessingFilter))
        if isinstance(keyword, RogueResonance):
            if len(self.blessings) == 1:
                return filter_
            filter_ = RESONANCE_FILTER
            if self.config.Rogue_PresetResonanceFilter == 'preset-1':
                RESONANCE_FILTER.load(parse_name(RESONANCE_PRESET_1))
            if self.config.Rogue_PresetResonanceFilter == 'custom':
                RESONANCE_FILTER.load(parse_name(self.config.Rogue_CustomResonanceFilter))
        return filter_

    def apply_filter(self):
        def match_ocr_result(matched_keyword: Keyword):
            for blessing in self.blessings:
                if blessing.matched_keyword == matched_keyword:
                    return blessing
            return None

        if not self.blessings:
            return []

        filter_ = self.load_filter()
        if not filter_:
            return self.blessings
        blessing_keywords = [blessing.matched_keyword for blessing in self.blessings]
        priority = filter_.apply(blessing_keywords)
        priority = [option if isinstance(option, str) else match_ocr_result(option) for option in priority]
        return priority

    def select_blessing(self, priority: list):
        if not self.blessings:
            logger.info('No blessing recognized, randomly choose one')
            self.ui_select_blessing(None, enforce=True)
            return

        if not len(priority):
            logger.info('No blessing project satisfies current filter, randomly choose one')
            choose = np.random.choice(self.blessings)
            self.ui_select_blessing(choose)
            return

        for option in priority:
            # preset
            if isinstance(option, str):
                if option.lower() == 'reset':
                    if self.reset_blessing_list():
                        self.wait_until_blessing_loaded()
                        self.buffs_recognition()
                        self.select_blessing(self.apply_filter())
                        return
                    else:
                        continue
                if option.lower() == 'random':
                    choose = np.random.choice(self.blessings)
                    self.ui_select_blessing(choose)
                    return

            if isinstance(option, OcrResultButton):
                self.ui_select_blessing(option)
                return
