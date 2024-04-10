import filecmp
import os
import shutil

from deploy.Windows.config import DeployConfig
from deploy.Windows.logger import Progress, logger


class AppManager(DeployConfig):
    @staticmethod
    def app_asar_replace(folder, path='./toolkit/WebApp/resources/app.asar'):
        """
        Args:
            folder (str): Path to AzurLaneAutoScript
            path (str): Path from AzurLaneAutoScript to app.asar

        Returns:
            bool: If updated.
        """
        source = os.path.abspath(os.path.join(folder, path))
        logger.info(f'Old file: {source}')

        try:
            import alas_webapp
        except ImportError:
            logger.info(f'Dependency alas_webapp not exists, skip updating')
            return False

        update = alas_webapp.app_file()
        logger.info(f'New version: {alas_webapp.__version__}')
        logger.info(f'New file: {update}')

        if os.path.exists(source):
            if filecmp.cmp(source, update, shallow=True):
                logger.info('app.asar is already up to date')
                return False
            else:
                # Keyword "Update app.asar" is used in AlasApp
                # to determine whether there is a hot update
                logger.info(f'Update app.asar {update} -----> {source}')
                os.remove(source)
                shutil.copy(update, source)
                return True
        else:
            logger.info(f'{source} not exists, skip updating')
            return False

    def app_update(self):
        logger.hr(f'Update app', 0)

        if not self.AppAsarUpdate:
            logger.info('AppAsarUpdate is disabled, skip')
            Progress.UpdateAlasApp()
            return False

        # self.app_asar_replace(os.getcwd())
        # Progress.UpdateAlasApp()
