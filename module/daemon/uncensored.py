from deploy.git import GitManager
from deploy.utils import *
from module.handler.login import LoginHandler
from module.logger import logger


class AzurLaneUncensored(LoginHandler):
    def run(self):
        """
        This will do:
        1. Update AzurLaneUncensored repo
        2. Adb push to emulator
        3. Restart game
        """
        repo = self.config.AzurLaneUncensored_Repository
        folder = './toolkit/AzurLaneUncensored'

        logger.hr('Update AzurLaneUncensored', level=1)
        logger.info('This will take a while at first use')
        manager = GitManager()
        manager.config['GitExecutable'] = os.path.abspath(manager.config['GitExecutable'])
        manager.config['AdbExecutable'] = os.path.abspath(manager.config['AdbExecutable'])
        os.makedirs(folder, exist_ok=True)
        prev = os.getcwd()

        # Running in ./toolkit/AzurLaneUncensored
        os.chdir(folder)
        # Monkey patch `print()` build-in to show logs.
        manager.git_repository_init(
            repo=repo,
            source='origin',
            branch='master',
            proxy=manager.config['GitProxy'],
            keep_changes=False
        )

        logger.hr('Push Uncensored Files', level=1)
        logger.info('This will take a few seconds')
        command = ['push', 'files', f'/sdcard/Android/data/{self.device.package}']
        logger.info(f'Command: {command}')
        self.device.adb_command(command, timeout=30)
        logger.info('Push success')

        # Back to root folder
        os.chdir(prev)
        logger.hr('Restart AzurLane', level=1)
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()

        logger.info('Uncensored Finished')


if __name__ == '__main__':
    AzurLaneUncensored('alas', task='AzurLaneUncensored').run()
