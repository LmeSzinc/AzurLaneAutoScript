
from datetime import datetime, timedelta

from module.equipment.assets import EQUIPMENT_OPEN
from module.exception import ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.notify import handle_notify as notify_handle_notify
from module.os.assets import FLEET_FLAGSHIP
from module.os.map import OSMap
from module.os.ship_exp import ship_info_get_level_exp
from module.os.ship_exp_data import LIST_SHIP_EXP
from module.os.tasks.smart_scheduling_utils import is_smart_scheduling_enabled
from module.os.tasks.scheduling import CoinTaskMixin
from module.os_handler.action_point import ActionPointLimit


class OpsiHazard1Leveling(CoinTaskMixin, OSMap):


    def _cl1_smart_scheduling_check(self, yellow_coins):
        """处理智能调度中的黄币检查与任务切换"""
        if not is_smart_scheduling_enabled(self.config):
            # 未启用智能调度时，凭证不足则推迟任务
            cl1_preserve = self.config.OpsiHazard1Leveling_OperationCoinsPreserve
            if yellow_coins < cl1_preserve:
                logger.info(f'[智能调度] 作战补给凭证不足 ({yellow_coins} < {cl1_preserve})，推迟侵蚀 1 任务至次日')
                self.config.task_delay(server_update=True)
                self.config.task_stop()
            return

        # 优先使用智能调度的黄币保留值
        if hasattr(self, '_get_smart_scheduling_operation_coins_preserve'):
            cl1_preserve = self._get_smart_scheduling_operation_coins_preserve()
        else:
            cl1_preserve = self.config.OpsiHazard1Leveling_OperationCoinsPreserve
        
        if yellow_coins < cl1_preserve:
            logger.info(f'[智能调度] 作战补给凭证不足 ({yellow_coins} < {cl1_preserve})，需要获取凭证')

            # 进入行动力界面读取当前行动力数据
            self.action_point_enter()
            self.action_point_safe_get()
            self.action_point_quit()

            # 读取短猫相接任务的行动力保留值
            meow_ap_preserve = int(self.config.cross_get(
                keys='OpsiMeowfficerFarming.OpsiMeowfficerFarming.ActionPointPreserve',
                default=1000
            ))

            # 覆盖为智能调度的行动力保留值
            if hasattr(self, '_get_smart_scheduling_action_point_preserve'):
                smart_ap_preserve = self._get_smart_scheduling_action_point_preserve()
                if smart_ap_preserve > 0:
                    meow_ap_preserve = smart_ap_preserve

            # 检查行动力是否足以执行补充任务
            _previous_coins_ap_insufficient = getattr(self.config, 'OpsiHazard1_PreviousCoinsApInsufficient', False)
            if self._action_point_total < meow_ap_preserve:
                logger.warning(f'行动力不足以执行短猫 ({self._action_point_total} < {meow_ap_preserve})')

                if not _previous_coins_ap_insufficient:
                    _previous_coins_ap_insufficient = True
                    self.notify_push(
                        title="[Alas] 智能调度 - 警告",
                        content=f"作战补给凭证 {yellow_coins} 低于保留值 {cl1_preserve}\n行动力 {self._action_point_total} 不足 (需要 {meow_ap_preserve})\n任务已推迟"
                    )
                else:
                    logger.info('上次检查行动力不足，跳过推送通知')

                logger.info('推迟任务 50 分钟')
                self.config.task_delay(minute=50)
                self.config.task_stop()
            else:
                # 行动力充足，切换到预设计的补充任务
                logger.info(f'[智能调度] 行动力充足 ({self._action_point_total})，开始执行补充任务')
                _previous_coins_ap_insufficient = False
                
                task_enable_config = {
                    'OpsiMeowfficerFarming': self.config.cross_get(
                        keys='OpsiScheduling.OpsiScheduling.EnableMeowfficerFarming',
                        default=True
                    ),
                    'OpsiObscure': self.config.cross_get(
                        keys='OpsiScheduling.OpsiScheduling.EnableObscure',
                        default=False
                    ),
                    'OpsiAbyssal': self.config.cross_get(
                        keys='OpsiScheduling.OpsiScheduling.EnableAbyssal',
                        default=False
                    ),
                    'OpsiStronghold': self.config.cross_get(
                        keys='OpsiScheduling.OpsiScheduling.EnableStronghold',
                        default=False
                    ),
                }
                
                task_names = {
                    'OpsiMeowfficerFarming': '短猫相接',
                    'OpsiObscure': '隐秘海域',
                    'OpsiAbyssal': '深渊海域',
                    'OpsiStronghold': '塞壬要塞'
                }
                
                all_coin_tasks = [task for task, enabled in task_enable_config.items() if enabled]
                if not all_coin_tasks:
                    logger.warning('[智能调度] 未启用任何作战补给凭证补充任务，将执行短猫相接')
                    all_coin_tasks = ['OpsiMeowfficerFarming']
                
                enabled_names = '、'.join([task_names.get(task, task) for task in all_coin_tasks])
                logger.info(f'[智能调度] 启用的补充任务: {enabled_names}')
                
                enabled_tasks = []
                auto_enabled_tasks = []
                with self.config.multi_set():
                    for task in all_coin_tasks:
                        if self.config.is_task_enabled(task):
                            enabled_tasks.append(task)
                            logger.info(f'[智能调度] 凭证补充已启用: {task_names.get(task, task)}')
                        else:
                            logger.info(f'[智能调度] 自动启用补充任务: {task_names.get(task, task)}')
                            self.config.cross_set(keys=f'{task}.Scheduler.Enable', value=True)
                            auto_enabled_tasks.append(task)
                
                available_tasks = enabled_tasks + auto_enabled_tasks
                if auto_enabled_tasks:
                    auto_enabled_names = '、'.join([task_names.get(task, task) for task in auto_enabled_tasks])
                    logger.info(f'[智能调度] 已自动启用以下补充任务: {auto_enabled_names}')
                
                if not available_tasks:
                    logger.error('[智能调度] 无法启用任何补充任务，处于异常状态')
                    self.config.task_delay(minute=60)
                    self.config.task_stop()
                    self.config.OpsiHazard1_PreviousCoinsApInsufficient = _previous_coins_ap_insufficient
                    return
                
                task_names_str = '、'.join([task_names.get(task, task) for task in available_tasks])
                self.notify_push(
                    title="[Alas info] 智能调度 - 切换至凭证补充任务",
                    content=f"作战补给凭证 {yellow_coins} 低于保留值 {cl1_preserve}\n行动力: {self._action_point_total} (需要 {meow_ap_preserve})\n切换至 {task_names_str} 获取凭证"
                )

                with self.config.multi_set():
                    for task in available_tasks:
                        self.config.task_call(task)
                    
                    cd = self.nearest_task_cooling_down
                    if cd is not None:
                        logger.info(f'[智能调度] 检测到冷却中的任务 {cd.command}，延迟侵蚀 1 任务至 {cd.next_run}')
                        self.config.task_delay(target=cd.next_run)
                self.config.task_stop()
            self.config.OpsiHazard1_PreviousCoinsApInsufficient = _previous_coins_ap_insufficient

    def _cl1_ap_check(self):
        """最低行动力保留检查"""
        self.action_point_enter()
        self.action_point_safe_get()
        self.action_point_quit()

        min_reserve = self.config.OS_ACTION_POINT_PRESERVE
        if self._action_point_total < min_reserve:
            logger.warning(f'[智能调度] 行动力低于最低保留 ({self._action_point_total} < {min_reserve})')

            _previous_ap_insufficient = getattr(self.config, 'OpsiHazard1_PreviousApInsufficient', False)
            if not _previous_ap_insufficient:
                _previous_ap_insufficient = True
                self.notify_push(
                    title="[Alas info] 智能调度 - 行动力低于最低保留",
                    content=f"当前行动力 {self._action_point_total} 低于最低保留 {min_reserve}，已推迟任务"
                )
            else:
                logger.info('上次检查行动力低于最低保留，跳过推送通知')

            logger.info('[智能调度] 推迟侵蚀 1 任务 50 分钟')
            self.config.task_delay(minute=50)
            self.config.task_stop()
        else:
            _previous_ap_insufficient = False
        self.config.OpsiHazard1_PreviousApInsufficient = _previous_ap_insufficient

    def _cl1_run_battle(self):
        """执行侵蚀 1 实际战斗逻辑"""
        if self.config.OpsiHazard1Leveling_TargetZone != 0:
            zone = self.config.OpsiHazard1Leveling_TargetZone
        else:
            zone = 22
        logger.hr(f'OS hazard 1 leveling, zone_id={zone}', level=1)
        if self.zone.zone_id != zone or not self.is_zone_name_hidden:
            self.globe_goto(self.name_to_zone(zone), types='SAFE', refresh=True)
        self.fleet_set(self.config.OpsiFleet_Fleet)
        search_completed = self.run_strategic_search()

        # 无论战略搜索是否正常完成，都执行后续重扫和巡逻，以确保任务不被遗漏
        if True: 
            if not search_completed and search_completed is not None:
                 logger.warning("战略搜索返回 False，但仍将继续执行重扫/巡逻")

            self._solved_map_event = set()
            self._solved_fleet_mechanism = False
            self.clear_question()
            self.map_rescan()

            if self.config.OpsiHazard1Leveling_ExecuteFixedPatrolScan:
                exec_fixed = getattr(self.config, 'OpsiHazard1Leveling_ExecuteFixedPatrolScan', False)
                if exec_fixed and not self._solved_map_event:
                    self._execute_fixed_patrol_scan(ExecuteFixedPatrolScan=True)
                    self._solved_map_event = set()
                    self.clear_question()
                    self.map_rescan()

        self.handle_after_auto_search()
        solved_events = getattr(self, '_solved_map_event', set())
        if 'is_akashi' in solved_events:
            try:
                from module.statistics.cl1_database import db as cl1_db
                instance_name = getattr(self.config, 'config_name', 'default')
                cl1_db.increment_akashi_encounter(instance_name)
                logger.info('已成功在数据库中增加侵蚀 1 明石遭遇次数')
            except Exception:
                logger.exception('无法将侵蚀 1 明石遭遇数据存入数据库')

    def _cl1_handle_telemetry(self):
        """处理遥测数据提交"""
        try:
            if not getattr(self.config, 'DropRecord_TelemetryReport', True):
                logger.info('[错误] 遥测上报已关闭')
            else:
                from module.statistics.cl1_data_submitter import get_cl1_submitter
                instance_name = getattr(self.config, 'config_name', None)
                submitter = get_cl1_submitter(instance_name=instance_name)
                raw_data = submitter.collect_data()
                if raw_data.get('battle_count', 0) > 0:
                    metrics = submitter.calculate_metrics(raw_data)
                    submitter.submit_data(metrics)
                    logger.info(f'侵蚀 1 数据提交已排队，实例名称: {instance_name}')
        except Exception as e:
            logger.debug(f'侵蚀 1 数据提交失败: {e}')

    def os_hazard1_leveling(self):
        """执行大世界侵蚀 1 练级任务。"""
        logger.hr('OS hazard 1 leveling', level=1)
        # 启用随机事件以获得收益
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=True,
        )

        while True:
            # 读取行动力保留值
            self.config.OS_ACTION_POINT_PRESERVE = int(getattr(
                self.config, 'OpsiHazard1Leveling_MinimumActionPointReserve', 200
            ))

            if self.config.is_task_enabled('OpsiAshBeacon') \
                    and not self._ash_fully_collected \
                    and self.config.OpsiAshBeacon_EnsureFullyCollected:
                logger.info('余烬信标未收集满，暂时忽略行动力限制')
                self.config.OS_ACTION_POINT_PRESERVE = 0
            logger.attr('OS_ACTION_POINT_PRESERVE', self.config.OS_ACTION_POINT_PRESERVE)

            # ===== 智能调度：黄币检查与任务切换 =====
            yellow_coins = self.get_yellow_coins()
            self._cl1_smart_scheduling_check(yellow_coins)

            # 获取当前区域
            self.get_current_zone()

            # 侵蚀 1 练级时，行动力优先用于此任务，而非短猫。
            keep_current_ap = True
            if self.config.OpsiGeneral_BuyActionPointLimit > 0:
                keep_current_ap = False
            self.action_point_set(cost=120, keep_current_ap=keep_current_ap, check_rest_ap=True)

            # ===== 智能调度：行动力阈值推送检查 =====
            self.check_and_notify_action_point_threshold()

            # ===== 最低行动力保留检查 =====
            self._cl1_ap_check()

            # ===== 执行侵蚀 1 实际战斗逻辑 =====
            self._cl1_run_battle()

            # ===== 处理遥测数据提交 =====
            self._cl1_handle_telemetry()

            self.config.check_task_switch()

    def os_check_leveling(self):
        """检查大世界阵容练级进度。"""
        logger.hr('OS check leveling', level=1)
        logger.attr('OpsiCheckLeveling_LastRun', self.config.OpsiCheckLeveling_LastRun)
        time_run = self.config.OpsiCheckLeveling_LastRun + timedelta(days=1)
        logger.info(f'练级检查下次运行时间: {time_run}')
        if datetime.now().replace(microsecond=0) < time_run:
            logger.info('未到运行时间，跳过')
            return
        target_level = self.config.OpsiCheckLeveling_TargetLevel
        if not isinstance(target_level, int) or target_level < 0 or target_level > 125:
            logger.error(f'目标等级无效: {target_level}，必须是 0 到 125 之间的整数')
            raise ScriptError(f'Invalid opsi ship target level: {target_level}')
        if target_level == 0:
            logger.info('目标等级为 0，跳过')
            return

        logger.attr('待检查舰队', self.config.OpsiFleet_Fleet)
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.equip_enter(FLEET_FLAGSHIP)
        all_full_exp = True
        
        ship_data_list = []
        position = 1

        while True:
            self.device.screenshot()
            level, exp = ship_info_get_level_exp(main=self)
            total_exp = LIST_SHIP_EXP[level - 1] + exp
            logger.info(f'位置: {position}, 等级: {level}, 经验: {exp}, 总经验: {total_exp}, 目标经验: {LIST_SHIP_EXP[target_level - 1]}')
            
            ship_data_list.append({
                'position': position,
                'level': level,
                'current_exp': exp,
                'total_exp': total_exp
            })
            
            if total_exp < LIST_SHIP_EXP[target_level - 1]:
                all_full_exp = False
            
            if not self.equip_view_next():
                break
            position += 1

        try:
            from module.statistics.ship_exp_stats import save_ship_exp_data
            from module.statistics.opsi_month import get_opsi_stats
            
            instance_name = self.config.config_name if hasattr(self.config, 'config_name') else None
            
            current_battles = get_opsi_stats(instance_name=instance_name).summary().get('total_battles', 0)
            
            save_ship_exp_data(
                ships=ship_data_list,
                target_level=target_level,
                fleet_index=self.config.OpsiFleet_Fleet,
                battle_count_at_check=current_battles,
                instance_name=instance_name  # 指定实例名称保存数据
            )
        except Exception as e:
            logger.warning(f'保存舰船经验数据失败: {e}')

        if all_full_exp:
            logger.info(f'舰队 {self.config.OpsiFleet_Fleet} 的所有舰船均已满经验（等级 {target_level} 或更高）')
            self.notify_push(
                title="练级检查通过",
                content=f"<{self.config.config_name}> {self.config.task} 已达到等级限制 {target_level}。"
            )
        self.ui_back(appear_button=EQUIPMENT_OPEN, check_button=self.is_in_map)
        self.config.OpsiCheckLeveling_LastRun = datetime.now().replace(microsecond=0)
        if all_full_exp and self.config.OpsiCheckLeveling_DelayAfterFull:
            logger.info('所有舰船满经验后延迟任务')
            self.config.task_delay(server_update=True)
            self.config.task_stop()
