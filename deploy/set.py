import sys
import typing as t

from deploy.Windows.utils import poor_yaml_read, poor_yaml_write, DEPLOY_TEMPLATE

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


def config_set(modify: t.Dict[str, str], output='./config/deploy.yaml') -> t.Dict[str, str]:
    """
    Args:
        modify: A dict of key-value in deploy.yaml
        output:

    Returns:
        The updated key-value in deploy.yaml
    """
    data = poor_yaml_read(DEPLOY_TEMPLATE)
    data.update(poor_yaml_read(output))
    for k, v in modify.items():
        if k in data:
            print(f'Key "{k}" set')
            data[k] = v
        else:
            print(f'Key "{k}" not exist')
    poor_yaml_write(data, file=output)
    return data


if __name__ == '__main__':
    config_set(get_args())
