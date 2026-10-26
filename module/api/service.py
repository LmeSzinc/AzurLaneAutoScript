import os
import re
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from module.logger import logger

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
LOG_DIR = ROOT_DIR / "log"

OIL_REGEX = re.compile(r'\[OCR_OIL.*?\]\s*(\d+)')
COIN_REGEX = re.compile(r'\[OCR_COIN.*?\]\s*(\d+)')
TASK_START_REGEX = re.compile(r'(?:Start task|Bind task.*?)\s*[`\'\[]([A-Za-z0-9_]+)')
TASK_FINISH_REGEX = re.compile(r'Task\s*[`\'\s]([A-Za-z0-9_]+)[`\'\s]\s*finished')
SLEEP_REGEX = re.compile(r'(?:Scheduler:\s*Sleep|Wait until|Scheduler loop)')
ERROR_REGEX = re.compile(r'(?:CRITICAL|Traceback|Request human takeover|GameNotRunningError)')

class AlasApiService:
    def __init__(self, config_name: str = "alas"):
        self.config_name = config_name
        self.config_file = CONFIG_DIR / f"{config_name}.json"
        self._ensure_config_file()

    def _ensure_config_file(self):
        """若对应配置文件不存在，从 template.json 初始化一份"""
        if not self.config_file.exists() and (CONFIG_DIR / "template.json").exists():
            try:
                with open(CONFIG_DIR / "template.json", "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"Failed to create config from template: {e}")

    def _get_process_manager(self):
        try:
            from module.webui.setting import State
            if State.manager is None:
                State.init()
            from module.webui.process_manager import ProcessManager
            return ProcessManager.get_manager(self.config_name)
        except Exception as e:
            logger.warning(f"ProcessManager not available: {e}")
            return None

    def _get_latest_log_file(self) -> Optional[Path]:
        if not LOG_DIR.exists():
            return None
        logs = list(LOG_DIR.glob(f"*{self.config_name}*.log")) or list(LOG_DIR.glob("*.log"))
        if not logs:
            return None
        return max(logs, key=lambda f: f.stat().st_mtime)

    def get_recent_log_lines(self, count: int = 100) -> List[str]:
        # 1. 优先从内存 ProcessManager 获取
        pm = self._get_process_manager()
        if pm and pm.renderables:
            try:
                from rich.console import Console
                console = Console(no_color=True)
                lines = []
                for item in pm.renderables[-count:]:
                    with console.capture() as capture:
                        console.print(item)
                    lines.append(capture.get())
                if lines:
                    return lines
            except Exception:
                pass

        # 2. 从文件读取
        log_file = self._get_latest_log_file()
        if log_file and log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    return f.readlines()[-count:]
            except Exception:
                pass
        return []

    def get_game_status(self) -> Dict[str, Any]:
        """
        获取当前运行状态与资源数量
        """
        pm = self._get_process_manager()
        is_alive = pm.alive if pm else False

        lines = self.get_recent_log_lines(200)

        oil, coin = None, None
        status = "idle" if is_alive else "stopped"
        status_text = "空闲" if is_alive else "未运行 (后台进程未启动)"
        current_task = None
        has_error = False
        last_log_time = None

        for line in reversed(lines):
            # 抓取资源
            if oil is None:
                m_oil = OIL_REGEX.search(line)
                if m_oil:
                    oil = int(m_oil.group(1))
            if coin is None:
                m_coin = COIN_REGEX.search(line)
                if m_coin:
                    coin = int(m_coin.group(1))

            # 抓取报错
            if not has_error and ERROR_REGEX.search(line):
                has_error = True

            # 抓取任务状态
            if is_alive and current_task is None and status == "idle":
                if SLEEP_REGEX.search(line) or TASK_FINISH_REGEX.search(line):
                    status = "idle"
                    status_text = "空闲"
                else:
                    m_task = TASK_START_REGEX.search(line)
                    if m_task:
                        task_name = m_task.group(1)
                        if task_name not in ["General", "Alas", "Deploy"]:
                            current_task = task_name
                            status = "running"
                            status_text = f"{current_task} 任务中"

        if is_alive and has_error and status != "running":
            status = "error"
            status_text = "报错 (异常卡住或需人工接管)"

        # 兜底回退从 config.Dashboard 拿数据
        raw_cfg = self.get_raw_config()
        dashboard = raw_cfg.get("Dashboard", {})
        if oil is None:
            oil = dashboard.get("Oil", {}).get("Value", 0)
        if coin is None:
            coin = dashboard.get("Coin", {}).get("Value", 0)

        return {
            "is_process_alive": is_alive,
            "status": status,
            "status_text": status_text,
            "current_task": current_task,
            "oil": oil or 0,
            "coin": coin or 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def refresh_resources_actively(self, force: bool = False) -> Dict[str, Any]:
        """
        主动进入主页截图识别最新石油与金币
        """
        current_state = self.get_game_status()

        # 任务执行中保护
        if current_state["status"] == "running" and not force:
            return {
                "success": False,
                "refreshed": False,
                "message": f"Alas 正在执行 [{current_state['current_task']}]，为避免中断战斗拒绝刷新。返回当前记录值。",
                "oil": current_state["oil"],
                "coin": current_state["coin"]
            }

        try:
            from alas import AzurLaneAutoScript
            from module.ui.page import page_main
            from module.ocr.ocr import Digit
            from module.base.button import Button

            alas = AzurLaneAutoScript(config_name=self.config_name)

            alas.ui_ensure(page_main)
            image = alas.device.screenshot()

            OIL_AREA = Button(area=(815, 15, 930, 48), color=(), button=(), name='OCR_OIL')
            COIN_AREA = Button(area=(990, 15, 1105, 48), color=(), button=(), name='OCR_COIN')

            ocr_oil = Digit(OIL_AREA, letter=(255, 255, 255), threshold=128, name='OCR_OIL')
            ocr_coin = Digit(COIN_AREA, letter=(255, 255, 255), threshold=128, name='OCR_COIN')

            fresh_oil = ocr_oil.ocr(image)
            fresh_coin = ocr_coin.ocr(image)

            now_iso = datetime.now().isoformat()
            self.update_task_config("Dashboard", {
                "Oil": {"Value": fresh_oil, "Record": now_iso},
                "Coin": {"Value": fresh_coin, "Record": now_iso}
            })

            return {
                "success": True,
                "refreshed": True,
                "message": "主动刷新成功",
                "oil": fresh_oil,
                "coin": fresh_coin,
                "refreshed_at": now_iso
            }
        except Exception as e:
            return {
                "success": False,
                "refreshed": False,
                "message": f"主动刷新失败: {str(e)}",
                "oil": current_state["oil"],
                "coin": current_state["coin"]
            }

    def get_raw_config(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Read config error: {e}")
            return {}

    def get_tasks_config(self) -> Dict[str, Any]:
        """获取所有带有 Scheduler 的任务项配置"""
        data = self.get_raw_config()
        tasks = {}
        for section, content in data.items():
            if isinstance(content, dict) and "Scheduler" in content:
                tasks[section] = {
                    "Enable": content["Scheduler"].get("Enable", False),
                    "NextRun": str(content["Scheduler"].get("NextRun", "")),
                    "Command": content["Scheduler"].get("Command", section),
                    "Settings": {k: v for k, v in content.items() if k != "Scheduler"}
                }
        return tasks

    def get_single_task_config(self, task_name: str) -> Optional[Dict[str, Any]]:
        tasks = self.get_tasks_config()
        return tasks.get(task_name)

    def update_task_config(self, task_name: str, new_settings: Dict[str, Any]) -> bool:
        """更新指定配置项"""
        data = self.get_raw_config()
        if task_name not in data:
            data[task_name] = {}

        def _merge(dest, src):
            for k, v in src.items():
                if isinstance(v, dict) and k in dest and isinstance(dest[k], dict):
                    _merge(dest[k], v)
                else:
                    dest[k] = v

        _merge(data[task_name], new_settings)

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Save config error: {e}")
            return False

    def trigger_task_now(self, task_name: str) -> bool:
        """立即触发某个任务（将 NextRun 设置为当前时间，并开启任务）"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.update_task_config(task_name, {
            "Scheduler": {
                "Enable": True,
                "NextRun": now_str
            }
        })

    def start_process(self) -> bool:
        pm = self._get_process_manager()
        if pm and not pm.alive:
            pm.start(func=None)
            return True
        return False

    def stop_process(self) -> bool:
        pm = self._get_process_manager()
        if pm and pm.alive:
            pm.stop()
            return True
        return False
