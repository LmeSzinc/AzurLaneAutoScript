import logging
import os
import queue
import threading
from multiprocessing import Process
from typing import Dict, List

from filelock import FileLock
from module.config.utils import deep_get, filepath_config
from module.logger import logger
from module.webui.setting import Setting
from module.webui.utils import QueueHandler, Thread


class ProcessManager:
    _processes: Dict[str, "ProcessManager"] = {}

    def __init__(self, config_name: str = 'alas') -> None:
        self.config_name = config_name
        self.log_queue = Setting.manager.Queue()
        self.log: List[str] = []
        self.log_max_length = 500
        self.log_reduce_length = 100
        self._process: Process = None
        self.thd_log_queue_handler: Thread = None

    def start(self, func: str, ev: threading.Event = None) -> None:
        if not self.alive:
            self._process = Process(
                target=ProcessManager.run_process,
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
                self.log.append(
                    f"[{self.config_name}] exited. Reason: Manual stop\n")
            if self.thd_log_queue_handler is not None:
                self.thd_log_queue_handler.stop()
        logger.info(f"[{self.config_name}] exited")

    def _thread_log_queue_handler(self) -> None:
        while self.alive:
            log = self.log_queue.get()
            self.log.append(log)
            if len(self.log) > self.log_max_length:
                self.log = self.log[self.log_reduce_length:]

    @property
    def alive(self) -> bool:
        if self._process is not None:
            return self._process.is_alive()
        else:
            return False

    @property
    def state(self) -> int:
        if self.alive:
            return 1
        elif len(self.log) == 0 or \
                self.log[-1].endswith("Reason: Manual stop\n") or \
                self.log[-1].endswith("Reason: Finish\n"):
            return 2
        elif self.log[-1].endswith("Reason: Update\n"):
            return 4
        else:
            return 3

    @classmethod
    def get_manager(cls, config_name: str) -> "ProcessManager":
        """
        Create a new alas if not exists.
        """
        if config_name not in cls._processes:
            cls._processes[config_name] = ProcessManager(config_name)
        return cls._processes[config_name]

    @staticmethod
    def run_process(config_name, func: str, q: queue.Queue, e: threading.Event = None) -> None:
        # Setup logger
        qh = QueueHandler(q)
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S')
        webconsole = logging.StreamHandler(stream=qh)
        webconsole.setFormatter(formatter)
        logger.addHandler(webconsole)

        # Set server before loading any buttons.
        import module.config.server as server
        from module.config.config import AzurLaneConfig
        AzurLaneConfig.stop_event = e
        config = AzurLaneConfig(config_name=config_name)
        server.server = deep_get(
            config.data, keys='Alas.Emulator.Server', default='cn')
        try:
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
            elif func == 'Benchmark':
                from module.daemon.benchmark import Benchmark
                Benchmark(config=config_name, task='Benchmark').run()
            elif func == 'GameManager':
                from module.daemon.game_manager import GameManager
                GameManager(config=config_name, task='GameManager').run()
            else:
                logger.critical("No function matched")
            logger.info(f"[{config_name}] exited. Reason: Finish")
        except Exception as e:
            logger.exception(e)

    @classmethod
    def running_instances(cls) -> List["ProcessManager"]:
        l = []
        for process in cls._processes.values():
            if process.alive:
                l.append(process)
        return l

    @staticmethod
    def restart_processes(instances: List["ProcessManager"] = None, ev: threading.Event = None):
        """
        After update and reload, or failed to perform an update,
        restart all alas that running before update
        """
        logger.hr("Restart alas")
        if not instances:
            instances = []
            try:
                with open('./config/reloadalas', mode='r') as f:
                    for line in f.readlines():
                        line = line.strip()
                        instances.append(ProcessManager.get_manager(line))
            except:
                pass

        for process in instances:
            logger.info(f"Starting [{process.config_name}]")
            process.start(func='Alas', ev=ev)

        try:
            os.remove('./config/reloadalas')
        except:
            pass
        logger.info("Start alas complete")
