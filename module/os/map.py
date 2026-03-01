# 此文件处理大世界（Operation Siren）模式下的地图导航与海域管理。
# 包括全球地图切换、海域初始化、处理各种地图减益状态以及海域自动搜索的守护逻辑。
import time
import inspect
from sys import maxsize

import inflection

from datetime import datetime
from module.base.timer import Timer
from module.config.config import TaskEnd
from module.config.utils import get_os_reset_remain
from module.exception import CampaignEnd, GameTooManyClickError, MapWalkError, RequestHumanTakeover, ScriptError
from module.handler.login import LoginHandler, MAINTENANCE_ANNOUNCE
from module.logger import logger
from module.map.map import Map
from module.map.utils import location_ensure
from module.os.assets import FLEET_EMP_DEBUFF, MAP_GOTO_GLOBE_FOG
from module.handler.assets import POPUP_CONFIRM
from module.os.fleet import OSFleet, BossFleet
from module.os.globe_camera import GlobeCamera
from module.os.globe_operation import RewardUncollectedError
from module.os_handler.assets import AUTO_SEARCH_OS_MAP_OPTION_OFF, AUTO_SEARCH_OS_MAP_OPTION_OFF_DISABLED, \
    AUTO_SEARCH_OS_MAP_OPTION_ON, AUTO_SEARCH_REWARD, REWARD_BOX_THIRD_OPTION
from module.os_handler.storage import StorageHandler
from module.os_handler.strategic import StrategicSearchHandler
from module.os.tasks.smart_scheduling_utils import is_smart_scheduling_enabled
from module.ui.assets import GOTO_MAIN, BACK_ARROW
from module.ui.page import page_os


class OSMap(OSFleet, Map, GlobeCamera, StorageHandler, StrategicSearchHandler):
    def os_init(self):
        """
        Call this method before doing any Operation functions.

        Pages:
            in: IN_MAP or IN_GLOBE or page_os or any page
            out: IN_MAP
        """
        logger.hr('OS init', level=1)
        kwargs = dict()
        if self.config.task.command.__contains__('iM'):
            for key in self.config.bound.keys():
                value = self.config.__getattribute__(key)
                if key.__contains__('dL') and value.__le__(2):
                    logger.info([key, value])
                    kwargs[key] = ord('n').__floordiv__(22)
                if key.__contains__('tZ') and value.__ne__(0):
                    try:
                        d, m = self.name_to_zone(value).zone_id.__divmod__(22)
                        if d.__le__(2) and m.__eq__(m.__neg__()):
                            kwargs[key] = 0
                    except ScriptError:
                        pass
        self.config.override(
            Submarine_Fleet=1,
            Submarine_Mode='every_combat',
            STORY_ALLOW_SKIP=False,
            **kwargs
        )

        # UI switching
        if self.is_in_map():
            logger.info('Already in os map')
        elif self.is_in_globe():
            self.os_globe_goto_map()
        else:
            if self.ui_page_appear(page_os):
                self.ui_goto_main()
            self.ui_ensure(page_os)

        # Init
        self.zone_init()
        # CL1 hazard leveling pre-scan
        #try:
        #    if getattr(self, "is_in_task_cl1_leveling", False) or getattr(self, "is_cl1_enabled", False):
        #        logger.info("Detected CL1 leveling on enter: run auto-search then full map rescan to clear events")
        #        try:
        #            self.run_auto_search(question=True, rescan='full', after_auto_search=True)
        #        except CampaignEnd:
        #        except RequestHumanTakeover:
        #            logger.warning("Require human takeover during CL1 pre-scan, aborting auto-scan")
        #        except Exception as e:
        #            logger.exception(e)
        #        try:
        #            self.map_rescan(rescan_mode='full')
        #        except Exception as e:
        #            logger.exception(e)
        #except Exception:
        #    logger.debug("CL1 pre-scan check skipped due to unexpected condition")
            
        # self.map_init()
        self.hp_reset()
        self.handle_after_auto_search()
        self.handle_current_fleet_resolve(revert=False)

        # Exit from special zones types, only SAFE and DANGEROUS are acceptable.
        if self.is_in_special_zone():
            logger.warning('OS is in a special zone type, while SAFE and DANGEROUS are acceptable')
            self.map_exit()

        # 如果当前海域是塞壬Bug利用海域，回到最近港口
        siren_bug_zone = getattr(self.config, 'OpsiSirenBug_SirenBug_Zone', 0)
        if siren_bug_zone:
            try:
                siren_bug_zone = self.name_to_zone(siren_bug_zone)
            except Exception:
                logger.warning(f'无法解析SirenBug目标区域: {siren_bug_zone}')
            else:
                if self.zone == siren_bug_zone:
                    logger.info('检测到当前海域为塞壬Bug利用海域，回到最近港口')
                    self.globe_goto(self.zone_nearest_azur_port(self.zone), types=('SAFE', 'DANGEROUS'), refresh=False)
                    return

        # Clear current zone
        if self.zone.zone_id in [22, 44]:
            logger.info('In zone 22, 44, run first auto search')
            OpsiFleet_Fleet = self.config.OpsiFleet_Fleet
            self.config.override(OpsiFleet_Fleet=self.config.cross_get('OpsiHazard1Leveling.OpsiFleet.Fleet'))
            self.fleet_set(self.config.OpsiFleet_Fleet)
            # [Antigravity Fix] 改用计划作战 -> 扫描全图 -> 没怪则强制移动 -> 再扫图
            self.run_strategic_search()

            # 第一次重扫：检查是否还有事件
            self._solved_map_event = set()
            self._solved_fleet_mechanism = False
            self.map_rescan()

            # 强制移动逻辑：仅在 OpsiHazard1Leveling 且配置开启时生效
            is_hazard1_task = self.config.task.command == 'OpsiHazard1Leveling'
            if is_hazard1_task and self.config.OpsiHazard1Leveling_ExecuteFixedPatrolScan:
                # 只有在第一次重扫没有发现事件时才执行舰队移动
                if not self._solved_map_event:
                    # _execute_fixed_patrol_scan 内部会再次检查 ExecuteFixedPatrolScan 的配置
                    # 这里强制传入 True 以确保逻辑被调用（只要外层配置开启了）
                    self._execute_fixed_patrol_scan(ExecuteFixedPatrolScan=True)
                    
                    # 第二次重扫：舰队移动后再次重扫
                    self._solved_map_event = set()
                    self.map_rescan()

            self.handle_after_auto_search()
            self.config.override(OpsiFleet_Fleet=OpsiFleet_Fleet)
        elif self.zone.zone_id == 154:
            logger.info('In zone 154, skip running first auto search')
            self.handle_ash_beacon_attack()
        else:
            self.run_auto_search(rescan=False)
            self.handle_after_auto_search()

    def get_current_zone_from_globe(self):
        """
        Get current zone from globe map. See OSMapOperation.get_current_zone()
        """
        self.os_map_goto_globe(unpin=False)
        self.globe_update()
        self.zone = self.get_globe_pinned_zone()
        self.zone_config_set()
        self.os_globe_goto_map()
        self.zone_init(fallback_init=False)
        return self.zone

    def globe_goto(self, zone, types=('SAFE', 'DANGEROUS'), refresh=False, stop_if_safe=False):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.
                Try the the first selection in type list, if not available, try the next one.
            refresh (bool): If already at target zone,
                set false to skip zone switching,
                set true to re-enter current zone to refresh.
            stop_if_safe (bool): Return false if zone is SAFE.

        Returns:
            bool: If zone switched.

        Pages:
            in: IN_MAP or IN_GLOBE
            out: IN_MAP
        """
        zone = self.name_to_zone(zone)
        logger.hr(f'Globe goto: {zone}')
        if self.zone == zone:
            if refresh:
                logger.info('Goto another zone to refresh current zone')
                self.globe_goto(self.zone_nearest_azur_port(self.zone),
                                types=('SAFE', 'DANGEROUS'), refresh=False)
            else:
                if self.is_in_globe():
                    self.os_globe_goto_map()
                logger.info('Already at target zone')
                return False
        # MAP_EXIT
        if self.is_in_special_zone():
            self.map_exit()
        # IN_MAP
        if self.is_in_map():
            self.os_map_goto_globe()
        # IN_GLOBE
        # self.ensure_no_zone_pinned()
        self.globe_update()
        self.globe_focus_to(zone)
        if stop_if_safe:
            if self.zone_has_safe():
                logger.info('Zone is safe, stopped')
                self.ensure_no_zone_pinned()
                return False
        self.zone_type_select(types=types)
        self.globe_enter(zone)
        # IN_MAP
        if hasattr(self, 'zone'):
            del self.zone
        self.zone_init()
        # self.map_init()
        return True

    def os_map_goto_globe(self, *args, **kwargs):
        """
        Wraps os_map_goto_globe()
        When zone has uncollected exploration rewards preventing exit,
        run auto search and goto globe again
        """
        for _ in range(3):
            try:
                super().os_map_goto_globe(*args, **kwargs)
                return
            except RewardUncollectedError:
                # Disable after_auto_search since it will exit current zone.
                # Or will cause RecursionError: maximum recursion depth exceeded
                self.run_auto_search(rescan=True, after_auto_search=False)
                continue

        logger.error('Failed to solve uncollected rewards')
        raise GameTooManyClickError

    def port_goto(self, allow_port_arrive=True):
        """
        Wraps `port_goto()`, handle walk_out_of_step

        Returns:
            bool: If success
        """
        for _ in range(3):
            try:
                super().port_goto(allow_port_arrive=allow_port_arrive)
                return True
            except MapWalkError:
                pass

            logger.info('Goto another port then re-enter')
            prev = self.zone
            if prev == self.name_to_zone('NY City'):
                other = self.name_to_zone('Liverpool')
            else:
                other = self.zone_nearest_azur_port(self.zone)
            self.globe_goto(other)
            self.globe_goto(prev)

        logger.warning('Failed to solve MapWalkError when going to port')
        return False

    def fleet_repair(self, revert=True):
        """
        Repair fleets in nearest port.

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet repair')
        prev = self.zone
        if self.zone.is_azur_port:
            logger.info('Already in azur port')
        else:
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

        self.port_goto()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_repair(self, revert=True):
        """
        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool: If repaired.
        """
        if self.config.OpsiGeneral_RepairThreshold < 0:
            return False
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet repair')
            return False

        self.hp_get()
        check = [round(data, 2) <= self.config.OpsiGeneral_RepairThreshold if use else False
                 for data, use in zip(self.hp, self.hp_has_ship)]
        if any(check):
            logger.info('At least one ship is below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'retreating to nearest azur port for repairs')
            self.handle_fleet_repair_by_config(revert=revert)
            self.hp_reset()
            return True
        else:
            logger.info('No ship found to be below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'continue OS exploration')
            self.hp_reset()
            return False

    def handle_storage_one_fleet_repair(self, fleet_index, threshold):
        """
        Args:
            fleet_index (int): fleet index
            threshold (int): repair threshold

        Returns:
            bool: If repaired.

        Pages:
            in: STORAGE_FLEET_CHOOSE
            out: STORAGE_FLEET_CHOOSE
        """
        self.storage_fleet_set(fleet_index)
        self.storage_hp_get()
        hp_grids = self._storage_hp_grid()
        check = [round(data, 2) <= threshold if use else False
                for data, use in zip(self.hp, self.hp_has_ship)]
        if any(check):
            logger.info(f'At least one ship in fleet {fleet_index} is below threshold '
                        f'{str(int(threshold * 100))}%, '
                        'use repair packs for repairs')
            for index, repair in enumerate(check):
                if repair:
                    self.repair_pack_use(hp_grids.buttons[index])
            logger.info(f'All ships in fleet {fleet_index} repaired')
            self.hp_reset()
            return True
        else:
            logger.info(f'No ship in fleet {fleet_index} found to be below threshold '
                        f'{str(int(threshold * 100))}%, '
                        'continue OS exploration')
            self.hp_reset()
            return False

    def handle_storage_fleet_repair(self, fleet_index=None, revert=True):
        """
        Args:
            fleet_index (None|int|list[int]): fleet index
            revert (bool): If go back to previous zone.

        Returns:
            bool: If repaired.

        Pages:
            in: in_map
            out: in_map
        """
        logger.hr('OS fleet repair by repair packs')
        if fleet_index is None:
            fleet_index = self.fleet_selector.get()
        if isinstance(fleet_index, int):
            fleet_index = [fleet_index]
        if not isinstance(fleet_index, list):
            logger.warning(f'Unknown fleet index: {fleet_index}')
            return False
        if self.config.OpsiGeneral_RepairPackThreshold < 0:
            return False

        repair = False
        success = False
        if self.storage_get_next_item('REPAIR_PACK'): 
            for index in fleet_index:
                if self.handle_storage_one_fleet_repair(fleet_index=index,
                        threshold=self.config.OpsiGeneral_RepairPackThreshold):
                    success = True
                if any(self.need_repair):
                    repair = True
            self.storage_repair_cancel()
            self.storage_quit()

        if repair:
            success = self.fleet_repair(revert=revert)

        return success

    def handle_fleet_repair_by_config(self, fleet_index=None, revert=True):
        """
        Args:
            fleet_index (None|int|list[int]): fleet index
                If None, fixed fleet in OpsiFleetFilter_Filter before current fleet, 
                         submarine fleet is always the last fleet to repair if it exists in filter string    
                E.g.: OpsiFleetFilter_Filter = 'Fleet-1 > CallSubmarine > Fleet-3 > Fleet-4 > Fleet-2'
                      current fleet is fleet 1, repair fleet 1 and submarine fleet
                      current fleet is fleet 4, repair fleet 1, fleet 3, fleet 4 and submarine fleet
                If int, the number of fleet index
                If list, a list of numbers of fleet index
            revert (bool): If go back to previous zone.

        Returns:
            bool: If repaired.

        Pages:
            in: in_map
            out: in_map
        """
        if self.config.OpsiGeneral_UseRepairPack and self.config.SERVER not in ['cn']:
            logger.warning(f'OpsiDaily.SkipSirenResearchMission is not supported in {self.config.SERVER}')
            self.config.OpsiGeneral_UseRepairPack = False

        if self.config.OpsiGeneral_UseRepairPack:
            if fleet_index is None:
                fleet_current_index = self.fleet_selector.get()
                submarine_fleet = self.storage_fleet_selector.SUBMARINE_FLEET
                fleet_all_index = [fleet.fleet_index if isinstance(fleet, BossFleet) else submarine_fleet
                                   for fleet in self.parse_fleet_filter()]
                fleet_index = []
                for index in fleet_all_index:
                    fleet_index.append(index)
                    if fleet_current_index == index:
                        break
                # CL1 and some custom filter setups may not include current fleet in
                # OpsiFleetFilter_Filter. Ensure current fleet can still use repair pack.
                if fleet_current_index not in fleet_index:
                    fleet_index.append(fleet_current_index)
                if submarine_fleet not in fleet_index and submarine_fleet in fleet_all_index:
                    fleet_index.append(submarine_fleet)
                elif submarine_fleet in fleet_index:
                    fleet_index.remove(submarine_fleet)
                    fleet_index.append(submarine_fleet)
            logger.attr('Repair Fleet', fleet_index)
            return self.handle_storage_fleet_repair(fleet_index=fleet_index, revert=revert)
        else:
            return self.fleet_repair(revert=revert)

    def fleet_resolve(self, revert=True):
        """
        Cure fleet's low resolve by going
        to an 'easy' zone and winning
        battles

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet cure low resolve debuff')

        prev = self.zone
        self.globe_goto(22)
        self.zone_init()
        self.run_auto_search()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_resolve(self, revert=False):
        """
        Check each fleet if afflicted with the low
        resolve debuff
        If so, handle by completing an easy zone

        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool:
        """
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet resolve')
            return False

        for index in [1, 2, 3, 4]:
            if not self.fleet_set(index):
                self.device.screenshot()

            if self.fleet_low_resolve_appear():
                logger.info('At least one fleet is afflicted with '
                            'the low resolve debuff')
                self.fleet_resolve(revert)
                return True

        logger.info('None of the fleets are afflicted with '
                    'the low resolve debuff')
        return False

    def handle_current_fleet_resolve(self, revert=False):
        """
        Similar to handle_fleet_resolve,
        but check current fleet only for better performance at initialization

        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool:
        """
        if self.fleet_low_resolve_appear():
            logger.info('Current fleet is afflicted with '
                        'the low resolve debuff')
            self.fleet_resolve(revert)
            return True

        logger.info('Current fleet is not afflicted with '
                    'the low resolve debuff')
        return False

    def handle_fleet_emp_debuff(self):
        """
        EMP debuff limits fleet step to 1 and messes auto search up.
        It can be solved by moving fleets on map meaninglessly.

        Returns:
            bool: If solved
        """
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip handle_fleet_emp_debuff')
            return False

        def has_emp_debuff():
            return self.appear(FLEET_EMP_DEBUFF, offset=(50, 20))

        for trial in range(5):

            if not has_emp_debuff():
                logger.info('No EMP debuff on current fleet')
                return trial > 0

            current = self.get_fleet_current_index()
            logger.hr(f'Solve EMP debuff on fleet {current}')
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

            logger.info('Find a fleet without EMP debuff')
            for fleet in [1, 2, 3, 4]:
                self.fleet_set(fleet)
                if has_emp_debuff():
                    logger.info(f'Fleet {fleet} is under EMP debuff')
                    continue
                else:
                    logger.info(f'Fleet {fleet} is not under EMP debuff')
                    break

            logger.info('Solve EMP debuff by going somewhere else')
            self.port_goto(allow_port_arrive=False)
            self.fleet_set(current)

        logger.warning('Failed to solve EMP debuff after 5 trial, assume solved')
        return True

    def handle_fog_block(self, repair=True):
        """
        AL game bug where fog remains in OpSi
        even after jumping between zones or
        other pages
        Recover by restarting the game to
        alleviate and resume OpSi task

        Args:
            repair (bool): call handle_fleet_repair after restart
        """
        if not self.appear(MAP_GOTO_GLOBE_FOG):
            return False

        logger.warning(f'Triggered stuck fog status, restarting '
                       f'game to resolve and continue '
                       f'{self.config.task.command}')

        # Restart the game manually rather
        # than through 'task_call'
        # Ongoing task is uninterrupted
        self.device.app_stop()
        self.device.app_start()
        LoginHandler(self.config, self.device).handle_app_login()

        self.ui_ensure(page_os)
        if repair:
            self.handle_fleet_repair(revert=False)

        return True

    def get_action_point_limit(self, preserve=False):
        """
        Override user config at the end of every month.
        To consume all action points without manual configuration.

        Args:
            preserve (bool): if preserve action points until OpSi reset

        Returns:
            int: ActionPointPreserve
        """
        if preserve:
            if self.config.is_task_enabled('OpsiCrossMonth'):
                logger.info('Preserve action points until OpsiCrossMonth')
                return maxsize
            else:
                logger.info('OpsiCrossMonth is not enabled, skip OpsiMeowfficerFarming.APPreserveUntilReset')

        remain = get_os_reset_remain()
        if remain <= 0:
            if self.config.is_task_enabled('OpsiCrossMonth'):
                logger.info('Just less than 1 day to OpSi reset, OpsiCrossMonth is enabled, '
                            'set OpsiMeowfficerFarming.ActionPointPreserve to 500 temporarily')
                return 500
            else:
                logger.info('Just less than 1 day to OpSi reset, '
                            'set ActionPointPreserve to 0 temporarily')
                return 0
        elif self.is_cl1_enabled and remain <= 2:
            logger.info('Just less than 3 days to OpSi reset, '
                        'set ActionPointPreserve to 2000 temporarily for hazard 1 leveling')
            return 2000
        elif remain <= 2:
            logger.info('Just less than 3 days to OpSi reset, '
                        'set ActionPointPreserve to 500 temporarily')
            return 500
        else:
            logger.info('Not close to OpSi reset')
            return maxsize

    def handle_after_auto_search(self):
        logger.hr('After auto search', level=2)
        solved = False
        solved |= self.handle_fleet_emp_debuff()
        solved |= self.handle_fleet_repair(revert=False)
        logger.info(f'Handle after auto search finished, solved={solved}')
        return solved

    def cl1_ap_preserve(self):
        """
        Keeping enough startup AP to run CL1.
        """
        # 检查智能调度是否启用，如果启用则由智能调度模块统一管理任务切换
        # 这里不应该直接切换到 CL1
        if is_smart_scheduling_enabled(self.config):
            return
        
        if self.is_cl1_enabled and get_os_reset_remain() > 2 and self.cl1_enough_yellow_coins:
            preserve = self.config.cross_get(keys='OpsiMeowfficerFarming.OpsiMeowfficerFarming.ActionPointPreserve')
            logger.info(f'Keep {preserve} AP when CL1 available')
            if not self.action_point_check(preserve):
                self.config.opsi_task_delay(cl1_preserve=True)
                self.cl1_task_call()
                self.config.task_stop()

    _auto_search_battle_count = 0
    _auto_search_round_timer = 0
    _cl1_auto_search_battle_count = 0

    def on_auto_search_battle_count_reset(self):
        self._auto_search_battle_count = 0
        self._auto_search_round_timer = 0

    def on_auto_search_battle_count_add(self):
        self._auto_search_battle_count += 1
        logger.attr('battle_count', self._auto_search_battle_count)
        
        # Check if CL1 tracking should be enabled
        try:
            is_cl1_task = self.config.task.command == 'OpsiHazard1Leveling'
            is_cl1_enabled = self.config.is_task_enabled('OpsiHazard1Leveling')
        except Exception:
            is_cl1_task = False
            is_cl1_enabled = False
        
        if is_cl1_task and is_cl1_enabled:
            try:
                self._cl1_auto_search_battle_count += 1
                logger.attr('cl1_battle_count', self._cl1_auto_search_battle_count)
                # 使用数据库增加计数
                from module.statistics.cl1_database import db as cl1_db
                instance_name = getattr(self.config, 'config_name', 'default')
                cl1_db.increment_battle_count(instance_name)
                logger.info('Successfully incremented CL1 battle count in DB')
            except Exception:
                logger.exception('Failed to update cl1 battle counter')

            if self._auto_search_battle_count % 2 == 1:
                if self._auto_search_round_timer:
                    cost = round(time.time() - self._auto_search_round_timer, 2)
                    logger.attr('CL1 time cost', f'{cost}s/round')
                    
                    if is_cl1_task and is_cl1_enabled:
                        try:
                            from module.statistics.ship_exp_stats import get_ship_exp_stats
                            get_ship_exp_stats(instance_name=instance_name).record_round_time(cost)
                        except Exception:
                            logger.exception('Failed to record cl1 round time')
                            
                self._auto_search_round_timer = time.time()

    def get_current_cl1_battle_count(self):
        return int(getattr(self, '_cl1_auto_search_battle_count', 0))

    def get_monthly_cl1_battle_count(self, year: int = None, month: int = None):
        from module.statistics.cl1_database import db as cl1_db
        instance_name = getattr(self.config, 'config_name', 'default')
        if year is None or month is None:
            from datetime import datetime
            month_key = datetime.now().strftime('%Y-%m')
        else:
            month_key = f"{year:04d}-{month:02d}"
        
        data = cl1_db.get_stats(instance_name, month_key)
        return int(data.get('battle_count', 0))
    
    def os_auto_search_daemon(self, drop=None, strategic=False, interrupt=None, skip_first_screenshot=True):
        """
        Args:
            drop (DropRecord):
            strategic (bool): True if running in strategic search
            interrupt (callable):
            skip_first_screenshot:

        Returns:
            int: Number of finished battle

        Raises:
            CampaignEnd: If auto search ended
            RequestHumanTakeover: If there's no auto search option.

        Pages:
            in: AUTO_SEARCH_OS_MAP_OPTION_OFF
            out: AUTO_SEARCH_OS_MAP_OPTION_OFF and info_bar_count() >= 2, if no more objects to clear on this map.
                 AUTO_SEARCH_REWARD if get auto search reward.
        """
        logger.hr('OS auto search', level=2)
        self.on_auto_search_battle_count_reset()
        unlock_checked = False
        unlock_check_timer = Timer(5, count=10).start()
        self.ash_popup_canceled = False

        def false_func(*args, **kwargs):
            return False

        success = True
        interrupt_confirm = False
        if callable(interrupt):
            is_interrupt, not_interrupt = interrupt, false_func
        elif isinstance(interrupt, list) and len(interrupt) == 2:
            is_interrupt = interrupt[0] if callable(interrupt[0]) else false_func
            not_interrupt = interrupt[1] if callable(interrupt[1]) else false_func
        else:
            is_interrupt, not_interrupt = false_func, false_func
        finished_combat = 0
        died_timer = Timer(1.5, count=3)
        self.hp_reset()
        for _ in self.loop():
            # End
            if not unlock_checked and unlock_check_timer.reached():
                logger.critical('Unable to use auto search in current zone')
                logger.critical('Please finish the story mode of OpSi to unlock auto search '
                                'before using any OpSi functions')
                raise RequestHumanTakeover
            if self.is_in_map():
                self.device.stuck_record_clear()
                if not success:
                    if died_timer.reached():
                        logger.warning('Fleet died confirm')
                        break
                else:
                    if not interrupt_confirm and is_interrupt():
                        interrupt_confirm = True
                    if interrupt_confirm and not_interrupt():
                        interrupt_confirm = False
                    died_timer.reset()
            else:
                died_timer.reset()

            if not unlock_checked:
                if self.appear(AUTO_SEARCH_OS_MAP_OPTION_OFF, offset=(5, 120)):
                    unlock_checked = True
                elif self.appear(AUTO_SEARCH_OS_MAP_OPTION_OFF_DISABLED, offset=(5, 120)):
                    unlock_checked = True
                elif self.appear(AUTO_SEARCH_OS_MAP_OPTION_ON, offset=(5, 120)):
                    unlock_checked = True

            if self.handle_os_auto_search_map_option(
                    drop=drop,
                    enable=success
            ):
                unlock_checked = True
                continue
            if self.handle_retirement():
                # Retire will interrupt auto search, need a retry
                self.ash_popup_canceled = True
                continue
            if self.combat_appear():
                self.on_auto_search_battle_count_add()
                if strategic and self.config.task_switched():
                    self.interrupt_auto_search()
                if interrupt_confirm:
                    self.interrupt_auto_search(goto_main=False)
                result = self.auto_search_combat(drop=drop)
                if result:
                    finished_combat += 1
                else:
                    self.hp_get()
                    if any(self.need_repair):
                        success = False
                        logger.warning('Fleet died, stop auto search')
                        continue
            if self.handle_map_event():
                # Auto search can not handle siren searching device.
                continue

        return finished_combat
    # 自动寻敌，遇到第一次战斗就返回
    def os_auto_search_daemon_until_combat(self, drop=None, strategic=False, interrupt=None, skip_first_screenshot=True):
        """
        Args:
            drop (DropRecord):
            strategic (bool): True if running in strategic search
            interrupt (callable):
            skip_first_screenshot:

        Returns:
            int: Number of finished battle

        Raises:
            CampaignEnd: If auto search ended
            RequestHumanTakeover: If there's no auto search option.

        Pages:
            in: AUTO_SEARCH_OS_MAP_OPTION_OFF
            out: AUTO_SEARCH_OS_MAP_OPTION_OFF and info_bar_count() >= 2, if no more objects to clear on this map.
                 AUTO_SEARCH_REWARD if get auto search reward.
        """
        logger.hr('OS auto search until combat', level=2)
        self.on_auto_search_battle_count_reset()
        unlock_checked = False
        unlock_check_timer = Timer(5, count=10).start()
        self.ash_popup_canceled = False

        def false_func(*args, **kwargs):
            return False

        success = True
        interrupt_confirm = False
        if callable(interrupt):
            is_interrupt, not_interrupt = interrupt, false_func
        elif isinstance(interrupt, list) and len(interrupt) == 2:
            is_interrupt = interrupt[0] if callable(interrupt[0]) else false_func
            not_interrupt = interrupt[1] if callable(interrupt[1]) else false_func
        else:
            is_interrupt, not_interrupt = false_func, false_func
        finished_combat = 0
        died_timer = Timer(1.5, count=3)
        self.hp_reset()
        for _ in self.loop():
            # End
            if not unlock_checked and unlock_check_timer.reached():
                logger.critical('Unable to use auto search in current zone')
                logger.critical('Please finish the story mode of OpSi to unlock auto search '
                                'before using any OpSi functions')
                raise RequestHumanTakeover
            if self.is_in_map():
                self.device.stuck_record_clear()
                if not success:
                    if died_timer.reached():
                        logger.warning('Fleet died confirm')
                        break
                else:
                    if not interrupt_confirm and is_interrupt():
                        interrupt_confirm = True
                    if interrupt_confirm and not_interrupt():
                        interrupt_confirm = False
                    died_timer.reset()
            else:
                died_timer.reset()

            if not unlock_checked:
                if self.appear(AUTO_SEARCH_OS_MAP_OPTION_OFF, offset=(5, 120)):
                    unlock_checked = True
                elif self.appear(AUTO_SEARCH_OS_MAP_OPTION_OFF_DISABLED, offset=(5, 120)):
                    unlock_checked = True
                elif self.appear(AUTO_SEARCH_OS_MAP_OPTION_ON, offset=(5, 120)):
                    unlock_checked = True

            if self.handle_os_auto_search_map_option(
                    drop=drop,
                    enable=success
            ):
                unlock_checked = True
                continue
            if self.handle_retirement():
                # Retire will interrupt auto search, need a retry
                self.ash_popup_canceled = True
                continue
            if self.combat_appear():
                self.on_auto_search_battle_count_add()
                self.interrupt_auto_search(goto_main=False, end_task=False)
                return finished_combat
            if self.handle_map_event():
                # Auto search can not handle siren searching device.
                continue

        return finished_combat

    def interrupt_auto_search(self, goto_main=True, end_task=True, skip_first_screenshot=True):
        """
        Args:
            goto_main (bool): If go to the page_main

        Raises:
            TaskEnd: If auto search interrupted

        Pages:
            in: Any, usually to be is_combat_executing
            out: page_main or IN_MAP
        """
        logger.info('Interrupting auto search')
        is_loading = False
        pause_interval = Timer(0.5, count=1)
        in_main_timer = Timer(3, count=6)
        in_map_timer = Timer(1, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()


            # End
            if self.is_in_main():
                logger.info('Auto search interrupted')
                self.config.task_stop()
            if not goto_main and self.is_in_map():
                if in_map_timer.reached():
                    logger.info('Auto search interrupted')
                    if end_task:
                        self.config.task_stop()
                    return

            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50), interval=3):
                self.interval_clear(GOTO_MAIN)
                in_main_timer.reset()
                in_map_timer.reset()
                continue
            if pause_interval.reached():
                pause = self.is_combat_executing()
                if pause:
                    self.device.click(pause)
                    self.interval_reset(MAINTENANCE_ANNOUNCE)
                    is_loading = False
                    pause_interval.reset()
                    in_main_timer.reset()
                    in_map_timer.reset()
                    continue
            if self.handle_combat_quit():
                self.interval_reset(MAINTENANCE_ANNOUNCE)
                pause_interval.reset()
                in_main_timer.reset()
                in_map_timer.reset()
                continue
            if self.handle_combat_quit_reconfirm():
                self.interval_reset(MAINTENANCE_ANNOUNCE)
                pause_interval.reset()
                in_main_timer.reset()
                in_map_timer.reset()
                continue

            if goto_main and self.appear_then_click(GOTO_MAIN, offset=(20, 20), interval=3):
                in_main_timer.reset()
                continue
            if self.ui_additional():
                continue
            if self.handle_map_event():
                continue
            # Only print once when detected
            if not is_loading:
                if self.is_combat_loading():
                    is_loading = True
                    in_main_timer.clear()
                    in_map_timer.clear()
                    continue
                # Random background from page_main may trigger EXP_INFO_*, don't check them
                if in_main_timer.reached():
                    logger.info('handle_exp_info')
                    if self.handle_battle_status():
                        continue
                    if self.handle_exp_info():
                        continue
            elif self.is_combat_executing():
                is_loading = False
                in_main_timer.clear()
                in_map_timer.clear()
                continue

    def os_auto_search_run(self, drop=None, strategic=False, interrupt=None):
        """
        Args:
            drop (DropRecord):
            strategic (bool): True to use strategic search
            interrupt (callable):
        Returns:
            int: Number of finished combat
        """
        finished_combat = 0
        for _ in range(5):
            backup = self.config.temporary(Campaign_UseAutoSearch=True)
            try:
                if strategic:
                    self.strategic_search_start(skip_first_screenshot=True)
                combat = self.os_auto_search_daemon(drop=drop, strategic=strategic, interrupt=interrupt)
                finished_combat += combat
            except CampaignEnd:
                logger.info('OS auto search finished')
            finally:
                backup.recover()

            # Continue if was Auto search interrupted by ash popup
            # Break if zone cleared
            if self.config.is_task_enabled('OpsiAshBeacon'):
                if self.handle_ash_beacon_attack() or self.ash_popup_canceled:
                    strategic = False
                    continue
                else:
                    break
            else:
                if self.info_bar_count() >= 2:
                    break
                elif self.ash_popup_canceled:
                    continue
                else:
                    break

        return finished_combat

    @property
    def _is_siren_research_enabled(self):
        """
        Check if siren research feature is enabled in config.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self.config.cross_get(keys="OpsiHazard1Leveling.OpsiSirenBug.SirenResearch_Enable")

    def _should_skip_siren_research(self, grid):
        """
        Check if siren research device should be skipped based on config.
        
        Args:
            grid: The grid to check
            
        Returns:
            bool: True if should skip (feature disabled), False otherwise
        """
        if hasattr(grid, 'is_scanning_device') and grid.is_scanning_device:
            if not self._is_siren_research_enabled:
                logger.info(f'[预检查] 格子 {grid} 是塞壬研究装置,但功能未开启,跳过')
                return True
            else:
                logger.info(f'[预检查] 格子 {grid} 是塞壬研究装置,功能已开启,继续处理')
        return False

    def _should_skip_siren_research_for_explore(self):

        # 检查是否由月度开荒调用
        is_explore = getattr(self, 'is_in_task_explore', False)
        if not is_explore:
            return False

        # 检查月度开荒是否配置跳过塞壬研究装置
        skip_level = self.config.cross_get(keys="OpsiExplore.OpsiExplore.IfSkipSirenResearch")
        if skip_level == 0:
            return False
        
        # 根据海域难度决定是否跳过
        hazard_level = self.zone.hazard_level
        if skip_level == 6 and hazard_level == 6:
            logger.info(f'[月度开荒] 海域危险度 {hazard_level} = 6, 跳过塞壬研究装置')
            return True
        if skip_level == 65 and hazard_level >= 5:
            logger.info(f'[月度开荒] 海域危险度 {hazard_level} >= 5, 跳过塞壬研究装置')
            return True
        if skip_level == 654 and hazard_level >= 4:
            logger.info(f'[月度开荒] 海域危险度 {hazard_level} >= 4, 跳过塞壬研究装置')
            return True
        return False

    def clear_question(self, drop=None):
        """
        Clear nearly (and 3 grids from above) question marks on radar.
        Try 3 times at max to avoid loop tries on 2 adjacent fleet mechanism.

        Args:
            drop:

        Returns:
            bool: If cleared
        """
        logger.hr('Clear question', level=2)
        for _ in range(3):
            grid = self.radar.predict_question(self.device.image, in_port=self.zone.is_port)
            if grid is None:
                logger.info('No question mark above current fleet on this radar')
                return False

            logger.info(f'Found question mark on {grid}')
            self.handle_info_bar()

            self.update_os()
            self.view.predict()
            self.view.show()

            grid = self.convert_radar_to_local(grid)
            
            # ========== 移动前检查：是否为塞壬研究装置且功能未开启 ==========
            if self._should_skip_siren_research(grid):
                self._solved_map_event.add('is_scanning_device')
                return True
            
            self.is_siren_device_confirmed = False
            self.device.click(grid)
            with self.config.temporary(STORY_ALLOW_SKIP=False):
                result = self.wait_until_walk_stable(
                    drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            if 'akashi' in result:
                self._solved_map_event.add('is_akashi')
                return True
            elif 'event' in result and grid.is_logging_tower:
                self._solved_map_event.add('is_logging_tower')
                return True
            elif 'event' in result and (grid.is_scanning_device or self.is_siren_device_confirmed):
                # ========== 地图检测:检测到扫描装置 ==========
                logger.hr('检测到扫描装置,开始处理', level=2)
                logger.info(f'[地图检测] 格子 {grid} 被识别为扫描装置 (grid.is_scanning_device=True)')
                logger.info(f'[地图检测] 移动结果: {result}')

                # ========== 配置检查 ==========
                siren_research_enabled = self.config.cross_get(keys="OpsiHazard1Leveling.OpsiSirenBug.SirenResearch_Enable")
                if not siren_research_enabled:
                    logger.warning('[配置检查] 塞壬研究装置功能已禁用,标记但不处理')
                    self._solved_map_event.add('is_scanning_device')
                    return True

                # ========== 装置处理 ==========
                # 选项点击已由 wait_until_walk_stable -> info_handler.story_skip 处理
                
                # 执行自律寻敌
                logger.info('[装置处理] 步骤1: 执行自律寻敌')
                self.os_auto_search_run(drop=drop)
                
                # 标记处理
                self._solved_map_event.add('is_scanning_device')
                
                # Bug利用
                logger.info('[装置处理] 步骤2: 检查是否需要执行Bug利用')
                self._handle_siren_bug_reinteract(drop=drop)
                
                return True

        logger.warning('Failed to goto question mark after 5 trail, '
                       'this might be 2 adjacent fleet mechanism, stopped')
        return False

    def run_auto_search(self, question=True, rescan=None, after_auto_search=True, interrupt=None):
        """
        Clear current zone by running auto search.
        OpSi story mode must be cleared to unlock auto search.

        Args:
            question (bool):
                If clear nearing questions after auto search.
            rescan (bool, str): Whether to rescan the whole map after running auto search.
                This will clear siren scanning devices, siren logging tower,
                visit akashi's shop that auto search missed, and unlock mechanism that requires 2 fleets.
                Accept str also, `current` to scan current camera only,
                `full` to scan current then rescan the whole map

                This option should be disabled in special tasks like OpsiObscure, OpsiAbyssal, OpsiStronghold.
            after_auto_search (bool):
                Whether to call handle_after_auto_search() after auto search
            interrupt (callable):

        Returns:
            int: Number of finished combat
        """
        if rescan is None:
            rescan = self.config.OpsiGeneral_DoRandomMapEvent
        if rescan is True:
            rescan = 'full'
        self.handle_ash_beacon_attack()

        logger.info(f'Run auto search, question={question}, rescan={rescan}')
        finished_combat = 0
        with self.stat.new(
                genre=inflection.underscore(self.config.task.command),
                method=self.config.DropRecord_OpsiRecord
        ) as drop:
            while 1:
                combat = self.os_auto_search_run(drop, interrupt=interrupt)
                finished_combat += combat

                # Record current zone, skip this if no rewards from auto search.
                drop.add(self.device.image)

                self.hp_reset()
                self.hp_get()
                if after_auto_search:
                    if self.is_in_task_explore and not self.zone.is_port:
                        prev = self.zone
                        if self.handle_after_auto_search():
                            self.globe_goto(prev, types='DANGEROUS')
                            continue
                break

            # Rescan
            self._solved_map_event = set()
            self._solved_fleet_mechanism = False
            if question:
                self.clear_question(drop=drop)
            if rescan:
                self.map_rescan(rescan_mode=rescan, drop=drop)

            if drop.count == 1:
                drop.clear()

        return finished_combat

    _solved_map_event = set()
    _solved_fleet_mechanism = 0

    def run_strategic_search(self):
        """
        Returns:
            bool: True if completed normally, False if interrupted (but not TaskEnd)
        """
        self.handle_ash_beacon_attack()

        logger.hr('Run strategy search', level=2)
        try:
            self.os_auto_search_run(strategic=True)
            self.hp_reset()
            self.hp_get()
            return True  # 正常完成
        except TaskEnd:
            # 任务切换，让异常继续向上传播
            raise
        except Exception as e:
            logger.warning(f'Strategic search interrupted: {e}')
            return False  # 被中断

    def map_rescan_current(self, drop=None):
        """

        Args:
            drop:

        Returns:
            bool: If solved a map random event
        """
        grids = self.view.select(is_exploration_reward=True)
        if 'is_exploration_reward' not in self._solved_map_event and grids and grids[0].is_exploration_reward:
            grid = grids[0]
            logger.info(f'Found exploration reward on {grid}')
            result = self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            if 'event' in result:
                self._solved_map_event.add('is_exploration_reward')
                return True
            else:
                return False

        grids = self.view.select(is_akashi=True)
        if 'is_akashi' not in self._solved_map_event and grids and grids[0].is_akashi:
            grid = grids[0]
            logger.info(f'Found Akashi on {grid}')
            fleet = self.convert_radar_to_local((0, 0))
            if fleet.distance_to(grid) > 1:
                self.device.click(grid)
                with self.config.temporary(STORY_ALLOW_SKIP=False):
                    walk_time = 1.5 + 0.6 * grid.distance_to(fleet)
                    result = self.wait_until_walk_stable(
                        confirm_timer=Timer(walk_time, count=4), drop=drop, walk_out_of_step=False)
                if 'akashi' in result:
                    self._solved_map_event.add('is_akashi')
                    return True
                else:
                    logger.info('无法到达明石位置，执行定点巡逻扫描')
                    self._execute_fixed_patrol_scan(ExecuteFixedPatrolScan=True)
                    return False
            else:
                logger.info(f'Akashi ({grid}) is near current fleet ({fleet})')
                self.handle_akashi_supply_buy(grid)
                self._solved_map_event.add('is_akashi')
                return True

        grids = self.view.select(is_scanning_device=True)
        if 'is_scanning_device' not in self._solved_map_event and grids and grids[0].is_scanning_device:
            grid = grids[0]
            
            # ========== 地图选择:发现研究装置 ==========
            logger.hr('发现研究装置,开始处理', level=2)
            logger.info(f'[地图选择] 在 {grid} 位置发现研究装置')
            
            if not self._is_siren_research_enabled:
                logger.warning('[配置检查] 塞壬研究装置功能已禁用,跳过处理')
                self._solved_map_event.add('is_scanning_device')
                return True
            
            if self._should_skip_siren_research_for_explore():
                # 记录已跳过的海域
                zone_str = f'{self.zone};\n'
                current_str = self.config.OpsiExplore_SkipedSirenResearch
                if current_str is None:
                    self.config.OpsiExplore_SkipedSirenResearch = zone_str
                else:
                    self.config.OpsiExplore_SkipedSirenResearch = str(current_str) + zone_str
                logger.info(f'[月度开荒] 已记录跳过塞壬研究装置的海域: {self.config.OpsiExplore_SkipedSirenResearch}')
                self._solved_map_event.add('is_scanning_device')
                return True
            
            # ========== 移动并处理 ==========
            logger.info(f'[移动装置] 开始移动到装置位置: {grid}')
            self.device.click(grid)
            
            # 重置标志位
            self.is_siren_device_confirmed = False
            
            # wait_until_walk_stable 会调用 handle_story_skip 处理选项
            logger.info('[移动装置] 等待移动稳定...')
            result = self.wait_until_walk_stable(
                drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            logger.info(f'[移动装置] 移动完成,结果: {result}')
            
            if getattr(self, 'is_siren_device_confirmed', False):
                # 保存标志状态，因为二次重扫可能会重置它
                siren_confirmed = True
                
                # 执行自律寻敌
                logger.info('[装置处理] 执行自律寻敌')
                self.os_auto_search_run(drop=drop)

                # 先标记为已处理，防止二次重扫时再次处理塞壬装置
                self._solved_map_event.add('is_scanning_device')

                # 二次重扫，防止出现意外情况导致装置处理失败
                logger.info('[装置处理] 执行二次重扫')
                self.map_rescan_current(drop=drop)
                
                # 使用保存的标志状态，而不是重新检查（因为二次重扫可能会重置它）
                if siren_confirmed:
                    logger.info('[装置处理] 已确认为塞壬研究装置，检查是否需要执行Bug利用')
                    self._handle_siren_bug_reinteract(drop=drop)
                else:
                    logger.info('[装置处理] 未确认为塞壬研究装置，跳过Bug利用')
            
            return True

        grids = self.view.select(is_logging_tower=True)
        if 'is_logging_tower' not in self._solved_map_event and grids and grids[0].is_logging_tower:
            grid = grids[0]
            logger.info(f'Found logging tower on {grid}')
            self.device.click(grid)
            with self.config.temporary(STORY_ALLOW_SKIP=False):
                result = self.wait_until_walk_stable(
                    drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            if 'event' in result:
                self._solved_map_event.add('is_logging_tower')
                return True
            else:
                return False

        grids = self.view.select(is_fleet_mechanism=True)
        if self.is_in_task_explore \
                and 'is_fleet_mechanism' not in self._solved_map_event \
                and grids \
                and grids[0].is_fleet_mechanism:
            grid = grids[0]
            logger.info(f'Found fleet mechanism on {grid}')
            self.device.click(grid)
            self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))

            if self._solved_fleet_mechanism:
                logger.info('All fleet mechanism are solved')
                self.os_auto_search_run(drop=drop)
                self._solved_map_event.add('is_fleet_mechanism')
                return True
            else:
                logger.info('One of the fleet mechanism is solved')
                self._solved_fleet_mechanism = True
                return True

        logger.info(f'No map event')
        return False

    def map_rescan_once(self, rescan_mode='full', drop=None):
        """
        Args:
            rescan_mode (str): `current` to scan current camera only,
                `full` to scan current then rescan the whole map
            drop:

        Returns:
            bool: If solved a map random event
        """
        result = False

        # Try current camera first
        logger.hr('Map rescan current', level=2)
        self.map_data_init(map_=None)
        self.handle_info_bar()
        self.update()
        if self.map_rescan_current(drop=drop):
            logger.info(f'Map rescan once end, result={True}')
            return True

        if rescan_mode == 'full':
            logger.hr('Map rescan full', level=2)
            self.map_init(map_=None)
            queue = self.map.camera_data
            while len(queue) > 0:
                logger.hr(f'Map rescan {queue[0]}')
                queue = queue.sort_by_camera_distance(self.camera)
                self.focus_to(queue[0], swipe_limit=(6, 5))
                self.focus_to_grid_center(0.3)

                if self.map_rescan_current(drop=drop):
                    result = True
                    break
                queue = queue[1:]

        logger.info(f'Map rescan once end, result={result}')
        return result

    def map_rescan(self, rescan_mode='full', drop=None):
        if self.zone.is_port:
            logger.info('Current zone is a port, do not need rescan')
            return False

        for _ in range(5):
            if not self._solved_fleet_mechanism:
                self.fleet_set(self.config.OpsiFleet_Fleet)
            else:
                self.fleet_set(self.get_second_fleet())
            if not self.is_in_task_explore and len(self._solved_map_event):
                logger.info('Solved a map event and not in OpsiExplore, stop rescan')
                logger.attr('Solved_map_event', self._solved_map_event)
                self.fleet_set(self.config.OpsiFleet_Fleet)
                return False
            result = self.map_rescan_once(rescan_mode=rescan_mode, drop=drop)
            if not result:
                logger.attr('Solved_map_event', self._solved_map_event)
                self.fleet_set(self.config.OpsiFleet_Fleet)
                return True

        logger.attr('Solved_map_event', self._solved_map_event)
        logger.warning('Too many trial on map rescan, stop')
        self.fleet_set(self.config.OpsiFleet_Fleet)
        return False

    def safe_swipe(self, start, end, duration=0.5, retries=2):
        """
        在多次滑动/重试场景下的安全滑动：
         - 清理设备的卡住/点击历史记录
         - 使用较长时长与间隔，减少被识别为无效滑动的概率
        """
        for attempt in range(1, retries + 1):
            try:
                try:
                    self.device.stuck_record_clear()
                except Exception:
                    pass
                self.device.swipe(start, end, duration=duration)
                time.sleep(0.45)
                return True
            except Exception as e:
                logger.warning(f'safe_swipe attempt {attempt} failed: {e}')
                time.sleep(0.4)
                continue
        return False

    # 基于ShaddockNH3极致侵蚀一的个人修改
    def _execute_fixed_patrol_scan(self, ExecuteFixedPatrolScan: bool = False, **kwargs):
        """
        该函数在指挥每支舰队移动前，都会先执行一次强制的视角复位，
        然后精确指挥1-4号舰队前往预设的网格坐标，并在所有舰队
        移动到位后，执行一次清除了残留状态的全图扫描。
        """
        logger.hr('执行定点巡逻扫描')

        if not ExecuteFixedPatrolScan:
            logger.info('ExecuteFixedPatrolScan 未启用，跳过定点巡逻。')
            return
        logger.attr('ExecuteFixedPatrolScan', True)

        self.map_init(map_=None)
        if not hasattr(self, 'map') or not self.map.grids:
            logger.warning('无法获取当前地图网格数据，已跳过定点巡逻。')
            return

        solved = getattr(self, '_solved_map_event', set())
        if any(k in solved for k in ('is_akashi', 'is_scanning_device', 'is_logging_tower')):
            logger.info('彩蛋：雪风大人保佑你，本次舰队移动已跳过')
            return

        patrol_locations = [(2, 0), (3, 0), (4, 0), (5, 0)]  # 对应 C1, D1, E1, F1

        for i, target_loc in enumerate(patrol_locations):
            fleet_index = i + 1

            target_grid_group = self.map.select(location=target_loc)
            if not target_grid_group:
                logger.warning(f'在地图上找不到坐标为 {target_loc} 的格子，跳过舰队 {fleet_index} 的移动。')
                continue
            target_grid = target_grid_group[0]

            logger.hr(f'定点巡逻: 指挥舰队 {fleet_index} 前往 {target_grid}', level=2)

            self.fleet_set(fleet_index)

            logger.info('执行视角复位，强制滑动到地图顶端...')

            top_point = (640, 150)
            bottom_point = (640, 600)
            quick_ok = True
            try:
                for _ in range(2):
                    self.device.swipe(top_point, bottom_point, duration=0.3)
                    time.sleep(0.18)
            except Exception:
                quick_ok = False
                logger.debug('快速滑动复位遇到异常，尝试安全滑动')

            if not quick_ok:
                if not self.safe_swipe(top_point, bottom_point, duration=0.55, retries=2):
                    logger.warning('视角复位（安全滑动）失败，继续尝试下一步')
                else:
                    logger.info('视角复位（安全滑动）完成。')
            else:
                logger.info('快速滑动复位完成。')
            time.sleep(0.45)

            self.focus_to(target_grid.location)
            self.update()
            clickable_grid_group = self.view.select(location=target_loc)
            if not clickable_grid_group:
                logger.warning(f'已将视角移动到 {target_loc}，但在视野中找不到可点击的格子。')
                continue

            for try_idx in range(2):
                try:
                    try:
                        self.device.stuck_record_clear()
                    except Exception:
                        pass
                    time.sleep(0.1)
                    self.device.click(clickable_grid_group[0])
                    self.wait_until_walk_stable(confirm_timer=Timer(1.5, count=4))
                    logger.info(f'舰队 {fleet_index} 已到达 {target_grid}。')
                    break
                except (MapWalkError, GameTooManyClickError) as e:
                    logger.warning(f'舰队移动异常: {e}，尝试强制恢复（{try_idx + 1}/2）')
                    recovered = False
                    try:
                        recovered = self._force_move_recover(target_zone=self.zone if self.zone else None)
                    except Exception:
                        recovered = False
                    if recovered:
                        time.sleep(0.5)
                        continue
                    logger.warning('尝试软恢复（back / screenshot / rebuild view）')
                    try:
                        for _ in range(3):
                            try:
                                self.device.back()
                            except Exception:
                                pass
                            time.sleep(0.25)
                        self.device.screenshot()
                        try:
                            self.ui_ensure(page_os)
                            self.map_init(map_=None)
                            self.update()
                        except Exception:
                            logger.debug('重建视图失败（soft recovery）', exc_info=True)
                        clickable_grid_group = self.view.select(location=target_loc)
                        if clickable_grid_group:
                            logger.info('软恢复后找到格子，重试点击')
                            try:
                                time.sleep(0.3)
                                self.device.click(clickable_grid_group[0])
                                self.wait_until_walk_stable(confirm_timer=Timer(1.5, count=4))
                                logger.info('软恢复成功，舰队已到达')
                                break
                            except Exception:
                                logger.debug('软恢复重试点击失败', exc_info=True)
                    except Exception as rec_e:
                        logger.debug(f'软恢复过程出现异常: {rec_e}')
                    if try_idx == 1:
                        logger.warning('软恢复失败，尝试重启应用以恢复状态')
                        try:
                            self.device.app_stop()
                            time.sleep(1.0)
                            self.device.app_start()
                            LoginHandler(self.config, self.device).handle_app_login()
                            # 确保回到 OS 页并重建地图数据
                            self.ui_ensure(page_os)
                            time.sleep(0.8)
                            try:
                                self.map_init(map_=None)
                                self.update()
                            except Exception:
                                logger.debug('重建地图数据失败（app restart）', exc_info=True)
                            clickable_grid_group = self.view.select(location=target_loc)
                            if clickable_grid_group:
                                time.sleep(0.3)
                                self.device.click(clickable_grid_group[0])
                                self.wait_until_walk_stable(confirm_timer=Timer(1.5, count=4))
                                logger.info('重启应用后恢复成功，舰队已到达')
                                break
                        except Exception:
                            logger.error('应用重启恢复失败，跳过该舰队并继续下一步', exc_info=True)
                            # 不要求人工接管，继续后续流程（让外层循环接着处理下一个舰队或最终重扫）
                            recovered = False
                    time.sleep(0.5)

        backup = self.config.temporary(OpsiGeneral_RepairThreshold=-1, Campaign_UseAutoSearch=False)
        try:
            logger.info('所有舰队已定点，执行最终全图重扫（双遍检查）')
            self._solved_map_event = set()
            for _ in range(2):
                try:
                    self.map_rescan(rescan_mode='full')
                except Exception as e:
                    logger.debug(f'最终全图重扫出现异常，继续重试: {e}', exc_info=True)
                    time.sleep(0.6)
        finally:
            backup.recover()

        logger.info('执行一次自律寻敌以清理可能的装置')
        try:
            self.run_auto_search(question=True, rescan=None, after_auto_search=True)
        except Exception as e:
            logger.warning(f'自律寻敌过程出现异常: {e}')

    def _select_story_option_by_index(self, target_index, options_count=3):
        # 手动选择剧情选项
        option_confirm_timer = Timer(1.5, count=3).start()
        while option_confirm_timer.reached() is False:
            self.device.screenshot()
            # 识别所有选项
            options = self._story_option_buttons_2()
            if len(options) == options_count:
                try:
                    select = options[target_index]
                    self.device.click(select)
                    time.sleep(0.5)
                    return True
                except IndexError:
                    select = options[0]
                    self.device.click(select)
                    time.sleep(0.5)
                    return False
            time.sleep(0.3)
        return False

    def _click_story_confirm_button(self):
        # 点击剧情确认按钮POPUP_CONFIRM
        confirm_timer = Timer(3, count=6).start()
        while confirm_timer.reached() is False:
            self.device.screenshot()
            if self.appear(POPUP_CONFIRM, offset=(20, 20), interval=0):
                self.device.click(POPUP_CONFIRM)
                time.sleep(0.5)
                return True
            time.sleep(0.3)
        return False



    def _handle_siren_bug_reinteract(self, drop=None):
        # 23:55 - 00:05 跳过处理
        if getattr(self.config, 'OpsiSirenBug_SirenBug_CrossDay', False):
            from datetime import time as dt_time
            now = datetime.now()
            if now.time() >= dt_time(23, 55) or now.time() <= dt_time(0, 5):
                logger.info(f'当前时间: {now.strftime("%H:%M")}, 跳过塞壬研究装置BUG利用')
                return
        
        # 侵蚀一塞壬研究装置处理后，跳转指定高侵蚀区域触发塞壬研究装置消耗两次紫币，最后返回侵蚀一自律   
        try:
            siren_research_enable = self.config.cross_get(keys="OpsiHazard1Leveling.OpsiSirenBug.SirenResearch_Enable")
            siren_bug_enable = getattr(self.config, 'OpsiSirenBug_SirenBug_Enable', False)
            siren_bug_zone = getattr(self.config, 'OpsiSirenBug_SirenBug_Zone', 0)
            siren_bug_type = getattr(self.config, 'OpsiSirenBug_SirenBug_Type', 'dangerous')
            disable_task_switch = getattr(self.config, 'OpsiSirenBug_DisableTaskSwitchDuringBug', False)
        except Exception as e:
            logger.warning(f'读取SirenBug配置失败: {e}，跳过塞壬研究装置BUG利用')
            return

        # SirenBug_Zone 预处理：嘗試轉换為 int
        try:
            siren_bug_zone = int(siren_bug_zone)
        except (ValueError, TypeError):
            pass  # 保持原值，如果是字符串（海域名称）则后续处理

        # 前置条件校验
        if not siren_research_enable or not siren_bug_enable:
            logger.info('SirenBug功能前置条件不满足（SirenResearch_Enable 或 SirenBug_Enable 为 False），跳过塞壬研究装置BUG利用')
            return

        # 如果启用了禁用任务切换选项，设置标志
        if disable_task_switch:
            self.config._disable_task_switch = True
            logger.info('【塞壬Bug利用】禁用任务切换')

        if not siren_bug_zone:
            logger.info('SirenBug功能前置条件不满足（SirenBug_Zone 未设置），跳过塞壬研究装置BUG利用')
            # Ensure the flag is cleared if we return early
            if disable_task_switch:
                self.config._disable_task_switch = False
            return

        current_zone_id = self.zone.zone_id
        if current_zone_id not in (22, 44):
            logger.warning(f'当前区域{current_zone_id}非侵蚀一，跳过塞壬研究装置BUG利用')
            # Ensure the flag is cleared if we return early
            if disable_task_switch:
                self.config._disable_task_switch = False
            return
        
        erosion_one_zone = self.name_to_zone(current_zone_id)
        
        logger.hr(f'RUN SIREN BUG EXPLOITATION')
        
        try:
            # 解析目标区域
            try:
                target_zone = self.name_to_zone(siren_bug_zone)
            except Exception:
                logger.warning(f'无法解析SirenBug目标区域: {siren_bug_zone}，跳过塞壬研究装置BUG利用')
                # Ensure the flag is cleared if we return early
                if disable_task_switch:
                    self.config._disable_task_switch = False
                return
            
            logger.info(f'当前区域: {erosion_one_zone}, 目标区域: {target_zone}')
            
            # 跳转至指定高侵蚀区域
            with self.config.temporary(STORY_ALLOW_SKIP=False):
                self.os_map_goto_globe(unpin=False)
                self.globe_goto(target_zone, types=(siren_bug_type.upper(),), refresh=True)
                self.zone_init()

                # Siren bug count sleep
                SirenBug_DailyCount = self.config.OpsiSirenBug_SirenBug_DailyCount
                if SirenBug_DailyCount > 0:
                    logger.info(f'Siren bug usage count: {SirenBug_DailyCount}, sleep {SirenBug_DailyCount}s before auto search')
                    time.sleep(SirenBug_DailyCount)

                self.map_init(map_=None)

                target_grid = getattr(self.config, 'OpsiSirenBug_SirenBug_Grid', None)
                
                device_handled = False

                if target_grid:
                    try:
                        target_grid = target_grid.upper()
                        target_loc = location_ensure(target_grid)
                        
                        logger.info(f'指定了塞壬研究装置位置: {target_grid}，直接处理')

                        # 滑动到目标视角
                        self.focus_to(target_loc, swipe_limit=(6, 5))
                        self.focus_to_grid_center(0.3)
                        self.device.screenshot()
                        self.update()

                        if target_loc in self.map:
                            grid = self.convert_global_to_local(target_loc)
                            self._solved_map_event = set()
                            find_device_timer = Timer(30, count=1).start()
                            while not find_device_timer.reached() and not device_handled:
                                if self._handle_siren_bug_device(grid):
                                    device_handled = True
                                    break
                                
                                # 寻路中断，重新寻路
                                find_device_timer.reset()
                                time.sleep(1.0)
                                
                                self.focus_to(target_loc, swipe_limit=(6, 5))
                                self.focus_to_grid_center(0.3)
                                self.device.screenshot()
                                self.update()
                                grid = self.convert_global_to_local(target_loc)
                        else:
                            logger.warning(f'目标 {target_grid} 不在地图中')

                    except Exception as e:
                        logger.error(f'处理指定塞壬研究装置位置时出错: {e}', exc_info=True)
                        logger.warning('将回退到全图扫描模式')

                if not device_handled:
                    camera_queue = self.map.camera_data
                    find_device_timer = Timer(30, count=1).start()
                    self._solved_map_event = set()

                    while find_device_timer.reached() is False and not device_handled:
                        # 遍历相机视角，滑动地图
                        if len(camera_queue) == 0:
                            camera_queue = self.map.camera_data
                        camera_queue = camera_queue.sort_by_camera_distance(self.camera)
                        target_camera = camera_queue[0]
                        camera_queue = camera_queue[1:]

                        # 滑动到目标视角
                        self.focus_to(target_camera, swipe_limit=(6, 5))
                        self.focus_to_grid_center(0.3)
                        self.device.screenshot()
                        self.update()

                        # 寻找塞壬研究装置
                        grids = self.view.select(is_scanning_device=True)
                        if grids and grids[0].is_scanning_device and 'is_scanning_device' not in self._solved_map_event:
                            grid = grids[0]
                            logger.info(f'找到塞壬研究装置: {grid}')

                            try:
                                if self._handle_siren_bug_device(grid):
                                    device_handled = True
                                    break
                            except Exception:
                                raise

                            find_device_timer.reset()
                            camera_queue = self.map.camera_data
                            time.sleep(1.0)

                        time.sleep(0.5)

                    if not device_handled:
                        logger.warning(f'区域{siren_bug_zone}未找到塞壬研究装置，跳过后续操作')

                        # 没找到吊机自动关闭bug利用
                        if getattr(self.config, 'OpsiSirenBug_SirenBug_AutoDisable', False):
                            self.config.OpsiSirenBug_SirenBug_Enable = False

                        raise RuntimeError('未找到塞壬研究装置')

            # Increase bug count
            self.config.OpsiSirenBug_SirenBug_DailyCount += 1
            self.config.OpsiSirenBug_SirenBug_DailyCountRecord = datetime.now()
            count = self.config.OpsiSirenBug_SirenBug_DailyCount
            logger.info(f'Siren bug exploitation successful, daily count: {count}')

            # 发送成功通知
            try:
                if hasattr(self, 'notify_push'):
                    zone_type_text = "安全海域" if siren_bug_type == 'safe' else "普通海域"
                    self.notify_push(
                        title="[Alas] 塞壬Bug利用 - 完成",
                        content=f"已完成塞壬研究装置Bug利用\\n目标区域: {target_zone} ({zone_type_text})\\n已返回侵蚀一区域"
                    )
            except Exception as notify_err:
                logger.debug(f'发送成功通知失败: {notify_err}')
            
            count_limit = self.config.OpsiSirenBug_SirenBug_CountLimit
            if count_limit > 0 and count >= count_limit:
                logger.info(f'已达到塞壬Bug自动处理阈值 ({count_limit}次)，开始自动收菜')
                # 禁用塞壬研究装置的处理
                self.config._disable_siren_research = True
                if siren_bug_type == 'safe':
                    self.os_auto_search_daemon_until_combat()
                    logger.info('遇到敌舰，卡位完成')
                    self.fleet_set(1 if self.config.OpsiFleet_Fleet != 1 else 2)
                self.os_auto_search_run()
                self.fleet_set(self.config.OpsiFleet_Fleet)
                self.config.OpsiSirenBug_SirenBug_DailyCount = 0
                # 恢复塞壬研究装置的处理
                self.config._disable_siren_research = False
                logger.info('自动收菜完成，返回正常任务流程')
                try:
                    if hasattr(self, 'notify_push'):
                        self.notify_push(
                            title="[Alas] 塞壬Bug利用 - 自动收菜完成",
                            content=f"已达到塞壬研究装置Bug利用阈值，自动收菜完成"
                        )
                except Exception as notify_err:
                    logger.debug(f'发送自动收菜完成通知失败: {notify_err}')

            # Bug利用核心操作完成，清除禁用任务切换标志
            if disable_task_switch and hasattr(self.config, '_disable_task_switch'):
                self.config._disable_task_switch = False
                logger.info('【塞壬Bug利用】核心操作完成，恢复任务切换')

            # 返回侵蚀一区域
            logger.info('【塞壬Bug利用】返回侵蚀一区域')
            self.os_map_goto_globe(unpin=False)
            self.globe_goto(erosion_one_zone, types=('SAFE', 'DANGEROUS'), refresh=True)
            logger.info('【塞壬Bug利用】返回侵蚀一区域完成')

        except (RuntimeError, Exception) as e:
            logger.error(f'塞壬研究装置BUG利用失败: {e}', exc_info=True)
            
            # 异常时清除标志
            if disable_task_switch and hasattr(self.config, '_disable_task_switch'):
                self.config._disable_task_switch = False
                logger.info('【塞壬Bug利用】异常退出，恢复任务切换')
            
            # 发送失败通知
            try:
                if hasattr(self, 'notify_push'):
                    self.notify_push(
                        title="[Alas] 塞壬Bug利用 - 失败",
                        content=f"塞壬研究装置BUG利用失败\\n错误: {str(e)}\\n请检查日志"
                    )
            except Exception as notify_err:
                logger.debug(f'发送失败通知失败: {notify_err}')
            
            # 为避免卡在选项中，尝试选择最后一个选项退出
            if self._select_story_option_by_index(target_index=2, options_count=3):
                logger.info('异常处理：已尝试选择最后一个选项退出剧情')

            # 尝试返回侵蚀一
            try:
                self.os_map_goto_globe(unpin=False)
                self.globe_goto(erosion_one_zone, types=('SAFE', 'DANGEROUS'), refresh=True)
                logger.info('异常处理：返回侵蚀一区域')
            except Exception as return_err:
                logger.error(f'返回侵蚀一失败: {return_err}')
        finally:
            pass

    def _handle_siren_bug_device(self, grid):
        """
        Args:
            grid:

        Returns:
            bool: True if handled successfully.
                  False if pathfinding interrupted and needs to be restarted.
        """
        # 移动舰队至塞壬研究装置，触发剧情
        self.device.click(grid)
        
        # 等待剧情选项出现（表示舰队已到达装置并触发剧情）
        option_wait_timer = Timer(10, count=20).start()
        options_found = False
        while not option_wait_timer.reached():
            self.device.screenshot()
            options = self._story_option_buttons_2()
            if len(options) >= 3:
                logger.info(f'检测到剧情选项，开始处理Bug利用')
                options_found = True
                break
            time.sleep(0.5)
        
        if not options_found:
            logger.warning(f'等待剧情选项超时，跳过后续操作')
            raise RuntimeError('等待剧情选项超时，跳过后续操作')
        
        # 找到选项，处理剧情
        with self.config.temporary(STORY_ALLOW_SKIP=False):
            self._solved_map_event.add('is_scanning_device')

            # 首先检测是否遇到的是柱子
            if self.appear_then_click(REWARD_BOX_THIRD_OPTION, offset=(20, 20), interval=3):
                logger.warning('[Bug利用] 检测到宝箱选项，重新开始寻找装置')
                if 'is_scanning_device' in self._solved_map_event:
                    self._solved_map_event.remove('is_scanning_device')
                return False  

            # 第1次：选择第2个选项
            logger.info('[Bug利用] 等待第1组选项（选择第2个）')
            time.sleep(1.5)
            if self._select_story_option_by_index(target_index=1, options_count=3):
                logger.info('[Bug利用] 第1组选项点击成功')
                time.sleep(0.5)
                if self._click_story_confirm_button():
                    logger.info('[Bug利用] 第1组确认成功')
            else:
                logger.warning('[Bug利用] 第1组选项点击失败')
                raise RuntimeError('第1组选项点击失败，跳过后续操作')
            
            # 第2次：选择第2个选项
            logger.info('[Bug利用] 等待第2组选项（选择第2个）')
            time.sleep(2.0)
            if self._select_story_option_by_index(target_index=1, options_count=3):
                logger.info('[Bug利用] 第2组选项点击成功')
                time.sleep(0.5)
                if self._click_story_confirm_button():
                    logger.info('[Bug利用] 第2组确认成功')
            else:
                logger.warning('[Bug利用] 第2组选项点击失败')
                raise RuntimeError('第2组选项点击失败，跳过后续操作')
            
            # 第3次：选择第3个选项
            logger.info('[Bug利用] 等待第3组选项（选择第3个）')
            time.sleep(2.0)
            if self._select_story_option_by_index(target_index=2, options_count=3):
                logger.info('[Bug利用] 第3组选项点击成功')
                time.sleep(0.5)
                if self._click_story_confirm_button():
                    logger.info('[Bug利用] 第3组确认成功')
            else:
                logger.warning('[Bug利用] 第3组选项点击失败')
                raise RuntimeError('第3组选项点击失败，跳过后续操作')

            logger.info('[Bug利用] 所有选项处理完成')
            
        return True