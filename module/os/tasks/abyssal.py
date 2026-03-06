from datetime import datetime, timedelta

from module.exception import RequestHumanTakeover
from module.logger import logger
from module.os.map import OSMap
from module.os.tasks.scheduling import CoinTaskMixin


class OpsiAbyssal(CoinTaskMixin, OSMap):
    
    def _is_submarine_task(self, task_name):
        """
        Check if a task uses submarine.
        
        Args:
            task_name (str): Task name to check.
            
        Returns:
            bool: True if task uses submarine.
        """
        # Check OpsiFleet.Submarine
        submarine_enabled = self.config.cross_get(f"{task_name}.OpsiFleet.Submarine", default=False)
        if submarine_enabled:
            return True
        
        # Check OpsiFleetFilter.Filter
        filter_str = self.config.cross_get(f"{task_name}.OpsiFleetFilter.Filter", default="")
        if filter_str and "submarine" in filter_str.lower():
            return True
        
        return False
    
    def _check_submarine_cooldown(self):
        """
        Check if submarine is on cooldown.
        
        Returns:
            tuple: (is_cooldown, cooldown_end_time)
                - is_cooldown: True if submarine is on cooldown
                - cooldown_end_time: datetime when cooldown ends, None if not on cooldown
        """
        now = datetime.now()
        
        # Tasks that can potentially use submarines
        submarine_tasks = ['OpsiExplore', 'OpsiDaily', 'OpsiObscure', 'OpsiAbyssal', 
                          'OpsiArchive', 'OpsiStronghold', 'OpsiMeowfficerFarming', 'OpsiMonthBoss']
        
        # Get all tasks
        all_tasks = self.config.pending_task + self.config.waiting_task
        task_map = {task.command: task for task in all_tasks}
        
        for task_name in submarine_tasks:
            task = task_map.get(task_name)
            if not task or not task.enable:
                continue
            
            # Check if task uses submarine
            if not self._is_submarine_task(task_name):
                continue
            
            # Task has submarine call enabled, check if it's on cooldown
            if task.next_run and task.next_run > now:
                time_diff = task.next_run - now
                if timedelta(0) < time_diff <= timedelta(minutes=60):
                    logger.info(f'检测到潜艇冷却：任务 {task_name} 的下次运行时间为 {task.next_run}')
                    return True, task.next_run
        
        logger.info('潜艇冷却检查通过，未检测到潜艇冷却')
        return False, None
    
    def _delay_until_submarine_cooldown_end(self, cooldown_end_time):
        """
        Delay abyssal task until submarine cooldown ends.
        
        Args:
            cooldown_end_time: datetime when submarine cooldown ends
        """
        logger.hr('Submarine cooldown detected', level=1)
        logger.info(f'潜艇冷却结束时间：{cooldown_end_time}')
        logger.info('延时深渊任务到潜艇冷却结束')
        
        # Calculate delay duration
        now = datetime.now()
        delay_seconds = int((cooldown_end_time - now).total_seconds())
        delay_minutes = delay_seconds // 60
        
        if delay_minutes <= 0:
            delay_minutes = 1
        
        logger.info(f'延时 {delay_minutes} 分钟到潜艇冷却结束')
        
        # Delay task
        self.config.task_delay(minute=delay_minutes)
        self.config.task_stop()
    
    def delay_abyssal(self, result=True):
        """
        Args:
            result(bool): If still have abyssal loggers.
        """
        # 无论是否有更多深渊记录器，都处理任务完成
        # 根据是否启用智能调度选择关闭或推迟任务
        self._finish_task_with_smart_scheduling('OpsiAbyssal', '深渊海域', consider_reset_remain=True)

    def clear_abyssal(self):
        """
        Get one abyssal logger in storage,
        attack abyssal boss,
        repair fleets in port.

        Raises:
            ActionPointLimit:
            TaskEnd: If no more abyssal loggers.
            RequestHumanTakeover: If unable to clear boss, fleets exhausted.
        """
        logger.hr('OS clear abyssal', level=1)
        self.cl1_ap_preserve()
        
        # ===== 检查潜艇冷却 =====
        # 在使用深渊记录器前检查潜艇冷却，如果潜艇在冷却中，延时到冷却结束
        is_cooldown, cooldown_end_time = self._check_submarine_cooldown()
        if is_cooldown:
            self._delay_until_submarine_cooldown_end(cooldown_end_time)
            return

        with self.config.temporary(STORY_ALLOW_SKIP=False):
            result = self.storage_get_next_item('ABYSSAL', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            # No abyssal loggers - handle and try other tasks if needed
            if self._handle_no_content_and_try_other_tasks('深渊海域', '深渊海域没有可执行内容'):
                return

        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0
        )
        self.zone_init()
        
        # ===== 进入深渊地图后禁止任务切换 =====
        # 在进入深渊地图后立即禁止所有任务切换，直到打完 boss
        logger.info('进入深渊地图，禁止所有任务切换')
        with self.config.temporary(_disable_task_switch=True):
            # ===== 禁止退出深渊地图 =====
            # 在打完 boss 前禁止退出深渊地图
            logger.info('打完 boss 前禁止退出深渊地图')
            
            result = self.run_abyssal()
            if not result:
                raise RequestHumanTakeover

            self.handle_fleet_repair_by_config(revert=False)

        # 不在这里预取/结算下一张深渊坐标，避免在后续检查失败时浪费坐标。
        self.delay_abyssal(result=True)

    def os_abyssal(self):
        # ===== 任务开始前黄币检查 =====
        # 如果启用了CL1且黄币充足，直接返回CL1，不执行深渊海域
        if self.is_cl1_enabled:
            return_threshold, cl1_preserve = self._get_operation_coins_return_threshold()
            if return_threshold is None:
                logger.info('OperationCoinsReturnThreshold 为 0，禁用黄币检查，仅使用行动力阈值控制')
            elif self._check_yellow_coins_and_return_to_cl1("任务开始前", "深渊海域"):
                return
        
        while True:
            self.clear_abyssal()
            # ===== 循环中黄币充足检查 =====
            # 在每次循环后检查黄币是否充足，如果充足则返回侵蚀1
            if self.is_cl1_enabled:
                if self._check_yellow_coins_and_return_to_cl1("循环中", "深渊海域"):
                    return
            self.config.check_task_switch()
