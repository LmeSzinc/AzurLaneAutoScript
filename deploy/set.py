import sys
import typing as t

from deploy.utils import poor_yaml_read, poor_yaml_write, DEPLOY_TEMPLATE

"""
Set config/deploy.yaml with commands like

python -m deploy.set GitExecutable=/usr/bin/git PythonExecutable=/usr/bin/python3.8
"""


def get_args() -> t.Dict[str, str]:
    args = {}
    for arg in sys.argv[1:]:
        if '=' not in arg:
            continue
        k, v = arg.split('=')
        k, v = k.strip(), v.strip()
        args[k] = v
    return args


def config_set(output='./config/deploy.yaml'):
    data = poor_yaml_read(DEPLOY_TEMPLATE)
    data.update(poor_yaml_read(output))
    for k, v in get_args().items():
        if k in data:
            print(f'{k} set')
            data[k] = v
        else:
            print(f'{k} not exist')
    poor_yaml_write(data, file=output)


if __name__ == '__main__':
    config_set()
