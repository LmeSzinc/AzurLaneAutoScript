import logging
from urllib.parse import urlparse

from deploy.emulator import *
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
        hr0('Show deploy config')
        for k, v in self.config.items():
            if k in ('Password', 'ApiToken'):
                continue
            print(f'{k}: {v}')

    def read(self):
        self.config = poor_yaml_read(DEPLOY_TEMPLATE)
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
        return os.path.abspath(os.path.join(self.root_filepath, self.config[key])) \
            .replace(r'\\', '/').replace('\\', '/').replace('\"', '"')

    @cached_property
    def root_filepath(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../')) \
            .replace(r'\\', '/').replace('\\', '/').replace('\"', '"')

    @staticmethod
    def to_bool(value):
        value = value.lower()
        if value == 'null' or value == 'false' or value == '':
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
        command = command.replace(r'\\', '/').replace('\\', '/').replace('\"', '"')
        print(command)
        error_code = os.system(command)
        if error_code:
            if allow_failure:
                print(f'[ allowed failure ], error_code: {error_code}')
                return False
            else:
                print(f'[ failure ], error_code: {error_code}')
                self.show_error()
                raise ExecutionError
        else:
            print(f'[ success ]')
            return True

    def execute_output(self, command) -> str:
        command = command.replace(
            r'\\', '/').replace('\\', '/').replace('\"', '"')
        log = subprocess.run(command, capture_output=True, text=True).stdout
        return log

    def show_error(self):
        self.show_config()
        print('')
        hr1('Update failed')
        print('Please check your deploy settings in config/deploy.yaml '
              'and re-open Alas.exe')


class GitManager(DeployConfig):
    @cached_property
    def git(self):
        return self.filepath('GitExecutable')

    def git_repository_init(self, repo, source='origin', branch='master', proxy='', keep_changes=False):
        hr1('Git Init')
        self.execute(f'"{self.git}" init')

        hr1('Set Git Proxy')
        if self.to_bool(proxy):
            self.execute(f'"{self.git}" config --local http.proxy {proxy}')
            self.execute(f'"{self.git}" config --local https.proxy {proxy}')
        else:
            self.execute(f'"{self.git}" config --local --unset http.proxy', allow_failure=True)
            self.execute(f'"{self.git}" config --local --unset https.proxy', allow_failure=True)

        hr1('Set Git Repository')
        if not self.execute(f'"{self.git}" remote set-url {source} {repo}', allow_failure=True):
            self.execute(f'"{self.git}" remote add {source} {repo}')

        hr1('Fetch Repository Branch')
        self.execute(f'"{self.git}" fetch {source} {branch}')

        hr1('Pull Repository Branch')
        if keep_changes:
            if self.execute(f'"{self.git}" stash', allow_failure=True):
                self.execute(f'"{self.git}" pull --ff-only {source} {branch}')
                if self.execute(f'"{self.git}" stash pop', allow_failure=True):
                    pass
                else:
                    # No local changes to existing files, untracked files not included
                    print('Stash pop failed, there seems to be no local changes, skip instead')
            else:
                print('Stash failed, this may be the first installation, drop changes instead')
                self.execute(f'"{self.git}" reset --hard {source}/{branch}')
                self.execute(f'"{self.git}" pull --ff-only {source} {branch}')
        else:
            self.execute(f'"{self.git}" reset --hard {source}/{branch}')
            self.execute(f'"{self.git}" pull --ff-only {source} {branch}')

        hr1('Show Version')
        self.execute(f'"{self.git}" log --no-merges -1')

    def git_install(self):
        hr0('Update Alas')

        if not self.bool('AutoUpdate'):
            print('AutoUpdate is disabled, skip')
            return

        self.git_repository_init(
            repo=self.config['Repository'],
            source='origin',
            branch=self.config['Branch'],
            proxy=self.config['GitProxy'],
            keep_changes=self.bool('KeepLocalChanges')
        )


class PipManager(DeployConfig):
    @cached_property
    def python(self):
        return self.filepath("PythonExecutable")

    @cached_property
    def pip(self):
        return f'"{self.python}" -m pip'

    def pip_install(self):
        hr0('Update Dependencies')

        if not self.bool('InstallDependencies'):
            print('InstallDependencies is disabled, skip')
            return

        hr1('Check Python')
        self.execute(f'"{self.python}" --version')

        arg = []
        if self.bool('PypiMirror'):
            mirror = self.config['PypiMirror']
            arg += ['-i', mirror]
            # Trust http mirror
            if 'http:' in mirror:
                arg += ['--trusted-host', urlparse(mirror).hostname]

        # Don't update pip, just leave it.
        # hr1('Update pip')
        # self.execute(f'"{self.pip}" install --upgrade pip{arg}')
        arg += ['--disable-pip-version-check']

        hr1('Update Dependencies')
        arg = ' ' + ' '.join(arg) if arg else ''
        self.execute(f'"{self.pip}" install -r requirements.txt{arg}')


class AdbManager(DeployConfig):
    @cached_property
    def adb(self):
        return self.filepath('AdbExecutable')

    def adb_install(self):
        hr0('Start ADB service')

        emulator = EmulatorConnect(adb=self.adb)
        if self.bool('ReplaceAdb'):
            hr1('Replace ADB')
            emulator.adb_replace()
        elif self.bool('AutoConnect'):
            hr1('ADB Connect')
            emulator.brute_force_connect()

        if self.bool('InstallUiautomator2'):
            hr1('Uiautomator2 Init')
            from uiautomator2.init import Initer
            import adbutils
            for device in adbutils.adb.iter_device():
                init = Initer(device, loglevel=logging.DEBUG)
                init.set_atx_agent_addr('127.0.0.1:7912')
                init.install()
                init._device.shell(["rm", "/data/local/tmp/minicap"])
                init._device.shell(["rm", "/data/local/tmp/minicap.so"])


class AppManager(DeployConfig):
    def app_asar_replace(self, folder, path='./toolkit/WebApp/resources/app.asar'):
        """
        Args:
            folder (str): Path to AzurLaneAutoScript
            path (str): Path from AzurLaneAutoScript to app.asar

        Returns:
            bool: If updated.
        """
        source = os.path.abspath(os.path.join(folder, path))
        print(f'Old file: {source}')

        try:
            import alas_webapp
        except ImportError:
            print(f'Dependency alas_webapp not exists, skip updating')
            return False

        update = alas_webapp.app_file()
        print(f'New version: {alas_webapp.__version__}')
        print(f'New file: {update}')

        if os.path.exists(source):
            if filecmp.cmp(source, update, shallow=True):
                print('app.asar is already up to date')
                return False
            else:
                print(f'Copy {update} -----> {source}')
                os.remove(source)
                shutil.copy(update, source)
                return True
        else:
            print(f'{source} not exists, skip updating')
            return False

    def app_update(self):
        hr0(f'Update app.asar')

        if not self.bool('AutoUpdate'):
            print('AutoUpdate is disabled, skip')
            return False

        return self.app_asar_replace(os.getcwd())


class AlasManager(DeployConfig):
    @cached_property
    def alas_folder(self):
        return [
            self.filepath("PythonExecutable"),
            self.root_filepath
        ]

    @cached_property
    def self_pid(self):
        return str(os.getpid())

    def iter_process_by_name(self, name):
        """
        Args:
            name (str): process name, such as 'alas.exe'

        Yields:
            str, str, str: executable_path, process_name, process_id
        """
        try:
            rows = self.execute_output(f'wmic process where name="{name}" get processid,executablepath,name')
        except (UnicodeDecodeError, IndexError):
            print(f'No {name} found')
            return False

        rows = rows.replace(r'\\', '/').replace('\\', '/').replace('\"', '"').replace('\r', '')
        for row in rows.split('\n'):
            if not row or 'ExecutablePath' in row:
                continue
            try:
                executable_path, process_name, process_id = [x for x in row.split(' ') if len(x)]
            except ValueError:
                print(f'Unable to parse {row}')
                continue

            for folder in self.alas_folder:
                if folder in executable_path and process_name == name and process_id != self.self_pid:
                    yield executable_path, process_name, process_id

    def kill_by_name(self, name):
        """
        Args:
            name (str): Process name
        """
        hr1(f'Kill {name}')
        for row in self.iter_process_by_name(name):
            print(' '.join(row))
            self.execute(f'taskkill /f /pid {row[2]}', allow_failure=True)

    def alas_kill(self):
        hr0(f'Kill existing Alas')
        self.kill_by_name('alas.exe')
        self.kill_by_name('python.exe')


class Installer(GitManager, PipManager, AdbManager, AppManager, AlasManager):
    def install(self):
        try:
            self.alas_kill()
            self.git_install()
            self.pip_install()
            self.app_update()
            self.adb_install()
        except ExecutionError:
            exit(1)


if __name__ == '__main__':
    Installer().install()
