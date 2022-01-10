import logging
from multiprocessing.managers import SyncManager
import os
import queue
import threading
from multiprocessing import Process
from typing import Dict, List

from filelock import FileLock
from module.config.utils import deep_get, filepath_config
from module.logger import logger
from module.webui.utils import QueueHandler, Thread


class AlasManager:
    sync_manager: SyncManager
    all_alas: Dict[str, "AlasManager"] = {}

    def __init__(self, config_name: str = 'alas') -> None:
        self.config_name = config_name
        self.log_queue = self.sync_manager.Queue()
        self.log = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self._process = Process()
        self.thd_log_queue_handler = Thread()

    def start(self, func: str = 'Alas', ev: threading.Event = None) -> None:
        if not self.alive:
            self._process = Process(
                target=AlasManager.run_alas,
                args=(self.config_name, func, self.log_queue, ev,))
            self._process.start()
            self.thd_log_queue_handler = Thread(
                target=self._thread_log_queue_handler)
            self.thd_log_queue_handler.start()

    def stop(self) -> None:
        lock = FileLock(f"{filepath_config(self.config_name)}.lock")
        with lock:
            if self.alive:
                self._process.terminate()
                self.log.append("Scheduler stopped.\n")
            if self.thd_log_queue_handler.is_alive():
                self.thd_log_queue_handler.stop()
        logger.info(f"Alas [{self.config_name}] stopped")

    def _thread_log_queue_handler(self) -> None:
        while self.alive:
            log = self.log_queue.get()
            self.log.append(log)
            if len(self.log) > self.log_max_length:
                self.log = self.log[self.log_reduce_length:]

    @property
    def alive(self) -> bool:
        return self._process.is_alive()

    @property
    def state(self) -> int:
        if self.alive:
            return 1
        elif len(self.log) == 0 or self.log[-1] == "Scheduler stopped.\n":
            return 2
        else:
            return 3

    @classmethod
    def get_alas(cls, config_name: str) -> "AlasManager":
        """
        Create a new alas if not exists.
        """
        if config_name not in cls.all_alas:
            cls.all_alas[config_name] = AlasManager(config_name)
        return cls.all_alas[config_name]

    @staticmethod
    def run_alas(config_name, func: str, q: queue.Queue, e: threading.Event) -> None:
        # Setup logger
        qh = QueueHandler(q)
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        webconsole = logging.StreamHandler(stream=qh)
        webconsole.setFormatter(formatter)
        logging.getLogger('alas').addHandler(webconsole)

        # Set server before loading any buttons.
        import module.config.server as server
        from module.config.config import AzurLaneConfig
        config = AzurLaneConfig(config_name=config_name)
        server.server = deep_get(
            config.data, keys='Alas.Emulator.Server', default='cn')

        # Run alas
        if func == 'Alas':
            from alas import AzurLaneAutoScript
            if e is not None:
                AzurLaneAutoScript.stop_event = e
            AzurLaneAutoScript(config_name=config_name).loop()
        elif func == 'Daemon':
            from module.daemon.daemon import AzurLaneDaemon
            AzurLaneDaemon(config=config_name, task='Daemon').run()
        elif func == 'OpsiDaemon':
            from module.daemon.os_daemon import AzurLaneDaemon
            AzurLaneDaemon(config=config_name, task='OpsiDaemon').run()
        elif func == 'AzurLaneUncensored':
            from module.daemon.uncensored import AzurLaneUncensored
            AzurLaneUncensored(config=config_name,
                               task='AzurLaneUncensored').run()
            q.put("Scheduler stopped.\n")  # Prevent status turns to warning
        elif func == 'Benchmark':
            from module.daemon.benchmark import Benchmark
            Benchmark(config=config_name, task='Benchmark').run()
            q.put("Scheduler stopped.\n")  # Prevent status turns to warning
        elif func == 'GameManager':
            from module.daemon.game_manager import GameManager
            GameManager(config=config_name, task='GameManager').run()
            q.put("Scheduler stopped.\n")
        else:
            logger.critical("No function matched")

    @classmethod
    def running_instances(cls) -> List["AlasManager"]:
        l = []
        for alas in cls.all_alas.values():
            if alas.alive:
                l.append(alas)
        return l

    @staticmethod
    def start_alas(instances: List["AlasManager"] = None, ev: threading.Event = None):
        """
        After update and reload, or failed to perform an update,
        restart all alas that running before update
        """
        logger.hr("Restart alas")
        if not instances:
            instances = []
            try:
                with open('./reloadalas', mode='r') as f:
                    for line in f.readlines():
                        line = line.strip()
                        instances.append(AlasManager.get_alas(line))
            except:
                pass

        for alas in instances:
            logger.info(f"Starting [{alas.config_name}]")
            alas.start(func='Alas', ev=ev)

        try:
            os.remove('./reloadalas')
        except:
            pass
        logger.info("Start alas complete")
