import copy

from filelock import FileLock

from deploy.config import DeployConfig as _DeployConfig
from deploy.utils import *


def poor_yaml_read_with_lock(file):
    if not os.path.exists(file):
        return {}

    with FileLock(f"{file}.lock"):
        return poor_yaml_read(file)


def poor_yaml_write_with_lock(data, file, template_file=DEPLOY_TEMPLATE):
    folder = os.path.dirname(file)
    if not os.path.exists(folder):
        os.mkdir(folder)

    with FileLock(f"{file}.lock"):
        with FileLock(f"{DEPLOY_TEMPLATE}.lock"):
            return poor_yaml_write(data, file, template_file)


class DeployConfig(_DeployConfig):
    def show_config(self):
        pass

    def read(self):
        """
        Read and update deploy config, copy `self.configs` to properties.
        """
        self.config = poor_yaml_read_with_lock(DEPLOY_TEMPLATE)
        self.config_template = copy.deepcopy(self.config)
        origin = poor_yaml_read_with_lock(self.file)
        self.config.update(origin)

        for key, value in self.config.items():
            if hasattr(self, key):
                super().__setattr__(key, value)

        self.config_redirect()

        if self.config != origin:
            self.write()

    def write(self):
        """
        Write `self.config` into deploy config.
        """
        poor_yaml_write_with_lock(self.config, self.file)

    def __setattr__(self, key: str, value):
        """
        Catch __setattr__, copy to `self.config`, write deploy config.
        """
        super().__setattr__(key, value)
        if key[0].isupper() and key in self.config:
            if key in self.config:
                before = self.config[key]
                if before != value:
                    self.config[key] = value
                    self.write()
            else:
                self.config[key] = value
                self.write()
