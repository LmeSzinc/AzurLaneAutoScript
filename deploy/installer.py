from deploy.patch import patch_trust_env

patch_trust_env()

from deploy.adb import AdbManager
from deploy.alas import AlasManager
from deploy.app import AppManager
from deploy.config import ExecutionError
from deploy.git import GitManager
from deploy.pip import PipManager


class Installer(GitManager, PipManager, AdbManager, AppManager, AlasManager):
    def install(self):
        try:
            self.git_install()
            self.alas_kill()
            self.pip_install()
            self.app_update()
            self.adb_install()
        except ExecutionError:
            exit(1)


if __name__ == '__main__':
    Installer().install()
