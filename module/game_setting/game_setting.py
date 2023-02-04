from os import system
from adbutils import AdbError
from io import BytesIO

from module.base.base import ModuleBase
from module.game_setting.setting_generated import GameSettingsGenerated, Field
from module.logger import logger


class GameSetting(ModuleBase, GameSettingsGenerated):
    world_flag_consume_item = GameSettingsGenerated.world_flag('consume_item')
    world_flag_auto_save_area = GameSettingsGenerated.world_flag('auto_save_area')
    world_flag_story_tips = GameSettingsGenerated.world_flag('story_tips')
    autoBattle = Field(formatter=int, value=1, regex='AutoBattle')
    rare_ship_vibrate = Field(formatter=int, value=1, regex='rare_ship_vibrate')
    display_ship_get_effect = Field(formatter=int, value=1, regex='display_ship_get_effect')
    AUTOFIGHT_DOWN_FRAME = Field(formatter=int, value=1, regex='AUTOFIGHT_DOWN_FRAME')
    battleHideBg = Field(formatter=int, value=1, regex='battleHideBg')
    battleExposeLine = Field(formatter=int, value=1, regex='battleExposeLine')
    GYRO_ENABLE = Field(formatter=int, value=1, regex='GYRO_ENABLE')
    show_touch_effect = Field(formatter=int, value=1, regex='show_touch_effect')
    autoSubIsAcitve_51 = GameSettingsGenerated.autoSubIsAcitve('_51')
    autoSubIsAcitve = GameSettingsGenerated.autoSubIsAcitve('')
    data: str
    src: str
    tmp: str
    name: str
    push_flag: bool

    def __setattr__(self, key, value):
        if key in dir(self) and isinstance(getattr(self, key), Field):
            if getattr(self, key).value != value:
                self.push_flag = True
                getattr(self, key).value = value
                getattr(self, key).update(self)
        else:
            super().__setattr__(key, value)

    def pull_setting(self):
        """
        Pull game setting from emulator.

        Return:
            bool: If handled.
        """
        logger.info('Pull setting')
        buf = b''
        self.src = f'/data/data/{self.device.package}/shared_prefs/'
        self.tmp = f'/data/local/tmp/'
        self.name = f'{self.device.package}.v2.playerprefs.xml'
        logger.info('Source :' + self.src)
        self.device.adb_root()
        try:
            # Adaptation provided for Bluestacks, applicable to other emulators
            self.device.adb_shell(f'su -c "cp -rf {self.src + self.name} {self.tmp}"')
            self.device.adb_shell(f'su -c "chmod 777 {self.tmp + self.name}"')
            for chunk in self.device.adb.sync.iter_content(self.tmp + self.name):
                buf += chunk
        except AdbError:
            logger.warning('Unable to get game setting from emulator, '
                           'this might because the emulator does not have root access, '
                           'skip the game setting')
            return False

        self.data = buf.decode(encoding='utf-8')

        for key in dir(self):
            if isinstance(getattr(self, key), Field):
                getattr(self, key).find(self)
        return True

    def push_setting(self):
        """
        Push game setting into emulator.
        """
        logger.info('Push setting')
        if not self.push_flag:
            logger.info('No setting changed, skip push setting')
            return

        buf = self.data.encode(encoding='utf-8')
        self.device.adb.sync.push(BytesIO(buf), self.tmp + self.name)
        # cp -rf does not change the file permissions
        self.device.adb_shell(f'su -c "cp -rf {self.tmp + self.name} {self.src}"')

    def setting_game(self):
        """
        Set in-game settings.
        """
        logger.hr('Set in-game setting')
        if self.config.Emulator_PackageName != 'com.bilibili.azurlane':
            logger.warning('Set in-game setting is only supported for CN server')
            return

        if not self.pull_setting():
            return
        self.push_flag = False

        logger.info('Update setting')
        # Set strategy search option
        self.auto_switch_mode = '1'
        self.auto_switch_difficult_safe = 'only'
        self.auto_switch_wait = '1'
        self.auto_switch_wait_2 = '1'
        # Set game option
        self.fps_limit = '60'
        self.WorldBossProgressTipFlag = '200'
        self.world_flag_consume_item = '1'
        self.world_flag_auto_save_area = '0'
        self.world_flag_story_tips = '1'
        self.story_autoplay_flag = '1'
        self.story_speed_flag = '9'
        # Set other option
        self.autoBattle = '0'
        self.rare_ship_vibrate = '0'
        self.display_ship_get_effect = '0'
        self.show_touch_effect = '1'
        self.bgFitMode = '0'
        self.battleHideBg = '1'
        self.battleExposeLine = '0'
        self.AUTOFIGHT_BATTERY_SAVEMODE = '0'
        self.AUTOFIGHT_DOWN_FRAME = '0'
        self.QUICK_CHANGE_EQUIP = '0'
        self.GYRO_ENABLE = '0'
        # Set retire option
        self.QuickSelectRarity1 = '3'
        self.QuickSelectRarity2 = '4'
        self.QuickSelectRarity3 = '2'
        self.QuickSelectWhenHasAtLeastOneMaxstar = 'KeepNone'
        if self.QuickSelectWithoutMaxstar == 'KeepAll':
            self.QuickSelectWithoutMaxstar = 'KeepNeeded'
        # Set submarine option
        self.autoSubIsAcitve = '0'
        self.autoSubIsAcitve_51 = '1'
        self.world_sub_auto_call = '0'
        self.world_sub_call_line = '0'

        self.push_setting()


if __name__ == '__main__':
    GameSetting(config='alas').setting_game()
