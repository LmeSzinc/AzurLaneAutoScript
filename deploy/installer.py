from deploy.Windows.patch import patch_trust_env

patch_trust_env()

from deploy.Windows.adb import AdbManager
from deploy.Windows.alas import AlasManager
from deploy.Windows.app import AppManager
from deploy.Windows.config import ExecutionError
from deploy.Windows.git import GitManager
from deploy.Windows.pip import PipManager


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
