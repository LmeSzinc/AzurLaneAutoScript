import copy
import os
import subprocess
import sys
from typing import Optional, Union

from deploy.Windows.logger import logger
from deploy.Windows.utils import DEPLOY_CONFIG, DEPLOY_TEMPLATE, cached_property, poor_yaml_read, poor_yaml_write


class ExecutionError(Exception):
    pass


class ConfigModel:
    # Git
    Repository: str = "https://github.com/LmeSzinc/AzurLaneAutoScript"
    Branch: str = "master"
    GitExecutable: str = "./toolkit/Git/mingw64/bin/git.exe"
    GitProxy: Optional[str] = None
    SSLVerify: bool = False
    AutoUpdate: bool = True
    KeepLocalChanges: bool = False

    # Python
    PythonExecutable: str = "./toolkit/python.exe"
    PypiMirror: Optional[str] = None
    InstallDependencies: bool = True
    RequirementsFile: str = "requirements.txt"

    # Adb
    AdbExecutable: str = "./toolkit/Lib/site-packages/adbutils/binaries/adb.exe"
    ReplaceAdb: bool = True
    AutoConnect: bool = True
    InstallUiautomator2: bool = True

    # Ocr
    UseOcrServer: bool = False
    StartOcrServer: bool = False
    OcrServerPort: int = 22268
    OcrClientAddress: str = "127.0.0.1:22268"

    # Update
    EnableReload: bool = True
    CheckUpdateInterval: int = 5
    AutoRestartTime: str = "03:50"

    # Misc
    DiscordRichPresence: bool = False

    # Remote Access
    EnableRemoteAccess: bool = False
    SSHUser: Optional[str] = None
    SSHServer: Optional[str] = None
    SSHExecutable: Optional[str] = None

    # Webui
    WebuiHost: str = "0.0.0.0"
    WebuiPort: int = 22367
    Language: str = "en-US"
    Theme: str = "default"
    DpiScaling: bool = True
    Password: Optional[str] = None
    CDN: Union[str, bool] = False
    Run: Optional[str] = None
    AppAsarUpdate: bool = True
    NoSandbox: bool = True

    # Dynamic
    GitOverCdn: bool = False


class DeployConfig(ConfigModel):
    def __init__(self, file=DEPLOY_CONFIG):
        """
        Args:
            file (str): User deploy config.
        """
        self.file = file
        self.config = {}
        self.config_template = {}
        self.read()

        self.show_config()

    def show_config(self):
        logger.hr("Show deploy config", 1)
        for k, v in self.config.items():
            if k in ("Password", "SSHUser"):
                continue
            if self.config_template.get(k) == v:
                continue
            logger.info(f"{k}: {v}")

        logger.info(f"Rest of the configs are the same as default")

    def read(self):
        self.config = poor_yaml_read(DEPLOY_TEMPLATE)
        self.config_template = copy.deepcopy(self.config)
        origin = poor_yaml_read(self.file)
        self.config.update(origin)

        for key, value in self.config.items():
            if hasattr(self, key):
                super().__setattr__(key, value)

        self.config_redirect()

        if self.config != origin:
            self.write()

    def write(self):
        poor_yaml_write(self.config, self.file)

    def config_redirect(self):
        """
        Redirect deploy config, must be called after each `read()`
        """
        # Bypass webui.config.DeployConfig.__setattr__()
        # Don't write these into deploy.yaml
        super().__setattr__('GitOverCdn', self.Repository in ['cn'])
        if self.Repository in ['global', 'cn']:
            super().__setattr__('Repository', 'https://github.com/LmeSzinc/StarRailCopilot')

    def filepath(self, path):
        """
        Args:
            path (str):

        Returns:
            str: Absolute filepath.
        """
        if os.path.isabs(path):
            return path

        return (
            os.path.abspath(os.path.join(self.root_filepath, path))
            .replace(r"\\", "/")
            .replace("\\", "/")
        )

    @cached_property
    def root_filepath(self):
        return (
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
            .replace(r"\\", "/")
            .replace("\\", "/")
        )

    @cached_property
    def adb(self) -> str:
        exe = self.filepath(self.AdbExecutable)
        if os.path.exists(exe):
            return exe

        logger.warning(f'AdbExecutable: {exe} does not exist, use `adb` instead')
        return 'adb'

    @cached_property
    def git(self) -> str:
        exe = self.filepath(self.GitExecutable)
        if os.path.exists(exe):
            return exe

        logger.warning(f'GitExecutable: {exe} does not exist, use `git` instead')
        return 'git'

    @cached_property
    def python(self) -> str:
        exe = self.filepath(self.PythonExecutable)
        if os.path.exists(exe):
            return exe

        current = sys.executable.replace("\\", "/")
        logger.warning(f'PythonExecutable: {exe} does not exist, use current python instead: {current}')
        return current

    @cached_property
    def requirements_file(self) -> str:
        if self.RequirementsFile == 'requirements.txt':
            return 'requirements.txt'
        else:
            return self.filepath(self.RequirementsFile)

    def execute(self, command, allow_failure=False, output=True):
        """
        Args:
            command (str):
            allow_failure (bool):
            output(bool):

        Returns:
            bool: If success.
                Terminate installation if failed to execute and not allow_failure.
        """
        command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        if not output:
            command = command + ' >nul 2>nul'
        logger.info(command)
        error_code = os.system(command)
        if error_code:
            if allow_failure:
                logger.info(f"[ allowed failure ], error_code: {error_code}")
                return False
            else:
                logger.info(f"[ failure ], error_code: {error_code}")
                self.show_error(command)
                raise ExecutionError
        else:
            logger.info(f"[ success ]")
            return True

    def subprocess_execute(self, cmd, timeout=10):
        """
        Args:
            cmd (list[str]):
            timeout:

        Returns:
            str:
        """
        logger.info(' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            process.kill()
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.info(f'TimeoutExpired, stdout={stdout}, stderr={stderr}')
        return stdout.decode()

    def show_error(self, command=None):
        logger.hr("Update failed", 0)
        self.show_config()
        logger.info("")
        logger.info(f"Last command: {command}")
        logger.info(
            "Please check your deploy settings in config/deploy.yaml "
            "and re-open Alas.exe"
        )
        logger.info("Take the screenshot of entire window if you need help")
