import pickle

from deploy.config import DeployConfig
from deploy.logger import logger
from deploy.utils import *


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

    def iter_process_by_name(self, name):
        """
        Args:
            name (str): process name, such as 'alas.exe'

        Yields:
            str, str, str: executable_path, process_name, process_id
        """
        for _ in range(2):
            try:
                from win32com.client import GetObject
            except ModuleNotFoundError:
                # No module named pywin32
                logger.info('pywin32 not installed, skip')
                return False
            except (pickle.UnpicklingError, EOFError) as e:
                # _pickle.UnpicklingError: invalid load key, '\x00'.
                # EOFError: Ran out of input
                logger.error(f'{type(e).__name__}: {e}')
                import sys
                import win32api
                # From win32com/client/__init__.py
                gen_path = os.path.join(win32api.GetTempPath(), "gen_py",
                                        "%d.%d" % (sys.version_info[0], sys.version_info[1]))
                # From win32com/client/gencache.py
                file = os.path.join(gen_path, "dicts.dat")
                # Try deleting it
                file = os.path.abspath(file).replace('\\', '/')
                if os.path.exists(file):
                    logger.info(f'win32com dicts.dat exists, removing: {file}')
                    os.remove(file)
                    continue
                else:
                    logger.warning(f'Cannot find win32com dicts.dat')
                    continue
        try:
            _ = GetObject
        except UnboundLocalError:
            logger.warning('Unable to import win32com.client, please fix it manually, '
                           'see https://github.com/LmeSzinc/AzurLaneAutoScript/issues/2382')
            exit(1)

        try:
            wmi = GetObject('winmgmts:')
            processes = wmi.InstancesOf('Win32_Process')
            for p in processes:
                executable_path = p.Properties_["ExecutablePath"].Value
                process_name = p.Properties_("Name").Value
                process_id = p.Properties_["ProcessID"].Value

                if executable_path is not None and process_name == name and process_id != self.self_pid:
                    executable_path = executable_path.replace(r'\\', '/').replace('\\', '/')
                    for folder in self.alas_folder:
                        if folder in executable_path:
                            yield executable_path, process_name, process_id
        except Exception as e:
            # Possible exception
            # pywintypes.com_error: (-2147217392, 'OLE error 0x80041010', None, None)
            logger.info(str(e))
            return False

    def kill_by_name(self, name):
        """
        Args:
            name (str): Process name
        """
        logger.hr(f'Kill {name}', 1)
        for row in self.iter_process_by_name(name):
            logger.info(' '.join(map(str, row)))
            self.execute(f'taskkill /f /pid {row[2]}', allow_failure=True, output=False)

    def alas_kill(self):
        logger.hr(f'Kill existing Alas', 0)
        self.kill_by_name('alas.exe')
        self.kill_by_name('python.exe')
