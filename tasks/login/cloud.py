import re

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset
from module.device.method.utils import AreaButton
from module.exception import GameNotRunningError, RequestHumanTakeover
from module.logger import logger


class XPath:
    # 帐号登录界面的进入游戏按钮，有这按钮说明帐号没登录
    ACCOUNT_LOGIN = '//*[@text="进入游戏"]'
    # 登录后的弹窗，获得免费时长
    GET_REWARD = '//*[@text="点击空白区域关闭"]'
    # 补丁资源已更新，重启游戏可活动更好的游玩体验
    # - 下次再说 - 关闭游戏
    POPUP_TITLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/titleTv"]'
    POPUP_CONFIRM = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/confirmTv"]'
    POPUP_CANCEL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/cancelTv"]'
    # 畅玩卡的剩余时间
    REMAIN_SEASON_PASS = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvCardStatus"]'
    # 星云币时长：0 分钟
    REMAIN_PAID = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvMiCoinDuration"]'
    # 免费时长： 600 分钟
    REMAIN_FREE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvRemainingFreeTime"]'
    # 主界面的开始游戏按钮
    START_GAME = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/btnLauncher"]'
    # 悬浮窗
    FLOAT_WINDOW = '//*[@class="android.widget.ImageView"]'
    # 悬浮窗内的延迟
    # 将这个区域向右偏移作为退出悬浮窗的按钮
    FLOAT_DELAY = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_delay"]'

    '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/ivPingIcon"]'
    '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_ping"]'


class LoginAndroidCloud(ModuleBase):
    def _cloud_start(self, skip_first=False):
        """
        Pages:
            out: START_GAME
        """
        logger.hr('Cloud start')
        update_checker = Timer(2)
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self.appear(XPath.START_GAME):
                logger.info('Login to cloud main page')
                break
            if self.appear(XPath.ACCOUNT_LOGIN):
                logger.critical('Account not login, you must have login once before running')
                raise RequestHumanTakeover
            if update_checker.started() and update_checker.reached():
                if not self.device.app_is_running():
                    logger.error('Detected hot fixes from game server, game died')
                    raise GameNotRunningError('Game not running')
                update_checker.clear()

            # Click
            if self.appear_then_click(XPath.GET_REWARD):
                continue
            if self.appear_then_click(XPath.POPUP_CONFIRM):
                update_checker.start()
                continue

    def _cloud_get_remain(self):
        """
        Pages:
            in: START_GAME
        """
        regex = re.compile(r'(\d+)')

        text = self.xpath(XPath.REMAIN_SEASON_PASS).text
        logger.info(f'Remain season pass: {text}')
        if res := regex.search(text):
            season_pass = int(res.group(1))
        else:
            season_pass = 0

        text = self.xpath(XPath.REMAIN_PAID).text
        logger.info(f'Remain paid: {text}')
        if res := regex.search(text):
            paid = int(res.group(1))
        else:
            paid = 0

        text = self.xpath(XPath.REMAIN_FREE).text
        logger.info(f'Remain free: {text}')
        if res := regex.search(text):
            free = int(res.group(1))
        else:
            free = 0

        logger.info(f'Cloud remain: season pass {season_pass} days, {paid} min paid, {free} min free')
        with self.config.multi_set():
            self.config.stored.CloudRemainSeasonPass = season_pass
            self.config.stored.CloudRemainPaid = paid
            self.config.stored.CloudRemainFree = free

    def _cloud_enter(self, skip_first=False):
        """
        Pages:
            out: START_GAME
        """
        logger.hr('Cloud enter')
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self.appear(XPath.FLOAT_WINDOW):
                logger.info('Cloud game entered')
                break

            # Click
            if self.appear_then_click(XPath.START_GAME):
                continue
            if self.appear(XPath.POPUP_CONFIRM, interval=5):
                # 计费提示
                # 本次游戏将使用畅玩卡无限畅玩
                # - 进入游戏(9s) - 退出游戏
                title = self.xpath(XPath.POPUP_TITLE).text
                logger.info(f'Popup: {title}')
                if title == '计费提示':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 连接中断
                # 因为您长时间未操作游戏，已中断连接，错误码: -1022
                # - 退出游戏
                if title == '连接中断':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue

    def _cloud_setting_enter(self, skip_first=True):
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            if self.appear(XPath.FLOAT_DELAY):
                break

            if self.appear_then_click(XPath.FLOAT_WINDOW, interval=3):
                continue

    def _cloud_setting_exit(self, skip_first=True):
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            if self.appear(XPath.FLOAT_WINDOW):
                break

            if self.appear(XPath.FLOAT_DELAY, interval=3):
                area = self.xpath(XPath.FLOAT_DELAY).area
                area = area_offset(area, offset=(150, 0))
                button = AreaButton(area=area, name='CLOUD_SETTING_EXIT')
                self.device.click(button)
                continue

    def cloud_ensure_ingame(self):
        logger.hr('Cloud ensure ingame', level=1)
        for _ in range(3):
            if self.device.app_is_running():
                logger.info('Cloud game is already running')
                self.device.dump_hierarchy()

                if self.appear(XPath.START_GAME):
                    logger.info('Cloud game is in main page')
                    self._cloud_get_remain()
                    self._cloud_enter()
                    return True
                elif self.appear(XPath.FLOAT_WINDOW):
                    logger.info('Cloud game is in game')
                    return True
                elif self.appear(XPath.FLOAT_DELAY):
                    logger.info('Cloud game is in game with float window expanded')
                    self._cloud_setting_exit()
                    return True
                elif self.appear(XPath.POPUP_CONFIRM):
                    logger.info('Cloud game have a popup')
                    self._cloud_enter()
                    return True
                else:
                    try:
                        self._cloud_start()
                    except GameNotRunningError:
                        continue
                    self._cloud_get_remain()
                    self._cloud_enter()
                    return True
            else:
                logger.info('Cloud game is not running')
                self.device.app_start()
                try:
                    self._cloud_start()
                except GameNotRunningError:
                    continue
                self._cloud_get_remain()
                self._cloud_enter()
                return True

        logger.error('Failed to enter cloud game after 3 trials')
        return False
