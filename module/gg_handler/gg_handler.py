from module.gg_handler.gg_data import GGData
from module.gg_handler.gg_u2 import GGU2
from module.gg_handler.gg_screenshot import GGScreenshot
from module.config.utils import deep_get, deep_set
from module.logger import logger
from module.base.timer import timeout


class GGHandler:
    """
    A module to handle needs of cheaters
    Args:
        config: AzurlaneConfig
        device: Device
    """

    def __init__(self, config=None, device=None):
        self.config = config
        self.device = device
        self.factor = deep_get(self.config.data,
                               'GameManager.GGHandler.GGMultiplyingFactor',
                               default=200)
        self.method = deep_get(self.config.data,
                               'GameManager.GGHandler.GGMethod',
                               default='screenshot')

    def restart(self, crashed=False):
        from module.handler.login import LoginHandler
        _crashed = crashed
        for _ in range(2):
            try:
                if _crashed:
                    timeout(self.handle_before_restart, timeout=60)
                timeout(LoginHandler(config=self.config, device=self.device).app_restart, timeout_sec=600)
                return True
            except Exception as e:
                if _crashed:
                    from module.notify import handle_notify
                    handle_notify(self.config.Error_OnePushConfig,
                                  title=f"Alas <{self.config.config_name}> crashed",
                                  content=f"<{self.config.config_name}> "
                                          f"RequestHumanTakeover\n"
                                          f"Maybe your emulator died"
                                  )
                    exit(1)
                _crashed = True

    def set(self, mode=True):
        """
            Set the GG status to True/False.
            Args:
                mode: bool
        """
        logger.hr('Enabling GG')
        gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')
        if mode:
            if self.method == 'screenshot' or gg_package_name == 'com.':
                GGScreenshot(config=self.config, device=self.device) \
                    .gg_set(mode=True, factor=self.factor)
            elif self.method == 'u2':
                GGU2(config=self.config, device=self.device) \
                    .set_on(factor=self.factor)
        else:
            self.gg_reset()

    def skip_error(self) -> bool:
        """
        Close all the windows of GG.
        Often to be used when game restarts with GG enabled.
        Returns:
            bool: Whether GG error panel occurs
        """
        gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')
        if self.method == 'screenshot' or gg_package_name == 'com.':
            return \
                GGScreenshot(config=self.config, device=self.device).skip_error()
        elif self.method == 'u2':
            return \
                GGU2(config=self.config, device=self.device).skip_error()

    def check_config(self) -> dict:
        """
        Reset GG config to the user's config and return gg_data.
        Returns:
            gg_data: dict = {
                        'gg_enable' : bool = Whether GG manager enabled,
                        'gg_auto' : bool = Whether to start GG before tasks,
                        'gg_on' : bool = Whether multiplier is on now}
        """
        gg_enable = deep_get(d=self.config.data, keys='GameManager.GGHandler.Enabled', default=False)
        gg_auto = deep_get(d=self.config.data, keys='GameManager.GGHandler.AutoRestartGG', default=False)
        GGData(self.config).set_data(target='gg_enable', value=gg_enable)
        GGData(self.config).set_data(target='gg_auto', value=gg_auto)
        gg_data = GGData(self.config).get_data()
        logger.info(f'GG status:')
        logger.info(
            f'Enabled={gg_data["gg_enable"]} AutoRestart={gg_data["gg_auto"]} Current stage={gg_data["gg_on"]}')
        return gg_data

    def handle_before_restart(self):
        _need_restart_atx = deep_get(d=self.config.data, keys='GameManager.GGHandler.RestartATX')
        if self.method == 'u2' and _need_restart_atx:
            try:
                timeout(self.device.restart_atx, 60)
            except Exception:
                from module.notify import handle_notify
                handle_notify(self.config.Error_OnePushConfig,
                              title=f"Alas <{self.config.config_name}> Emulator error",
                              content=f"<{self.config.config_name}> RequestHumanTakeover\nMaybe your emulator died", )
                exit(1)
            import uiautomator2 as u2
            logger.info('Reset UiAutomator')
            u2.connect(self.config.Emulator_Serial).reset_uiautomator()

    def handle_restart(self):
        """
        Handle the restart errors of GG.
        """
        gg_data = GGData(config=self.config).get_data()
        gg_enable = gg_data['gg_enable']
        if gg_enable:
            GGData(config=self.config).set_data(target='gg_on', value=False)
            logger.info(f'GG status:')
            logger.info(
                f'Enabled={gg_data["gg_enable"]} AutoRestart={gg_data["gg_auto"]} Current stage={gg_data["gg_on"]}')
            if not self.skip_error():
                logger.hr('Assume game died without GG panel')

    def gg_reset(self):
        """
        Force restart the game to reset GG status to False
        """
        gg_data = GGData(self.config).get_data()
        if gg_data['gg_enable'] and gg_data['gg_on']:
            logger.hr('Disabling GG')
            self.restart()
            logger.attr('GG', 'Disabled')

    def check_status(self, mode=True):
        """
        A check before a task begins to decide whether to enable GG and set it.
        Args:
            mode: The multiplier status when finish the check.
        """
        gg_data = GGData(self.config).get_data()
        if gg_data['gg_enable']:
            gg_auto = mode if deep_get(d=self.config.data,
                                       keys='GameManager.GGHandler.AutoRestartGG',
                                       default=False) else False
            logger.info(f'Check GG status:')
            logger.info(
                f'Enabled={gg_data["gg_enable"]} AutoRestart={gg_data["gg_auto"]} Current stage={gg_data["gg_on"]}')
            if gg_auto:
                if not gg_data['gg_on']:
                    self.set(True)
            elif gg_data['gg_on']:
                self.gg_reset()

    def power_limit(self, task=''):
        """
        Forced final check before some dangerous tasks for cheaters.
        If power is too high, disable the multiplier and assume the user need GG to be Enabled before the other tasks.
        Args:
            task: str = What task it is to limit power, default limit is 17000 for front ships.
        """
        from module.gg_handler.assets import OCR_PRE_BATTLE_CHECK
        from module.ocr.ocr import Digit
        self.device.screenshot()
        OCR_CHECK = Digit(OCR_PRE_BATTLE_CHECK, letter=(255, 255, 255), threshold=128)
        ocr = OCR_CHECK.ocr(self.device.image)
        from module.config.utils import deep_get
        limit = deep_get(self.config.data, keys=f'GameManager.PowerLimit.{task}', default=17000)
        logger.attr('Power Limit', limit)
        if ocr >= limit:
            logger.critical('There''s high chance that GG is on, restart to disable it')
            from module.gg_handler.gg_data import GGData
            GGData(self.config).set_data(target='gg_on', value=False)
            GGData(self.config).set_data(target='gg_enable', value=True)
            deep_set(d=self.config.data, keys='GameManager.GGHandler.Enabled', value=True)
            deep_set(d=self.config.data, keys='GameManager.GGHandler.AutoRestartGG', value=True)
            self.config.task_call('Restart')
            self.config.task_delay(minute=0.5)
            self.config.task_stop('Restart for sake of safty')

    def handle_restart_before_tasks(self) -> bool:
        """
        Check if user need to restart everytime alas starts before tasks, and handle it.
        Returns:
            bool: If it needs restart first
        """
        gg_data = GGData(self.config).get_data()
        if (deep_get(d=self.config.data,
                     keys='GameManager.GGHandler.RestartEverytime',
                     default=True)
                and gg_data['gg_enable']):
            logger.info('Restart to reset GG status.')
            self.restart()
            return True
        return False

    def check_then_set_gg_status(self, task=''):
        """
        If task is in list _disabled or _group_enabled defined in this function,
        set gg to the defined status
        Args:
            task : str = the next task to run
        """
        _disabled_task = deep_get(self.config.data, 'GameManager.GGHandler.DisabledTask')
        """
            'disable_all_dangerous_task'
            'disable_meta_and_exercise'
            'disable_exercise'
            'enable_all'
        """
        _group_exercise = [
            'exercise'
        ]
        _group_meta = [
            'opsi_ash_assist',
            'opsi_ash_beacon'
        ]
        _group_raid = [
            'raid',
            'raid_daily'
        ]
        _group_personal_choice = [
            'guild'
        ]
        _group_enabled = [
            'hard',
            'sos',
            'war_archives',
            'event_a',
            'event_b',
            'event_c',
            'event_d',
            'event_sp',
            'maritime_escort',
            'opsi_explore',
            'opsi_daily',
            'opsi_obscure',
            'opsi_month_boss',
            'opsi_abyssal',
            'opsi_archive',
            'opsi_stronghold',
            'opsi_meowfficer_farming',
            'opsi_hazard1_leveling',
            'opsi_cross_month',
            'main_normal',
            'main_hard',
            'main',
            'main2',
            'event',
            'event2',
            'event3',
            'gems_farming',
            'c72_mystery_farming',
            'c122_medium_leveling',
            'c124_large_leveling',
        ]

        # Handle ignorance

        if _disabled_task == 'disable_meta_and_exercise':
            _disabled = _group_exercise + _group_meta
            _enabled = _group_enabled + _group_raid + _group_personal_choice
        elif _disabled_task == 'disable_exercise':
            _disabled = _group_exercise
            _enabled = _group_enabled + _group_personal_choice + _group_raid + _group_meta
        elif _disabled_task == 'enable_all':
            _enabled = _group_enabled + _group_personal_choice + _group_raid + _group_meta + _group_exercise
            _disabled = []
        elif _disabled_task == 'disable_guild_and_dangerous':
            _disabled = _group_exercise + _group_meta + _group_raid + _group_personal_choice
            _enabled = _group_enabled
        else:  # _disabled_task == 'disable_all_dangerous_task':
            _disabled = _group_exercise + _group_meta + _group_raid
            _enabled = _group_enabled + _group_personal_choice

        if task in _disabled:
            self.check_status(False)
        elif task in _enabled:
            self.check_status(True)
