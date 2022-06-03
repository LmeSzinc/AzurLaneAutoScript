import filecmp
import shutil

from deploy.config import DeployConfig
from deploy.utils import *


class AppManager(DeployConfig):
    @staticmethod
    def app_asar_replace(folder, path="./toolkit/WebApp/resources/app.asar"):
        """
        Args:
            folder (str): Path to AzurLaneAutoScript
            path (str): Path from AzurLaneAutoScript to app.asar

        Returns:
            bool: If updated.
        """
        source = os.path.abspath(os.path.join(folder, path))
        print(f"Old file: {source}")

        try:
            import alas_webapp
        except ImportError:
            print(f"Dependency alas_webapp not exists, skip updating")
            return False

        update = alas_webapp.app_file()
        print(f"New version: {alas_webapp.__version__}")
        print(f"New file: {update}")

        if os.path.exists(source):
            if filecmp.cmp(source, update, shallow=True):
                print("app.asar is already up to date")
                return False
            else:
                print(f"Copy {update} -----> {source}")
                os.remove(source)
                shutil.copy(update, source)
                return True
        else:
            print(f"{source} not exists, skip updating")
            return False

    def app_update(self):
        hr0(f"Update app.asar")

        if not self.bool("AutoUpdate"):
            print("AutoUpdate is disabled, skip")
            return False

        return self.app_asar_replace(os.getcwd())
