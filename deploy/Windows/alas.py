import typing as t
from dataclasses import dataclass

from deploy.Windows.config import DeployConfig
from deploy.Windows.logger import logger
from deploy.Windows.utils import *


@dataclass
class DataProcessInfo:
    name: str
    pid: int
    cmdline: str


class AlasManager(DeployConfig):
    @cached_property
    def alas_folder(self):
        return [
            self.filepath("PythonExecutable"),
            self.root_filepath
        ]

    @cached_property
    def self_pid(self):
        return os.getpid()

    def iter_process_by_names(self, names) -> t.Iterable[DataProcessInfo]:
        """
        Args:
            names (str, list[str]): process name, such as 'alas.exe'

        Yields:
            DataProcessInfo:
        """
        try:
            import psutil
        except ModuleNotFoundError:
            logger.info('psutil not installed, skip')
            return False

        if not isinstance(names, list):
            names = [names]
        try:
            for proc in psutil.process_iter():
                name = proc.name()
                if name and name in names and proc.pid != self.self_pid:
                    cmdline = ' '.join(proc.cmdline()).replace(r'\\', '/').replace('\\', '/')
                    for folder in self.alas_folder:
                        if folder in cmdline:
                            yield DataProcessInfo(
                                name=name,
                                pid=proc.pid,
                                cmdline=cmdline,
                            )
        except Exception as e:
            logger.info(str(e))
            return False

    def alas_kill(self):
        logger.hr(f'Kill existing Alas', 0)
        for proc in self.iter_process_by_names(['alas.exe', 'python.exe']):
            logger.info(proc)
            self.execute(f'taskkill /f /t /pid {proc.pid}', allow_failure=True, output=False)
