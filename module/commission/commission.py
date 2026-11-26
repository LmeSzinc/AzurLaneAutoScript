import copy
from datetime import datetime, timedelta

import numpy as np

from scipy import signal

from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import *
from module.commission.assets import *
from module.commission.preset import DICT_FILTER_PRESET, SHORTEST_FILTER
from module.commission.project import COMMISSION_FILTER, Commission
from module.config.config_generated import GeneratedConfig
from module.config.utils import get_server_last_update, get_server_next_update
from module.dorm.dorm import RewardDorm
from module.exception import GameStuckError, OilMaxed, RequestHumanTakeover
from module.handler.assets import POPUP_CANCEL, POPUP_CONFIRM
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.retire.assets import DOCK_CHECK, SORTING_CLICK
from module.combat.level import LevelOcr
from module.retire.dock import CARD_GRIDS, DOCK_SCROLL, DOCK_SORTING, Dock, OCR_DOCK_SELECTED
from module.retire.scanner import FleetScanner, LevelScanner
from module.ui.assets import BACK_ARROW, REWARD_GOTO_COMMISSION
from module.ui.page import page_commission, page_reward
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from module.ui.ui import UI
from module.ui_white.assets import REWARD_1_WHITE, REWARD_GOTO_COMMISSION_WHITE

COMMISSION_SWITCH = Switch('Commission_switch', is_selector=True)
COMMISSION_SWITCH.add_state('daily', COMMISSION_DAILY)
COMMISSION_SWITCH.add_state('urgent', COMMISSION_URGENT)
COMMISSION_SCROLL = Scroll(COMMISSION_SCROLL_AREA, color=(247, 211, 66), name='COMMISSION_SCROLL')

# First ship slot of the commission detail pane, clicking it opens the ship
# dock. The pane is located through the orange COMMISSION_ADVICE button at a
# fixed distance (ADVICE centre 935,352 -> slot centre 270,347); slot colors
# change once recommend fills ships in, so this button must never be matched
# by color, area/color below are placeholders for the constructor only.
COMMISSION_SHIP_SLOT = Button(
    area=(229, 306, 311, 388), color=(127, 134, 150),
    button=(229, 306, 311, 388), name='COMMISSION_SHIP_SLOT')

# TEMP TEST (2026-09-30): skip Recommend and enter the dock straight from the
# first ship slot, so the manual pick can be observed live. Set False to
# restore the normal recommend-first flow.
COMMISSION_TEST_DIRECT_DOCK = True

# Commissions that can not be started (e.g. level-capped) are given up after a
# short wait rather than looping until GameStuckError restarts the game.
COMMISSION_SKIP_AFTER_RECOMMEND = 5   # Start still grey this long after Recommend.
COMMISSION_SKIP_TIMEOUT = 90          # Absolute cap for one commission.
COMMISSION_SKIP_MAX_RECOMMEND = 3     # Recommend clicks before the flashing bug.

# Filter panel of the commission ship dock, calibrated on 1280x720 cn
# screenshots (2026-09-30). States are read back from the area mean color.
DOCK_FILTER_OPEN = Button(area=(1088, 5, 1177, 45), color=(96, 124, 168),
                          button=(1088, 5, 1177, 45), name='DOCK_FILTER_OPEN')
DOCK_FILTER_LEVEL = Button(area=(360, 28, 505, 78), color=(199, 144, 62),
                           button=(360, 28, 505, 78), name='DOCK_FILTER_LEVEL')
DOCK_FILTER_CONFIRM = Button(area=(712, 642, 888, 702), color=(64, 99, 160),
                             button=(712, 642, 888, 702), name='DOCK_FILTER_CONFIRM')
DOCK_FILTER_CANCEL_AREA = (400, 650, 560, 695)
DOCK_FILTER_CANCEL = Button(area=(390, 642, 567, 702), color=(160, 84, 84),
                            button=(390, 642, 567, 702), name='DOCK_FILTER_CANCEL')
DOCK_FILTER_ALL_RARITY = Button(area=(218, 427, 357, 469), color=(131, 142, 154),
                                button=(218, 427, 357, 469), name='DOCK_FILTER_ALL_RARITY')
DOCK_FILTER_RARITY = {
    'common': Button(area=(365, 427, 505, 469), color=(103, 132, 175),
                     button=(365, 427, 505, 469), name='FILTER_COMMON'),
    'rare': Button(area=(512, 427, 652, 469), color=(103, 132, 175),
                   button=(512, 427, 652, 469), name='FILTER_RARE'),
    'elite': Button(area=(659, 427, 799, 469), color=(103, 132, 175),
                    button=(659, 427, 799, 469), name='FILTER_ELITE'),
    'super_rare': Button(area=(806, 427, 946, 469), color=(103, 132, 175),
                         button=(806, 427, 946, 469), name='FILTER_SUPER_RARE'),
    'ultra': Button(area=(953, 427, 1093, 469), color=(103, 132, 175),
                    button=(953, 427, 1093, 469), name='FILTER_ULTRA'),
}
# Rarity stages walked from the user's minimum upward.
_COMMISSION_RARITY_STAGES = ['common', 'rare', 'elite', 'super_rare', 'ultra']
# One page turn is one viewport dragged on the scrollbar itself, the dark
# row gap is measured afterwards and corrected onto the OCR grid lines.
CARD_GRIDS_ROW3 = ButtonGrid(
    origin=(93, 530), delta=(164 + 2 / 3, 227), button_shape=(138, 204),
    grid_shape=(7, 1), name='CARD_ROW3')

# Minimum ship level each commission demands (at least ONE ship at or above
# it, per the game's own auto-fill rule). CN names as OCR'd; unknown -> 0.
# Source: wiki.biligame.com/blhx/军事委托, column "需求舰娘等级".
_COMMISSION_LEVEL_GROUP = {
    '日常资源开发': {'I': 1, 'II': 1, 'III': 10, 'IV': 10, 'V': 30, 'VI': 30},
    '高阶战术研发': {'I': 100, 'II': 100},
    '小型油田开发': {'I': 1, 'II': 10, 'III': 30},
    '中型油田开发': {'I': 1, 'II': 10, 'III': 30},
    '大型油田开发': {'I': 1, 'II': 10, 'III': 30},
    '保卫运输部队': {'I': 5, 'II': 25, 'III': 50},
    '解救商船': {'I': 5, 'II': 25, 'III': 50},
    '敌袭': {'I': 12, 'II': 35, 'III': 60},
}
_COMMISSION_LEVEL_SINGLE = {
    '初级矿脉护卫委托': 1, '中级矿脉护卫委托': 10, '高级矿脉护卫委托': 30,
    '初级林木护卫委托': 1, '中级林木护卫委托': 10, '高级林木护卫委托': 30,
    '小型商船护卫': 1, '中型商船护卫': 10, '大型商船护卫': 30,
    '短距离航行训练': 1, '中距离航行训练': 10, '远距离航行训练': 30,
    '舰队护卫演习': 1, '舰队运输演习': 10, '舰队实战演习': 30,
    '近海防卫巡逻': 1, '海域浮标检查作业': 10, '前沿基地防卫巡逻': 30,
    '舰队初阶演习': 1, '舰队中阶演习': 10, '舰队高阶演习': 30,
    '初阶自主训练': 10, '中阶自主训练': 30, '高阶自主训练': 70,
    '初阶对抗演习': 10, '中阶对抗演习': 30, '高阶对抗演习': 70,
    '初阶科研任务': 10, '中阶科研任务': 30, '高阶科研任务': 70,
    '初阶工具整备': 10, '中阶工具整备': 30, '高阶工具整备': 70,
    '初阶战术课程': 10, '中阶战术课程': 30, '高阶战术课程': 70,
    '初阶货物运输': 10, '中阶货物运输': 30, '高阶货物运输': 70,
    '支援土豪尔岛': 5, '支援姆波罗岛': 12, '支援马拉基岛': 25,
    '支援卡波罗岛': 35, '支援玛丽岛': 50, '支援特林岛': 60,
    '支援维拉维拉岛': 5, '支援伊岛': 12, '支援多伦瓦岛': 25,
    '支援恐班纳': 35, '支援马内岛': 50, '支援萌岛': 60,
    'BIW装备运输': 5, 'BIW要员护卫': 12, 'BIW物资交接': 25,
    'BIW度假护卫': 35, 'BIW装备研发': 50, 'BIW巡视护卫': 60,
    'NYB装备运输': 5, 'NYB要员护卫': 12, 'NYB物资交接': 25,
    'NYB度假护卫': 35, 'NYB装备研发': 50, 'NYB巡视护卫': 60,
    '小型观舰仪式': 20, '联合观舰仪式': 45, '同盟观舰仪式': 80,
    '歼灭敌侦查部队': 12, '歼灭敌主力部队': 35, '歼灭敌精锐部队': 60,
}
_ROMAN_MAP = {'Ⅰ': 'I', 'Ⅱ': 'II', 'Ⅲ': 'III',
              'Ⅳ': 'IV', 'Ⅴ': 'V', 'Ⅵ': 'VI'}
_ROMAN_TRANS = str.maketrans(_ROMAN_MAP)


def commission_level_requirement(name):
    """Minimum ship level the commission demands (>=1 ship), 0 if unknown."""
    raw = (name or '').upper().replace(' ', '')
    raw = re.sub(r'[「」『』“”\'\“（）()]', '', raw)
    # OCR splits one roman glyph into ascii letters plus a numeral character
    # (敌袭IⅡ is 敌袭Ⅱ), so the last unicode numeral decides the threat and
    # the ascii letters in front of it belong to the same glyph.
    numerals = list(re.finditer(r'[ⅠⅡⅢⅣⅤⅥ]', raw))
    if numerals:
        last = numerals[-1]
        # 敌袭IⅡ: the ascii letters before the glyph are part of it, the
        # group key is what is left of the whole numeral.
        group = _COMMISSION_LEVEL_GROUP.get(raw[:last.start()].rstrip('IV'))
        if group:
            return group.get(_ROMAN_MAP[last.group()], 0)
        return 0
    name = raw.translate(_ROMAN_TRANS)
    for key, value in _COMMISSION_LEVEL_SINGLE.items():
        if name.startswith(key):
            return value
    match = re.search(r'(III|IV|VI|II|V|I)$', name)
    if match:
        group = _COMMISSION_LEVEL_GROUP.get(name[:match.start()])
        if group:
            return group.get(match.group(1), 0)
    return 0

def lines_detect(image):
    """
    Args:
        image:

    Returns:
        np.ndarray: Coordinate Y of the white lines under each commission.
    """
    # Find white lines under each commission to locate them.
    # (597, 0, 619, 720) is somewhere with white lines only.
    color_height = np.mean(rgb2gray(crop(image, (597, 0, 619, 720), copy=False)), axis=1)
    parameters = {'height': 200, 'distance': 100}
    peaks, _ = signal.find_peaks(color_height, **parameters)
    # 67 is the height of commission list header
    # 117 is the height of one commission card.
    peaks = [y for y in peaks if y > 67 + 117]
    return np.array(peaks)


class RewardCommission(Dock, UI, InfoHandler):
    daily: SelectedGrids
    urgent: SelectedGrids
    daily_choose: SelectedGrids
    urgent_choose: SelectedGrids
    comm_choose: SelectedGrids
    max_commission = 4

    def _commission_detect(self, image):
        """
        Get all commissions from an image.

        Args:
            image (np.ndarray):

        Returns:
            SelectedGrids:
        """
        logger.hr('Commission detect')
        commission = []
        for y in lines_detect(image):
            comm = Commission(image, y=y, config=self.config)
            logger.attr('Commission', comm)
            repeat = len([c for c in commission if c == comm])
            comm.repeat_count += repeat
            commission.append(comm)

        return SelectedGrids(commission)

    def commission_detect(self, trial=1, area=None, skip_first_screenshot=True):
        """
        Args:
            trial (int): Retry if has one invalid commission,
                         usually because info_bar didn't disappear completely.
            area (tuple):
            skip_first_screenshot (bool):

        Returns:
            SelectedGrids:
        """
        commissions = SelectedGrids([])
        for _ in range(trial):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = self.device.image
            if area is not None:
                image = crop(image, area, copy=False)
            commissions = self._commission_detect(image)

            if commissions.count >= 2 and commissions.select(valid=False).count == 1:
                logger.warning('Found 1 invalid commission, retry commission detect')
                continue
            else:
                return commissions

        logger.info('trials of commission detect exhausted, stop')
        return commissions

    def _commission_choose(self, daily, urgent):
        """
        Args:
            daily (SelectedGrids):
            urgent (SelectedGrids):

        Returns:
            SelectedGrids, SelectedGrids: Chosen daily commission, Chosen urgent commission
        """
        self.comm_choose = SelectedGrids([])
        # Count Commission
        total = daily.add_by_eq(urgent)
        # Commissions with higher suffix are always below those with smaller suffix
        # Reverse the commission list to choose commissions with higher suffix first
        total = total[::-1]
        self.max_commission = 4
        for comm in total:
            if comm.genre == 'daily_event':
                self.max_commission = 5
        running_count = int(
            np.sum([1 for c in total if c.status == 'running']))
        logger.attr('Running', f'{running_count}/{self.max_commission}')

        # Load filter string
        preset = self.config.Commission_PresetFilter
        if preset == 'custom':
            string = self.config.Commission_CustomFilter
        else:
            if f'{preset}_night' in DICT_FILTER_PRESET:
                start_time = get_server_last_update('02:00')
                end_time = get_server_last_update('21:00')
                if start_time < end_time:
                    preset = f'{preset}_night'
            if preset not in DICT_FILTER_PRESET:
                logger.warning(f'Preset not found: {preset}, use default preset')
                preset = GeneratedConfig.Commission_PresetFilter
            string = DICT_FILTER_PRESET[preset]
        logger.attr('Commission Filter', preset)

        # Filter
        COMMISSION_FILTER.load(string)
        run = COMMISSION_FILTER.apply(total.grids, func=self._commission_check)
        logger.attr('Filter_sort', ' > '.join([str(c) for c in run]))
        run = SelectedGrids(run)

        # Add shortest
        no_shortest = run.delete(SelectedGrids(['shortest']))
        if no_shortest.count + running_count < self.max_commission:
            if daily.count:
                logger.info('Not enough commissions to run, add shortest daily commissions')
                COMMISSION_FILTER.load(SHORTEST_FILTER)
                shortest = COMMISSION_FILTER.apply(daily[::-1], func=self._commission_check)
                # Reverse the daily list to choose better commissions
                run = no_shortest.add_by_eq(SelectedGrids(shortest))
                logger.attr('Filter_sort', ' > '.join([str(c) for c in run]))
            else:
                logger.info('Not enough commissions to run')

        self.comm_choose = run
        if running_count >= self.max_commission:
            return SelectedGrids([]), SelectedGrids([])

        # Separate daily and urgent
        run = run[:self.max_commission - running_count]
        daily_choose = run.intersect_by_eq(daily)
        urgent_choose = run.intersect_by_eq(urgent)
        if daily_choose:
            logger.info('Choose daily commission')
            for comm in daily_choose:
                logger.info(comm)
        if urgent_choose:
            logger.info('Choose urgent commission')
            for comm in urgent_choose:
                logger.info(comm)

        return daily_choose, urgent_choose

    def _commission_check(self, commission):
        """
        Args:
            commission (Commission):

        Returns:
            bool:
        """
        if not commission.valid or commission.status != 'pending':
            return False
        if not self.config.Commission_DoMajorCommission and commission.category_str == 'major':
            return False
        return True

    def _commission_ensure_mode(self, mode):
        # Switch.set has no retry limit: off the commission list it clicks the
        # same button until GameTooManyClickError restarts the game. Take a
        # fresh screenshot first, a cached frame still shows the commission
        # list after the page has already been left.
        self.device.screenshot()
        if not COMMISSION_SWITCH.appear(main=self):
            logger.warning('Not on the commission list, mode switch skipped')
            return False
        if COMMISSION_SWITCH.set(mode, main=self):
            # If daily list has commissions > 4, usually to be 5, and 1 <= urgent <= 4
            # commission list will have an animation to scroll,
            # which causes the topmost one undetected.
            if not COMMISSION_SCROLL.appear(main=self) or COMMISSION_SCROLL.cal_position(main=self) < 0.05 or COMMISSION_SCROLL.length / COMMISSION_SCROLL.total > 0.98:
                pre_peaks = lines_detect(self.device.image)
                if not len(pre_peaks):
                    return True
                self.device.screenshot()
                while 1:
                    peaks = lines_detect(self.device.image)
                    if (not len(peaks) or peaks[0] > 67 + 117) and (not len(pre_peaks) or not len(peaks) or abs(peaks[0] - pre_peaks[0]) < 3):
                        break
                    pre_peaks = peaks
                    self.device.screenshot()

            return True
        else:
            return False

    def _commission_mode_reset(self):
        logger.hr('Commission mode reset')
        # The cached screenshot can be older than the last click, and a stale
        # frame makes the switch click on a page that is not the commission list.
        self.device.screenshot()
        if self.appear(COMMISSION_DAILY):
            current, another = 'daily', 'urgent'
        elif self.appear(COMMISSION_URGENT):
            current, another = 'urgent', 'daily'
        else:
            logger.warning('Unknown Commission mode')
            return False

        self._commission_ensure_mode(another)
        self._commission_ensure_mode(current)

        return True

    def _commission_swipe(self):
        if COMMISSION_SCROLL.appear(main=self):
            if COMMISSION_SCROLL.at_bottom(main=self):
                return False
            else:
                COMMISSION_SCROLL.next_page(main=self)
                return True
        else:
            return False

    def _commission_swipe_to_top(self):
        if not COMMISSION_SCROLL.appear(main=self):
            return False
        COMMISSION_SCROLL.set_top(main=self, skip_first_screenshot=True)
        return True

    def _commission_scan_list(self):
        """
        Returns:
            SelectedGrids: SelectedGrids containing Commission objects
        """
        self.device.click_record_clear()
        commission = SelectedGrids([])
        for _ in range(15):
            new = self.commission_detect(trial=2)
            commission = commission.add_by_eq(new)

            # End
            if not self._commission_swipe():
                break

        self.device.click_record_clear()
        return commission

    def _commission_scan_all(self):
        """
        Pages:
            in: page_commission
            out: page_commission
        """
        logger.hr('Commission scan', level=1)
        # Urgent list is lazy loaded. Check it first for a force update.
        self._commission_ensure_mode('urgent')

        logger.hr('Scan daily', level=2)
        self._commission_ensure_mode('daily')
        self._commission_swipe_to_top()
        daily = self._commission_scan_list()

        urgent = SelectedGrids([])
        for _ in range(2):
            logger.hr('Scan urgent', level=2)
            self._commission_ensure_mode('urgent')
            self._commission_swipe_to_top()
            urgent = self._commission_scan_list()
            # Convert extra commission to night
            urgent.call('convert_to_night')

            # Not in 21:00~03:00, but scanned night commissions
            # Probably some outdated commissions, a refresh should solve it
            if datetime.now() - get_server_next_update('21:00') > timedelta(hours=6):
                night = urgent.select(category_str='night')
                if night:
                    logger.warning('Not in 21:00~03:00, but scanned night commissions')
                    for comm in night:
                        logger.attr('Commission', comm)
                    logger.info('Re-scan urgent commission list')
                    # Poor sleep but acceptable in rare cases
                    self.device.sleep(2)
                    self._commission_ensure_mode('daily')
                    continue

            break

        logger.hr('Showing commission', level=2)
        logger.info('Daily commission')
        for comm in daily.sort('status', 'genre'):
            logger.attr('Commission', comm)
        if urgent.count:
            logger.info('Urgent commission')
            for comm in urgent.sort('status', 'genre'):
                logger.attr('Commission', comm)

        self.daily = daily
        self.urgent = urgent
        self.daily_choose, self.urgent_choose = self._commission_choose(self.daily, self.urgent)
        return daily, urgent

    def _commission_dock_ship_count(self):
        """Read the dock selected counter, (-1, -1) when unreadable."""
        current, _, total = OCR_DOCK_SELECTED.ocr(self.device.image)
        if total <= 0 or current < 0 or current > total:
            return -1, -1
        return current, total

    def _commission_dock_fleet_question(self):
        """True when the game asks to move the clicked ship out of its fleet."""
        # The confirm button here is blue, the stock asset is orange, so
        # handle_popup_confirm() never sees it and we must dismiss it ourselves.
        return self.appear(POPUP_CANCEL, offset=self._popup_offset)

    def _commission_dock_answer_fleet_question(self, confirm):
        """Answer the fleet question; confirm pulls the ship out of its fleet."""
        button = POPUP_CONFIRM if confirm else POPUP_CANCEL
        # Clear the stale offset a stock button carries from its last match.
        button.clear_offset()
        self.device.click(button)
        self.device.sleep(0.5)
        self.device.screenshot()

    def _commission_dock_click_ship(self, button, select=True, allow_fleet=False):
        """Click a card once, answer popups, and return the selected counter
        after the click; -1 when unreadable or the game refused the ship.
        The caller compares it with the count before the click."""
        before, _ = self._commission_dock_ship_count()
        if before < 0:
            return -1
        self.device.click(button)
        self.device.sleep(0.4)
        self.device.screenshot()
        if self._commission_dock_fleet_question():
            if not allow_fleet:
                # The card belongs to a fleet and this option never takes a
                # ship out of one, so the card is left alone.
                self._commission_dock_answer_fleet_question(confirm=False)
                return -1
            logger.warning('The ship belongs to a fleet, '
                           'taking it out of that fleet to use it here')
            self._commission_dock_answer_fleet_question(confirm=True)
            after, _ = self._commission_dock_ship_count()
            return after
        if self.handle_popup_confirm('COMMISSION_DOCK_SHIP'):
            # A ship the game refuses answers with a popup instead of a
            # selection, dismissing it leaves the counter where it was.
            return -1
        after, _ = self._commission_dock_ship_count()
        return after

    def _commission_protected_fleets(self):
        """Fleets used by any enabled scheduler task must not be raided, the
        task would lose those ships on its next sortie."""
        fleets = set()
        try:
            data = self.config.data
        except Exception:
            return fleets
        for node in data.values():
            if not isinstance(node, dict):
                continue
            if not node.get('Scheduler', {}).get('Enable'):
                continue
            stack = [node]
            while stack:
                d = stack.pop(0)
                for key, value in d.items():
                    if isinstance(value, dict):
                        stack.append(value)
                        continue
                    if not isinstance(value, int) or not 1 <= value <= 6:
                        continue
                    if key in ('Fleet1', 'Fleet2', 'Fleet') or key.endswith('Fleet'):
                        fleets.add(value)
        return fleets

    def _commission_dock_ship_occupied(self, button):
        """True when the card carries a red occupation banner such as
        大型作战中. The banner is a solid strip, card art never forms one."""
        image = np.asarray(self.device.image).astype(int)
        x0, y0, x1, y1 = button.area
        strip = image[y0 + 118:y0 + 170, x0:x1]
        red = (strip[:, :, 0] > 90) & (strip[:, :, 0] > strip[:, :, 1] + 20) \
            & (strip[:, :, 0] > strip[:, :, 2] + 20)
        rows = 0
        for line in red:
            run = best = 0
            for v in line:
                run = run + 1 if v else 0
                best = max(best, run)
            if best >= 85:
                rows += 1
                if rows >= 2:
                    return True
        return False

    def _commission_dock_scan_page(self, level_scanner, fleet_scanner):
        """Read the top two card rows: level OCR, fleet badge, occupation."""
        image = self.device.image
        levels = level_scanner.scan(image)
        fleets = fleet_scanner.scan(image)
        ships = []
        for idx, button in enumerate(CARD_GRIDS.buttons):
            ships.append({
                'idx': idx,
                'level': int(levels[idx]) if idx < len(levels) else 0,
                'fleet': fleets[idx] if idx < len(fleets) else 0,
                'occupied': self._commission_dock_ship_occupied(button),
                'button': button,
            })
        return ships

    def _commission_dock_scan_row3(self, row3_scanner):
        """Read the third card row, only valid at the bottom of the list.
        Its fleet badge is cut by the bottom bar, so it reports no fleet."""
        image = self.device.image
        levels = row3_scanner.scan(image)
        ships = []
        for idx, button in enumerate(CARD_GRIDS_ROW3.buttons):
            ships.append({
                'idx': 14 + idx,
                'level': int(levels[idx]) if idx < len(levels) else 0,
                'occupied': self._commission_dock_ship_occupied(button),
                'button': button,
            })
        return ships

    def _commission_dock_wait_stable(self, timeout=4):
        """Wait until the scrollbar stops moving, the list has settled."""
        timer = Timer(timeout)
        timer.reset()
        last = None
        while not timer.reached():
            self.device.screenshot()
            position = DOCK_SCROLL.cal_position(main=self)
            if last is not None and abs(position - last) < 0.01:
                return True
            last = position
        return False

    def _commission_dock_gap_offset(self):
        """Distance of the dark gap below row one from its aligned position
        (centre 292), None when no gap shows in the window."""
        image = np.asarray(self.device.image).astype(float)
        band = image[240:344, 93:1219].mean(axis=2).mean(axis=1)
        if band.min() > 110:
            return None
        return int(np.argmin(band)) + 240 - 292

    def _commission_dock_align(self):
        """The thumb drag lands within a row but not exactly on the grid
        lines; measure the gap and correct with a small slow swipe."""
        for _ in range(3):
            self.device.screenshot()
            offset = self._commission_dock_gap_offset()
            if offset is None:
                # No gap in the window, aligned or at the list edge, the
                # caller reads what is visible either way.
                return True
            if abs(offset) <= 4:
                return True
            self.device.swipe((650, 400), (650, 400 - offset), name='DOCK_ALIGN')
            self._commission_dock_wait_stable()
        return False

    def _commission_filter_panel_open(self):
        """The panel is up when its own red cancel button covers this area."""
        image = np.asarray(self.device.image).astype(int)
        x0, y0, x1, y1 = DOCK_FILTER_CANCEL_AREA
        button = image[y0:y1, x0:x1]
        mean = button.mean(axis=(0, 1))
        return mean[0] > 110 and mean[0] > mean[2] + 35

    def _commission_filter_rarity_selected(self, button):
        """Selected filter buttons turn bright blue, idle ones stay gray."""
        image = np.asarray(self.device.image).astype(int)
        x0, y0, x1, y1 = button.area
        area = image[y0:y1, x0:x1]
        return float(area[:, :, 2].mean() - area[:, :, 0].mean()) > 50

    def _commission_dock_set_filter(self, stage, descending):
        """Set the rarity stage through the game's own filter panel, sorting
        by level. False when the panel could not be controlled."""
        for _ in range(3):
            if self._commission_filter_panel_open():
                break
            self.device.click(DOCK_FILTER_OPEN)
            self.device.sleep(0.8)
            self.device.screenshot()
        if not self._commission_filter_panel_open():
            logger.warning('Dock filter panel did not open')
            return False
        # 等级 must be the active sort type before stages make any sense.
        if not self._commission_filter_sort_is_level():
            self.device.click(DOCK_FILTER_LEVEL)
            self.device.sleep(0.4)
            self.device.screenshot()
        if self._commission_filter_rarity_selected(DOCK_FILTER_ALL_RARITY):
            self.device.click(DOCK_FILTER_ALL_RARITY)
            self.device.sleep(0.3)
            self.device.screenshot()
        for name, button in DOCK_FILTER_RARITY.items():
            if name == stage:
                continue
            if self._commission_filter_rarity_selected(button):
                logger.info(f'Dock filter deselect rarity: {name}')
                self.device.click(button)
                self.device.sleep(0.3)
                self.device.screenshot()
        if not self._commission_filter_rarity_selected(DOCK_FILTER_RARITY[stage]):
            self.device.click(DOCK_FILTER_RARITY[stage])
            self.device.sleep(0.4)
            self.device.screenshot()
        if not self._commission_filter_rarity_selected(DOCK_FILTER_RARITY[stage]):
            logger.warning(f'Dock filter stage {stage} did not select')
            self.device.click(DOCK_FILTER_CANCEL)
            return False
        logger.attr('Dock filter stage', stage)
        self.device.click(DOCK_FILTER_CONFIRM)
        timer = Timer(3)
        timer.reset()
        while not timer.reached():
            self.device.screenshot()
            if not self._commission_filter_panel_open():
                break
        self.handle_dock_cards_loading()
        self._commission_dock_set_sort(descending)
        return True

    def _commission_dock_sort_direction(self):
        """Read the little arrow next to the sorting button, unknown when
        neither arrow pixel matches."""
        image = np.asarray(self.device.image).astype(int)
        for name, (x0, y0, x1, y1) in (('asc', (1014, 22, 1020, 27)),
                                       ('desc', (1014, 29, 1020, 34))):
            pixel = image[y0:y1, x0:x1]
            if np.abs(pixel.mean(axis=(0, 1)) - np.array([189, 207, 231])).mean() < 35:
                return name
        return 'unknown'

    def _commission_dock_set_sort(self, descending):
        """Point the arrow to the wanted direction with a bounded retry,
        never blind clicking when the arrow is unreadable."""
        target = 'desc' if descending else 'asc'
        for _ in range(3):
            self.device.screenshot()
            current = self._commission_dock_sort_direction()
            if current == target:
                return True
            if current == 'unknown':
                logger.warning('Dock sorting arrow unreadable, direction not set')
                return False
            self.device.click(SORTING_CLICK)
            self.device.sleep(0.6)
        logger.warning('Dock sorting direction did not settle')
        return False

    def _commission_filter_sort_is_level(self):
        image = np.asarray(self.device.image).astype(int)
        area = image[35:72, 370:495]
        mean = area.mean(axis=(0, 1))
        return mean[0] > 150 and mean[0] > mean[2] + 40

    def _commission_wait_dock(self, timeout=10):
        """Wait for the dock to open after clicking a ship slot. Returns False
        when the dock never shows up."""
        timer = Timer(timeout)
        timer.reset()
        while not timer.reached():
            self.device.screenshot()
            if self.appear(DOCK_CHECK, offset=(20, 20)):
                return True
            if self.info_bar_count():
                # Game refused the start, commission is truly unstartable.
                return False
        return self.appear(DOCK_CHECK, offset=(20, 20))

    def _commission_dock_fill_stage(self, allow_fleet, protected, required,
                                    scanners, picked):
        """Fill slots from one rarity stage, paging one viewport at a time
        and reading the top two rows only. A card already picked stays
        selected across the rarity stages and must never be clicked again,
        the second click would deselect it."""
        level_scanner, fleet_scanner, row3_scanner = scanners
        count, total = self._commission_dock_ship_count()
        if count < 0 or total <= 0:
            logger.warning('Dock selected counter unreadable')
            return False
        if count >= total:
            return True
        swipes = 0
        while 1:
            if not self.appear(DOCK_CHECK, offset=(20, 20)):
                # A full pick can close the dock by itself, stop instead of
                # scanning whatever screen is left behind.
                logger.warning('Dock closed during the scan, stop picking')
                return False
            for ship in self._commission_dock_scan_page(level_scanner, fleet_scanner):
                if count >= total:
                    break
                if ship['idx'] in picked:
                    continue
                if ship['occupied']:
                    continue
                if not allow_fleet and ship['fleet']:
                    continue
                if allow_fleet and ship['fleet'] and ship['fleet'] in protected:
                    continue
                if not 1 <= ship['level'] <= 125 or ship['level'] < required:
                    continue
                after = self._commission_dock_click_ship(
                    ship['button'], allow_fleet=allow_fleet)
                if after < 0:
                    continue
                if after == count - 1:
                    # A card the recommend already selected, the click
                    # deselected it, bring it back and do not count it.
                    self.device.click(ship['button'])
                    self.device.sleep(0.4)
                    self.device.screenshot()
                    restored, _ = self._commission_dock_ship_count()
                    if restored >= 0:
                        count = restored
                    continue
                count = after
                picked.add(ship['idx'])
                logger.attr('Picked ship', f'Lv{ship["level"]} fleet{ship["fleet"]}')
            if count >= total:
                return True
            if DOCK_SCROLL.at_bottom(main=self):
                # The last row peeks above the bottom bar, its fleet badge is
                # cut off so raiding fleets skips it.
                if not allow_fleet:
                    for ship in self._commission_dock_scan_row3(row3_scanner):
                        if count >= total:
                            break
                        if ship['idx'] in picked:
                            continue
                        if ship['occupied']:
                            continue
                        if not 1 <= ship['level'] <= 125 or ship['level'] < required:
                            continue
                        after = self._commission_dock_click_ship(
                            ship['button'], allow_fleet=False)
                        if after < 0:
                            continue
                        if after == count - 1:
                            self.device.click(ship['button'])
                            self.device.sleep(0.4)
                            self.device.screenshot()
                            restored, _ = self._commission_dock_ship_count()
                            if restored >= 0:
                                count = restored
                            continue
                        count = after
                        picked.add(ship['idx'])
                        logger.attr('Picked ship', f'Lv{ship["level"]} (bottom row)')
                return count >= total
            before = DOCK_SCROLL.cal_position(main=self)
            if not DOCK_SCROLL.drag_page(1.0, main=self):
                logger.warning('Dock scrollbar did not move, stop paging')
                return False
            swipes += 1
            if swipes % 6 == 0:
                # Paging can take many drags, keep the click guard quiet.
                self.device.click_record_clear()
            self._commission_dock_wait_stable()
            if abs(DOCK_SCROLL.cal_position(main=self) - before) < 0.005:
                logger.warning('Dock scrollbar did not move, stop paging')
                return False
            if not self._commission_dock_align():
                logger.warning('Dock page did not align, stop paging')
                return False

    def _commission_dock_pick_ships(self, comm=None):
        """Fill the slots by hand through the dock's own filter panel: sorted
        by level, walking rarity stages from the user's minimum upward, free
        ships only until every stage runs out. Fleets are raided last, never
        the ones other enabled tasks use."""
        logger.hr('Commission dock pick')
        required = commission_level_requirement(comm.name) if comm is not None else 0
        if required:
            logger.info(f'Commission level requirement: Lv{required}+')
        # High requirements find nothing in low levels, read the list from
        # the top instead of paging through hundreds of lesser ships.
        descending = required >= 100
        min_rarity = self.config.Commission_PickMinRarity
        if min_rarity not in _COMMISSION_RARITY_STAGES:
            min_rarity = 'rare'
        stages = _COMMISSION_RARITY_STAGES[_COMMISSION_RARITY_STAGES.index(min_rarity):]
        protected = self._commission_protected_fleets()
        if protected:
            logger.attr('Protected fleets', sorted(protected))
        level_scanner = LevelScanner()
        fleet_scanner = FleetScanner()
        row3_grids = CARD_GRIDS_ROW3.crop(area=(77, 5, 138, 27), name='LEVEL_ROW3')
        row3_scanner = LevelScanner()
        row3_scanner.grids = row3_grids
        row3_scanner.ocr_model = LevelOcr(row3_grids.buttons, name='DOCK_LEVEL_OCR', threshold=64)
        scanners = (level_scanner, fleet_scanner, row3_scanner)

        count, total = self._commission_dock_ship_count()
        if count < 0 or total <= 0:
            logger.warning('Dock selected counter unreadable')
            return False
        if count >= total and required <= 1:
            self.dock_select_confirm(check_button=COMMISSION_ADVICE)
            return True
        if count >= total:
            # Slots full but Start grey: the picked ships miss the level
            # requirement. Free the first card to take one that meets it.
            after = self._commission_dock_click_ship(CARD_GRIDS[(0, 0)], select=False)
            if after != count - 1:
                logger.warning('Could not free a slot, first card not selected')
                return False
            count = after

        picked = set()

        def fill(allow_fleet):
            for stage in stages:
                current, _ = self._commission_dock_ship_count()
                if current >= total:
                    return True
                if not self._commission_dock_set_filter(stage, descending):
                    logger.warning(f'Dock filter stage {stage} failed, next stage')
                    continue
                if self._commission_dock_fill_stage(
                        allow_fleet, protected, required, scanners, picked):
                    return True
            return False

        picked = fill(allow_fleet=False)
        if not picked and self.config.Commission_NoFreeShipPolicy == 'use_fleet':
            logger.info('Retrying the pick with fleet ships allowed')
            self.device.click_record_clear()
            picked = fill(allow_fleet=True)
        if not picked:
            count, _ = self._commission_dock_ship_count()
            if count <= 0:
                logger.warning('No ship picked for the commission, skip')
                return False
            logger.warning(f'Ships still short ({count}/{total}), start anyway')
        self.dock_select_confirm(check_button=COMMISSION_ADVICE)
        return True

    def _commission_start_click(self, comm, is_urgent=False, skip_first_screenshot=True):
        """Start a commission, letting the caller skip it when it can not be
        started at all (see COMMISSION_SKIP_*)."""
        logger.hr('Commission start')
        self.interval_clear(COMMISSION_ADVICE)
        self.interval_clear(COMMISSION_START)
        comm_timer = Timer(7)
        skip_timer = Timer(COMMISSION_SKIP_TIMEOUT)
        skip_timer.reset()
        # Set once Recommend has been clicked, then counts down to the moment the
        # Start button is expected to light up. None when Recommend was not used.
        recommend_timer = None
        # Confirming a grey start to force the dock open is tried once too.
        enter_dock_tried = False
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break

            # Can not start: skip instead of raising GameStuckError, which would
            # restart the game and drop every running commission.
            if skip_timer.reached():
                logger.warning(f'Commission start timeout, skip: {comm.name}')
                return False
            if count >= COMMISSION_SKIP_MAX_RECOMMEND:
                # After you click "Recommend", your ships appear and then suddenly disappear.
                # At the same time, the icon of commission is flashing.
                logger.warning('Triggered commission list flashing bug, skip this commission')
                return False
            if recommend_timer is not None and recommend_timer.reached():
                # Recommend filled the fleet but Start stays grey: the ships do
                # not meet the requirement, so give up on this commission.
                if self.match_template_color(COMMISSION_START, offset=(5, 20)):
                    recommend_timer = None
                elif self.config.Commission_AutoPickShip and not enter_dock_tried \
                        and self.match_template_color(COMMISSION_ADVICE, offset=(10, 10)):
                    # Start still grey after recommend: open the dock from the
                    # first ship slot, the dock takes up to six ships at once.
                    # Gated on the orange Recommend button, the slot row sits a
                    # fixed distance left of it and is clicked blind by design.
                    logger.info('Recommend left start grey, entering dock from the first ship slot')
                    enter_dock_tried = True
                    COMMISSION_SHIP_SLOT.clear_offset()
                    self.device.click(COMMISSION_SHIP_SLOT)
                    if not self._commission_wait_dock():
                        logger.warning(f'Dock did not open from the ship slot, skip: {comm.name}')
                        return False
                    recommend_timer = None
                    comm_timer.reset()
                    continue
                else:
                    # Last resort only: reached when no fill option is enabled,
                    # or every enabled option was tried in the dock and Start is
                    # still grey. Skipping is never the first move.
                    logger.warning(f'Ships do not meet the requirement, skip: {comm.name}')
                    # Leave the dock only when the dock is what is on screen, the
                    # back arrow of the detail pane quits the whole page.
                    if self.appear(DOCK_CHECK, offset=(20, 20)):
                        self.device.click(BACK_ARROW)
                        self.device.sleep(1)
                    return False

            # Click
            if self.match_template_color(COMMISSION_START, offset=(5, 20), interval=7):
                self.device.click(COMMISSION_START)
                self.interval_reset(COMMISSION_ADVICE)
                comm_timer.reset()
                recommend_timer = None
                continue
            if self.handle_popup_confirm('COMMISSION_START'):
                self.interval_reset(COMMISSION_ADVICE)
                comm_timer.reset()
                continue
            # Entered dock, either by confirming a grey start or by accident.
            if self.appear(DOCK_CHECK, offset=(20, 20), interval=3):
                picked = self.config.Commission_AutoPickShip and self._commission_dock_pick_ships(comm=comm)
                if picked:
                    # Back at the details pane, give Start one window to light
                    # up before the grey check skips the commission.
                    recommend_timer = Timer(COMMISSION_SKIP_AFTER_RECOMMEND)
                    recommend_timer.reset()
                    comm_timer.reset()
                    continue
                logger.warning(f'Sent to dock after recommend, skip: {comm.name}')
                # Leave the dock so the caller finds the commission page as it expects.
                self.device.click(BACK_ARROW)
                self.device.sleep(1)
                return False
            # Check if is the right commission
            if self.appear(COMMISSION_ADVICE, offset=(5, 20), interval=7):
                area = (0, 0, image_size(self.device.image)[0], COMMISSION_ADVICE.button[1])
                current = self.commission_detect(area=area)
                if is_urgent:
                    current.call('convert_to_night')  # Convert extra commission to night
                if current.count >= 1:
                    current = current[0]
                    if current == comm:
                        logger.info('Selected to the correct commission')
                    else:
                        logger.warning('Selected to the wrong commission')
                        return False
                else:
                    logger.warning('No selected commission detected, assuming correct')
                if COMMISSION_TEST_DIRECT_DOCK and self.config.Commission_AutoPickShip:
                    # TEMP TEST: click the first ship slot instead of Recommend,
                    # the dock takes up to six ships so one slot is enough.
                    logger.info('TEST: skipping recommend, entering dock from the first ship slot')
                    enter_dock_tried = True
                    COMMISSION_SHIP_SLOT.clear_offset()
                    self.device.click(COMMISSION_SHIP_SLOT)
                    if not self._commission_wait_dock():
                        logger.warning(f'TEST: dock did not open from the ship slot, skip: {comm.name}')
                        return False
                    recommend_timer = None
                    comm_timer.reset()
                    continue
                self.device.click(COMMISSION_ADVICE)
                count += 1
                recommend_timer = Timer(COMMISSION_SKIP_AFTER_RECOMMEND)
                recommend_timer.reset()
                self.interval_reset(COMMISSION_ADVICE)
                self.interval_clear(COMMISSION_START)
                comm_timer.reset()
                continue
            # Enter
            if comm_timer.reached():
                self.device.click(comm.button)
                self.device.sleep(0.3)
                comm_timer.reset()

        return True

    def _commission_find_and_start(self, comm, is_urgent=False):
        """
        Args:
            comm (Commission):
            is_urgent (bool):
        """
        self.device.click_record_clear()
        comm = copy.deepcopy(comm)
        comm.repeat_count = 1
        for _ in range(3):
            logger.hr('Commission find and start', level=2)
            logger.info(f'Finding commission {comm}')

            failed = True

            for _ in range(15):
                new = self.commission_detect(trial=2)
                if is_urgent:
                    new.call('convert_to_night')  # Convert extra commission to night

                # Update commission position.
                # In different scans, they have the same information, but have different locations.
                current = None
                for new_comm in new:
                    if new_comm == comm:
                        current = new_comm
                if current is not None:
                    if self._commission_start_click(current, is_urgent=is_urgent):
                        self.device.click_record_clear()
                        return True
                    else:
                        self._commission_mode_reset()
                        self._commission_swipe_to_top()
                        failed = False
                        break

                # End
                if not self._commission_swipe():
                    break

            if failed:
                logger.warning(f'Failed to select commission: {comm}')
                self._commission_mode_reset()
                self._commission_swipe_to_top()
                self.device.click_record_clear()
                continue
            else:
                # _commission_start_click gave up (wrong commission or
                # unstartable), so leave it and go on to the next one.
                logger.warning(f'Give up on commission: {comm}')
                self.device.click_record_clear()
                return False

        logger.warning(f'Failed to select commission after 3 trial')
        self.device.click_record_clear()
        return False

    def commission_start(self):
        """
        Scan and Start all chosen commissions.

        Pages:
            in: page_commission
            out: page_commission
        """
        self._commission_scan_all()

        logger.hr('Commission run', level=1)
        if self.daily_choose:
            for comm in self.daily_choose:
                self._commission_ensure_mode('daily')
                self._commission_swipe_to_top()
                self.handle_info_bar()
                if self._commission_find_and_start(comm, is_urgent=False):
                    comm.convert_to_running()
                self._commission_mode_reset()
        if self.urgent_choose:
            for comm in self.urgent_choose:
                self._commission_ensure_mode('urgent')
                self._commission_swipe_to_top()
                self.handle_info_bar()
                if self._commission_find_and_start(comm, is_urgent=True):
                    comm.convert_to_running()
                self._commission_mode_reset()
        if not self.daily_choose and not self.urgent_choose:
            logger.info('No commission chose')

    def _commission_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward
            out: page_commission
        """
        logger.hr('Reward receive')

        reward = False
        click_timer = Timer(1)
        with self.stat.new(
                'commission', method=self.config.DropRecord_CommissionRecord
        ) as drop:
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # End
                if self.ui_page_appear(page_commission, offset=(20, 20)):
                    # Leaving at page_commission
                    # Commission rewards may appear too slow, causing stuck in UI switching
                    break

                for button in [EXP_INFO_S_REWARD, GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3]:
                    if self.appear(button, interval=1):
                        if drop:
                            self.ensure_no_info_bar(timeout=1)
                            drop.add(self.device.image)

                        REWARD_SAVE_CLICK.name = button.name
                        self.device.click(REWARD_SAVE_CLICK)
                        click_timer.reset()
                        reward = True
                        continue
                if click_timer.reached() and self.appear_then_click(REWARD_1, offset=(20, 20), interval=1):
                    self.interval_reset(GET_SHIP)
                    click_timer.reset()
                    reward = True
                    continue
                if click_timer.reached() and self.appear_then_click(REWARD_1_WHITE, offset=(20, 20), interval=1):
                    self.interval_reset(GET_SHIP)
                    click_timer.reset()
                    reward = True
                    continue
                if click_timer.reached() and self.appear_then_click(REWARD_GOTO_COMMISSION, offset=(20, 20)):
                    self.interval_reset(GET_SHIP)
                    click_timer.reset()
                    continue
                if click_timer.reached() and self.appear_then_click(REWARD_GOTO_COMMISSION_WHITE, offset=(20, 20)):
                    self.interval_reset(GET_SHIP)
                    click_timer.reset()
                    continue
                if self.ui_main_appear_then_click(page_reward, interval=3):
                    self.interval_reset(GET_SHIP)
                    # no need to reset click_timer, just instant click REWARD_1
                    # click_timer.reset()
                    continue
                # handle oil maxed
                if self.config.SERVER in ['cn']:
                    if self.appear(OIL_MAXED, offset=(20, 20), interval=3):
                        raise OilMaxed
                # Check GET_SHIP at last to handle random white background at page_main
                for button in [GET_SHIP]:
                    if click_timer.reached() and self.appear(button, offset=(20, 20), interval=1):
                        self.ensure_no_info_bar(timeout=1)
                        drop.add(self.device.image)

                        REWARD_SAVE_CLICK.name = button.name
                        self.device.click(REWARD_SAVE_CLICK)
                        click_timer.reset()
                        reward = True
                        continue
                if click_timer.reached() and self.ui_additional():
                    click_timer.reset()
                    continue

        return reward

    def commission_receive(self):
        """
        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward
            out: page_commission
        """
        for _ in range(3):
            try:
                reward = self._commission_receive()
                return reward
            except OilMaxed:
                logger.info("Oil maxed, buy food to consume oil")
                RewardDorm(self.config, self.device).dorm_food_run(amount=10)
                self.ui_ensure(page_reward)

        logger.critical(f'Failed to handle oil maxed after 3 trial')
        raise RequestHumanTakeover

    def run(self):
        """
        Pages:
            in: Any
            out: page_commission
        """
        self.ui_ensure(page_reward)
        self.commission_receive()

        # info_bar appears when get ship in Launch Ceremony commissions
        # This is a game bug, the info_bar shows get ship, will appear over and over again, until you click get_ship.
        self.handle_info_bar()
        self.commission_start()

        # Scheduler
        total = self.daily.add_by_eq(self.urgent)
        future_finish = sorted([f for f in total.get('finish_time') if f is not None])
        logger.info(f'Commission finish: {[str(f) for f in future_finish]}')
        if len(future_finish):
            self.config.task_delay(target=future_finish)
        else:
            logger.info('No commission running')
            self.config.task_delay(success=False)

        # Delay GemsFarming
        if self.config.cross_get(keys='GemsFarming.GemsFarming.CommissionLimit', default=False):
            daily = self.daily.select(category_str='daily', status='pending').count
            filtered_urgent = self.comm_choose.intersect_by_eq(self.urgent.select(status='pending')).count
            logger.info(f'Daily commission: {daily}, filtered_urgent: {filtered_urgent}')
            if daily > 0 and filtered_urgent >= 1:
                logger.info('Having daily commissions to do, delay task `GemsFarming`')
                self.config.task_delay(
                    minute=120, target=future_finish if len(future_finish) else None, task='GemsFarming')
            elif filtered_urgent >= 4:
                logger.info('Having too many urgent commissions, delay task `GemsFarming`')
                self.config.task_delay(
                    minute=120, target=future_finish if len(future_finish) else None, task='GemsFarming')
