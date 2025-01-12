import copy
from datetime import datetime, timedelta

from scipy import signal

from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import *
from module.commission.assets import *
from module.commission.preset import DICT_FILTER_PRESET, SHORTEST_FILTER
from module.commission.project import COMMISSION_FILTER, Commission
from module.config.config_generated import GeneratedConfig
from module.config.utils import get_server_last_update, get_server_next_update
from module.exception import GameStuckError
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.retire.assets import DOCK_CHECK
from module.ui.assets import BACK_ARROW, COMMISSION_CHECK, REWARD_GOTO_COMMISSION
from module.ui.page import page_reward
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from module.ui.ui import UI
from module.ui_white.assets import REWARD_1_WHITE, REWARD_GOTO_COMMISSION_WHITE

COMMISSION_SWITCH = Switch('Commission_switch', is_selector=True)
COMMISSION_SWITCH.add_state('daily', COMMISSION_DAILY)
COMMISSION_SWITCH.add_state('urgent', COMMISSION_URGENT)
COMMISSION_SCROLL = Scroll(COMMISSION_SCROLL_AREA, color=(247, 211, 66), name='COMMISSION_SCROLL')


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


class RewardCommission(UI, InfoHandler):
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
            if no_shortest.count < run.count:
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

    def _commission_start_click(self, comm, is_urgent=False, skip_first_screenshot=True):
        """
        Start a commission.

        Args:
            comm (Commission):
            is_urgent (bool):
            skip_first_screenshot:

        Returns:
            bool: If success

        Pages:
            in: page_commission
            out: page_commission, info_bar, commission details unfold
        """
        logger.hr('Commission start')
        self.interval_clear(COMMISSION_ADVICE)
        self.interval_clear(COMMISSION_START)
        comm_timer = Timer(7)
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break
            if count >= 3:
                # Restart game and handle commission recommend bug.
                # After you click "Recommend", your ships appear and then suddenly disappear.
                # At the same time, the icon of commission is flashing.
                logger.warning('Triggered commission list flashing bug')
                raise GameStuckError('Triggered commission list flashing bug')

            # Click
            if self.match_template_color(COMMISSION_START, offset=(5, 20), interval=7):
                self.device.click(COMMISSION_START)
                self.interval_reset(COMMISSION_ADVICE)
                comm_timer.reset()
                continue
            if self.handle_popup_confirm('COMMISSION_START'):
                self.interval_reset(COMMISSION_ADVICE)
                comm_timer.reset()
                continue
            # Accidentally entered dock
            if self.appear(DOCK_CHECK, offset=(20, 20), interval=3):
                logger.info(f'equip_enter {DOCK_CHECK} -> {BACK_ARROW}')
                self.device.click(BACK_ARROW)
                comm_timer.reset()
                continue
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
                self.device.click(COMMISSION_ADVICE)
                count += 1
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
                logger.warning(f'Commission not found: {comm}')
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

    def commission_receive(self, skip_first_screenshot=True):
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
                if self.appear(COMMISSION_CHECK, offset=(20, 20)):
                    # Leaving at page_commission
                    # Commission rewards may appear too slow, causing stuck in UI switching
                    break

                for button in [EXP_INFO_S_REWARD, GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3]:
                    if self.appear(button, interval=1):
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
                    click_timer.reset()
                    continue
                # Check GET_SHIP at last to handle random white background at page_main
                for button in [GET_SHIP]:
                    if self.appear(button, interval=1):
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
