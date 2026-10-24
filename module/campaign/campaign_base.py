from module.base.decorator import Config, cached_property
from module.campaign.campaign_ui import CampaignUI
from module.combat.auto_search_combat import AutoSearchCombat
from module.exception import CampaignEnd, MapEnemyMoved, ScriptError
from module.logger import logger
from module.map.map import Map
from module.map.map_base import CampaignMap


class CampaignBase(CampaignUI, Map, AutoSearchCombat):
    FUNCTION_NAME_BASE = 'battle_'
    MAP: CampaignMap

    def ensure_campaign_ui(self, name, mode='normal', skip_first_screenshot=True):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
            skip_first_screenshot:

        Returns:
            bool: If success.

        Raises:
            ScriptEnd: If failed to switch after retries

        Pages:
            in: Any page
            out: page_campaign or page_event
        """
        # Re-anchor emotion on the measured value before Alas picks a stage.
        # Everything that desyncs it, manual play, scheduler gap between two
        # tasks, changing ships or dorm placement, client side bug, happens
        # while Alas is not running, so one sync per task covers them all, and
        # Emotion ignores every call after the first one.
        #
        # This is the only safe spot. ensure_campaign_ui() is the one entry
        # every sortie task goes through, main story, event, raid, coalition
        # and GemsFarming alike, and it is where the stage gets chosen, by
        # campaign_set_chapter() plus campaign_get_entrance() below. The sync
        # navigates the game into the dorm and back, so it has to happen before
        # that choice and not after it. Syncing after the stage is picked takes
        # the game off the campaign page silently, the game decides on its own
        # which tab and scroll position to restore, and the entrance button
        # Alas clicks afterwards is a stale coordinate, which lands on another
        # map, an EX stage for example, and the run gets stuck there.
        #
        # ui_goto() can not be used for this. CampaignEvent.ui_goto_event()
        # returns early when the game is already on page_event, which is the
        # common case between two sorties, and no ui_goto() call happens then,
        # so the sync would be skipped exactly when it is needed.
        self.emotion.sync_from_dorm(self.device, origin=None)

        return super().ensure_campaign_ui(
            name=name,
            mode=mode,
            skip_first_screenshot=skip_first_screenshot,
        )

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

        remain = self.map.select(is_enemy=True) \
            .add(self.map.select(is_siren=True)) \
            .add(self.map.select(is_fortress=True)) \
            .delete(self.map.select(is_boss=True))
        logger.info(f'Enemy remain: {remain}')
        if remain.count > 0:
            if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
                if self.clear_any_enemy(sort=('cost_2',)):
                    return True
                return self.battle_default()
            else:
                if self.clear_bouncing_enemy():
                    return True
                if self.clear_siren():
                    return True
                self.clear_mechanism()
                return self.battle_default()
        else:
            result = self.battle_boss()
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
            if self.config.Error_HandleError:
                logger.warning('ScriptError, No combat executed, Withdrawing')
                self.withdraw()
            else:
                raise ScriptError('No combat executed.')

        return result

    def run(self):
        logger.hr(self.ENTRANCE, level=2)

        # Enter map
        self.emotion.check_reduce(self._map_battle)
        self.ENTRANCE.area = self.ENTRANCE.button
        self.enter_map(self.ENTRANCE, mode=self.config.Campaign_Mode)

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
        if self.config.Error_HandleError:
            logger.warning('ScriptError, Battle function exhausted, Withdrawing')
            try:
                self.withdraw()
            except CampaignEnd:
                pass
        else:
            raise ScriptError('Battle function exhausted.')

    @cached_property
    def _map_battle(self):
        """
        Returns:
            int: Battle on this map.
        """
        for data in self.MAP.spawn_data:
            if 'boss' in data:
                if 'battle' in data:
                    return data['battle'] + 1
                else:
                    logger.warning('No battle count in spawn_data')

        logger.warning('No boss data found in spawn_data')
        return 0

    def auto_search_execute_a_battle(self):
        logger.hr(f'{self.FUNCTION_NAME_BASE}{self.battle_count}', level=2)
        self.auto_search_moving()
        self.auto_search_combat(fleet_index=self.fleet_show_index)
        self.battle_count += 1
