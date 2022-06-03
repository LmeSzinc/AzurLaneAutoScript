import copy

from deploy.utils import *


class ExecutionError(Exception):
    pass


class DeployConfig:
    def __init__(self, file=DEPLOY_CONFIG):
        """
        Args:
            file (str): User deploy config.
        """
        self.file = file
        self.config = {}
        self.read()
        self.write()
        self.show_config()

    def show_config(self):
        hr0("Show deploy config")
        for k, v in self.config.items():
            if k in ("Password", "ApiToken"):
                continue
            if self.config_template[k] == v:
                continue
            print(f"{k}: {v}")

        print(f"Rest of the configs are the same as default")

    def read(self):
        self.config = poor_yaml_read(DEPLOY_TEMPLATE)
        self.config_template = copy.deepcopy(self.config)
        self.config.update(poor_yaml_read(self.file))

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

    @staticmethod
    def to_bool(value):
        value = value.lower()
        if value == "null" or value == "false" or value == "":
            return False
        return True

    def bool(self, key):
        """
        Args:
            key (str):

        Returns:
            bool: Option is ON or OFF.
        """
        return self.to_bool(self.config[key])

    def execute(self, command, allow_failure=False):
        """
        Args:
            command (str):
            allow_failure (bool):

        Returns:
            bool: If success.
                Terminate installation if failed to execute and not allow_failure.
        """
        command = command.replace(r"\\", "/").replace("\\", "/").replace('"', '"')
        print(command)
        error_code = os.system(command)
        if error_code:
            if allow_failure:
                print(f"[ allowed failure ], error_code: {error_code}")
                return False
            else:
                print(f"[ failure ], error_code: {error_code}")
                self.show_error()
                raise ExecutionError
        else:
            print(f"[ success ]")
            return True

    def show_error(self):
        self.show_config()
        print("")
        hr1("Update failed")
        print(
            "Please check your deploy settings in config/deploy.yaml "
            "and re-open Alas.exe"
        )
