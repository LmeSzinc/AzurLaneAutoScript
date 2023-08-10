import re

import numpy as np

from dev_tools.keyword_extract import UI_LANGUAGES
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import area_offset
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton, DigitCounter
from tasks.rogue.assets.assets_rogue_blessing import *
from tasks.rogue.keywords import *
from tasks.rogue.preset import *
from tasks.rogue.ui import RogueUI

REGEX_PUNCTUATION = re.compile(r'[ ,.\'"“”，。:：!！?？·•—/()（）「」『』【】]')


def parse_name(n):
    n = REGEX_PUNCTUATION.sub('', str(n)).lower()
    return n


def get_regex_from_keyword_name(keyword, attr_name):
    regex_pat = ""
    attrs = tuple()
    for server in UI_LANGUAGES:
        string = ""
        for path in keyword.instances.values():
            string += f"{parse_name(getattr(path, server))}|"
        # some pattern contain each other, make sure each pattern end with "-" or the end of string
        regex_pat += f"(?:({string[:-1]})(?:-|$))?"
        attrs += (f"{attr_name}_{server}",)
    return regex_pat, attrs


# normal blessing
pattern = ""
BLESSING_FILTER_ATTR = tuple()
PATH_ATTR_NAME = 'path'
path_regex, path_attr = get_regex_from_keyword_name(RoguePath, PATH_ATTR_NAME)
pattern += path_regex
BLESSING_FILTER_ATTR += path_attr

pattern += "([123])?-?"
BLESSING_FILTER_ATTR += ("rarity",)
BLESSING_ATTR_NAME = 'blessing'
blessing_regex, blessing_attr = get_regex_from_keyword_name(RogueBlessing, BLESSING_ATTR_NAME)
pattern += blessing_regex
BLESSING_FILTER_ATTR += blessing_attr

FILETER_REGEX = re.compile(pattern)
BLESSING_FILTER_PRESET = ("reset", "same_path", "random")
BLESSING_FILTER = Filter(FILETER_REGEX, BLESSING_FILTER_ATTR, BLESSING_FILTER_PRESET)

# resonance
RESONANCE_ATTR_NAME = 'resonance'
pattern, RESONANCE_FILTER_ATTR = get_regex_from_keyword_name(RogueResonance, 'resonance')

FILETER_REGEX = re.compile(pattern)
RESONANCE_FILTER_PRESET = ("random",)
RESONANCE_FILTER = Filter(FILETER_REGEX, RESONANCE_FILTER_ATTR, RESONANCE_FILTER_PRESET)


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
                "苦表": "苦衷",
                "[沦沧]肌髓": "沦浃肌髓",
                "进发": "迸发",
                "永缩体": "永坍缩体",
            }
            for pattern, replace in replace_pattern_dict.items():
                result = re.sub(pattern, replace, result)
        return result


class RogueBlessingUI(RogueUI):
    def buffs_recognition(self):
        ocr = RogueBuffOcr(OCR_ROGUE_BUFF)
        results = ocr.matched_ocr(self.device.image, [RogueBlessing, RogueResonance])

        if results:
            logger.info(f"Buffs recognized: {len(results)}")
        else:
            logger.warning("No buff recognized")
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

    def wait_until_blessing_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait blessing page loaded timeout')
                return False
            if self.image_color_count(BLESSING_STABLE_FLAG, (255, 255, 255)):
                logger.info("Blessing page loaded")
                return True

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

    def apply_filter(self):
        paths = RoguePath.instances

        if not self.blessings:
            return []

        if isinstance(self.blessings[0].matched_keyword, RogueBlessing):
            for blessing in self.blessings:
                path = paths[blessing.matched_keyword.path_id]
                for server in UI_LANGUAGES:
                    setattr(blessing, f"{PATH_ATTR_NAME}_{server}", parse_name(getattr(path, server)))
                    setattr(blessing, f"{BLESSING_ATTR_NAME}_{server}",
                            parse_name(getattr(blessing.matched_keyword, server)))
                setattr(blessing, "rarity", getattr(blessing.matched_keyword, "rarity"))

            if self.config.Rogue_PresetBlessingFilter == 'preset-1':
                BLESSING_FILTER.load(parse_name(BLESSING_PRESET_1))
            if self.config.Rogue_PresetBlessingFilter == 'custom':
                BLESSING_FILTER.load(parse_name(self.config.Rogue_CustomBlessingFilter))

        if isinstance(self.blessings[0].matched_keyword, RogueResonance):
            if len(self.blessings) == 1:  # resonance can not be reset. So have not choice when there's only one option
                return self.blessings
            for blessing in self.blessings:
                for server in UI_LANGUAGES:
                    setattr(blessing, f"{RESONANCE_ATTR_NAME}_{server}",
                            parse_name(getattr(blessing.matched_keyword, server)))

            if self.config.Rogue_PresetResonanceFilter == 'preset-1':
                RESONANCE_FILTER.load(parse_name(RESONANCE_PRESET_1))
            if self.config.Rogue_PresetResonanceFilter == 'custom':
                RESONANCE_FILTER.load(parse_name(self.config.Rogue_CustomResonanceFilter))

        priority = BLESSING_FILTER.apply(self.blessings)
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
                if option.lower() == 'same_path':
                    chosen = False
                    for blessing in self.blessings:
                        if blessing.path_id == self.path.id:
                            self.ui_select_blessing(blessing)
                            chosen = True
                    if chosen:
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
