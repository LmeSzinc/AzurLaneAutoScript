"""
Device ID 管理模块
负责生成、存储和加载设备唯一标识符
"""
import hashlib
import json
import platform
from pathlib import Path
from typing import Optional

from module.logger import logger


def generate_device_id() -> str:
    """
    基于UUID生成唯一标识符
    
    Returns:
        str: 32位十六进制字符串作为设备唯一标识
    """
    import uuid
    return uuid.uuid1().hex


_device_id: Optional[str] = None


def get_device_id() -> str:
    """
    获取设备ID (单例模式)
    
    Returns:
        str: 设备唯一标识
    """
    global _device_id
    if _device_id is None:
        _device_id = _load_or_generate_device_id()
    return _device_id


def _load_or_generate_device_id() -> str:
    """
    从文件加载或生成新的设备ID
    优先级: log/device_id.json > log/cl1/cl1_monthly.json > 生成新ID
    
    Returns:
        str: 设备ID
    """
    project_root = Path(__file__).resolve().parents[2]
    device_id_file = project_root / 'log' / 'device_id.json'
    cl1_file = project_root / 'log' / 'cl1' / 'cl1_monthly.json'
    
    # 1. 尝试从新的存储位置读取
    device_id = _load_from_file(device_id_file)
    if device_id:
        logger.info('Loaded device ID from device_id.json')
        return device_id
    
    # 2. 尝试从旧的CL1文件迁移
    device_id = _load_from_file(cl1_file)
    if device_id:
        logger.info('Migrated device ID from cl1_monthly.json')
        _save_device_id(device_id, device_id_file)
        return device_id
    
    # 3. 生成新ID
    device_id = generate_device_id()
    logger.info(f'Generated new device ID: {device_id[:8]}...')
    _save_device_id(device_id, device_id_file)
    return device_id


def _load_from_file(file_path: Path) -> Optional[str]:
    """
    从JSON文件读取device_id
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[str]: device_id或None
    """
    try:
        if file_path.exists():
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'device_id' in data:
                    return data['device_id']
    except Exception as e:
        logger.warning(f'Failed to load device ID from {file_path}: {e}')
    return None


def _save_device_id(device_id: str, file_path: Path):
    """
    保存device_id到JSON文件
    
    Args:
        device_id: 设备ID
        file_path: 文件路径
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有数据
        data = {}
        if file_path.exists():
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        data = {}
            except Exception:
                pass
        
        # 添加或更新device_id
        data['device_id'] = device_id
        
        # 写回文件
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f'Saved device ID to {file_path}')
    except Exception as e:
        logger.exception(f'Failed to save device ID to {file_path}: {e}')
