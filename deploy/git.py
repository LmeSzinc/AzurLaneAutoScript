from deploy.config import DeployConfig
from deploy.utils import *


class GitManager(DeployConfig):
    @cached_property
    def git(self):
        return self.filepath('GitExecutable')

    def git_repository_init(self, repo, source='origin', branch='master', proxy='', keep_changes=False):
        hr1('Git Init')
        self.execute(f'"{self.git}" init')

        hr1('Set Git Proxy')
        if proxy:
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
        # Remove git lock
        lock_file = './.git/index.lock'
        if os.path.exists(lock_file):
            print(f'Lock file {lock_file} exists, removing')
            os.remove(lock_file)
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

        if not self.AutoUpdate:
            print('AutoUpdate is disabled, skip')
            return

        self.git_repository_init(
            repo=self.Repository,
            source='origin',
            branch=self.Branch,
            proxy=self.GitProxy,
            keep_changes=self.KeepLocalChanges,
        )
