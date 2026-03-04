"""
OpsiScheduling - 智能调度模块

智能调度功能，用于在侵蚀1练级和短猫相接/其他黄币补充任务之间智能切换。

功能说明:
    1. 黄币检查与任务切换 - 当黄币低于保留值时，自动切换到黄币补充任务
    2. 行动力阈值推送通知 - 当行动力跨越阈值时发送推送通知
    3. 最低行动力保留检查 - 检查行动力是否低于最低保留值
    4. 任务智能调度 - 在不同任务之间智能切换以获取资源

任务层级:
    - OpsiScheduling 是和 OpsiHazard1Leveling、OpsiMeowfficerFarming 相同层级的调度器
    - 它负责协调这些任务的执行顺序和切换逻辑

配置项:
    - Scheduler.Enable: 任务启用开关（启用此任务即启用智能调度功能）
    - OperationCoinsPreserve: 智能调度时侵蚀1保留的黄币阀值（优先级高于原配置）
    - ActionPointPreserve: 智能调度时保留的行动力阀值（同时作用于所有任务）
    - ActionPointNotifyLevels: 行动力阈值列表，用于推送通知
    - OperationCoinsReturnThreshold: 黄币返回阈值
    - OperationCoinsReturnThresholdApplyToAllCoinTasks: 黄币阈值是否适用于所有黄币补充任务

此模块包含:
    - OpsiScheduling: 智能调度任务主类
    - CoinTaskMixin: 黄币补充任务的通用 Mixin 类（供其他任务继承使用）
"""
import re
from datetime import datetime, timedelta

from module.logger import logger
from module.os.map import OSMap
from module.os.tasks.smart_scheduling_utils import is_smart_scheduling_enabled


class CoinTaskMixin:
    """
    黄币补充任务的通用 Mixin 类。
    
    提供黄币补充任务（OpsiObscure、OpsiAbyssal、OpsiStronghold、OpsiMeowfficerFarming）
    所需的通用功能，包括黄币阈值检查、任务切换等。
    
    使用方法:
        class OpsiMeowfficerFarming(CoinTaskMixin, OSMap):
            ...
    """
    
    # 任务名称映射（用于通知显示）
    TASK_NAMES = {
        'OpsiMeowfficerFarming': '短猫相接',
        'OpsiObscure': '隐秘海域',
        'OpsiAbyssal': '深渊海域',
        'OpsiStronghold': '塞壬要塞'
    }
    
    # 所有黄币补充任务（固定顺序）
    ALL_COIN_TASKS = ['OpsiObscure', 'OpsiAbyssal', 'OpsiStronghold', 'OpsiMeowfficerFarming']
    
    # 配置路径常量
    CONFIG_PATH_CL1_PRESERVE = 'OpsiHazard1Leveling.OpsiHazard1Leveling.OperationCoinsPreserve'
    CONFIG_PATH_RETURN_THRESHOLD = 'OpsiScheduling.OpsiScheduling.OperationCoinsReturnThreshold'
    # 四个独立任务开关的配置路径
    CONFIG_PATH_ENABLE_MEOWFFICER = 'OpsiScheduling.OpsiScheduling.EnableMeowfficerFarming'
    CONFIG_PATH_ENABLE_OBSCURE = 'OpsiScheduling.OpsiScheduling.EnableObscure'
    CONFIG_PATH_ENABLE_ABYSSAL = 'OpsiScheduling.OpsiScheduling.EnableAbyssal'
    CONFIG_PATH_ENABLE_STRONGHOLD = 'OpsiScheduling.OpsiScheduling.EnableStronghold'
    # 智能调度新增配置路径
    CONFIG_PATH_USE_SMART_CL1_PRESERVE = 'OpsiScheduling.OpsiScheduling.UseSmartSchedulingOperationCoinsPreserve'
    CONFIG_PATH_SMART_CL1_PRESERVE = 'OpsiScheduling.OpsiScheduling.OperationCoinsPreserve'
    CONFIG_PATH_SMART_AP_PRESERVE = 'OpsiScheduling.OpsiScheduling.ActionPointPreserve'
    
    # 各任务的配置路径常量（集中管理，避免硬编码）
    CONFIG_PATH_MEOW_AP_PRESERVE = 'OpsiMeowfficerFarming.OpsiMeowfficerFarming.ActionPointPreserve'
    CONFIG_PATH_CL1_MIN_AP_RESERVE = 'OpsiHazard1Leveling.OpsiHazard1Leveling.MinimumActionPointReserve'
    
    # 短猫相接任务名称
    TASK_NAME_MEOWFFICER_FARMING = 'OpsiMeowfficerFarming'
    
    # ==================== 推送通知相关方法 ====================
    
    def notify_push(self, title, content):
        """
        发送推送通知（智能调度功能）
        
        Args:
            title (str): 通知标题（会自动添加实例名称前缀）
            content (str): 通知内容
            
        Notes:
            - 仅在启用智能调度时生效
            - 需要在配置中设置 Error_OnePushConfig 才能发送推送
            - 使用 onepush 库发送通知到配置的推送渠道
            - 标题会自动格式化为 "[Alas <实例名>] 原标题" 的形式
        """
        # 检查是否启用智能调度
        if not is_smart_scheduling_enabled(self.config):
            return
        # 检查是否启用推送大世界相关邮件
        if not self.config.OpsiGeneral_NotifyOpsiMail:
            return
        
        # 检查是否配置了推送
        push_config = self.config.Error_OnePushConfig
        if not self._is_push_config_valid(push_config):
            logger.warning("推送配置未设置或 provider 为 null，跳过推送。请在 Alas 设置 -> 错误处理 -> OnePush 配置中设置有效的推送渠道。")
            return
        
        # 获取实例名称并格式化标题
        instance_name = getattr(self.config, 'config_name', 'Alas')
        if title.startswith('[Alas]'):
            formatted_title = f"[Alas <{instance_name}>]{title[6:]}"
        else:
            formatted_title = f"[Alas <{instance_name}>] {title}"
        
        try:
            from module.notify import handle_notify as notify_handle_notify
            success = notify_handle_notify(
                self.config.Error_OnePushConfig,
                title=formatted_title,
                content=content
            )
            if success:
                logger.info(f"推送通知成功: {formatted_title}")
            else:
                logger.warning(f"推送通知失败: {formatted_title}")
        except Exception as e:
            logger.error(f"推送通知异常: {e}")
    
    def _is_push_config_valid(self, push_config):
        """
        检查推送配置是否有效
        
        Args:
            push_config: 推送配置字符串或对象
            
        Returns:
            bool: True 表示配置有效，False 表示无效
        """
        if not push_config:
            return False
        
        # 尝试解析为结构化数据
        if isinstance(push_config, dict):
            provider = push_config.get('provider')
            return provider is not None and provider.lower() != 'null'
        
        # 回退到字符串匹配
        if isinstance(push_config, str):
            push_config_lower = push_config.lower()
            if 'provider:null' in push_config_lower or 'provider: null' in push_config_lower:
                return False
            if 'provider' in push_config_lower:
                if re.search(r'provider\s*[:=]\s*null', push_config_lower):
                    return False
        
        return True
    
    def check_and_notify_action_point_threshold(self):
        """
        发送行动力变化推送通知，并保存体力快照数据。
        需要类中包含 _action_point_total 属性。
        """
        if not hasattr(self, '_action_point_total'):
            return
            
        current_ap = self._action_point_total

        # 保存体力快照到数据库（用于 WebUI 体力变化曲线图）
        try:
            from module.statistics.cl1_database import db as cl1_db
            instance_name = getattr(self.config, 'config_name', 'default')
            source = 'cl1' if getattr(self, 'is_in_task_cl1_leveling', False) else 'meow'
            cl1_db.add_ap_snapshot(instance_name, current_ap, source=source)
        except Exception:
            logger.exception('Failed to save AP snapshot')

        # 上报体力到大盘（异步，不阻塞主流程）
        try:
            from module.base.api_client import ApiClient
            ApiClient.report_stamina(current_ap)
        except Exception:
            logger.exception('Failed to report stamina')

        self.notify_push(
            title="[Alas] 行动力出现变化！",
            content=f"当前行动力: {current_ap}"
        )
    
    # ==================== 黄币阈值相关方法 ====================
    
    def _get_operation_coins_return_threshold(self):
        """
        计算返回 CL1 的黄币阈值
        
        Returns:
            tuple: (return_threshold, cl1_preserve) 或 (None, cl1_preserve)（如果禁用检查）
                - return_threshold: 阈值数值，如果禁用检查则为 None
                - cl1_preserve: CL1 保留值（用于复用）
        """
        if not self.is_cl1_enabled:
            return None, None

        # 如果未启用智能调度，或者未开启黄币控制开关，则禁用黄币返回检查
        # 此时任务会一直运行到行动力不足（即传统模式）
        smart_enabled = is_smart_scheduling_enabled(self.config)
        use_smart_preserve = self.config.cross_get(
            keys=self.CONFIG_PATH_USE_SMART_CL1_PRESERVE
        )
        
        # 获取并缓存 CL1 保留值
        cl1_preserve = self._get_smart_scheduling_operation_coins_preserve()

        if not (smart_enabled and use_smart_preserve):
            logger.info('未开启智能调度黄币控制，禁用 OperationCoinsReturnThreshold 黄币返回检查')
            return None, cl1_preserve
        
        # 检查适用范围开关
        if not self._is_operation_coins_return_threshold_applicable():
            logger.info('OperationCoinsReturnThreshold 适用范围开关关闭：仅短猫相接启用；当前任务跳过黄币返回检查')
            return None, cl1_preserve

        # 从 OpsiScheduling 配置读取黄币返回阈值
        return_threshold_config = self.config.cross_get(
            keys=self.CONFIG_PATH_RETURN_THRESHOLD
        )

        logger.info(f'OperationCoinsReturnThreshold 配置值: {return_threshold_config}, CL1保留值: {cl1_preserve}')
        
        # 计算最终阈值：CL1 保留值 + 返回阈值
        return_threshold = (cl1_preserve or 0) + (return_threshold_config or 0)
        
        return return_threshold, cl1_preserve
    
    def _get_smart_scheduling_operation_coins_preserve(self):
        """
        获取智能调度模式下的侵蚀1黄币保留值

        Returns:
            int: 保留的黄币数量
        """
        # 检查是否启用智能调度黄币保留配置
        use_smart_preserve = self.config.cross_get(
            keys=self.CONFIG_PATH_USE_SMART_CL1_PRESERVE
        )
        
        if not use_smart_preserve:
            # 开关未开启，回退到侵蚀1原配置
            cl1_preserve_original = self.config.cross_get(
                keys=self.CONFIG_PATH_CL1_PRESERVE
            )
            # 保证返回 int 以免后续比较报错
            if cl1_preserve_original is None:
                cl1_preserve_original = 0
            logger.info(f'【智能调度】黄币保留使用原配置: {cl1_preserve_original} (智能调度开关未启用)')
            return cl1_preserve_original
        else:
            # 开关开启，使用智能调度自己的配置，允许为 0
            preserve = self.config.cross_get(
                keys=self.CONFIG_PATH_SMART_CL1_PRESERVE
            )
            if preserve is None:
                preserve = 0
            logger.info(f'【智能调度】黄币保留使用智能调度配置: {preserve} (开关已开启)')
            return preserve
    
    def _get_smart_scheduling_action_point_preserve(self):
        """
        获取智能调度模式下的行动力保留“覆盖值”。

        注意：此处不做回退。
        - 返回值 > 0：表示启用智能调度覆盖值（由调用方决定覆盖哪个任务的阀值）
        - 返回值 == 0：表示不覆盖，调用方应回退到各自任务的原配置

        Returns:
            int: 智能调度行动力保留覆盖值（0 表示不覆盖）
        """
        preserve = self.config.cross_get(
            keys=self.CONFIG_PATH_SMART_AP_PRESERVE
        )
        return preserve or 0
    
    def _get_current_coin_task_name(self):
        """
        获取当前任务名称（用于调度范围检查）
        
        Returns:
            str: 任务命令名称（如 'OpsiObscure'），如果不可用则返回类名
        """
        if hasattr(self.config, 'task') and hasattr(self.config.task, 'command') and self.config.task.command:
            return self.config.task.command
        return self.__class__.__name__
    
    def _get_enabled_coin_tasks(self):
        """
        获取智能调度中启用的黄币补充任务列表
        
        Returns:
            list: 启用的任务名称列表
        """
        enabled_tasks = []
        
        # 检查每个任务的独立开关
        task_config_map = {
            'OpsiMeowfficerFarming': self.CONFIG_PATH_ENABLE_MEOWFFICER,
            'OpsiObscure': self.CONFIG_PATH_ENABLE_OBSCURE,
            'OpsiAbyssal': self.CONFIG_PATH_ENABLE_ABYSSAL,
            'OpsiStronghold': self.CONFIG_PATH_ENABLE_STRONGHOLD,
        }
        
        for task_name, config_path in task_config_map.items():
            if self.config.cross_get(keys=config_path):
                enabled_tasks.append(task_name)
        
        return enabled_tasks
    
    def _is_operation_coins_return_threshold_applicable(self):
        """
        判断当前任务是否应该应用黄币返回阈值
        
        Config:
            OpsiScheduling.EnableMeowfficerFarming (bool) - 启用短猫相接
            OpsiScheduling.EnableObscure (bool) - 启用隐秘海域
            OpsiScheduling.EnableAbyssal (bool) - 启用深渊海域
            OpsiScheduling.EnableStronghold (bool) - 启用塞壬要塞
        """
        enabled_tasks = self._get_enabled_coin_tasks()
        current_task = self._get_current_coin_task_name()
        return current_task in enabled_tasks
    
    def _check_yellow_coins_and_return_to_cl1(self, context="循环中", task_display_name=None):
        """
        检查黄币是否充足，如果充足则返回 CL1

        Args:
            context: 上下文字符串（如 "任务开始前"、"循环中"）
            task_display_name: 任务显示名称（如 "隐秘海域"）

        Returns:
            bool: True 表示已返回 CL1，False 表示未返回
        """
        # 未启用智能调度时，跳过黄币充足检查，短猫会一直运行到行动力不足才停止
        smart_enabled = is_smart_scheduling_enabled(self.config)
        if not smart_enabled:
            return False

        if not self.is_cl1_enabled:
            return False

        # 获取智能调度配置
        return_threshold, cl1_preserve = self._get_operation_coins_return_threshold()
        # return_threshold 为 None 表示禁用黄币检查（OperationCoinsReturnThreshold=0 或其他禁用条件）
        if return_threshold is None:
            logger.info('OperationCoinsReturnThreshold 为 0，跳过黄币检查，仅使用行动力阈值控制')
            return False

        # 获取当前黄币数量
        yellow_coins = self.get_yellow_coins()

        logger.info(f'【{context}黄币检查】黄币={yellow_coins}, CL1保留值={cl1_preserve}, 阈值=CL1保留值+{return_threshold - cl1_preserve}={return_threshold}')

        if yellow_coins >= return_threshold:
            logger.info(f'黄币充足 ({yellow_coins} >= {return_threshold})，切换回侵蚀1继续执行')

            # 获取任务显示名称
            if task_display_name is None:
                task_name = self.__class__.__name__
                task_display_name = self.TASK_NAMES.get(task_name, task_name)

            self.notify_push(
                title=f"[Alas] {task_display_name} - 黄币充足",
                content=f"黄币 {yellow_coins} 达到阈值 {return_threshold}\n切换回侵蚀1继续执行"
            )
            self._disable_all_coin_tasks_and_return_to_cl1()
            return True

        # 黄币不足，继续执行当前任务
        return False
    
    # ==================== 任务切换相关方法 ====================
    
    def _disable_all_coin_tasks_and_return_to_cl1(self):
        """
        禁用所有黄币补充任务并返回 CL1
        """
        with self.config.multi_set():
            for task in self.ALL_COIN_TASKS:
                self.config.cross_set(keys=f'{task}.Scheduler.Enable', value=False)
            self.config.task_call('OpsiHazard1Leveling')
        self.config.task_stop()
    
    def _try_other_coin_tasks(self, current_task_name=None):
        """
        尝试调用其他黄币补充任务
        使用固定顺序：OpsiObscure -> OpsiAbyssal -> OpsiStronghold -> OpsiMeowfficerFarming
        
        Args:
            current_task_name: 当前任务名称（如 'OpsiObscure'）
        """
        if current_task_name is None:
            current_task_name = self.__class__.__name__
        
        # 查找当前任务索引
        try:
            current_index = self.ALL_COIN_TASKS.index(current_task_name)
        except ValueError:
            current_index = -1
        
        # 尝试当前任务之后的任务
        for i in range(current_index + 1, len(self.ALL_COIN_TASKS)):
            task = self.ALL_COIN_TASKS[i]
            if task == current_task_name:
                continue
            if self.config.is_task_enabled(task):
                task_display = self.TASK_NAMES.get(task, task)
                logger.info(f'尝试调用黄币补充任务: {task_display}')
                self.config.task_call(task)
                return
        
        # 如果没有之后的任务可用，尝试之前任务（跳过自身）
        for i in range(0, current_index):
            task = self.ALL_COIN_TASKS[i]
            if task == current_task_name:
                continue
            if self.config.is_task_enabled(task):
                task_display = self.TASK_NAMES.get(task, task)
                logger.info(f'尝试调用黄币补充任务: {task_display}')
                self.config.task_call(task)
                return
        
        # 如果所有任务都不可用，返回 CL1
        logger.warning('所有黄币补充任务都不可用，返回侵蚀1')
        self.config.task_call('OpsiHazard1Leveling')
        self.config.task_stop()
    
    def _finish_task_with_smart_scheduling(self, task_name, task_display_name=None, consider_reset_remain=True):
        """
        根据智能调度状态完成任务
        
        Args:
            task_name: 任务名称（如 'OpsiObscure'）
            task_display_name: 任务显示名称（如 '隐秘海域'）
            consider_reset_remain: 是否考虑大世界重置剩余时间
        
        Returns:
            bool: 是否已处理（True 表示已调用 task_stop）
        """
        if task_display_name is None:
            task_display_name = task_name
        
        smart_enabled = is_smart_scheduling_enabled(self.config)
        
        if smart_enabled:
            logger.info(f'{task_display_name}任务完成（智能调度已启用），禁用任务调度')
            self.config.cross_set(keys=f'{task_name}.Scheduler.Enable', value=False)
            self.config.task_stop()
        else:
            if consider_reset_remain and task_name in ('OpsiObscure', 'OpsiAbyssal'):
                try:
                    from module.config.utils import get_os_reset_remain
                    remain = get_os_reset_remain()
                    if remain == 0:
                        logger.info(f'{task_display_name}任务完成，距离大世界重置不足1天，延迟2.5小时后再运行')
                        self.config.task_delay(minute=150, server_update=True)
                    else:
                        logger.info(f'{task_display_name}任务完成，延迟到下次服务器刷新后再运行')
                        self.config.task_delay(server_update=True)
                except ImportError:
                    logger.info(f'{task_display_name}任务完成，延迟到下次服务器刷新后再运行')
                    self.config.task_delay(server_update=True)
            else:
                logger.info(f'{task_display_name}任务完成，延迟到下次服务器刷新后再运行')
                self.config.task_delay(server_update=True)
            self.config.task_stop()
        
        return True
    
    def _handle_no_content_and_try_other_tasks(self, task_display_name, log_message):
        """
        处理任务没有可执行内容的情况
        
        Args:
            task_display_name: 任务显示名称（如 "隐秘海域"）
            log_message: 没有内容时的日志消息
        
        Returns:
            bool: True 表示已处理（应提前返回），False 表示未处理
        """
        logger.info(f'{log_message}，准备结束当前任务')
        
        # 获取实际任务名称
        if hasattr(self.config, 'task') and hasattr(self.config.task, 'command'):
            task_name = self.config.task.command
        else:
            task_name = self.__class__.__name__
            if task_name == 'OperationSiren':
                for cls in self.__class__.__mro__:
                    if cls.__name__ in self.ALL_COIN_TASKS:
                        task_name = cls.__name__
                        break
        
        logger.info(f'处理任务: {task_name}')
        
        # 检查是否应该尝试其他任务
        should_try_other = False
        smart_enabled = is_smart_scheduling_enabled(self.config)
        if self.is_cl1_enabled and smart_enabled:
            yellow_coins = self.get_yellow_coins()
            cl1_preserve = self._get_smart_scheduling_operation_coins_preserve()
            if yellow_coins < cl1_preserve:
                should_try_other = True
                logger.info(f'黄币不足 ({yellow_coins} < {cl1_preserve})，尝试其他黄币补充任务')
        
        with self.config.multi_set():
            if smart_enabled:
                far_future = datetime.now() + timedelta(days=30)
                logger.info(f'智能调度已启用，禁用任务 {task_name} 并将下次运行时间延迟到 {far_future}')
                self.config.cross_set(keys=f'{task_name}.Scheduler.Enable', value=False)
                self.config.cross_set(keys=f'{task_name}.Scheduler.NextRun', value=far_future)
                
                if should_try_other:
                    self._try_other_coin_tasks(task_name)
                    self.config.cross_set(keys=f'{task_name}.Scheduler.Enable', value=False)
                    self.config.cross_set(keys=f'{task_name}.Scheduler.NextRun', value=far_future)
            else:
                logger.info(f'智能调度未启用，对任务 {task_name} 执行延迟而非关闭')
                try:
                    from module.config.utils import get_os_reset_remain
                except ImportError:
                    get_os_reset_remain = None
                
                if task_name in ('OpsiObscure', 'OpsiAbyssal') and get_os_reset_remain is not None:
                    remain = get_os_reset_remain()
                    if remain == 0:
                        logger.info(f'{task_name} 没有更多可执行内容，距离大世界重置不足1天，延迟2.5小时后再运行')
                        self.config.task_delay(minute=150, server_update=True)
                    else:
                        logger.info(f'{task_name} 没有更多可执行内容，延迟到下次服务器刷新后再运行')
                        self.config.task_delay(server_update=True)
                else:
                    logger.info(f'{task_name} 没有更多可执行内容，延迟到下次服务器刷新后再运行')
                    self.config.task_delay(server_update=True)
        
        self.config.task_stop()
        return True


class OpsiScheduling(CoinTaskMixin, OSMap):
    """
    智能调度任务主类
    
    负责协调大世界（Operation Siren）中的各项任务调度，
    包括侵蚀1练级、短猫相接、隐秘海域、深渊海域、塞壬要塞等。
    
    主要功能:
        1. 黄币管理 - 当黄币不足时自动切换到补充任务
        2. 行动力监控 - 监控行动力并发送阈值通知
        3. 任务协调 - 在不同任务之间智能切换
    """
    
    def run_smart_scheduling(self):
        """
        执行智能调度主逻辑
        
        此方法是智能调度任务的入口点，负责：
        1. 检查是否启用智能调度
        2. 根据黄币和行动力状态决定当前应该执行的任务
        3. 协调各任务之间的切换
        """
        logger.hr('Opsi Smart Scheduling', level=1)
        
        # 检查是否启用智能调度
        if not is_smart_scheduling_enabled(self.config):
            logger.info('智能调度未启用，跳过执行')
            return
        
        # 获取当前黄币数量
        yellow_coins = self.get_yellow_coins()
        
        # 获取黄币保留值（根据开关决定使用原配置还是智能调度配置）
        cl1_preserve = self._get_smart_scheduling_operation_coins_preserve()
        
        # 获取行动力
        self.action_point_enter()
        self.action_point_safe_get()
        self.action_point_quit()
        
        current_ap = self._action_point_total
        
        logger.info(f'【智能调度初始检查】黄币: {yellow_coins}, 保留值: {cl1_preserve}')
        logger.info(f'【智能调度初始检查】行动力: {current_ap}')
        
        # 检查是否需要执行黄币补充任务
        if yellow_coins < cl1_preserve:
            logger.info(f'黄币不足 ({yellow_coins} < {cl1_preserve})，需要执行黄币补充任务')
            
            # 获取短猫相接的行动力保留值
            meow_ap_preserve = self.config.cross_get(
                keys=self.CONFIG_PATH_MEOW_AP_PRESERVE
            ) or 1000
            
            if current_ap < meow_ap_preserve:
                # 行动力也不足，推迟任务
                logger.warning(f'行动力不足以执行短猫 ({current_ap} < {meow_ap_preserve})')
                self._notify_coins_ap_insufficient(yellow_coins, current_ap, cl1_preserve, meow_ap_preserve)
                
                logger.info('推迟智能调度任务1小时')
                self.config.task_delay(minute=60)
                self.config.task_stop()
                return
            
            # 行动力充足，切换到黄币补充任务
            self._switch_to_coin_task(yellow_coins, current_ap, cl1_preserve, meow_ap_preserve)
            return
        
        # 黄币充足，检查是否应该执行侵蚀1
        logger.info(f'黄币充足 ({yellow_coins} >= {cl1_preserve})，执行侵蚀1练级')
        
        # 获取侵蚀1的最低行动力保留值
        min_ap_reserve = self.config.cross_get(
            keys=self.CONFIG_PATH_CL1_MIN_AP_RESERVE
        ) or 200
        
        if current_ap < min_ap_reserve:
            logger.warning(f'行动力低于最低保留 ({current_ap} < {min_ap_reserve})')
            self._notify_ap_insufficient(current_ap, min_ap_reserve)
            
            logger.info('推迟智能调度任务1小时')
            self.config.task_delay(minute=60)
            self.config.task_stop()
            return
        
        # 一切条件满足，执行侵蚀1练级
        self._execute_hazard1_leveling(yellow_coins, current_ap)
    
    def _notify_coins_ap_insufficient(self, yellow_coins, current_ap, cl1_preserve, meow_ap_preserve):
        """
        发送黄币与行动力双重不足的通知
        """
        if not is_smart_scheduling_enabled(self.config):
            return
        
        if not self.config.OpsiGeneral_NotifyOpsiMail:
            return
        
        push_config = self.config.Error_OnePushConfig
        if not self._is_push_config_valid(push_config):
            logger.warning("推送配置未设置或 provider 为 null，跳过推送")
            return
        
        instance_name = getattr(self.config, 'config_name', 'Alas')
        formatted_title = f"[Alas <{instance_name}>] 智能调度 - 黄币与行动力双重不足"
        
        try:
            from module.notify import handle_notify as notify_handle_notify
            content = f"黄币 {yellow_coins} 低于保留值 {cl1_preserve}\n行动力 {current_ap} 不足 (需要 {meow_ap_preserve})\n推迟任务"
            success = notify_handle_notify(push_config, title=formatted_title, content=content)
            if success:
                logger.info(f"推送通知成功: {formatted_title}")
        except Exception as e:
            logger.error(f"推送通知异常: {e}")
    
    def _notify_ap_insufficient(self, current_ap, min_reserve):
        """
        发送行动力低于最低保留的通知
        """
        if not is_smart_scheduling_enabled(self.config):
            return
        
        if not self.config.OpsiGeneral_NotifyOpsiMail:
            return
        
        push_config = self.config.Error_OnePushConfig
        if not self._is_push_config_valid(push_config):
            logger.warning("推送配置未设置或 provider 为 null，跳过推送")
            return
        
        instance_name = getattr(self.config, 'config_name', 'Alas')
        formatted_title = f"[Alas <{instance_name}>] 智能调度 - 行动力不足"
        
        try:
            from module.notify import handle_notify as notify_handle_notify
            content = f"当前行动力 {current_ap} 低于最低保留 {min_reserve}，推迟任务"
            success = notify_handle_notify(push_config, title=formatted_title, content=content)
            if success:
                logger.info(f"推送通知成功: {formatted_title}")
        except Exception as e:
            logger.error(f"推送通知异常: {e}")
    
    def _switch_to_coin_task(self, yellow_coins, current_ap, cl1_preserve, meow_ap_preserve):
        """
        切换到黄币补充任务
        """
        task_names = {
            'OpsiMeowfficerFarming': '短猫相接',
            'OpsiObscure': '隐秘海域',
            'OpsiAbyssal': '深渊海域',
            'OpsiStronghold': '塞壬要塞'
        }
        
        # 获取智能调度中启用的任务列表
        all_coin_tasks = self._get_enabled_coin_tasks()
        
        if not all_coin_tasks:
            logger.warning('智能调度中没有启用任何黄币补充任务，默认启用短猫相接')
            all_coin_tasks = ['OpsiMeowfficerFarming']
        
        enabled_names = '、'.join([task_names.get(task, task) for task in all_coin_tasks])
        logger.info(f'【智能调度】启用的黄币补充任务: {enabled_names}')
        
        # 自动启用黄币补充任务的调度器
        enabled_tasks = []
        auto_enabled_tasks = []
        
        with self.config.multi_set():
            for task in all_coin_tasks:
                if self.config.is_task_enabled(task):
                    enabled_tasks.append(task)
                    logger.info(f'黄币补充任务已启用: {task_names.get(task, task)}')
                else:
                    logger.info(f'自动启用黄币补充任务: {task_names.get(task, task)}')
                    self.config.cross_set(keys=f'{task}.Scheduler.Enable', value=True)
                    auto_enabled_tasks.append(task)
        
        available_tasks = enabled_tasks + auto_enabled_tasks
        
        if auto_enabled_tasks:
            auto_enabled_names = '、'.join([task_names.get(task, task) for task in auto_enabled_tasks])
            logger.info(f'已自动启用以下黄币补充任务: {auto_enabled_names}')
        
        if not available_tasks:
            logger.error('无法启用任何黄币补充任务，这是一个错误状态')
            self.config.task_delay(minute=60)
            self.config.task_stop()
            return
        
        task_names_str = '、'.join([task_names.get(task, task) for task in available_tasks])
        self._notify_switch_to_coin_task(yellow_coins, current_ap, cl1_preserve, meow_ap_preserve, task_names_str)
        
        with self.config.multi_set():
            for task in available_tasks:
                self.config.task_call(task)
            
            cd = self.nearest_task_cooling_down
            if cd is not None:
                logger.info(f'有冷却任务 {cd.command}，延迟智能调度到 {cd.next_run}')
                self.config.task_delay(target=cd.next_run)
        
        self.config.task_stop()
    
    def _notify_switch_to_coin_task(self, yellow_coins, current_ap, cl1_preserve, meow_ap_preserve, task_names):
        """
        发送切换到黄币补充任务的通知
        """
        if not is_smart_scheduling_enabled(self.config):
            return
        
        if not self.config.OpsiGeneral_NotifyOpsiMail:
            return
        
        push_config = self.config.Error_OnePushConfig
        if not self._is_push_config_valid(push_config):
            logger.warning("推送配置未设置或 provider 为 null，跳过推送")
            return
        
        instance_name = getattr(self.config, 'config_name', 'Alas')
        formatted_title = f"[Alas <{instance_name}>] 智能调度 - 切换至黄币补充任务"
        
        try:
            from module.notify import handle_notify as notify_handle_notify
            content = (f"黄币 {yellow_coins} 低于保留值 {cl1_preserve}\n"
                      f"行动力: {current_ap} (需要 {meow_ap_preserve})\n"
                      f"切换至{task_names}获取黄币")
            success = notify_handle_notify(push_config, title=formatted_title, content=content)
            if success:
                logger.info(f"推送通知成功: {formatted_title}")
        except Exception as e:
            logger.error(f"推送通知异常: {e}")
    
    def _execute_hazard1_leveling(self, yellow_coins, current_ap):
        """
        执行侵蚀1练级任务
        """
        logger.info('切换到侵蚀1练级任务')
        
        with self.config.multi_set():
            # 禁用所有黄币补充任务
            for task in ['OpsiMeowfficerFarming', 'OpsiObscure', 'OpsiAbyssal', 'OpsiStronghold']:
                self.config.cross_set(keys=f'{task}.Scheduler.Enable', value=False)
            
            # 调用侵蚀1任务
            self.config.task_call('OpsiHazard1Leveling')
        
        self.config.task_stop()
    
    def notify_action_point_threshold(self, title, content):
        """
        发送行动力阈值变化通知
        
        Args:
            title (str): 通知标题
            content (str): 通知内容
        """
        if not is_smart_scheduling_enabled(self.config):
            return
        
        if not self.config.OpsiGeneral_NotifyOpsiMail:
            return
        
        push_config = self.config.Error_OnePushConfig
        if not self._is_push_config_valid(push_config):
            logger.warning("推送配置未设置或 provider 为 null，跳过推送")
            return
        
        instance_name = getattr(self.config, 'config_name', 'Alas')
        if title.startswith('[Alas]'):
            formatted_title = f"[Alas <{instance_name}>]{title[6:]}"
        else:
            formatted_title = f"[Alas <{instance_name}>] {title}"
        
        try:
            from module.notify import handle_notify as notify_handle_notify
            success = notify_handle_notify(push_config, title=formatted_title, content=content)
            if success:
                logger.info(f"推送通知成功: {formatted_title}")
            else:
                logger.warning(f"推送通知失败: {formatted_title}")
        except Exception as e:
            logger.error(f"推送通知异常: {e}")
