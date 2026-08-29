"""Deploy template generation mixin (split from config_updater.py, Phase 5.1)."""
from copy import deepcopy

from deploy.utils import DEPLOY_TEMPLATE, poor_yaml_read, poor_yaml_write


class DeployTemplatesMixin:
    @staticmethod
    def generate_deploy_template():
        template = poor_yaml_read(DEPLOY_TEMPLATE)
        cn = {
            'Repository': 'git://git.lyoko.io/AzurLaneAutoScript',
            'PypiMirror': 'https://mirrors.aliyun.com/pypi/simple',
            'Language': 'zh-CN',
        }
        aidlux = {
            'GitExecutable': '/usr/bin/git',
            'AdbExecutable': '/usr/bin/adb',
        }

        docker = {
            'GitExecutable': '/usr/bin/git',
            'RequirementsFile': './deploy/docker/requirements.txt',
            'AdbExecutable': '/usr/bin/adb',
        }

        linux = {
            'GitExecutable': '/usr/bin/git',
            'AdbExecutable': '/usr/bin/adb',
            'SSHExecutable': '/usr/bin/ssh',
            'ReplaceAdb': 'false'
        }

        def update(suffix, *args):
            file = f'./config/deploy.{suffix}.yaml'
            new = deepcopy(template)
            for dic in args:
                new.update(dic)
            poor_yaml_write(data=new, file=file)

        update('template')
        update('template-cn', cn)
        update('template-AidLux', aidlux)
        update('template-AidLux-cn', aidlux, cn)
        update('template-docker', docker)
        update('template-docker-cn', docker, cn)
        update('template-linux', linux)
        update('template-linux-cn', linux, cn)
