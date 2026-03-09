# -*- coding: utf-8 -*-
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

from module.base.device_id import get_device_id
from module.logger import logger

class Cl1Database:
    """
    CL1 数据加密 SQLite 数据库管理类。
    所有实例共享一个数据库文件，但数据经过 AES-GCM 加密，并由 device_id 保护。
    """
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            self.db_dir = project_root / 'config'
            self.db_path = self.db_dir / 'cl1_data.db'
        else:
            self.db_path = db_path
            self.db_dir = self.db_path.parent

        self._ensure_dir()
        self._init_db()
        self._encryption_key = self._derive_key()
        self._auto_migrate()

    def _ensure_dir(self):
        try:
            self.db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")

    def _init_db(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 存储各实例、月份的加密数据
                # encrypted_blob 包含 nonce + tag + ciphertext
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cl1_data (
                        instance TEXT,
                        month TEXT,
                        encrypted_blob BLOB,
                        PRIMARY KEY (instance, month)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.exception(f"Failed to initialize CL1 database: {e}")

    def _derive_key(self) -> bytes:
        """基于 device_id 派生 256 位 AES 密钥"""
        device_id = get_device_id()
        salt = b'AlasCl1SecureStorage' # 固定盐
        return PBKDF2(device_id.encode(), salt, dkLen=32, count=1000, hmac_hash_module=SHA256)

    def _encrypt(self, data: Dict[str, Any]) -> bytes:
        """使用 AES-GCM 加密数据"""
        try:
            cipher = AES.new(self._encryption_key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode('utf-8'))
            # 拼接: nonce (16) + tag (16) + ciphertext
            return cipher.nonce + tag + ciphertext
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return b""

    def _decrypt(self, blob: bytes) -> Optional[Dict[str, Any]]:
        """使用 AES-GCM 解密数据，并验证完整性"""
        if not blob or len(blob) < 32:
            return None
        try:
            nonce = blob[:16]
            tag = blob[16:32]
            ciphertext = blob[32:]
            cipher = AES.new(self._encryption_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return json.loads(plaintext.decode('utf-8'))
        except (ValueError, KeyError) as e:
            logger.error(f"Decryption failed (Tamper detected or Wrong key): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected decryption error: {e}")
            return None

    def get_stats(self, instance: str, month: str) -> Dict[str, Any]:
        """获取指定实例和月份的统计数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT encrypted_blob FROM cl1_data WHERE instance = ? AND month = ?", 
                             (instance, month))
                row = cursor.fetchone()
                if row:
                    data = self._decrypt(row[0])
                    if data:
                        return data
        except Exception as e:
            logger.error(f"Failed to query stats for {instance} {month}: {e}")
        
        return self._empty_data(month)

    def _empty_data(self, month: str) -> Dict[str, Any]:
        return {
            'battle_count': 0,
            'akashi_encounters': 0,
            'akashi_ap': 0,
            'akashi_ap_entries': [],
            # 短猫数据
            'meow_battle_count': 0,
            'meow_round_times': [],
            'meow_battle_times': [],  # 短猫单场战斗时间
        }

    def save_stats(self, instance: str, month: str, data: Dict[str, Any]):
        """保存统计数据"""
        try:
            blob = self._encrypt(data)
            if not blob:
                return
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cl1_data (instance, month, encrypted_blob) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(instance, month) DO UPDATE SET encrypted_blob = excluded.encrypted_blob
                ''', (instance, month, blob))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save stats for {instance} {month}: {e}")

    def increment_battle_count(self, instance: str, delta: int = 1):
        """增加战斗次数"""
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)
        data['battle_count'] = data.get('battle_count', 0) + delta
        self.save_stats(instance, month, data)

    def increment_akashi_encounter(self, instance: str):
        """增加明石奇遇次数"""
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)
        data['akashi_encounters'] = data.get('akashi_encounters', 0) + 1
        self.save_stats(instance, month, data)

    def add_akashi_ap_entry(self, instance: str, amount: int, base: int, count: int, source: str):
        """记录明石行动力购买条目"""
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)
        
        entry = {
            'ts': datetime.now().isoformat(),
            'amount': amount,
            'base': base,
            'count': count,
            'source': source
        }
        
        entries = data.get('akashi_ap_entries', [])
        entries.append(entry)
        data['akashi_ap_entries'] = entries
        
        data['akashi_ap'] = data.get('akashi_ap', 0) + amount
        self.save_stats(instance, month, data)

    def add_ap_snapshot(self, instance: str, ap_current: int, source: str = 'cl1'):
        """记录行动力快照（真实剩余体力）

        Args:
            instance: 实例名称
            ap_current: 当前行动力剩余
            source: 数据来源标记 (cl1 / meow 等)
        """
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)

        snapshot = {
            'ts': datetime.now().isoformat(),
            'ap': int(ap_current),
            'source': source,
        }

        snapshots = data.get('ap_snapshots', [])
        snapshots.append(snapshot)
        data['ap_snapshots'] = snapshots
        self.save_stats(instance, month, data)

    def migrate_from_json(self, json_path: Path, instance: str):
        """从 JSON 文件迁移数据到数据库"""
        if not json_path.exists():
            return
        
        logger.info(f"Migrating CL1 data from {json_path} for instance {instance}")
        try:
            with json_path.open('r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            if not isinstance(old_data, dict):
                return

            # JSON 格式比较杂乱，需要按月份归档
            # 格式可能是: {"2026-02": 10, "2026-02-akashi": 1, "2026-02-akashi-ap": 120, "2026-02-akashi-ap-entries": [...]}
            months = set()
            for key in old_data.keys():
                if len(key) >= 7 and key[4] == '-':
                    months.add(key[:7])
            
            for month in months:
                # 首先检查数据库是否已有数据，避免覆盖
                with sqlite3.connect(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM cl1_data WHERE instance = ? AND month = ?", (instance, month))
                    if c.fetchone():
                        logger.info(f"Data for {instance} {month} already exists in DB, skipping migration")
                        continue

                new_stats = self._empty_data(month)
                new_stats['battle_count'] = old_data.get(month, 0)
                new_stats['akashi_encounters'] = old_data.get(f"{month}-akashi", 0)
                new_stats['akashi_ap'] = old_data.get(f"{month}-akashi-ap", 0)
                new_stats['akashi_ap_entries'] = old_data.get(f"{month}-akashi-ap-entries", [])
                
                self.save_stats(instance, month, new_stats)
                logger.info(f"Successfully migrated {instance} {month}")

            # 迁移成功后可以删除 JSON 或重命名 (此处建议重命名为 .bak 以防万一)
            bak_path = json_path.with_suffix('.json.bak')
            json_path.replace(bak_path)
            logger.info(f"Retired old JSON to {bak_path}")

        except Exception as e:
            logger.exception(f"Failed to migrate CL1 data from JSON: {e}")

    def _auto_migrate(self):
        """
        初始化时自动扫描 log/cl1 下的所有实例并迁移旧数据
        """
        project_root = Path(__file__).resolve().parents[2]
        old_db_dir = project_root / 'log' / 'cl1'
        old_db_path = old_db_dir / 'cl1_data.db'

        if old_db_path.exists() and not self.db_path.exists():
            import shutil
            try:
                shutil.move(str(old_db_path), str(self.db_path))
                logger.info(f"Moved old CL1 database from {old_db_path} to {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to move old CL1 database: {e}")

        if not old_db_dir.exists():
            return
            
        # logger.info(f"Scanning for legacy CL1 data in {old_db_dir}...")
        try:
            for instance_dir in old_db_dir.iterdir():
                if instance_dir.is_dir():
                    json_file = instance_dir / 'cl1_monthly.json'
                    if json_file.exists():
                        # logger.info(f"Found legacy data for instance: {instance_dir.name}")
                        self.migrate_from_json(json_file, instance_dir.name)
        except Exception as e:
            logger.error(f"Error during auto migration scan: {e}")

    # ========== 短猫数据记录方法 ==========

    def increment_meow_battle_count(self, instance: str, delta: int = 1):
        """增加短猫战斗次数"""
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)
        data['meow_battle_count'] = data.get('meow_battle_count', 0) + delta
        self.save_stats(instance, month, data)

    def add_meow_round_time(self, instance: str, duration: float, hazard_level: int = None):
        """记录短猫单轮战斗时间

        Args:
            instance: 实例名称
            duration: 战斗耗时（秒）
            hazard_level: 侵蚀等级，用于计算出击轮次
        """
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)

        if 'meow_round_times' not in data:
            data['meow_round_times'] = []

        times = data['meow_round_times']
        # 保存为字典，包含时长和侵蚀等级
        entry = {
            'duration': round(duration, 2),
            'hazard_level': hazard_level
        }
        times.append(entry)

        # 只保留最近100个样本
        if len(times) > 100:
            times = times[-100:]

        data['meow_round_times'] = times
        self.save_stats(instance, month, data)

    def add_meow_battle_time(self, instance: str, duration: float):
        """记录短猫单场战斗时间

        Args:
            instance: 实例名称
            duration: 战斗耗时（秒）
        """
        month = datetime.now().strftime('%Y-%m')
        data = self.get_stats(instance, month)

        if 'meow_battle_times' not in data:
            data['meow_battle_times'] = []

        times = data['meow_battle_times']
        times.append(round(duration, 2))

        # 只保留最近100个样本
        if len(times) > 100:
            times = times[-100:]

        data['meow_battle_times'] = times
        self.save_stats(instance, month, data)

    def get_meow_stats(self, instance: str, year: int = None, month: int = None) -> Dict[str, Any]:
        """获取短猫统计数据

        Args:
            instance: 实例名称
            year: 年份，默认当前年
            month: 月份，默认当前月

        Returns:
            短猫统计数据字典
        """
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        key = f"{year:04d}-{month:02d}"

        data = self.get_stats(instance, key)

        battle_count = int(data.get('meow_battle_count', 0))
        round_times = data.get('meow_round_times', [])
        battle_times = data.get('meow_battle_times', [])

        # 计算平均每轮时间
        avg_round_time = 0.0
        if round_times:
            avg_round_time = round(sum(round_times) / len(round_times), 2)

        # 计算平均单场战斗时间
        avg_battle_time = 0.0
        if battle_times:
            avg_battle_time = round(sum(battle_times) / len(battle_times), 2)

        return {
            'month': key,
            'battle_count': battle_count,
            'round_times': round_times,
            'avg_round_time': avg_round_time,
            'battle_times': battle_times,
            'avg_battle_time': avg_battle_time,
        }


# 单例实例
db = Cl1Database()
