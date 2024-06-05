from deploy.Windows.logger import Progress, logger
from deploy.Windows.patch import pre_checks

pre_checks()

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


def run():
    Progress.Start()
    installer = Installer()
    Progress.ShowDeployConfig()

    installer.install()

    logger.info('Finish')
    Progress.Finish()
