import os
import queue
import threading
from multiprocessing import Process
from typing import Dict, List, Union

from filelock import FileLock
from module.config.utils import filepath_config
from module.logger import logger, set_file_logger, set_func_logger
from module.submodule.submodule import load_mod
from module.submodule.utils import get_config_mod
from module.webui.setting import State
from rich.console import Console, ConsoleRenderable


class ProcessManager:
    _processes: Dict[str, "ProcessManager"] = {}

    def __init__(self, config_name: str = "alas") -> None:
        self.config_name = config_name
        self._renderable_queue: queue.Queue[ConsoleRenderable] = State.manager.Queue()
        self.renderables: List[ConsoleRenderable] = []
        self.renderables_max_length = 400
        self.renderables_reduce_length = 80
        self._process: Process = None
        self.thd_log_queue_handler: threading.Thread = None

    def start(self, func, ev: threading.Event = None) -> None:
        if not self.alive:
            if func is None:
                func = get_config_mod(self.config_name)
            self._process = Process(
                target=ProcessManager.run_process,
                args=(
                    self.config_name,
                    func,
                    self._renderable_queue,
                    ev,
                ),
            )
            self._process.start()
            self.start_log_queue_handler()

    def start_log_queue_handler(self):
        if (
            self.thd_log_queue_handler is not None
            and self.thd_log_queue_handler.is_alive()
        ):
            return
        self.thd_log_queue_handler = threading.Thread(
            target=self._thread_log_queue_handler
        )
        self.thd_log_queue_handler.start()

    def stop(self) -> None:
        lock = FileLock(f"{filepath_config(self.config_name)}.lock")
        with lock:
            if self.alive:
                self._process.kill()
                self.renderables.append(
                    f"[{self.config_name}] exited. Reason: Manual stop\n"
                )
            if self.thd_log_queue_handler is not None:
                self.thd_log_queue_handler.join(timeout=1)
                if self.thd_log_queue_handler.is_alive():
                    logger.warning(
                        "Log queue handler thread does not stop within 1 seconds"
                    )
        logger.info(f"[{self.config_name}] exited")

    def _thread_log_queue_handler(self) -> None:
        while self.alive:
            try:
                log = self._renderable_queue.get(timeout=1)
            except queue.Empty:
                continue
            self.renderables.append(log)
            if len(self.renderables) > self.renderables_max_length:
                self.renderables = self.renderables[self.renderables_reduce_length :]
        logger.info("End of log queue handler loop")

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
        elif len(self.renderables) == 0:
            return 2
        else:
            console = Console(no_color=True)
            with console.capture() as capture:
                console.print(self.renderables[-1])
            s = capture.get().strip()
            if s.endswith("Reason: Manual stop"):
                return 2
            elif s.endswith("Reason: Finish"):
                return 2
            elif s.endswith("Reason: Update"):
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
    def run_process(
        config_name, func: str, q: queue.Queue, e: threading.Event = None
    ) -> None:
        # Setup logger
        set_file_logger(name=config_name)
        set_func_logger(func=q.put)

        from module.config.config import AzurLaneConfig

        AzurLaneConfig.stop_event = e
        try:
            # Run alas
            if func == "alas":
                from alas import AzurLaneAutoScript

                if e is not None:
                    AzurLaneAutoScript.stop_event = e
                AzurLaneAutoScript(config_name=config_name).loop()
            elif func == "Daemon":
                from module.daemon.daemon import AzurLaneDaemon

                AzurLaneDaemon(config=config_name, task="Daemon").run()
            elif func == "OpsiDaemon":
                from module.daemon.os_daemon import AzurLaneDaemon

                AzurLaneDaemon(config=config_name, task="OpsiDaemon").run()
            elif func == "AzurLaneUncensored":
                from module.daemon.uncensored import AzurLaneUncensored

                AzurLaneUncensored(config=config_name, task="AzurLaneUncensored").run()
            elif func == "Benchmark":
                from module.daemon.benchmark import Benchmark

                Benchmark(config=config_name, task="Benchmark").run()
            elif func == "GameManager":
                from module.daemon.game_manager import GameManager

                GameManager(config=config_name, task="GameManager").run()
            elif func == 'maa':
                mod = load_mod('maa')

                if e is not None:
                    mod.set_stop_event(e)
                mod.loop(config_name)
            elif func == "MaaCopilot":
                mod = load_mod('maa')
                mod.maa_copilot(config_name)
            else:
                logger.critical(f"No function matched: {func}")
            logger.info(f"[{config_name}] exited. Reason: Finish\n")
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
    def restart_processes(
        instances: List[Union["ProcessManager", str]] = None, ev: threading.Event = None
    ):
        """
        After update and reload, or failed to perform an update,
        restart all alas that running before update
        """
        logger.hr("Restart alas")
        if instances is None:
            instances = []

        _instances = set()

        for instance in instances:
            if isinstance(instance, str):
                _instances.add(ProcessManager.get_manager(instance))
            elif isinstance(instance, ProcessManager):
                _instances.add(instance)

        try:
            with open("./config/reloadalas", mode="r") as f:
                for line in f.readlines():
                    line = line.strip()
                    _instances.add(ProcessManager.get_manager(line))
        except FileNotFoundError:
            pass

        for process in _instances:
            logger.info(f"Starting [{process.config_name}]")
            process.start(func=get_config_mod(process.config_name), ev=ev)

        try:
            os.remove("./config/reloadalas")
        except:
            pass
        logger.info("Start alas complete")
