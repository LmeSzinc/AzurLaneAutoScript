import copy

from deploy.logger import logger
from deploy.utils import DEPLOY_CONFIG, DEPLOY_TEMPLATE, cached_property, os, poor_yaml_read, poor_yaml_write


class ExecutionError(Exception):
    pass


class ConfigModel:
    # Git
    Repository: str = "https://github.com/LmeSzinc/AzurLaneAutoScript"
    Branch: str = "master"
    GitExecutable: str = "git"
    GitProxy: str | None = None
    SSLVerify: bool = True
    AutoUpdate: bool = True

    # Python
    PythonExecutable: str = "python"
    PypiMirror: str | None = None
    InstallDependencies: bool = True
    RequirementsFile: str = "requirements.txt"

    # Adb
    AdbExecutable: str = "adb"
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
    SSHUser: str | None = None
    SSHServer: str | None = None
    SSHExecutable: str | None = None

    # Webui
    WebuiHost: str = "0.0.0.0"
    WebuiPort: int = 22267
    WebuiSSLKey: str | None = None
    WebuiSSLCert: str | None = None
    Language: str = "en-US"
    Theme: str = "default"
    DpiScaling: bool = True
    Password: str | None = None
    Run: str | None = None


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

        logger.info("Rest of the configs are the same as default")

    def read(self):
        """
        Read and update deploy config, copy `self.configs` to properties.
        """
        self.config = poor_yaml_read(DEPLOY_TEMPLATE)
        self.config_template = copy.deepcopy(self.config)
        origin = poor_yaml_read(self.file)
        self.config.update(origin)

        for key, value in self.config.items():
            if hasattr(self, key):
                super().__setattr__(key, value)

        if self.config != origin:
            self.write()

    def write(self):
        poor_yaml_write(self.config, self.file)

    def filepath(self, key):
        """
        Args:
            key (str):

        Returns:
            str: Absolute filepath.
        """
        return (
            os.path.abspath(os.path.join(self.root_filepath, self.config[key]))
            .replace(r"\\", "/")
            .replace("\\", "/")
            .replace('"', '"')
        )

    @cached_property
    def root_filepath(self):
        return (
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
            .replace(r"\\", "/")
            .replace("\\", "/")
            .replace('"', '"')
        )

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
            command = command + " >nul 2>nul"
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
            logger.info("[ success ]")
            return True

    def show_error(self, command=None):
        logger.hr("Update failed", 0)
        self.show_config()
        logger.info("")
        logger.info(f"Last command: {command}")
        logger.info("Please check your deploy settings in config/deploy.yaml and re-open Alas.exe")
        logger.info("Take the screenshot of entire window if you need help")
