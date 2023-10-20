import re

import numpy as np

from module.base.filter import MultiLangFilter
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter, Ocr, OcrResultButton
from module.ocr.utils import split_and_pair_buttons
from tasks.rogue.assets.assets_rogue_blessing import *
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.bleesing.preset import *
from tasks.rogue.bleesing.selector import RogueSelector
from tasks.rogue.bleesing.utils import get_regex_from_keyword_name, is_card_selected, parse_name
from tasks.rogue.keywords import *

# normal blessing filter
# path name
pattern = ""
BLESSING_FILTER_ATTR = tuple()
PATH_ATTR_NAME = 'path_name'
path_regex = get_regex_from_keyword_name(RoguePath, PATH_ATTR_NAME)
pattern += path_regex
# remove 'the' in path 'the hunt'
pattern = pattern.lower().replace('the', '')
BLESSING_FILTER_ATTR += (PATH_ATTR_NAME,)

# rarity
pattern += "([123])?-?"
BLESSING_FILTER_ATTR += ("rarity",)

# blessing name
BLESSING_ATTR_NAME = 'blessing_name'
blessing_regex = get_regex_from_keyword_name(RogueBlessing, BLESSING_ATTR_NAME)
pattern += blessing_regex
BLESSING_FILTER_ATTR += (BLESSING_ATTR_NAME,)

# enhanced
ENHANCEMENT_ATTR_NAME = "enhancement"
enhancement_regex = get_regex_from_keyword_name(RogueEnhancement, "enhancement_keyword")
pattern += enhancement_regex
BLESSING_FILTER_ATTR += (ENHANCEMENT_ATTR_NAME,)

FILETER_REGEX = re.compile(pattern)
BLESSING_FILTER_PRESET = ("reset", "random", "unrecorded")
BLESSING_FILTER = MultiLangFilter(FILETER_REGEX, BLESSING_FILTER_ATTR, BLESSING_FILTER_PRESET)

# resonance filter
RESONANCE_ATTR_NAME = 'resonance_name'
pattern = get_regex_from_keyword_name(RogueResonance, RESONANCE_ATTR_NAME)

FILETER_REGEX = re.compile(pattern)
RESONANCE_FILTER_PRESET = ("random", "unrecorded")
RESONANCE_FILTER = MultiLangFilter(FILETER_REGEX, (RESONANCE_ATTR_NAME,), RESONANCE_FILTER_PRESET)


class RogueBuffOcr(Ocr):
    merge_thres_x = 40
    merge_thres_y = 20

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'cn':
            replace_pattern_dict = {
                "蓬失": "蓬矢",
                "柘弓危失": "柘弓危矢",
                "飞虹珠?凿?齿": "飞虹诛凿齿",
                "天[培梧]步危": "天棓步危",
                "云[摘销锅]?逐步离": "云镝逐步离",
                "制桑": "制穹桑",
                "乌号[綦基]?箭?": "乌号綦箭",
                "流岚追摩?物": "流岚追孽物",
                "特月": "狩月",
                "彤弓素.*": "彤弓素矰",
                "白决射御": "白矢决射御",
                "苦表": "苦衷",
                "[沦沧][決]?肌髓": "沦浃肌髓",
                "进发": "迸发",
                "永缩体": "永坍缩体",
                "完美体验：[绒]?默": "完美体验：缄默",
                "[涯]?灭回归不等式": "湮灭回归不等式",
                r".*灾$": "禳灾",
                "虚安供品": "虚妄供品",
                "原初的苦$": "原初的苦衷",
                "厌离邪[移]?苦": "厌离邪秽苦",
                r".*繁.*": "葳蕤繁祉，延彼遐龄",
                "回馈底护": "回馈庇护",
            }
        elif self.lang == 'en':
            replace_pattern_dict = {
                "RestIin": "Restin",
            }
        else:
            replace_pattern_dict = {}
        for pat, replace in replace_pattern_dict.items():
            result = re.sub(pat, replace, result)
        return result


class RogueBlessingSelector(RogueSelector):
    """
    Usage:
        self = RogueBlessingSelector('alas')
        self.device.screenshot()
        self.recognize_and_select()
    """

    def get_blessing_count(self) -> int:
        """
        Returns: The number of blessing
        """
        if not self.main.image_color_count(BOTTOM_WHITE_BAR.area, color=(255, 255, 255), count=5000):
            return 0
        color = get_color(self.main.device.image, BOTTOM_WHITE_BAR.area)
        mean = np.mean(color)
        return int(mean // 60)  # the magic number that maps blessing num with mean_color

    def recognition(self):
        def not_enhancement_keyword(keyword):
            return keyword != KEYWORDS_ROGUE_ENHANCEMENT.Already_Enhanced

        self.ocr_results = []
        self._wait_until_blessing_loaded()
        ocr = RogueBuffOcr(OCR_ROGUE_BUFF)
        results = ocr.matched_ocr(self.main.device.image,
                                  [RogueBlessing, RogueResonance, RogueEnhancement])

        enhanced_blessing = [result for result, _ in
                             split_and_pair_buttons(results, split_func=not_enhancement_keyword,
                                                    relative_area=(-300, -720, 0, 0))]
        results = [result for result in results if not_enhancement_keyword(result)]
        blessing_count = self.get_blessing_count()
        if blessing_count != len(results):
            logger.warning(f"The OCR result does not match the blessing count. "
                           f"Expect {blessing_count}, but recognized {len(results)} only.")
        for result in results:
            if result in enhanced_blessing:
                result.matched_keyword.enhancement = KEYWORDS_ROGUE_ENHANCEMENT.Already_Enhanced.enhancement_keyword
        self.ocr_results = results
        return results

    def ui_select(self, target: OcrResultButton | None, skip_first_screenshot=True):
        """
        Select buff once. Multiple calls needed if there's more than one time to choose
        It might occur that all listed blessings are not recognized
        So this method provides a hard code way to choose one, which fit in case when blessing num is 1-3
        """

        def is_select_blessing_complete():
            """
                Case 1: back to main page
                Case 2: choose curio
                Case 3: another choose blessings, but no blessing is selected when the new selection page loaded
                Case 4: event ui
            """
            if self.main.is_in_main():
                logger.info("Main page checked")
                return True
            if self.main.is_page_choose_curio():
                logger.info("Choose curio page checked")
                return True
            if self.main.is_page_choose_blessing() and not is_card_selected(self.main, target, BLESSING_CONFIRM):
                logger.info("A new choose blessing page checked")
                return True
            if self.main.is_page_event():
                logger.info("Event page checked")
                return True
            return False

        interval = Timer(1)
        enforce = False

        if not target:
            enforce = True

        # start -> selected
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_card_selected(self.main, target, confirm_button=BLESSING_CONFIRM):
                if enforce:
                    logger.info("Buff selected (enforce)")
                else:
                    logger.info(f"Buff {target} selected")
                break
            if interval.reached():
                if enforce:
                    self.main.device.click(BLESSING_ENFORCE)
                else:
                    self.main.device.click(target)
                interval.reset()

        skip_first_screenshot = True
        # Avoid double-clicking
        interval = Timer(3, count=6)
        # selected -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_select_blessing_complete():
                logger.info("Select blessing complete")
                break
            if self.main.handle_popup_confirm():
                continue
            if interval.reached():
                self.main.device.click(BLESSING_CONFIRM)
                interval.reset()

    def _get_reset_count(self):
        current, _, _ = DigitCounter(OCR_RESET_COUNT).ocr_single_line(self.main.device.image)
        return current

    def _wait_until_blessing_loaded(self, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        timer.reset()
        timeout.reset()
        previous_count = self.get_blessing_count()
        while 1:
            self.main.device.screenshot()
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
        if not self.main.is_page_choose_blessing():
            return False

        reset_count = self._get_reset_count()
        if not reset_count:
            logger.info("Does not have enough reset count")
            return False

        reset_cost = Digit(OCR_RESET_COST).ocr_single_line(self.main.device.image)
        if reset_cost > self.main.cosmic_fragment:
            logger.info("Does not have enough cosmic fragment")
            return False

        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            new_count = self._get_reset_count()

            if reset_count - new_count == 1:
                logger.info("Reset once")
                break
            if interval.reached():
                self.main.device.click(BLESSING_RESET)
                interval.reset()
        return True

    def load_filter(self):
        try:
            keyword = self.ocr_results[0].matched_keyword
        except IndexError:
            return
        if not isinstance(keyword, (RogueBlessing, RogueResonance)):
            return
        filter_configs = {
            RogueBlessing: {
                "filter_": BLESSING_FILTER,
                "preset_config": self.main.config.RogueBlessing_PresetBlessingFilter,
                "strategy_config": self.main.config.RogueBlessing_BlessingSelectionStrategy,
                "preset_values": {
                    'preset-1': BLESSING_PRESET_1,
                    'custom': self.main.config.RogueBlessing_CustomBlessingFilter
                },
            },
            RogueResonance: {
                "filter_": RESONANCE_FILTER,
                "preset_config": self.main.config.RoguePath_PresetResonanceFilter,
                "strategy_config": self.main.config.RoguePath_ResonanceSelectionStrategy,
                "preset_values": {
                    'preset-1': RESONANCE_PRESET_1,
                    'custom': self.main.config.RoguePath_PresetResonanceFilter,
                },
            }
        }
        # preset
        config = filter_configs[type(keyword)]
        filter_ = config['filter_']
        preset_config = config['preset_config']
        preset_values = config['preset_values']
        string = preset_values[preset_config]
        string = parse_name(string)

        # strategy
        if not string.endswith('random'):
            string += '> random'
        strategy_config = config['strategy_config']
        if strategy_config == 'unrecorded-first':
            string = "unrecorded > " + string
        if strategy_config == 'before-random':
            string = string.replace('random', 'unrecorded > random')

        filter_.load(string)
        self.filter_ = filter_

    def try_select(self, option: OcrResultButton | str):
        if isinstance(option, str):
            if option.lower() == 'reset':
                if self.reset_blessing_list():
                    self.recognize_and_select()
                    return True
            if option.lower() == 'random':
                choose = np.random.choice(self.ocr_results)
                self.ui_select(choose)
                return True
            if option.lower() == 'unrecorded':
                for result in self.ocr_results:
                    if self.main.is_unrecorded(result, (0, -720, 300, 0)):
                        self.ui_select(result)
                        return True
                return False

        if isinstance(option, OcrResultButton):
            self.ui_select(option)
            return True
        return False
