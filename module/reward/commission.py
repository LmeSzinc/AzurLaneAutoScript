import re
from datetime import datetime, timedelta

from scipy import signal

from module.base.decorator import Config
from module.base.timer import Timer
from module.base.utils import *
from module.exception import GameStuckError
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.ocr.ocr import Ocr
from module.reward.assets import *
from module.ui.page import page_reward, page_commission, CAMPAIGN_CHECK
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from module.ui.ui import UI

dictionary_cn = {
    'major_comm': ['自主训练', '对抗演习', '科研任务', '工具整备', '战术课程', '货物运输'],
    'daily_comm': ['日常资源开发', '高阶战术研发'],
    'extra_drill': ['航行训练', '防卫巡逻', '海域浮标检查作业'],
    'extra_part': ['委托'],
    'extra_cube': ['演习'],
    'extra_oil': ['油田'],
    'extra_book': ['商船护卫'],
    'urgent_drill': ['运输部队', '侦查部队', '主力部队', '精锐部队'],
    'urgent_part': ['维拉', '伊', '多伦瓦', '恐班纳', '马内', '萌'],
    'urgent_book': ['土豪尔', '姆波罗', '马拉基', '卡波罗', '玛丽', '特林'],
    'urgent_box': ['装备', '物资'],
    'urgent_cube': ['解救', '敌袭'],
    'urgent_gem': ['要员', '度假', '巡视'],
    'urgent_ship': ['观舰'],
}
dictionary_en = {
    'daily_comm': ['DAILY RESOURCE EXTRACTION', 'AWAKENING TACTICAL RESEARCH'],
    'extra_drill': ['SAILING', 'BUOY', 'FRONTIER', 'COASTAL', 'SALING'],
    'extra_part': ['VEIN', 'FOREST'],
    'extra_cube': ['FLEET ESCORT EXERCISE', 'FLEET EXERCISE', 'FLEET CARGO TRANSPORT', 'FLEET COMBAT EXERCISE'],
    'extra_oil': ['OIL'],
    'extra_book': ['MERCHANT ESCORT'],
    'urgent_drill': ['CARGO DEFENSE', 'DESTROY', 'COASTAL'],
    'urgent_part': ['LAVELLA', 'MAUI', 'RENDOVA', 'KONGBANNA', 'MANNE', 'ISLE'],
    'urgent_book': ['TYRANT', 'PORO', 'MAKIRA', 'KAPOLO', 'MARY', 'KOTLIN'],
    'urgent_box': ['GEAR', 'HANDOVER'],
    'urgent_cube': ['ENEMY ATTACK', 'MERCHANT RESCUE'],
    'urgent_gem': ['VIP', 'HOLIDAY ESCORT', 'PATROL ESCORT'],
    'urgent_ship': ['LAUNCH'],
    'major_comm': ['SELF TRAINING', 'DEFENSE EXERCISE', 'RESEARCH MISSION', 'TOOL PREP', 'TACTICAL CLASS', 'CARGO TRANSPORT'],
}
dictionary_jp = {
    'major_comm': ['初級自主訓練', '中級自主訓練', '上級自主訓練', '初級対抗演習', '中級対抗演習', '上級対抗演習', '初級科学研究', '中級科学研究', '上級科学研究', '初級資材整理', '中級資材整理', '上級資材整理', '初級戦術課程', '中級戦術課程', '上級戦術課程', '初級貨物輸送', '中級貨物輸送', '上級貨物輸送'],
    'daily_comm': ['日常資源開発', '覚醒実証研究'],
    'extra_drill': ['短距離練習航海', '中距離練習航海', '外洋練習航海', '近海防衛巡回', '前線基地防衛巡回', '海域浮標保守作業'],
    'extra_part': ['初級木材輸送護衛', '中級木材輸送護衛', '上級木材輸送護衛', '初級鉄鋼輸送護衛', '中級鉄鋼輸送護衛', '上級鉄鋼輸送護衛'],
    'extra_cube': ['船団護衛演習', '艦隊輸送演習', '艦隊実弾演習', '装備慣熟演習', '艦隊慣熟演習', '艦隊運動演習'],
    'extra_oil': ['小型油田開発', '中型油田開発', '大型油田開発'],
    'extra_book': ['小型船団護衛', '中型船団護衛', '大型船団護衛'],
    'urgent_drill': ['敵偵察部隊迎撃', '敵主力艦隊撃破', '敵精鋭部隊撃破', '輸送部隊護衛'],
    'urgent_part': ['近海掃海任務', '近海航行展示', '離島火力支援', '離島兵員輸送', '外敵生態調査', '兵站航路確保'],
    'urgent_book': ['離島物資輸送', '近海パトロール', '離島漸減支援', '外敵動静哨戒', '前線部隊支援', '外敵中枢偵察'],
    'urgent_box': ['装備輸送', '物資交換', '装備試験'],
    'urgent_cube': ['船団救出', '敵襲'],
    'urgent_gem': ['要人護衛', '休暇護衛'],
    'urgent_ship': ['小型観艦式', '連合艦隊観艦式', '多国連合観艦式'],
}
COMMISSION_SWITCH = Switch('Commission_switch', is_selector=True)
COMMISSION_SWITCH.add_status('daily', COMMISSION_DAILY)
COMMISSION_SWITCH.add_status('urgent', COMMISSION_URGENT)
COMMISSION_SCROLL = Scroll(COMMISSION_SCROLL_AREA, color=(247, 211, 66), name='COMMISSION_SCROLL')


class Commission:
    button: Button
    name: str
    genre: str
    status: str
    duration: timedelta
    expire: timedelta

    def __init__(self, image, y, config):
        self.config = config
        self.y = y
        self.stack_y = y
        self.area = (188, y - 119, 1199, y)
        self.image = image
        self.valid = True
        self.commission_parse()

    @Config.when(SERVER='en')
    def commission_parse(self):
        # Name
        # This is different from CN, EN has longer names
        area = area_offset((176, 23, 420, 53), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='COMMISSION')
        ocr = Ocr(button, lang='cnocr')
        self.button = button
        self.name = ocr.ocr(self.image)
        self.genre = self.commission_name_parse(self.name.upper())

        # Duration time
        area = area_offset((290, 68, 390, 95), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='DURATION')
        ocr = Ocr(button, alphabet='0123456789:')
        self.duration = self.parse_time(ocr.ocr(self.image))

        # Expire time
        area = area_offset((-49, 68, -45, 84), self.area[0:2])
        button = Button(area=area, color=(189, 65, 66),
                        button=area, name='IS_URGENT')
        if button.appear_on(self.image):
            area = area_offset((-49, 67, 45, 94), self.area[0:2])
            button = Button(area=area, color=(), button=area, name='EXPIRE')
            ocr = Ocr(button, alphabet='0123456789:')
            self.expire = self.parse_time(ocr.ocr(self.image))
        else:
            self.expire = None

        # Status
        area = area_offset((179, 71, 187, 93), self.area[0:2])
        dic = {
            0: 'finished',
            1: 'running',
            2: 'pending'
        }
        color = get_color(self.image, area)
        # if self.genre == 'doa_daily':
        #     color -= [50, 30, 20]
        self.status = dic[int(np.argmax(color))]

    @Config.when(SERVER='jp')
    def commission_parse(self):
        # Name
        area = area_offset((176, 23, 420, 53), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='COMMISSION')
        ocr = Ocr(button, lang='jp')
        self.button = button
        self.name = ocr.ocr(self.image)
        self.genre = self.commission_name_parse(self.name)

        # Duration time
        area = area_offset((290, 68, 390, 95), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='DURATION')
        ocr = Ocr(button, alphabet='0123456789:')
        self.duration = self.parse_time(ocr.ocr(self.image))

        # Expire time
        area = area_offset((-49, 68, -45, 84), self.area[0:2])
        button = Button(area=area, color=(189, 65, 66),
                        button=area, name='IS_URGENT')
        if button.appear_on(self.image):
            area = area_offset((-49, 67, 45, 94), self.area[0:2])
            button = Button(area=area, color=(), button=area, name='EXPIRE')
            ocr = Ocr(button, alphabet='0123456789:')
            self.expire = self.parse_time(ocr.ocr(self.image))
        else:
            self.expire = None

        # Status
        area = area_offset((179, 71, 187, 93), self.area[0:2])
        dic = {
            0: 'finished',
            1: 'running',
            2: 'pending'
        }
        color = get_color(self.image, area)
        # if self.genre == 'doa_daily':
        #     color -= [50, 30, 20]
        self.status = dic[int(np.argmax(color))]

    @Config.when(SERVER='cn')
    def commission_parse(self):
        # Name
        area = area_offset((176, 23, 420, 53), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='COMMISSION')
        ocr = Ocr(button, lang='cnocr', threshold=256)
        self.button = button
        self.name = ocr.ocr(self.image)
        self.genre = self.commission_name_parse(self.name)

        # Duration time
        area = area_offset((290, 68, 390, 95), self.area[0:2])
        button = Button(area=area, color=(), button=area, name='DURATION')
        ocr = Ocr(button, alphabet='0123456789:')
        self.duration = self.parse_time(ocr.ocr(self.image))

        # Expire time
        area = area_offset((-49, 68, -45, 84), self.area[0:2])
        button = Button(area=area, color=(189, 65, 66),
                        button=area, name='IS_URGENT')
        if button.appear_on(self.image):
            area = area_offset((-49, 67, 45, 94), self.area[0:2])
            button = Button(area=area, color=(), button=area, name='EXPIRE')
            ocr = Ocr(button, alphabet='0123456789:')
            self.expire = self.parse_time(ocr.ocr(self.image))
        else:
            self.expire = None

        # Status
        area = area_offset((179, 71, 187, 93), self.area[0:2])
        dic = {
            0: 'finished',
            1: 'running',
            2: 'pending'
        }
        color = get_color(self.image, area)
        # if self.genre == 'doa_daily':
        #     color -= [50, 30, 20]
        self.status = dic[int(np.argmax(color))]

    def __str__(self):
        if self.valid:
            if self.expire:
                return f'{self.name} (Genre: {self.genre}, Status: {self.status}, Duration: {self.duration}, Expire: {self.expire})'
            else:
                return f'{self.name} (Genre: {self.genre}, Status: {self.status}, Duration: {self.duration})'
        else:
            return f'{self.name} (Invalid)'

    def __eq__(self, other):
        """
        Args:
            other (Commission):

        Returns:
            bool:
        """
        threshold = timedelta(seconds=120)
        if not self.valid or not other.valid:
            return False
        if self.genre != other.genre or self.status != other.status:
            return False
        if (other.duration < self.duration - threshold) or (other.duration > self.duration + threshold):
            return False
        if (not self.expire and other.expire) or (self.expire and not other.expire):
            return False
        if self.expire and other.expire:
            if (other.expire < self.expire - threshold) or (other.expire > self.expire + threshold):
                return False

        return True

    def parse_time(self, string):
        """
        Args:
            string (str): Such as 01:00:00, 05:47:10, 17:50:51.

        Returns:
            timedelta: datetime.timedelta instance.
        """
        string = string.replace('D', '0')  # Poor OCR
        result = re.search('(\d+):(\d+):(\d+)', string)
        if not result:
            logger.warning(f'Invalid time string: {string}')
            self.valid = False
            return None
        else:
            result = [int(s) for s in result.groups()]
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])

    @Config.when(SERVER='en')
    def commission_name_parse(self, string):
        """
        Args:
            string (str): Commission name, such as 'NYB要员护卫'.

        Returns:
            str: Commission genre, such as 'urgent_gem'.
        """
        # string = string.replace(' ', '').replace('-', '')
        # if self.is_doa_commission():
        #     return 'doa_daily'
        for key, value in dictionary_en.items():
            for keyword in value:
                if keyword in string:
                    return key

        logger.warning(f'Name with unknown genre: {string}')
        self.valid = False
        return ''

    @Config.when(SERVER='jp')
    def commission_name_parse(self, string):
        """
        Args:
            string (str): Commission name, such as 'NYB要员护卫'.

        Returns:
            str: Commission genre, such as 'urgent_gem'.
        """
        # if self.is_doa_commission():
        #     return 'doa_daily'
        import jellyfish
        min_key = ''
        min_distance = 100
        string = re.sub(r'[\x00-\x7F]', '', string)
        for key, value in dictionary_jp.items():
            for keyword in value:
                distance = jellyfish.levenshtein_distance(keyword, string)
                if distance < min_distance:
                    min_key = key
                    min_distance = distance
        if min_distance < 3:
            return min_key

        logger.warning(f'Name with unknown genre: {string}')
        self.valid = False
        return ''

    @Config.when(SERVER=None)
    def commission_name_parse(self, string):
        """
        Args:
            string (str): Commission name, such as 'NYB要员护卫'.

        Returns:
            str: Commission genre, such as 'urgent_gem'.
        """
        # if self.is_doa_commission():
        #     return 'doa_daily'
        for key, value in dictionary_cn.items():
            for keyword in value:
                if keyword in string:
                    return key

        logger.warning(f'Name with unknown genre: {string}')
        self.valid = False
        return ''

    # def is_doa_commission(self):
    #     """
    #     Event commission in Vacation Lane, with pink area on the left.
    #
    #     Returns:
    #         bool:
    #     """
    #     area = area_offset((5, 5, 30, 30), self.area[0:2])
    #     return color_similar(color1=get_color(self.image, area), color2=(239, 166, 231))


class CommissionGroup:
    show = (188, 67, 1199, 692)
    height = 360  # About 2.5 commission height
    lower = int(show[3] - height - 10)
    template_area = (620, lower, 1154, lower + height)

    def __init__(self, config):
        self.config = config
        self.template = None
        self.swipe = 0
        self.commission = []

    def __contains__(self, item):
        for commission in self.commission:
            if commission == item:
                return True

        return False

    def __iter__(self):
        return iter(self.commission)

    def __bool__(self):
        return len(self.commission) > 0

    @property
    def count(self):
        return len(self.commission)

    def merge(self, image):
        """Load commissions from image.
        If you want to load commissions from multiple image,
        make sure that the next one and previous one have something same.
        Which means, you merge a image, then swipe a little bit, then merge another image.

        Args:
            image (PIl.Image.Image):
        """
        # Find swipe distance
        if self.template is None:
            self.template = np.array(image.crop(self.template_area))
            self.swipe = 0
        res = cv2.matchTemplate(
            self.template, np.array(image), cv2.TM_CCOEFF_NORMED)
        _, similarity, _, position = cv2.minMaxLoc(res)
        if similarity < 0.85:
            logger.warning(
                f'Low similarity when finding swipe. Similarity: {similarity}, Position: {position}')
        self.swipe -= position[1] - self.template_area[1]
        self.template = np.array(image.crop(self.template_area))

        # Find commission position
        color_height = np.mean(image.crop(
            (597, 0, 619, 720)).convert('L'), axis=1)
        parameters = {'height': 200, 'distance': 100}
        peaks, _ = signal.find_peaks(color_height, **parameters)
        peaks = [y for y in peaks if y > 67 + 117]

        # Add commission to list
        for y in peaks:
            stack_y = y + self.swipe
            diff = np.array([c.stack_y - stack_y for c in self.commission])
            if np.any(np.abs(diff) < 3):
                continue
            commission = Commission(image, y=y, config=self.config)
            commission.stack_y = stack_y
            logger.info(f'Add commission: {commission}')
            self.commission.append(commission)


class RewardCommission(UI, InfoHandler):
    daily: CommissionGroup
    urgent: CommissionGroup
    daily_choose: CommissionGroup
    urgent_choose: CommissionGroup
    max_commission = 4

    def _commission_choose(self, daily, urgent, priority, time_limit=None):
        """
        Args:
            daily (CommissionGroup):
            urgent (CommissionGroup):
            priority (dict):
            time_limit (datetime):

        Returns:
            CommissionGroup, CommissionGroup: Chosen daily commission, Chosen urgent commission
        """
        # Count Commission
        commission = daily.commission + urgent.commission
        self.max_commission = 4
        # for comm in commission:
        #     if comm.genre == 'doa_daily':
        #         self.max_commission = 5
        running_count = int(
            np.sum([1 for c in commission if c.status == 'running']))
        logger.attr('Running', running_count)
        if running_count >= self.max_commission:
            return [], []

        # Calculate priority
        commission = [
            c for c in commission if c.valid and c.status == 'pending']
        comm_priority = []
        for comm in commission:
            pri = priority[comm.genre]
            if comm.duration <= timedelta(hours=2):
                pri += priority['duration_shorter_than_2']
            if comm.duration >= timedelta(hours=6):
                pri += priority['duration_longer_than_6']
            if comm.expire:
                if comm.expire <= timedelta(hours=2):
                    pri += priority['expire_shorter_than_2']
                if comm.expire >= timedelta(hours=6):
                    pri += priority['expire_longer_than_6']
            comm_priority.append(pri)

        # Sort
        commission = list(np.array(commission)[np.argsort(comm_priority)])[::-1]
        # Select priority > 0
        commission = [comm for comm in commission if priority[comm.genre] > 0]
        # Select within time_limit
        if time_limit:
            commission = [
                comm for comm in commission if datetime.now() + comm.duration <= time_limit]

        commission = commission[:self.max_commission - running_count]
        daily_choose, urgent_choose = CommissionGroup(self.config), CommissionGroup(self.config)
        for comm in commission:
            if comm in daily:
                daily_choose.commission.append(comm)
            if comm in urgent:
                urgent_choose.commission.append(comm)

        if daily_choose:
            logger.info('Choose daily commission')
            for comm in daily_choose:
                logger.info(comm)
        if urgent_choose:
            logger.info('Choose urgent commission')
            for comm in urgent_choose:
                logger.info(comm)

        return daily_choose, urgent_choose

    def _commission_ensure_mode(self, mode):
        return COMMISSION_SWITCH.set(mode, main=self)

    def _commission_mode_reset(self):
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

    @Config.when(DEVICE_CONTROL_METHOD='minitouch')
    def _commission_swipe(self, distance=190):
        # Distance of two commission is 146px
        p1, p2 = random_rectangle_vector(
            (0, -distance), box=(620, 67, 1154, 692), random_range=(-20, -5, 20, 5))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                         point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.sleep(0.3)
        self.device.screenshot()

    @Config.when(DEVICE_CONTROL_METHOD=None)
    def _commission_swipe(self, distance=300):
        # Distance of two commission is 146px
        p1, p2 = random_rectangle_vector(
            (0, -distance), box=(620, 67, 1154, 692), random_range=(-20, -5, 20, 5))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                         point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.sleep(0.3)
        self.device.screenshot()

    def _commission_swipe_to_top(self):
        if not COMMISSION_SCROLL.appear(main=self):
            return False
        COMMISSION_SCROLL.set_top(main=self, skip_first_screenshot=True)
        return True

    def _commission_scan_list(self):
        commission = CommissionGroup(self.config)
        commission.merge(self.device.image)
        if commission.count <= 3:
            return commission
        if not COMMISSION_SCROLL.appear(main=self):
            return commission

        prev = commission.count
        for _ in range(15):
            self._commission_swipe()
            commission.merge(self.device.image)
            if commission.count - prev <= 0:
                break
            prev = commission.count
            if COMMISSION_SCROLL.at_bottom(main=self):
                break

        return commission

    def _commission_scan_all(self):
        logger.hr('Scan daily')
        self._commission_ensure_mode('daily')
        self._commission_swipe_to_top()
        daily = self._commission_scan_list()

        logger.hr('Scan urgent')
        self._commission_ensure_mode('urgent')
        self._commission_swipe_to_top()
        urgent = self._commission_scan_list()

        logger.hr('Showing commission')
        logger.info('Daily commission')
        for comm in daily:
            logger.info(comm)
        if urgent.count:
            logger.info('Urgent commission')
            for comm in urgent:
                logger.info(comm)

        self.daily = daily
        self.urgent = urgent
        self.daily_choose, self.urgent_choose = self._commission_choose(
            self.daily,
            self.urgent,
            priority=self.config.COMMISSION_PRIORITY,
            time_limit=self.config.COMMISSION_TIME_LIMIT)
        return daily, urgent

    def _commission_start_click(self, comm):
        """
        Args:
            comm (Commission):
        """
        logger.info(f'Start commission {comm}')
        comm_timer = Timer(7)
        count = 0
        while 1:
            if comm_timer.reached():
                self.device.click(comm.button)
                comm_timer.reset()

            if self.handle_popup_confirm():
                comm_timer.reset()
                pass
            if self.appear_then_click(COMMISSION_ADVICE, offset=(5, 20), interval=7):
                count += 1
                comm_timer.reset()
                pass
            if self.appear_then_click(COMMISSION_START, offset=(5, 20), interval=7):
                comm_timer.reset()
                pass

            # End
            if self.handle_info_bar():
                break
            if count >= 3:
                # Restart game and handle commission recommend bug.
                # After you click "Recommend", your ships appear and then suddenly disappear.
                # At the same time, the icon of commission is flashing.
                logger.warning('Triggered commission list flashing bug')
                raise GameStuckError('Triggered commission list flashing bug')

            self.device.screenshot()

        return True

    def _commission_find_and_start(self, comm):
        """
        Args:
            comm (Commission):
        """
        logger.hr(f'Finding commission')
        logger.info(f'Finding commission {comm}')

        commission = CommissionGroup(self.config)
        prev = 0
        for _ in range(15):
            commission.merge(self.device.image)

            if commission.count - prev <= 0:
                return True
            prev = commission.count

            if comm in commission:
                # Update commission position.
                # Because once you start a commission, the commission list changes.
                for new_comm in commission:
                    if comm == new_comm:
                        comm = new_comm
                self._commission_start_click(comm)
                return True

            self._commission_swipe()

        logger.warning(f'Commission not found: {comm}')
        return False

    def commission_start(self):
        """
        Method to scan and run commissions.
        Make sure current page is page_commission before calls.
        """
        logger.hr('Commission scan', level=2)
        self._commission_scan_all()

        logger.hr('Commission run', level=2)
        if self.daily_choose:
            for comm in self.daily_choose:
                if not self._commission_ensure_mode('daily'):
                    self._commission_mode_reset()
                self._commission_swipe_to_top()
                self._commission_find_and_start(comm)
        if self.urgent_choose:
            for comm in self.urgent_choose:
                if not self._commission_ensure_mode('urgent'):
                    self._commission_mode_reset()
                self._commission_swipe_to_top()
                self._commission_find_and_start(comm)
        if not self.daily_choose and not self.urgent_choose:
            logger.info('No commission chose')

    def handle_commission_start(self):
        """Remember to make sure current page is page_reward before calls.

        Returns:
            bool: If runs a commission.
        """
        if not self.config.ENABLE_COMMISSION_REWARD:
            return False

        if not self.image_color_count(COMMISSION_HAS_PENDING, color=(74, 199, 173), threshold=221, count=40):
            logger.info('No commission pending')
            return False

        self.ui_goto(page_commission, skip_first_screenshot=True)
        # info_bar appears when get ship in Launch Ceremony commissions
        # This is a game bug, the info_bar shows get ship, will appear over and over again, until you click get_ship.
        self.handle_info_bar()

        self.commission_start()

        self.ui_goto(page_reward, skip_first_screenshot=True)
        return True

    def commission_notice_show_at_campaign(self):
        """
        Returns:
            bool: If any commission finished.
        """
        return self.appear(CAMPAIGN_CHECK) and self.appear(COMMISSION_NOTICE_AT_CAMPAIGN)
