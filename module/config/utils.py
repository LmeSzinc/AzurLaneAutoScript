import json
import os
import random
import string
from datetime import datetime, timedelta, timezone

import yaml
from tinydb import where

import module.config.server as server

LANGUAGES = ['zh-CN', 'en-US', 'zh-TW']


# LANGUAGES = ['zh-CN']


# https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data/15423007
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def filepath_arg():
    return './module/config/args.yaml'


def filepath_db(lang):
    return os.path.join('./module/config/storage', f'{lang}.yaml')


def filepath_config(filename):
    return os.path.join('./config', f'{filename}.yaml')


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


def parse_value(value, data):
    """
    Convert a string to float, int, datetime, if possible.

    Args:
        value (str):
        data (dict):

    Returns:

    """
    option = data['option']
    if option:
        if value not in option:
            return data['value']
    if isinstance(value, str):
        if value == '':
            return None
        if '.' in value:
            try:
                return float(value)
            except ValueError:
                pass
        else:
            try:
                return int(value)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

    return value


def data_to_type(data):
    """
    | Condition                            | Type     |
    | ------------------------------------ | -------- |
    | Value is bool                        | checkbox |
    | Arg has options                      | select   |
    | `Filter` is in name (in data['arg']) | textarea |
    | Rest of the args                     | input    |

    Args:
        data (dict):

    Returns:
        str:
    """
    if isinstance(data['value'], bool):
        return 'checkbox'
    elif data['option']:
        return 'select'
    elif 'Filter' in data['arg']:
        return 'textarea'
    else:
        return 'input'


def request_to_query(request):
    """
    Converts a request in dict to TinyDB query conditions.

    Args:
        request (dict):

    Returns:

    """
    func = request.get('func', None)
    group = request.get('group', None)
    arg = request.get('arg', None)
    lang = request.get('lang', None)

    query = None
    if func:
        query = where('func') == func if query is None else query & (where('func') == func)
    if group:
        query = where('group') == group if query is None else query & (where('group') == group)
    if arg:
        query = where('arg') == arg if query is None else query & (where('arg') == arg)
    if lang:
        query = where('lang') == lang if query is None else query & (where('lang') == lang)

    return query


def data_to_path(data):
    """
    Args:
        data (dict):

    Returns:
        str: <func>.<group>.<arg>
    """
    return '.'.join([data.get(attr, '') for attr in ['func', 'group', 'arg']])


def path_to_arg(path):
    """
    Convert dictionary keys in .yaml files to argument names in config.

    Args:
        path (str): Such as `Scheduler.ServerUpdate`

    Returns:
        str: Such as `Scheduler_ServerUpdate`
    """
    return path.replace('.', '_')


def dict_to_kv(dictionary, allow_none=True):
    """
    Args:
        dictionary: Such as `{'path': 'Scheduler.ServerUpdate', 'value': True}`
        allow_none (bool):

    Returns:
        str: Such as `path='Scheduler.ServerUpdate', value=True`
    """
    return ', '.join([f'{k}={repr(v)}' for k, v in dictionary.items() if allow_none or v is not None])


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


def nearest_future(future, interval=120):
    """
    Get the neatest future time.
    Return the last one if two things will finish within `interval`.

    Args:
        future (list[datetime.datetime]):
        interval (int): Seconds

    Returns:
        datetime.datetime:
    """
    future = [datetime.fromisoformat(f) if isinstance(f, str) else f for f in future]
    future = sorted(future)
    next_run = future[0]
    for finish in future:
        if finish - next_run < timedelta(seconds=interval):
            next_run = finish

    return next_run


def random_id(length=32):
    """
    Args:
        length (int):

    Returns:
        str: Random azurstat id.
    """
    return ''.join(random.sample(string.ascii_lowercase + string.digits, length))


def to_list(text, length=1):
    """
    Args:
        text (str): Such as `1, 2, 3`
        length (int): If there's only one digit, return a list expanded to given length,
            i.e. text='3', length=5, returns `[3, 3, 3, 3, 3]`

    Returns:
        list[int]:
    """
    if text.isdigit():
        return [int(text)] * length
    out = [int(letter.strip()) for letter in text.split(',')]
    return out
