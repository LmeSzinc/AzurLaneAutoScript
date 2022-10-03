from io import BytesIO

from module.base.base import ModuleBase
from module.exception import RequestHumanTakeover
from module.game_setting.setting_generated import GameSettingsGenerated, Field
from module.logger import logger


class GameSetting(ModuleBase, GameSettingsGenerated):
    world_flag_consume_item = GameSettingsGenerated.world_flag('consume_item')
    world_flag_auto_save_area = GameSettingsGenerated.world_flag('auto_save_area')
    world_flag_story_tips = GameSettingsGenerated.world_flag('story_tips')
    data: str
    src: str

    def __setattr__(self, key, value):
        if key in dir(self) and isinstance(getattr(self, key), Field):
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
        logger.info('pull setting')
        buf = b''
        self.src = f'/data/data/{self.device.package}/shared_prefs' \
                   f'/{self.device.package}.v2.playerprefs.xml'
        logger.info('Source :' + self.src)
        try:
            for chunk in self.device.adb.sync.iter_content(self.src):
                buf += chunk
        except FileNotFoundError:
            logger.warning('Unable to get game setting from emulator, '
                           'please check your emulator settings or turn off this feature')
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
        logger.info('push setting')
        buf = self.data.encode(encoding='utf-8')
        self.device.adb.sync.push(BytesIO(buf), self.src)

    def setting_game(self):
        """
        Set in-game settings.
        """
        logger.hr('Set in-game setting')
        if not self.pull_setting():
            raise RequestHumanTakeover
        logger.info('update setting')
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
        # Set retire option
        self.QuickSelectRarity1 = '3'
        self.QuickSelectRarity2 = '4'
        self.QuickSelectRarity3 = '2'
        self.QuickSelectWhenHasAtLeastOneMaxstar = 'KeepNone'
        if self.QuickSelectWithoutMaxstar == 'KeepAll':
            self.QuickSelectWithoutMaxstar = 'KeepNeeded'
        self.push_setting()


if __name__ == '__main__':
    GameSetting(config='alas').setting_game()
