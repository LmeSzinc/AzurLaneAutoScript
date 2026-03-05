"""
OpsiDailyDelay - 大世界任务延后模块（延后cl1和短猫连接任务）

在每日0点服务器重启前的可配置时间段内，将cl1和短猫连接任务自动延后至次日0点重启完成后再执行。

功能说明:
    1. 定时触发 - 在每日0点前X分钟自动触发（X可配置，范围1-60分钟，默认5分钟）
    2. 任务过滤 - 只延后cl1（OpsiHazard1Leveling）和短猫（OpsiMeowfficerFarming）任务
    3. 任务延后 - 将cl1和短猫连接任务延后到0点后执行
    4. 状态暂存 - 保存任务状态，支持断点续传

任务层级:
    - OpsiDailyDelay 是和 OpsiCrossMonth 相同层级的调度器
    - 它负责在每日0点前延后cl1和短猫连接任务，避免任务在服务器重启时中断

配置项:
    - Scheduler.Enable: 任务启用开关（启用此任务即启用cl1和短猫连接任务延后功能）
    - OpsiDailyDelay.TriggerMinutesBeforeReset: 提前触发时间（分钟，默认5，范围1-60）

此模块包含:
    - OpsiDailyDelay: cl1和短猫连接任务延后主类
"""
import json
import os
from datetime import datetime, timedelta

from module.config.utils import get_server_next_update
from module.exception import ScriptError
from module.os.map import OSMap


class OpsiDailyDelay(OSMap):
    """
    cl1和短猫连接任务延后主类
    
    功能:
    - 在每日0点前X分钟自动触发
    - 延后cl1（OpsiHazard1Leveling）和短猫（OpsiMeowfficerFarming）连接任务到0点后
    - 保存任务状态，支持断点续传
    """
    
    # 需要延后的任务列表（只延后cl1和短猫）
    DELAYED_TASKS = [
        'OpsiHazard1Leveling',  # cl1（侵蚀一练级）
        'OpsiMeowfficerFarming',  # 短猫（短猫相接）
    ]
    
    # 任务状态文件路径
    STATUS_FILE = './log/opsi_daily_delay_status.json'
    
    # 配置路径常量
    CONFIG_PATH_TRIGGER_MINUTES = 'OpsiDailyDelay.OpsiDailyDelay.TriggerMinutesBeforeReset'
    
    # ==================== 时间计算相关方法 ====================
    
    def _calculate_trigger_time(self, minutes_before_reset):
        """
        计算触发时间（0点前X分钟）
        
        Args:
            minutes_before_reset: 提前分钟数
            
        Returns:
            datetime: 触发时间（本地时间）
        """
        # 获取下次0点时间（服务器时间）
        next_reset = get_server_next_update("00:00")
        
        # 计算触发时间（0点前X分钟）
        trigger_time = next_reset - timedelta(minutes=minutes_before_reset)
        
        return trigger_time
    
    def _calculate_recovery_time(self):
        """
        计算恢复时间（0点后）
        
        Returns:
            datetime: 恢复时间（本地时间）
        """
        # 获取下次0点时间（服务器时间）
        next_reset = get_server_next_update("00:00")
        
        # 恢复时间为0点后5分钟
        recovery_time = next_reset + timedelta(minutes=5)
        
        return recovery_time
    
    # ==================== 任务过滤相关方法 ====================
    
    def _should_delay_task(self, task_name):
        """
        判断任务是否应该被延后
        
        只延后cl1（OpsiHazard1Leveling）和短猫（OpsiMeowfficerFarming）连接任务
        
        Args:
            task_name: 任务名称
            
        Returns:
            bool: True表示应该延后，False表示不应该延后
        """
        # 只延后cl1和短猫任务
        if task_name not in self.DELAYED_TASKS:
            return False
        
        return True
    
    # ==================== 任务状态管理相关方法 ====================
    
    def _save_task_status(self, task_name, original_next_run, delayed_next_run):
        """
        保存cl1或短猫连接任务状态
        
        Args:
            task_name: 任务名称（cl1或短猫）
            original_next_run: 原始NextRun时间
            delayed_next_run: 延后后的NextRun时间
        """
        # 读取现有状态
        status = {}
        if os.path.exists(self.STATUS_FILE):
            try:
                with open(self.STATUS_FILE, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            except Exception as e:
                pass
        
        # 保存任务状态
        status[task_name] = {
            'original_next_run': original_next_run.strftime('%Y-%m-%d %H:%M:%S'),
            'delayed_next_run': delayed_next_run.strftime('%Y-%m-%d %H:%M:%S'),
            'delayed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 写入文件
        try:
            with open(self.STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass
    
    def _load_task_status(self, task_name):
        """
        加载cl1或短猫连接任务状态
        
        Args:
            task_name: 任务名称（cl1或短猫）
            
        Returns:
            dict: 任务状态，如果不存在则返回None
        """
        # 检查文件是否存在
        if not os.path.exists(self.STATUS_FILE):
            return None
        
        # 读取状态
        try:
            with open(self.STATUS_FILE, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return status.get(task_name)
        except Exception as e:
            return None
    
    def _clear_task_status(self, task_name=None):
        """
        清除任务状态
        
        Args:
            task_name: 任务名称，如果为None则清除所有状态
        """
        # 检查文件是否存在
        if not os.path.exists(self.STATUS_FILE):
            return
        
        if task_name is None:
            # 清除所有状态
            try:
                os.remove(self.STATUS_FILE)
            except Exception as e:
                pass
        else:
            # 清除指定任务状态
            try:
                with open(self.STATUS_FILE, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                
                if task_name in status:
                    pass
                
                with open(self.STATUS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(status, f, ensure_ascii=False, indent=2)
            except Exception as e:
                pass
    
    # ==================== 任务延后相关方法 ====================
    
    def _delay_task(self, task_name, delay_to):
        """
        延后cl1或短猫连接任务到指定时间
        
        Args:
            task_name: 任务名称（cl1或短猫）
            delay_to: 延后到的时间（datetime对象）
            
        Returns:
            bool: 是否成功延后
        """
        try:
            # 获取任务原始NextRun时间
            original_next_run = self.config.cross_get(keys=f'{task_name}.Scheduler.NextRun')
            
            if not isinstance(original_next_run, datetime):
                return False
            
            # 保存任务状态
            self._save_task_status(task_name, original_next_run, delay_to)
            
            # 设置延后时间
            self.config.cross_set(keys=f'{task_name}.Scheduler.NextRun', value=delay_to)
            
            return True
        except Exception as e:
            return False
    
    def _delay_all_pending_tasks(self, delay_to):
        """
        延后所有待执行的cl1和短猫连接任务
        
        Args:
            delay_to: 延后到的时间（datetime对象）
            
        Returns:
            int: 成功延后的任务数量
        """
        # 获取所有待执行任务
        pending_tasks = self.config.pending_task
        waiting_tasks = self.config.waiting_task
        
        # 合并所有任务
        all_tasks = pending_tasks + waiting_tasks
        
        if not all_tasks:
            return 0
        
        # 延后cl1和短猫连接任务
        delayed_count = 0
        for task in all_tasks:
            task_name = task.command
            
            # 检查是否应该延后
            if self._should_delay_task(task_name):
                if self._delay_task(task_name, delay_to):
                    delayed_count +=1
        
        return delayed_count
    
    # ==================== 任务恢复相关方法 ====================
    
    def _restore_task(self, task_name):
        """
        恢复cl1或短猫连接任务到原始时间
        
        Args:
            task_name: 任务名称（cl1或短猫）
            
        Returns:
            bool: 是否成功恢复
        """
        try:
            # 加载任务状态
            status = self._load_task_status(task_name)
            
            if not status:
                return False
            
            # 解析原始时间
            original_next_run = datetime.strptime(status['original_next_run'], '%Y-%m-%d %H:%M:%S')
            
            # 恢复原始时间
            self.config.cross_set(keys=f'{task_name}.Scheduler.NextRun', value=original_next_run)
            
            # 清除任务状态
            self._clear_task_status(task_name)
            
            return True
        except Exception as e:
            return False
    
    def _restore_all_delayed_tasks(self):
        """
        恢复所有延后的cl1和短猫连接任务
        
        Returns:
            int: 成功恢复的任务数量
        """
        # 检查状态文件是否存在
        if not os.path.exists(self.STATUS_FILE):
            return 0
        
        # 读取所有任务状态
        try:
            with open(self.STATUS_FILE, 'r', encoding='utf-8') as f:
                status = json.load(f)
        except Exception as e:
            return 0
        
        if not status:
            return 0
        
        # 恢复所有任务
        restored_count = 0
        for task_name in list(status.keys()):
            if self._restore_task(task_name):
                restored_count +=1
        
        return restored_count
    
    # ==================== 配置验证相关方法 ====================
    
    def _validate_trigger_minutes(self, minutes):
        """
        验证提前触发时间是否有效
        
        Args:
            minutes: 提前分钟数
            
        Returns:
            bool: 是否有效
        """
        if not isinstance(minutes, int):
            return False
        
        if minutes < 1 or minutes > 60:
            return False
        
        return True
    
    # ==================== 主任务方法 ====================
    
    def opsi_daily_delay_end(self):
        """
        任务结束处理
        
        1. 返回大世界港区（如NY港区、利维浦港区等）
        2. 延后cl1和短猫连接任务到0点后
        3. 延迟到下次触发时间（0点前X分钟）
        4. 停止任务（不返回主界面）
        """
        # 返回大世界港区
        self._return_to_port()
        
        # 延后cl1和短猫连接任务
        self._delay_cl1_and_short_cat()
        
        # 获取提前触发时间
        trigger_minutes = self.config.cross_get(keys=self.CONFIG_PATH_TRIGGER_MINUTES)
        
        # 验证配置
        if not self._validate_trigger_minutes(trigger_minutes):
            trigger_minutes = 5
        
        # 计算下次触发时间（下一天的0点前X分钟）
        next_reset = get_server_next_update("00:00")
        # 如果当前时间已经过了0点前X分钟，则计算下一天的触发时间
        now = datetime.now()
        next_trigger_time = next_reset - timedelta(minutes=trigger_minutes)
        
        # 如果触发时间已经过去，则跳到下一天
        if next_trigger_time < now:
            # 获取下一天的0点时间
            next_reset = next_reset + timedelta(days=1)
            next_trigger_time = next_reset - timedelta(minutes=trigger_minutes)
        
        # 延迟到下次触发时间
        self.config.task_delay(target=next_trigger_time)
        
        # 停止任务（不返回主界面）
        self.config.task_stop()
    
    def _delay_cl1_and_short_cat(self):
        """
        延后cl1和短猫连接任务到0点后
        
        将cl1（OpsiHazard1Leveling）和短猫（OpsiMeowfficerFarming）连接任务延后到0点后5分钟
        """
        try:
            # 获取下次0点时间
            next_reset = get_server_next_update("00:00")
            now = datetime.now()

            # 核心修复：只有在距离0点重置还有 1 小时以内时，才执行延后动作
            # 避免在0点重置后的收尾流程中，误将任务再次推后到明天的0点
            if (next_reset - now) > timedelta(minutes=65):
                return
            
            # 计算延后时间（0点后5分钟）
            delay_time = next_reset + timedelta(minutes=5)
            
            # 延后cl1任务
            if 'OpsiHazard1Leveling' in self.DELAYED_TASKS:
                self._delay_task('OpsiHazard1Leveling', delay_time)
            
            # 延后短猫任务
            if 'OpsiMeowfficerFarming' in self.DELAYED_TASKS:
                self._delay_task('OpsiMeowfficerFarming', delay_time)
        except Exception as e:
            pass
    
    def _return_to_port(self):
        """
        返回大世界港区
        
        如果当前不在港区，则导航到最近的港区（如NY港区、利维浦港区等）
        """
        try:
            # 检查是否在大世界地图中
            if not self.is_in_map() and not self.is_in_globe():
                return
            
            # 获取当前区域
            current_zone = self.zone
            
            # 检查是否已经在港区
            if current_zone.is_azur_port:
                return
            
            # 获取最近的港区
            nearest_port = self.zone_nearest_azur_port(current_zone)
            
            # 导航到港区
            self.globe_goto(nearest_port)
            
            # 进入港区
            self.port_enter()
            
            # 退出港区（回到大世界地图）
            self.port_quit()
        except Exception as e:
            pass
    
    def opsi_daily_delay(self):
        """
        cl1和短猫连接任务延后主任务
        
        执行流程:
        1. 计算触发时间
        2. 检查是否在触发时间窗口内
        3. 延后cl1和短猫连接任务到0点后
        4. 等待到0点
        5. 恢复所有延后的任务
        6. 任务结束（不返回主界面）
        """
        # 获取提前触发时间
        trigger_minutes = self.config.cross_get(keys=self.CONFIG_PATH_TRIGGER_MINUTES)
        
        # 验证配置
        if not self._validate_trigger_minutes(trigger_minutes):
            trigger_minutes = 5
        
        # 计算触发时间和0点时间
        next_reset = get_server_next_update("00:00")
        trigger_time = next_reset - timedelta(minutes=trigger_minutes)
        now = datetime.now()
        
        # 检查开始时间
        if next_reset < now:
            raise ScriptError(f'Invalid OpsiNextReset: {next_reset} < {now}')
        if next_reset - now > timedelta(days=3):
            self.opsi_daily_delay_end()
            return
        if next_reset - now > timedelta(minutes=trigger_minutes):
            self.opsi_daily_delay_end()
            return
        
        # Now we are X minutes before OpSi reset
        
        # 计算恢复时间（0点后5分钟）
        recovery_time = next_reset + timedelta(minutes=5)
        
        # 延后cl1和短猫连接任务
        delayed_count = self._delay_all_pending_tasks(recovery_time)
        
        while True:
            now = datetime.now()
            remain = (next_reset - now).total_seconds()
            if remain <= 0:
                break
            else:
                self.device.sleep(min(remain, 60))
                continue
        
        # 等待5分钟，确保服务器重启完成
        self.device.sleep(300)
        
        # 恢复所有延后的任务
        restored_count = self._restore_all_delayed_tasks()
        
        # 任务结束
        self.opsi_daily_delay_end()
