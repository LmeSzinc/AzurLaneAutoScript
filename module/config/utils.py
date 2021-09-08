import json
import os
from datetime import datetime, timedelta, timezone

import inflection
import yaml

import module.config.server as server

# LANGUAGES = ['zh-CN', 'en-US', 'zh-TW']
LANGUAGES = ['zh-CN']
FOLDER_CONFIG = './config'


def filepath_arg():
    return './module/config/args.yaml'


def filepath_db():
    return './module/config/args_db.yaml'


def filepath_config(filename):
    return os.path.join(FOLDER_CONFIG, filename + '.yaml')


def filepath_code():
    return './module/config/config_generated.py'


def read_file(file):
    """
    Read a file, support both .yaml and .json format.
    Return empty dict if file not exists.

    Args:
        file (str):

    Returns:
        dict, list:
    """
    print(f'read: {file}')
    folder = os.path.dirname(file)
    if not os.path.exists(folder):
        os.mkdir(folder)

    if not os.path.exists(file):
        return {}

    _, ext = os.path.splitext(file)
    if ext == '.yaml':
        with open(file, mode='r', encoding='utf-8') as f:
            s = f.read()
            data = list(yaml.safe_load_all(s))
            if len(data) == 1:
                data = data[0]
            return data
    elif ext == '.json':
        with open(file, mode='r', encoding='utf-8') as f:
            s = f.read()
            return json.loads(s)
    else:
        print(f'Unsupported config file extension: {ext}')
        return {}


def write_file(file, data):
    """
    Write data into a file, supports both .yaml and .json format.

    Args:
        file (str):
        data (dict, list):
    """
    print(f'write: {file}')
    folder = os.path.dirname(file)
    if not os.path.exists(folder):
        os.mkdir(folder)

    _, ext = os.path.splitext(file)
    if ext == '.yaml':
        with open(file, mode='w', encoding='utf-8') as f:
            if isinstance(data, list):
                yaml.safe_dump_all(data, f, default_flow_style=False, encoding='utf-8', allow_unicode=True,
                                   sort_keys=False)
            else:
                yaml.safe_dump(data, f, default_flow_style=False, encoding='utf-8', allow_unicode=True,
                               sort_keys=False)
    elif ext == '.json':
        with open(file, mode='w', encoding='utf-8') as f:
            s = json.dumps(data, indent=2, ensure_ascii=True, sort_keys=False, default=str)
            f.write(s)
    else:
        print(f'Unsupported config file extension: {ext}')


def iter_folder(folder, ext=None):
    """
    Args:
        folder (str):
        ext (str): File extension

    Yields:
        str: Absolute path of files
    """
    for file in os.listdir(folder):
        if ext is not None:
            _, extension = os.path.splitext(file)
            if extension == ext:
                yield os.path.join(folder, file)
        else:
            yield os.path.join(folder, file)


def deep_get(d, keys, default=None):
    """
    Get values in dictionary safely.
    https://stackoverflow.com/questions/25833613/safe-method-to-get-value-of-nested-dictionary

    Args:
        d (dict):
        keys (str, list): Such as `Scheduler.NextRun.value`
        default: Default return if key not found.

    Returns:

    """
    if isinstance(keys, str):
        keys = keys.split('.')
    assert type(keys) is list
    if d is None:
        return default
    if not keys:
        return d
    return deep_get(d.get(keys[0]), keys[1:], default)


def deep_set(d, keys, value):
    """
    Set value into dictionary safely, imitating deep_get().
    """
    if isinstance(keys, str):
        keys = keys.split('.')
    assert type(keys) is list
    if not keys:
        return value
    if not isinstance(d, dict):
        d = {}
    d[keys[0]] = deep_set(d.get(keys[0], {}), keys[1:], value)
    return d


def deep_default(d, keys, value):
    """
    Set default value into dictionary safely, imitating deep_get().
    Value is set only when the dict doesn't contain such keys.
    """
    if isinstance(keys, str):
        keys = keys.split('.')
    assert type(keys) is list
    if not keys:
        if d:
            return d
        else:
            return value
    if not isinstance(d, dict):
        d = {}
    d[keys[0]] = deep_default(d.get(keys[0], {}), keys[1:], value)
    return d


def path_to_arg(string):
    """
    Convert dictionary keys in .yaml files to argument names in config.

    Args:
        string (str): Such as `Scheduler.ServerUpdate`

    Returns:
        str: Such as `SCHEDULER__SERVER_UPDATE`
    """
    return inflection.underscore(string.replace('.', '__')).upper()


def dict_to_kv(dictionary):
    """
    Args:
        dictionary: Such as `{'path': 'Scheduler.ServerUpdate', 'value': True}`

    Returns:
        str: Such as `path='Scheduler.ServerUpdate', value=True`
    """
    return ', '.join([f'{k}={repr(v)}' for k, v in dictionary.items()])


def server_timezone():
    if server.server == 'en':
        return -7
    elif server.server == 'cn':
        return 8
    elif server.server == 'jp':
        return 9
    elif server.server == 'tw':
        return 8
    else:
        return 8


def get_server_next_update(daily_trigger):
    """
    Args:
        daily_trigger (list[str], str): [ "00:00", "12:00", "18:00",]

    Returns:
        datetime.datetime
    """
    if isinstance(daily_trigger, str):
        daily_trigger = daily_trigger.replace(' ', '').split(',')
    d = datetime.now(timezone.utc).astimezone()
    diff = d.utcoffset() // timedelta(seconds=1) // 3600 - server_timezone()
    trigger = []
    for t in daily_trigger:
        h, m = [int(x) for x in t.split(':')]
        h = (h + diff) % 24
        future = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        future = future + timedelta(days=1) if future < datetime.now() else future
        trigger.append(future)
    update = sorted(trigger)[0]
    return update
