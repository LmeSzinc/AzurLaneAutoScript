<<<<<<< HEAD
from deploy.Windows.logger import Progress, logger
from deploy.Windows.patch import pre_checks

pre_checks()

from deploy.Windows.adb import AdbManager
from deploy.Windows.alas import AlasManager
from deploy.Windows.app import AppManager
from deploy.Windows.config import ExecutionError
from deploy.Windows.git import GitManager
from deploy.Windows.pip import PipManager
=======
from deploy.patch import pre_checks

pre_checks()

from deploy.adb import AdbManager
from deploy.alas import AlasManager
from deploy.app import AppManager
from deploy.config import ExecutionError
from deploy.git import GitManager
from deploy.pip import PipManager
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0


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


<<<<<<< HEAD
def run():
    Progress.Start()
    installer = Installer()
    Progress.ShowDeployConfig()

    installer.install()

    logger.info('Finish')
    Progress.Finish()
=======
if __name__ == '__main__':
    Installer().install()
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
