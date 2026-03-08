# 此文件用于统计舰船经验检测数据和战斗时间
# 包含每日经验效率统计，用于预估升级时间

from __future__ import annotations

import math
import time
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional, List

from module.os.ship_exp_data import LIST_SHIP_EXP
from module.logger import logger


class ShipExpStats:
    """
    舰船经验统计类
    - 记录每场战斗时间和经验
    - 统计每日效率 (经验/小时)
    - 保存舰船检测数据
    """
    
    # 每个位置的每场战斗经验值
    EXP_PER_BATTLE = {
        1: 431,  # 旗舰
        2: 288, 3: 288, 4: 288, 5: 288, 6: 288  # 其他位置
    }
    
    MAX_BATTLE_TIME_SAMPLES = 100  # 保留最近100场战斗时间样本
    MAX_DAILY_STATS_DAYS = 30      # 保留最近30天的统计
    
    def __init__(self, path: Optional[Path] = None, instance_name: Optional[str] = None):
        if path is None:
            project_root = Path(__file__).resolve().parents[2]
            instance_dir = instance_name or "default"
            self._path = project_root / "log" / "cl1" / instance_dir / "ship_exp_data.json"
        else:
            self._path = Path(path)
        self._instance_name = instance_name or "default"
        self.data = self._load()
        
        # 当前战斗的开始时间
        self._battle_start_time: Optional[float] = None
    
    def _load(self) -> Dict[str, Any]:
        """加载数据文件"""
        if not self._path.exists():
            return {}
        try:
            text = self._path.read_text(encoding='utf-8')
            data = json.loads(text)
            if isinstance(data, dict):
                return data
            return {}
        except Exception as e:
            logger.warning(f'Failed to load ship exp data: {e}')
            return {}
    
    def _save(self) -> None:
        """保存数据文件"""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            logger.warning(f'Failed to save ship exp data: {e}')
    
    # ========== 战斗时间记录 ==========
    
    def on_battle_start(self) -> None:
        """战斗开始时调用（侵蚀1 / 短猫等统一入口）"""
        self._battle_start_time = time.time()
    
    def on_battle_end(self, fleet_index: int = 1, source: str = "cl1") -> Optional[float]:
        """
        战斗结束时调用
        
        Args:
            fleet_index: 舰队索引 (1-6), 用于确定经验值
            source: 战斗来源:
                - "cl1": 侵蚀1练级
                - "meow": 短猫
                - 其他值默认按 "cl1" 处理
        
        Returns:
            本场战斗耗时(秒), 如果未记录开始时间则返回None
        """
        if self._battle_start_time is None:
            return None
        
        duration = time.time() - self._battle_start_time
        self._battle_start_time = None
        
        # 过滤异常值 (太短或太长的战斗)
        if duration < 1 or duration > 300:
            logger.debug(f'Battle duration {duration:.1f}s out of range, not recorded')
            return duration
        
        # 记录战斗时间（根据来源分别统计）
        self._record_battle_time(duration, source=source)
        
        # 计算本场经验 (使用平均值，因为每个位置经验不同)
        # 旗舰 431 + 其他位置 288*5 = 1871, 平均 312
        avg_exp = 312
        
        # 更新每日统计
        self._update_daily_stats(exp_gained=avg_exp, battle_duration=duration)
        
        logger.info(f'Battle recorded: {duration:.1f}s, exp: {avg_exp}')
        return duration
    
    def _record_battle_time(self, duration: float, source: str = "cl1") -> None:
        """记录单场战斗时间到样本
        
        Args:
            duration: 本场战斗时长（秒）
            source: 战斗来源 ("cl1" / "meow")
        """
        # 不同来源使用不同的键，避免侵蚀1与短猫混合统计
        if source == "meow":
            key = 'meow_battle_times'
            default_avg = 52.0  # 默认值，后续会被真实样本覆盖
        else:
            key = 'battle_times'
            default_avg = 52.0
        
        if key not in self.data:
            self.data[key] = {'samples': [], 'average': default_avg}
        
        samples = self.data[key]['samples']
        samples.append(round(duration, 2))
        
        # 只保留最近N个样本
        if len(samples) > self.MAX_BATTLE_TIME_SAMPLES:
            self.data[key]['samples'] = samples[-self.MAX_BATTLE_TIME_SAMPLES:]
            samples = self.data[key]['samples']
        
        # 更新平均值
        if samples:
            self.data[key]['average'] = round(sum(samples) / len(samples), 2)
        
        self._save()
    
    def record_round_time(self, round_duration: float) -> None:
        """记录单轮侵蚀1时间到样本"""
        if 'round_times' not in self.data:
            self.data['round_times'] = {'samples': [], 'average': 120.0}
        
        samples = self.data['round_times']['samples']
        samples.append(round(round_duration, 2))
        
        # 只保留最近100个样本
        if len(samples) > 100:
            self.data['round_times']['samples'] = samples[-100:]
            samples = self.data['round_times']['samples']
        
        # 更新平均值
        if samples:
            self.data['round_times']['average'] = round(sum(samples) / len(samples), 2)
        
        self._save()
    
    # ========== 每日经验效率统计 ==========
    
    def _update_daily_stats(self, exp_gained: int, battle_duration: float) -> None:
        """
        更新每日统计数据
        每场战斗结束后调用，累加到当天的统计
        """
        today = date.today().isoformat()  # "2026-01-01"
        
        if 'daily_stats' not in self.data:
            self.data['daily_stats'] = {}
        
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'total_run_time': 0.0,
                'total_exp_gained': 0,
                'battle_count': 0,
                'exp_per_hour': 0.0
            }
        
        stats = self.data['daily_stats'][today]
        stats['total_run_time'] += battle_duration
        stats['total_exp_gained'] += exp_gained
        stats['battle_count'] += 1
        
        # 计算每小时经验效率
        hours = stats['total_run_time'] / 3600
        if hours > 0:
            stats['exp_per_hour'] = round(stats['total_exp_gained'] / hours, 2)
        
        # 清理旧数据
        self._cleanup_old_daily_stats()
        
        self._save()
    
    def _cleanup_old_daily_stats(self) -> None:
        """清理超过30天的旧统计数据"""
        if 'daily_stats' not in self.data:
            return
        
        dates = sorted(self.data['daily_stats'].keys(), reverse=True)
        if len(dates) > self.MAX_DAILY_STATS_DAYS:
            for old_date in dates[self.MAX_DAILY_STATS_DAYS:]:
                del self.data['daily_stats'][old_date]
    
    def get_average_battle_time(self) -> float:
        """获取平均每场战斗时间(秒)"""
        return self.data.get('battle_times', {}).get('average', 52.0)
    
    def get_average_meow_battle_time(self) -> float:
        """获取短猫平均每场战斗时间(秒)"""
        return self.data.get('meow_battle_times', {}).get('average', self.get_average_battle_time())
    
    def get_average_round_time(self) -> float:
        """获取平均每轮侵蚀1时间(秒)"""
        if 'round_times' in self.data and self.data['round_times'].get('samples'):
            return self.data['round_times']['average']
        return self.get_average_battle_time() * 2 + 15
    
    def get_exp_per_hour(self) -> float:
        """
        获取经验效率 (经验/小时)
        优先使用今日数据，否则计算最近7天平均
        """
        if 'daily_stats' not in self.data or not self.data['daily_stats']:
            # 无统计数据，使用理论值估算
            avg_battle_time = self.get_average_battle_time()
            avg_exp_per_battle = 312  # 平均每场经验
            if avg_battle_time > 0:
                battles_per_hour = 3600 / avg_battle_time
                return battles_per_hour * avg_exp_per_battle
            return 22000.0  # 默认值
        
        today = date.today().isoformat()
        
        # 优先使用今日数据 (如果今日战斗超过10场)
        if today in self.data['daily_stats']:
            today_stats = self.data['daily_stats'][today]
            if today_stats.get('battle_count', 0) >= 10:
                exp_per_hour = today_stats.get('exp_per_hour', 0)
                if exp_per_hour > 0:
                    return exp_per_hour
        
        # 计算最近7天的平均效率
        dates = sorted(self.data['daily_stats'].keys(), reverse=True)[:7]
        total_exp = 0
        total_time = 0.0
        for d in dates:
            stats = self.data['daily_stats'][d]
            total_exp += stats.get('total_exp_gained', 0)
            total_time += stats.get('total_run_time', 0)
        
        if total_time > 0:
            hours = total_time / 3600
            return round(total_exp / hours, 2)
        
        return 22000.0  # 默认值
    
    def get_today_stats(self) -> Optional[Dict[str, Any]]:
        """获取今日统计数据"""
        today = date.today().isoformat()
        if 'daily_stats' not in self.data:
            return None
        return self.data['daily_stats'].get(today)
    
    # ========== 舰船数据保存与进度计算 ==========
    
    def save_ship_data(
        self,
        ships: List[Dict[str, Any]],
        target_level: int,
        fleet_index: int,
        battle_count_at_check: int
    ) -> None:
        """
        保存舰船经验检测数据
        
        Args:
            ships: 舰船数据列表, 每项包含 position, level, current_exp, total_exp
            target_level: 目标等级
            fleet_index: 舰队索引
            battle_count_at_check: 检测时的战斗场次
        """
        self.data['last_check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.data['target_level'] = target_level
        self.data['fleet_index'] = fleet_index
        self.data['battle_count_at_check'] = battle_count_at_check
        self.data['ships'] = ships
        self._save()
        logger.info(f'Ship exp data saved: {len(ships)} ships, target level {target_level}')
    
    def calculate_progress(
        self,
        ship: Dict[str, Any],
        target_level: int,
        current_battle_count: int
    ) -> Dict[str, Any]:
        """
        计算单艘舰船的升级进度
        
        Args:
            ship: 舰船数据 (position, level, current_exp, total_exp)
            target_level: 目标等级
            current_battle_count: 当前战斗场次
        
        Returns:
            进度数据字典
        """
        # 处理等级边界 (1-125)
        if target_level < 1:
            target_level = 1
        elif target_level > 125:
            target_level = 125
        
        target_exp = LIST_SHIP_EXP[target_level - 1]
        current_total_exp = ship.get('total_exp', 0)
        exp_needed = max(0, target_exp - current_total_exp)
        
        # 计算还需出击次数
        position = ship.get('position', 1)
        exp_per_battle = self.EXP_PER_BATTLE.get(position, 288)
        battles_needed = math.ceil(exp_needed / exp_per_battle) if exp_needed > 0 else 0
        
        # 计算已战斗场次 (自上次检测以来)
        battle_count_at_check = self.data.get('battle_count_at_check', 0)
        battles_done = max(0, current_battle_count - battle_count_at_check)
        
        # 计算预估时间 (使用经验效率)
        exp_per_hour = self.get_exp_per_hour()
        if exp_per_hour > 0 and exp_needed > 0:
            hours_needed = exp_needed / exp_per_hour
            time_seconds = hours_needed * 3600
        else:
            time_seconds = 0
        
        return {
            'position': position,
            'level': ship.get('level', 0),
            'current_exp': ship.get('current_exp', 0),
            'total_exp': current_total_exp,
            'target_exp': target_exp,
            'battles_done': battles_done,
            'exp_needed': exp_needed,
            'battles_needed': battles_needed,
            'time_needed': self._format_time(time_seconds)
        }
    
    def get_all_progress(self, current_battle_count: int) -> List[Dict[str, Any]]:
        """
        获取所有舰船的升级进度
        
        Args:
            current_battle_count: 当前战斗场次
        
        Returns:
            所有舰船的进度数据列表
        """
        ships = self.data.get('ships', [])
        target_level = self.data.get('target_level', 125)
        
        return [
            self.calculate_progress(ship, target_level, current_battle_count)
            for ship in ships
        ]
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间显示"""
        if seconds <= 0:
            return "0分钟"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{minutes}分钟"


# ========== 单例模式和便捷函数 ==========

_stats_instances: Dict[str, ShipExpStats] = {}


def get_ship_exp_stats(instance_name: Optional[str] = None) -> ShipExpStats:
    """获取 ShipExpStats 实例"""
    global _stats_instances
    key = instance_name or "default"
    if key not in _stats_instances:
        _stats_instances[key] = ShipExpStats(instance_name=instance_name)
    else:
        # 刷新数据
        _stats_instances[key].data = _stats_instances[key]._load()
    return _stats_instances[key]


def save_ship_exp_data(
    ships: List[Dict[str, Any]],
    target_level: int,
    fleet_index: int,
    battle_count_at_check: int,
    instance_name: Optional[str] = None
) -> None:
    """便捷函数: 保存舰船经验检测数据"""
    get_ship_exp_stats(instance_name=instance_name).save_ship_data(
        ships=ships,
        target_level=target_level,
        fleet_index=fleet_index,
        battle_count_at_check=battle_count_at_check
    )


__all__ = [
    'ShipExpStats',
    'get_ship_exp_stats',
    'save_ship_exp_data',
]
