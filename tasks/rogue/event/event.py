import random
import re
from dataclasses import dataclass
from functools import cached_property

from pponnxcr.predict_system import BoxedResult

from module.base.button import ClickButton
from module.base.decorator import del_cached_property
from module.base.utils import area_limit, area_offset
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ui.scroll import Scroll
from tasks.rogue.assets.assets_rogue_event import *
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM, PAGE_EVENT
from tasks.rogue.bleesing.ui import RogueUI
from tasks.rogue.event.preset import STRATEGIES, STRATEGY_COMMON
from tasks.rogue.keywords import (KEYWORDS_ROGUE_EVENT_OPTION,
                                  KEYWORDS_ROGUE_EVENT_TITLE, RogueEventOption,
                                  RogueEventTitle)


@dataclass
class OptionButton:
    prefix_icon: ClickButton
    button: OcrResultButton = None
    is_valid: bool = True       # Option with requirements might be disabled
    is_bottom_page: bool = False

    def __str__(self) -> str:
        if self.button is not None:
            return str(self.button.matched_keyword)
        return super().__str__()


class OcrRogueEvent(Ocr):
    merge_thres_y = 5
    OCR_REPLACE = {
        'cn': [],
        'en': []
    }

    @cached_property
    def ocr_regex(self) -> re.Pattern | None:
        rules = self.OCR_REPLACE.get(self.lang)
        if not rules:
            return None
        return re.compile('|'.join(
            f'(?P<{kw.name}>{pat})'
            for kw, pat in rules
        ))

    def _after_process(self, result, keyword_class):
        result = super().after_process(result)
        if self.ocr_regex is None:
            return result
        matched = self.ocr_regex.fullmatch(result)
        if matched is None:
            return result
        matched = keyword_class.find(matched.lastgroup)
        matched = getattr(matched, self.lang)
        return matched


class OcrRogueEventTitle(OcrRogueEvent):
    OCR_REPLACE = {
        'cn': [
            (KEYWORDS_ROGUE_EVENT_TITLE.Rock_Paper_Scissors, '^猜拳.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Ka_ching_IPC_Banking_Part_1, '^咔.*其一.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Ka_ching_IPC_Banking_Part_2, '^咔.*其二.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Beast_Horde_Voracious_Catastrophe, '^兽群.*'),
        ],
        'en': [
            (KEYWORDS_ROGUE_EVENT_TITLE.Nomadic_Miners, '^Nomadic.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Nildis, '^Nildis.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Tavern, '^Tavern.*'),
            (KEYWORDS_ROGUE_EVENT_TITLE.Insights_from_the_Universal_Dancer, '.*Dancer$'),
        ]
    }

    def after_process(self, result):
        result = re.sub('卫[成戌]', '卫戍', result)
        return self._after_process(result, RogueEventTitle)


class OcrRogueEventOption(OcrRogueEvent):
    expected_options: list[OptionButton] = []
    OCR_REPLACE = {
        'cn': [
            # Special cases with placeholder
            (KEYWORDS_ROGUE_EVENT_OPTION.Deposit_2_Cosmic_Fragments_91, '存入\d+.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Withdraw_2_Cosmic_Fragments_91, '取出\d+.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Record_of_the_Aeon_of_1, '^关于.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.I_ll_buy_it, '我买下?了'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Wait_for_them, '^等待.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Choose_number_two_It_snores_like_Andatur_Zazzalo, '.*二号.*安达.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Choose_number_three_Its_teeth_are_rusted, '.*三号.*牙齿.*'),
        ],
        'en': [
            (KEYWORDS_ROGUE_EVENT_OPTION.Deposit_2_Cosmic_Fragments_91, 'Deposit \d+.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Withdraw_2_Cosmic_Fragments_91, 'Withdraw \d+.*'),
            (KEYWORDS_ROGUE_EVENT_OPTION.Record_of_the_Aeon_of_1,
             '^Record of the Aeon.*'),
        ]
    }

    def filter_detected(self, result: BoxedResult) -> bool:
        if not self.expected_options:
            return True
        right_bound = self.expected_options[0].prefix_icon.area[2]
        if result.box[0] < right_bound:
            return False
        return True

    def pre_process(self, image):
        # Mask starlike icons to avoid them to be recognized as */#/+/米
        offset = tuple(-x for x in self.button.area[:2])
        for option in self.expected_options:
            x1, y1, x2, y2 = area_offset(option.prefix_icon.area, offset)
            image[y1:y2, x1:x2] = (0, 0, 0)
        return image

    def after_process(self, result):
        return self._after_process(result, RogueEventOption)


class OptionScroll(Scroll):
    def position_to_screen(self, position, random_range=(-0.05, 0.05)):
        # This scroll itself can not be dragged, but OCR_OPTION.area can
        area = super().position_to_screen(position, random_range)
        confirm_width = self.area[0] - CHOOSE_OPTION_CONFIRM.button[0]
        area_width = CHOOSE_OPTION_CONFIRM.button[0] - OCR_OPTION.area[0]
        # A fixed offset is easy to fail for some reason
        random_offset = random.uniform(0.2, 0.8) * area_width + confirm_width
        area = area_offset(area, (-random_offset, 0))
        # Flip drag direction upside down
        return (
            area[0], self.area[1] + self.area[3] - area[1],
            area[2], self.area[1] + self.area[3] - area[3],
        )


SCROLL_OPTION = OptionScroll(OPTION_SCROLL, color=(
    219, 194, 145), name='SCROLL_OPTION')


class RogueEvent(RogueUI):
    event_title: RogueEventTitle = None
    options: list[OptionButton] = []

    @cached_property
    def valid_options(self) -> list[OptionButton]:
        return [x for x in self.options if x.is_valid]

    def handle_event_continue(self):
        if self.appear(PAGE_EVENT, interval=0.6):
            logger.info(f'{PAGE_EVENT} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        if self.appear_then_click(CHOOSE_STORY, interval=2):
            return True
        if self.appear_then_click(CHOOSE_OPTION_CONFIRM, interval=2):
            self.interval_reset([
                PAGE_EVENT,
                CHOOSE_STORY,
                CHOOSE_OPTION,
            ])
            return True

        return False

    def handle_event_option(self):
        """
        self.event_title SHOULD be set to None before calling this function

        Pages:
            in: page_rogue
        """
        self.options = []
        del_cached_property(self, 'valid_options')
        self._event_option_match()
        count = len(self.valid_options)
        if count == 0:
            return False

        logger.attr('EventOption', f'{count}/{len(self.options)}')
        # Only one option, click directly
        if count == 1:
            if self.interval_is_reached(CHOOSE_OPTION, interval=2):
                self.device.click(self.valid_options[0].prefix_icon)
                self.interval_reset(CHOOSE_OPTION)
                return True

        if self.interval_is_reached(CHOOSE_OPTION, interval=2):
            option = self._event_option_filter()
            if SCROLL_OPTION.appear(main=self):
                if option.is_bottom_page:
                    SCROLL_OPTION.set_bottom(main=self)
                else:
                    SCROLL_OPTION.set_top(main=self)
            self.device.click(option.prefix_icon)
            self.interval_reset(CHOOSE_OPTION)
            return True

        return False

    def _event_option_match(self, is_bottom_page=False) -> int:
        """
        Returns:
            int: Number of option icons matched
        """
        option_icons = CHOOSE_OPTION.match_multi_template(self.device.image)
        for button in option_icons:
            button.button = area_limit(button.button, OCR_OPTION.area)
        self.options += [OptionButton(
            prefix_icon=icon,
            is_valid=self.image_color_count(icon.area, color=(
                181, 162, 126), threshold=221, count=25),
            is_bottom_page=is_bottom_page
        ) for icon in option_icons]
        if option_icons:
            del_cached_property(self, 'valid_options')
        return len(option_icons)

    def _event_option_ocr(self, expected_count: int) -> None:
        """
        Args:
            expected_count (int): Number of option icons matched
        """
        expected_options = self.options[-expected_count:]
        ocr = OcrRogueEventOption(OCR_OPTION)
        ocr.expected_options = expected_options
        ocr_results = ocr.matched_ocr(self.device.image, [RogueEventOption])
        # Pair icons and ocr results
        index = 0
        all_matched = True
        for option in expected_options:
            _, y1, _, y2 = option.prefix_icon.area
            for index in range(index, len(ocr_results)):
                _, yy1, _, yy2 = ocr_results[index].area
                if yy2 < y1:
                    continue
                if yy1 > y2:
                    break
                option.button = ocr_results[index]
                break
            if option.button is None:
                option.is_valid = False
                all_matched = False
        if not all_matched:
            logger.warning('Count of OCR_OPTION results is not as expected')
            del_cached_property(self, 'valid_options')

    def _event_option_filter(self) -> OptionButton:
        if self.event_title is None:
            # OCR area of rest area is different from other occurrences
            if self.appear(REST_AREA):
                self.event_title = KEYWORDS_ROGUE_EVENT_TITLE.Rest_Area
            else:
                # Title may contains multi lines
                results = OcrRogueEventTitle(OCR_TITLE).matched_ocr(
                    self.device.image,
                    [RogueEventTitle]
                )
                if results:
                    self.event_title = results[0].matched_keyword
        if self.event_title is None:
            random_index = random.choice(range(len(self.valid_options)))
            logger.warning('Failed to OCR title')
            logger.info(f'Randomly select option {random_index+1}')
            return self.valid_options[random_index]

        strategy_name = self.config.RoguePath_DomainStrategy
        logger.attr('DomainStrategy', strategy_name)
        if strategy_name not in STRATEGIES:
            logger.warning(
                'Unknown domain strategy, fall back to STRATEGY_COMMON'
            )
        strategy = STRATEGIES.get(strategy_name, STRATEGY_COMMON)
        if self.event_title not in strategy:
            random_index = random.choice(range(len(self.valid_options)))
            logger.info(f'No strategy preset for {self.event_title}')
            logger.info(f'Randomly select option {random_index+1}')
            return self.valid_options[random_index]
        # Try ocr
        if not self.options:
            self._event_option_match()
        self._event_option_ocr(len(self.options))
        # Check next page if there is scroll
        if SCROLL_OPTION.appear(main=self):
            if SCROLL_OPTION.set_bottom(main=self):
                expected = self._event_option_match(is_bottom_page=True)
                self._event_option_ocr(expected)
        # Reason why _keywords_to_find()[0] is used to compare:
        # Text of options in different events can be the same,
        # so it is possible that keywords returned by matched_ocr
        # is not exactly the same as options in RogueEventTitle.option_ids.
        for expect in strategy[self.event_title]:
            for i, option in enumerate(self.valid_options):
                ocr_text = option.button.matched_keyword._keywords_to_find()[0]
                expect_text = expect._keywords_to_find()[0]
                if ocr_text == expect_text:
                    logger.info(f'Select option {i+1}: {option}')
                    return option
        logger.error('No option was selected, return the last instead')
        logger.info(f'Select last option: {self.valid_options[-1]}')
        return self.valid_options[-1]
