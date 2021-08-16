from module.base.decorator import Config, cached_property
from module.campaign.campaign_ui import CampaignUI
from module.combat.auto_search_combat import AutoSearchCombat
from module.exception import CampaignEnd, ScriptError, MapEnemyMoved
from module.logger import logger
from module.map.map import Map
from module.map.map_base import CampaignMap


class CampaignBase(CampaignUI, Map, AutoSearchCombat):
    FUNCTION_NAME_BASE = 'battle_'
    MAP: CampaignMap

    def battle_default(self):
        if self.clear_enemy():
            return True

        logger.warning('No battle executed.')
        return False

    def battle_boss(self):
        if self.brute_clear_boss():
            return True

        logger.warning('No battle executed.')
        return False

    @Config.when(POOR_MAP_DATA=True, MAP_CLEAR_ALL_THIS_TIME=False)
    def battle_function(self):
        logger.info('Using function: battle_with_poor_map_data')
        if self.fleet_2_break_siren_caught():
            return True
        self.clear_all_mystery()

        if self.battle_count >= 3:
            self.pick_up_ammo()

        if self.map.select(is_boss=True):
            if self.brute_clear_boss():
                return True
        else:
            if self.clear_siren():
                return True
            return self.clear_enemy()

        return False

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=True)
    def battle_function(self):
        logger.info('Using function: clear_all')
        if self.fleet_2_break_siren_caught():
            return True
        self.clear_all_mystery()

        if self.battle_count >= 3:
            self.pick_up_ammo()

        remain = self.map.select(is_enemy=True, is_boss=False)
        logger.info(f'Enemy remain: {remain}')
        if remain.count > 0:
            if self.clear_siren():
                return True

            self.clear_mechanism()

            return self.battle_default()
        else:
            backup = self.config.FLEET_BOSS
            if self.config.FLEET_2 != 0:
                self.config.FLEET_BOSS = 2
            result = self.battle_boss()
            self.config.FLEET_BOSS = backup
            return result

    @Config.when(MAP_CLEAR_ALL_THIS_TIME=False, POOR_MAP_DATA=False)
    def battle_function(self):
        func = self.FUNCTION_NAME_BASE + 'default'
        for extra_battle in range(10):
            if hasattr(self, self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)):
                func = self.FUNCTION_NAME_BASE + str(self.battle_count - extra_battle)
                break

        logger.info(f'Using function: {func}')
        func = self.__getattribute__(func)

        result = func()

        return result

    def execute_a_battle(self):
        logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
        prev = self.battle_count
        result = False
        for _ in range(10):
            try:
                result = self.battle_function()
                break
            except MapEnemyMoved:
                if self.battle_count > prev:
                    result = True
                    break
                else:
                    continue

        if not result:
            logger.warning('ScriptError, No combat executed.')
            self.device.send_notification('ScriptError', 'No combat executed, please check GUI.')
            if self.config.ENABLE_EXCEPTION:
                raise ScriptError('No combat executed.')
            else:
                logger.warning('ScriptError, Withdrawing because enable_exception = no')
                self.withdraw()

        return result

    def run(self):
        logger.hr(self.ENTRANCE, level=2)

        # Enter map
        if self.config.ENABLE_EMOTION_REDUCE:
            if not self.map_is_auto_search:
                self.emotion.wait()
            else:
                self.handle_auto_search_emotion_wait()
        self.ENTRANCE.area = self.ENTRANCE.button
        self.enter_map(self.ENTRANCE, mode=self.config.CAMPAIGN_MODE)

        # Map init
        if not self.map_is_auto_search:
            self.handle_map_fleet_lock()
            self.map_init(self.MAP)
        else:
            self.map = self.MAP
            self.battle_count = 0
            self.lv_reset()
            self.lv_get()

        # Run
        for _ in range(20):
            try:
                if not self.map_is_auto_search:
                    self.execute_a_battle()
                else:
                    self.auto_search_execute_a_battle()
            except CampaignEnd:
                logger.hr('Campaign end')
                return True

        # Exception
        logger.warning('Battle function exhausted.')
        if self.config.ENABLE_EXCEPTION:
            raise ScriptError('Battle function exhausted.')
        else:
            logger.warning('ScriptError, Battle function exhausted, Withdrawing because enable_exception = no')
            self.withdraw()

    @cached_property
    def _emotion_expected_reduce(self):
        """
        Returns:
            tuple(int): Mob fleet emotion reduce, BOSS fleet emotion reduce
        """
        default = (self.emotion.get_expected_reduce, self.emotion.get_expected_reduce)
        for data in self.MAP.spawn_data:
            if 'boss' in data:
                battle = data.get('battle')
                reduce = (battle * default[0], default[1])
                if self.config.AUTO_SEARCH_SETTING in ['fleet1_all_fleet2_standby', 'fleet1_standby_fleet2_all']:
                    reduce = (reduce[0] + reduce[1], 0)
                return reduce

        logger.warning('No boss data found in spawn_data')
        return default

    def auto_search_execute_a_battle(self):
        logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
        self.auto_search_moving()
        self.auto_search_combat(fleet_index=self.fleet_current_index)
        self.battle_count += 1
