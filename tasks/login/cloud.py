import re

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset, random_rectangle_vector_opted
from module.device.method.utils import AreaButton
from module.exception import GameNotRunningError, RequestHumanTakeover
from module.logger import logger


class XPath:
    """
    xpath 元素，元素可通过 uiautomator2 内的 weditor.exe 查找
    """

    """
    登录界面元素
    """
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
    # 排队剩余时间
    QUEUE_REMAIN = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvQueueInfoWaitTimeContent"]'

    """
    游戏界面元素
    """
    # 网络状态 简洁
    FLOAT_STATE_SIMPLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvSimpleNetStateMode"]'
    # 网络状态 详细
    FLOAT_STATE_DETAIL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_ping_value"]'
    """
    悬浮窗及侧边栏元素
    """
    # 悬浮窗
    FLOAT_WINDOW = '//*[@class="android.widget.ImageView"]'
    # 弹出侧边栏的 节点信息
    # 将这个区域向右偏移作为退出悬浮窗的按钮
    FLOAT_DELAY = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_node_region"]'
    # 弹出侧边栏的滚动区域
    SCROLL_VIEW = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/innerScrollView"]'
    # 画质选择 超高清
    # 选中时selected=True
    SETTING_BITRATE_UHD = '//*[@text="超高清"]'
    # 网络状态 开关
    SETTING_NET_STATE_TOGGLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/sw_net_state"]'
    SETTING_NET_STATE_SIMPLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mTvTitleOfSimpleMode"]'
    SETTING_NET_STATE_DETAIL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mTvTitleOfDetailMode"]'
    # 问题反馈
    SETTING_PROBLEM = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_problem"]'
    # 下载游戏
    SETTING_DOWNLOAD = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_downloadGame"]'


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
            in: START_GAME
            out: page_main
        """
        logger.hr('Cloud enter')
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            button = self.xpath(XPath.FLOAT_WINDOW)
            if self.appear(button):
                # Confirm float window size
                width, height = button.size
                if (width < 120 and height < 120) and (width / height < 0.6 or height / width < 0.6):
                    logger.info('Cloud game entered')
                    break

            # Queue daemon
            button = self.xpath(XPath.QUEUE_REMAIN)
            if self.appear(button):
                remain = button.text
                logger.info(f'Queue remain: {remain}')
                self.device.stuck_record_clear()

            # Click
            if self.appear_then_click(XPath.START_GAME):
                continue
            if self.appear(XPath.POPUP_CONFIRM, interval=5):
                title = self.xpath(XPath.POPUP_TITLE).text
                logger.info(f'Popup: {title}')
                # 计费提示
                # 本次游戏将使用畅玩卡无限畅玩
                # - 进入游戏(9s) - 退出游戏
                if title == '计费提示':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 是否使用星云币时长进入游戏
                # 使用后可优先排队进入游戏，本次游戏仅可使用星云币时长，无法消耗免费时长
                # - 确认使用 - 暂不使用
                if title == '是否使用星云币时长进入游戏':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 连接中断
                # 因为您长时间未操作游戏，已中断连接，错误码: -1022
                # - 退出游戏
                if title == '连接中断':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue

        # Disable net state display
        if self._cloud_net_state_appear():
            self._cloud_setting_disable_net_state()
        # Login to game
        from tasks.login.login import Login
        Login(config=self.config, device=self.device).handle_app_login()

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

    def _cloud_setting_disable_net_state(self, skip_first=True):
        """
        Pages:
            in: page_main
            out: page_main
        """
        self._cloud_setting_enter(skip_first=skip_first)

        skip_first = True
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            button = self.xpath(XPath.SETTING_BITRATE_UHD)
            if self.appear(button, interval=3):
                if not button.selected:
                    logger.info('Set bitrate to UHD')
                    self.device.click(button)
                    continue
            if self.appear(XPath.SETTING_NET_STATE_TOGGLE):
                if self.appear(XPath.SETTING_NET_STATE_SIMPLE) or self.appear(XPath.SETTING_NET_STATE_DETAIL):
                    logger.info('Set net state to disabled')
                    self.appear_then_click(XPath.SETTING_NET_STATE_TOGGLE, interval=3)
                    continue
                else:
                    logger.info('Net state display disabled')
                    break
            # Scroll down
            if not self.appear(XPath.SETTING_PROBLEM):
                area = self.xpath(XPath.SCROLL_VIEW).area
                # An area safe to swipe
                area = (area[0], area[1], area[0] + 25, area[3])
                p1, p2 = random_rectangle_vector_opted(
                    (0, -450), box=area, random_range=(-10, -30, 10, 30), padding=2)
                self.device.swipe(p1, p2, name='SETTING_SCROLL')
                continue

        self._cloud_setting_exit(skip_first=True)

    def _cloud_net_state_appear(self):
        """
        Returns:
            bool: True if net state display is enabled
        """
        if self.appear(XPath.FLOAT_STATE_SIMPLE):
            logger.attr('Net state', 'FLOAT_STATE_SIMPLE')
            return True
        if self.appear(XPath.FLOAT_STATE_DETAIL):
            logger.attr('Net state', 'FLOAT_STATE_DETAIL')
            return True
        logger.attr('Net state', None)
        return False

    def cloud_ensure_ingame(self):
        """
        Pages:
            in: Any
            out: page_main
        """
        logger.hr('Cloud ensure ingame', level=1)

        with self.config.multi_set():
            if self.config.Emulator_GameClient != 'cloud_android':
                self.config.Emulator_GameClient = 'cloud_android'
            if self.config.Emulator_PackageName != 'CN-Official':
                self.config.Emulator_PackageName = 'CN-Official'
            if self.config.Optimization_WhenTaskQueueEmpty != 'close_game':
                self.config.Optimization_WhenTaskQueueEmpty = 'close_game'

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

    def cloud_keep_alive(self):
        """
        Randomly do something to prevent being kicked

        WARNING:
            this may cause extra fee
        """
        logger.hr('cloud_keep_alive', level=2)
        while 1:
            self.device.sleep((45, 60))

            logger.info('cloud_keep_alive')
            self._cloud_setting_enter(skip_first=False)
            self._cloud_setting_exit(skip_first=True)


if __name__ == '__main__':
    self = LoginAndroidCloud('src')
    self.cloud_ensure_ingame()
    self.cloud_keep_alive()
