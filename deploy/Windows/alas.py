import time
import typing as t

from deploy.Windows.config import DeployConfig
from deploy.Windows.logger import logger
from deploy.Windows.utils import *


class AlasManager(DeployConfig):
    _process_cache = []
    _process_cache_time = 0.

    @cached_property
    def alas_folder(self):
        return [
            self.filepath(self.PythonExecutable),
            self.root_filepath
        ]

    @cached_property
    def self_pid(self):
        return os.getpid()

    def list_process(self, cache=5) -> t.List[DataProcessInfo]:
        """
        Args:
            cache: Cache expire time
        """
        if time.time() - self._process_cache_time <= cache and len(self._process_cache):
            logger.info('Hit process cache')
            return self._process_cache

        logger.info('List process')
        process = list(iter_process())
        logger.info(f'Found {len(process)} processes')
        self._process_cache = process
        self._process_cache_time = time.time()
        return self._process_cache

    def iter_process_by_names(self, names, in_alas=False) -> t.Iterable[DataProcessInfo]:
        """
        Args:
            names (str, list[str]): process name, such as 'alas.exe'
            in_alas (bool): If the output process must in Alas

        Yields:
            DataProcessInfo:
        """
        if not isinstance(names, list):
            names = [names]
        try:
            for proc in self.list_process():

                if not (proc.name and proc.name in names):
                    continue
                if proc.pid == self.self_pid:
                    continue
                if in_alas:
                    for folder in self.alas_folder:
                        if folder in proc.cmdline:
                            yield proc
                else:
                    yield proc
        except Exception as e:
            logger.info(str(e))
            return False

    def kill_process(self, process: DataProcessInfo):
        self.execute(f'taskkill /f /t /pid {process.pid}', allow_failure=True, output=False)

    def alas_kill(self):
        logger.hr(f'Kill existing Alas', 0)
        for proc in self.iter_process_by_names(['alas.exe', 'python.exe'], in_alas=True):
            logger.info(proc)
            self.kill_process(proc)
