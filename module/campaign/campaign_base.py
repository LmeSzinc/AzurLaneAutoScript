from module.base.button import Button
from module.logger import logger
from module.map.exception import CampaignEnd
from module.map.exception import ScriptError
from module.map.map import Map
from module.map.map_base import CampaignMap
from module.base.decorator import Config


class CampaignBase(Map):
    FUNCTION_NAME_BASE = 'battle_'
    ENTRANCE = Button(area=(), color=(), button=(), name='default_button')
    MAP: CampaignMap

    def battle_default(self):
        if self.clear_enemy():
            return True

        logger.warning('No battle executed.')
        return False

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=True)
    def execute_a_battle(self):
        logger.info('Using function: clear_all')
        self.clear_all_mystery()

        if self.battle_count >= 3:
            self.pick_up_ammo()

        if self.map.select(is_enemy=True, is_boss=False).count > 0:
            return self.battle_default()
        else:
            if self.config.FLEET_2:
                return self.fleet_2.clear_boss()
            else:
                return self.clear_boss()

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=False)
    def execute_a_battle(self):
        func = self.FUNCTION_NAME_BASE + 'default'
        for extra_battle in range(10):
            if hasattr(self, self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)):
                func = self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)
                break

        logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
        logger.info(f'Using function: {func}')
        func = self.__getattribute__(func)

        result = func()
        if not result:
            logger.warning('No combat executed.')
            raise ScriptError('No combat executed.')

        return result

    def run(self):
        logger.hr(self.ENTRANCE, level=2)
        self.handle_spare_fleet()
        self.ENTRANCE.area = self.ENTRANCE.button
        self.enter_map(self.ENTRANCE, mode=self.config.CAMPAIGN_MODE)
        self.handle_map_fleet_lock()
        self.handle_fleet_reverse()
        self.map_init(self.MAP)

        for _ in range(20):
            try:
                self.execute_a_battle()
            except CampaignEnd:
                logger.hr('Campaign end')
                break
