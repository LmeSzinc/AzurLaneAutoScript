# -*- coding: utf-8 -*-
"""
CL1 数据自动提交模块
负责收集侵蚀1统计数据并定时提交到云端API
"""
from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import requests

from module.base.device_id import get_device_id
from module.base.api_client import ApiClient
from module.logger import logger
from module.statistics.cl1_database import db as cl1_db


class Cl1DataSubmitter:
    """CL1数据提交器"""
    
    def __init__(self, instance_name: str | None = None):
        """
        初始化数据提交器
        
        Args:
            instance_name: Alas实例名称
        """
        self._device_id: Optional[str] = None
        self._last_submit_time: float = 0
        self._submit_interval: int = 600  # 10分钟
        
        # 获取项目根目录
        self.project_root = Path(__file__).resolve().parents[2]
        self._instance_name = instance_name or 'default'
        
        # 自动执行迁移
        old_dir = self.project_root / 'log' / 'cl1' / self._instance_name
        old_file = old_dir / 'cl1_monthly.json'
        if old_file.exists():
            cl1_db.migrate_from_json(old_file, self._instance_name)
    
    @property
    def device_id(self) -> str:
        """获取设备ID"""
        return get_device_id()
    
    def collect_data(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        收集指定月份的CL1统计数据
        
        Args:
            year: 年份 (默认当前年份)
            month: 月份 (默认当前月份)
        
        Returns:
            包含统计数据的字典
        """
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        month_key = f"{year:04d}-{month:02d}"
        
        # 从数据库读取加密存储的统计数据
        data = cl1_db.get_stats(self._instance_name, month_key)
        
        return {
            'month': month_key,
            'battle_count': int(data.get('battle_count', 0)),
            'akashi_encounters': int(data.get('akashi_encounters', 0)),
            'akashi_ap': int(data.get('akashi_ap', 0)),
        }
    
    def _empty_data(self, month_key: str) -> Dict[str, Any]:
        """返回空数据"""
        return {
            'month': month_key,
            'battle_count': 0,
            'akashi_encounters': 0,
            'akashi_ap': 0,
        }
    
    def calculate_metrics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算各项指标
        
        Args:
            raw_data: 原始统计数据
        
        Returns:
            包含计算后指标的完整数据
        """
        battle_count = raw_data['battle_count']
        akashi_encounters = raw_data['akashi_encounters']
        akashi_ap = raw_data['akashi_ap']
        
        # 计算战斗轮次 (每2次战斗为1轮)
        battle_rounds = battle_count // 2
        
        # 计算出击消耗 (每轮消耗120行动力)
        sortie_cost = battle_rounds * 120
        
        # 计算明石遇见概率
        if battle_rounds > 0:
            akashi_probability = round(akashi_encounters / battle_rounds, 4)
        else:
            akashi_probability = 0.0
        
        # 计算平均体力 (每次从明石处获得的平均行动力)
        if akashi_encounters > 0:
            average_stamina = round(akashi_ap / akashi_encounters, 2)
        else:
            average_stamina = 0.0
        
        # 净赚体力 = 从明石获得的总行动力
        net_stamina_gain = akashi_ap
        
        # 生成匿名 instance_id（使用 device_id + instance_name 的哈希值）
        instance_hash = hashlib.md5(f"{self.device_id}_{self._instance_name}".encode()).hexdigest()[:16]
        
        return {
            'device_id': self.device_id,
            'instance_id': instance_hash,
            'month': raw_data['month'],
            'battle_count': battle_count,
            'battle_rounds': battle_rounds,
            'sortie_cost': sortie_cost,
            'akashi_encounters': akashi_encounters,
            'akashi_probability': akashi_probability,
            'average_stamina': average_stamina,
            'net_stamina_gain': net_stamina_gain,
        }
    
    def submit_data(self, data: Dict[str, Any], timeout: int = 10) -> bool:
        """
        提交数据到API
        
        Args:
            data: 要提交的数据
            timeout: 请求超时时间(秒)
        
        Returns:
            是否提交成功
        """
        # 委托给ApiClient处理
        ApiClient.submit_cl1_data(data, timeout=timeout)
        return True
    
    def should_submit(self) -> bool:
        """
        检查是否应该提交数据
        基于时间间隔判断
        
        Returns:
            是否应该提交
        """
        current_time = time.time()
        if current_time - self._last_submit_time >= self._submit_interval:
            return True
        return False
    
    def auto_submit(self) -> bool:
        """
        自动提交当月数据
        会检查时间间隔,避免频繁提交
        
        Returns:
            是否成功提交
        """
        if not self.should_submit():
            return False
        
        try:
            # 收集数据
            raw_data = self.collect_data()
            
            # 计算指标
            metrics = self.calculate_metrics(raw_data)
            
            # 提交数据
            success = self.submit_data(metrics)
            
            if success:
                self._last_submit_time = time.time()
            
            return success
        
        except Exception as e:
            logger.exception(f'Failed to auto submit CL1 data: {e}')
            return False
    
    def auto_submit_daemon(self):
        """
        定时提交守护进程 (生成器函数,用于task_handler)
        每次被调用时检查是否需要提交
        """
        while True:
            try:
                self.auto_submit()
            except Exception as e:
                logger.exception(f'Error in CL1 auto submit daemon: {e}')
            yield


# 全局单例 - 每个实例一个提交器
_submitters: Dict[str, Cl1DataSubmitter] = {}


def get_cl1_submitter(instance_name: str | None = None) -> Cl1DataSubmitter:
    """获取CL1数据提交器实例"""
    global _submitters
    key = instance_name or 'default'
    if key not in _submitters:
        _submitters[key] = Cl1DataSubmitter(instance_name=instance_name)
    return _submitters[key]


__all__ = ['Cl1DataSubmitter', 'get_cl1_submitter']
