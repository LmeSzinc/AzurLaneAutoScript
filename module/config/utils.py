import json
import random
import string
from datetime import datetime, timedelta, timezone

import yaml

import module.config.server as server_
from deploy.atomic import atomic_read_text, atomic_read_bytes, atomic_write
from module.submodule.utils import *

LANGUAGES = ['zh-CN', 'en-US', 'ja-JP', 'zh-TW']
SERVER_TO_LANG = {
    'cn': 'zh-CN',
    'en': 'en-US',
    'jp': 'ja-JP',
    'tw': 'zh-TW',
}
LANG_TO_SERVER = {v: k for k, v in SERVER_TO_LANG.items()}
SERVER_TO_TIMEZONE = {
    'cn': timedelta(hours=8),
    'en': timedelta(hours=-7),
    'jp': timedelta(hours=9),
    'tw': timedelta(hours=8),
}
DEFAULT_TIME = datetime(2020, 1, 1, 0, 0)


# https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data/15423007
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def filepath_args(filename='args', mod_name='alas'):
    if mod_name == 'alas':
        return f'./module/config/argument/{filename}.json'
    else:
        return os.path.join(get_mod_filepath(mod_name), f'./module/config/argument/{filename}.json')


def filepath_argument(filename):
    return f'./module/config/argument/{filename}.yaml'


def filepath_i18n(lang, mod_name='alas'):
    if mod_name == 'alas':
        return os.path.join('./module/config/i18n', f'{lang}.json')
    else:
        return os.path.join(get_mod_filepath(mod_name), './module/config/i18n', f'{lang}.json')


def filepath_config(filename, mod_name='alas'):
    if mod_name == 'alas':
        return os.path.join('./config', f'{filename}.json')
    else:
        return os.path.join('./config', f'{filename}.{mod_name}.json')


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
    if file.endswith('.json'):
        content = atomic_read_bytes(file)
        if not content:
            return {}
        return json.loads(content)
    elif file.endswith('.yaml'):
        content = atomic_read_text(file)
        data = list(yaml.safe_load_all(content))
        if len(data) == 1:
            data = data[0]
        if not data:
            data = {}
        return data
    else:
        print(f'Unsupported config file extension: {file}')
        return {}


def write_file(file, data):
    """
    Write data into a file, supports both .yaml and .json format.

    Args:
        file (str):
        data (dict, list):
    """
    print(f'write: {file}')
    if file.endswith('.json'):
        content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False, default=str)
        atomic_write(file, content)
    elif file.endswith('.yaml'):
        if isinstance(data, list):
            content = yaml.safe_dump_all(
                data, default_flow_style=False, encoding='utf-8', allow_unicode=True, sort_keys=False)
        else:
            content = yaml.safe_dump(
                data, default_flow_style=False, encoding='utf-8', allow_unicode=True, sort_keys=False)
        atomic_write(file, content)
    else:
        print(f'Unsupported config file extension: {file}')


def iter_folder(folder, is_dir=False, ext=None):
    """
    Args:
        folder (str):
        is_dir (bool): True to iter directories only
        ext (str): File extension, such as `.yaml`

    Yields:
        str: Absolute path of files
    """
    for file in os.listdir(folder):
        sub = os.path.join(folder, file)
        if is_dir:
            if os.path.isdir(sub):
                yield sub.replace('\\\\', '/').replace('\\', '/')
        elif ext is not None:
            if not os.path.isdir(sub):
                _, extension = os.path.splitext(file)
                if extension == ext:
                    yield os.path.join(folder, file).replace('\\\\', '/').replace('\\', '/')
        else:
            yield os.path.join(folder, file).replace('\\\\', '/').replace('\\', '/')


def alas_template():
    """
        Returns:
            list[str]: Name of all Alas instances, except `template`.
        """
    out = []
    for file in os.listdir('./config'):
        name, extension = os.path.splitext(file)
        if name == 'template' and extension == '.json':
            out.append(f'{name}-alas')

    out.extend(list_mod_template())

    return out


def alas_instance():
    """
    Returns:
        list[str]: Name of all Alas instances, except `template`.
    """
    out = []
    for file in os.listdir('./config'):
        name, extension = os.path.splitext(file)
        config_name, mod_name = os.path.splitext(name)
        mod_name = mod_name[1:]
        if name != 'template' and extension == '.json' and mod_name == '':
            out.append(name)

    out.extend(list_mod_instance())

    if not len(out):
        out = ['alas']

    return out


def parse_value(value, data):
    """
    Convert a string to float, int, datetime, if possible.

    Args:
        value (str):
        data (dict):

    Returns:

    """
    if 'option' in data:
        if value not in data['option']:
            return data['value']
    if isinstance(value, str):
        if value == '':
            return None
        if value == 'true' or value == 'True':
            return True
        if value == 'false' or value == 'False':
            return False
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


def data_to_type(data, **kwargs):
    """
    | Condition                            | Type     |
    | ------------------------------------ | -------- |
    | Value is bool                        | checkbox |
    | Arg has options                      | select   |
    | `Filter` is in name (in data['arg']) | textarea |
    | Rest of the args                     | input    |

    Args:
        data (dict):
        kwargs: Any additional properties

    Returns:
        str:
    """
    kwargs.update(data)
    if isinstance(kwargs['value'], bool):
        return 'checkbox'
    elif 'option' in kwargs and kwargs['option']:
        return 'select'
    elif 'Filter' in kwargs['arg']:
        return 'textarea'
    else:
        return 'input'


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


def server_timezone() -> timedelta:
    return SERVER_TO_TIMEZONE.get(server_.server, SERVER_TO_TIMEZONE['cn'])


def server_time_offset() -> timedelta:
    """
    To convert local time to server time:
        server_time = local_time + server_time_offset()
    To convert server time to local time:
        local_time = server_time - server_time_offset()
    """
    return datetime.now(timezone.utc).astimezone().utcoffset() - server_timezone()


def random_normal_distribution_int(a, b, n=3):
    """
    A non-numpy implementation of the `random_normal_distribution_int` in module.base.utils


    Generate a normal distribution int within the interval.
    Use the average value of several random numbers to
    simulate normal distribution.

    Args:
        a (int): The minimum of the interval.
        b (int): The maximum of the interval.
        n (int): The amount of numbers in simulation. Default to 3.

    Returns:
        int
    """
    if a < b:
        output = sum([random.randint(a, b) for _ in range(n)]) / n
        return int(round(output))
    else:
        return b


def ensure_time(second, n=3, precision=3):
    """Ensure to be time.

    Args:
        second (int, float, tuple): time, such as 10, (10, 30), '10, 30'
        n (int): The amount of numbers in simulation. Default to 5.
        precision (int): Decimals.

    Returns:
        float:
    """
    if isinstance(second, tuple):
        multiply = 10 ** precision
        return random_normal_distribution_int(second[0] * multiply, second[1] * multiply, n) / multiply
    elif isinstance(second, str):
        if ',' in second:
            lower, upper = second.replace(' ', '').split(',')
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        if '-' in second:
            lower, upper = second.replace(' ', '').split('-')
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        else:
            return int(second)
    else:
        return second


def get_os_next_reset():
    """
    Get the first day of next month.

    Returns:
        datetime.datetime
    """
    diff = server_time_offset()
    server_now = datetime.now() - diff
    server_reset = (server_now.replace(day=1) + timedelta(days=32)) \
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    local_reset = server_reset + diff
    return local_reset


def get_os_reset_remain():
    """
    Returns:
        int: number of days before next opsi reset
    """
    from module.logger import logger

    next_reset = get_os_next_reset()
    now = datetime.now()
    logger.attr('OpsiNextReset', next_reset)

    remain = int((next_reset - now).total_seconds() // 86400)
    logger.attr('ResetRemain', remain)
    return remain


def get_server_next_update(daily_trigger):
    """
    Args:
        daily_trigger (list[str], str): [ "00:00", "12:00", "18:00",]

    Returns:
        datetime.datetime
    """
    if isinstance(daily_trigger, str):
        daily_trigger = daily_trigger.replace(' ', '').split(',')

    diff = server_time_offset()
    local_now = datetime.now()
    trigger = []
    for t in daily_trigger:
        h, m = [int(x) for x in t.split(':')]
        future = local_now.replace(hour=h, minute=m, second=0, microsecond=0) + diff
        s = (future - local_now).total_seconds() % 86400
        future = local_now + timedelta(seconds=s)
        trigger.append(future)
    update = sorted(trigger)[0]
    return update


def get_server_last_update(daily_trigger):
    """
    Args:
        daily_trigger (list[str], str): [ "00:00", "12:00", "18:00",]

    Returns:
        datetime.datetime
    """
    if isinstance(daily_trigger, str):
        daily_trigger = daily_trigger.replace(' ', '').split(',')

    diff = server_time_offset()
    local_now = datetime.now()
    trigger = []
    for t in daily_trigger:
        h, m = [int(x) for x in t.split(':')]
        future = local_now.replace(hour=h, minute=m, second=0, microsecond=0) + diff
        s = (future - local_now).total_seconds() % 86400 - 86400
        future = local_now + timedelta(seconds=s)
        trigger.append(future)
    update = sorted(trigger)[-1]
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


def get_nearest_weekday_date(target):
    """
    Get nearest weekday date starting
    from current date

    Args:
        target (int): target weekday to
                      calculate

    Returns:
        datetime.datetime
    """
    diff = server_time_offset()
    server_now = datetime.now() - diff

    days_ahead = target - server_now.weekday()
    if days_ahead <= 0:
        # Target day has already happened
        days_ahead += 7
    server_reset = (server_now + timedelta(days=days_ahead)) \
        .replace(hour=0, minute=0, second=0, microsecond=0)

    local_reset = server_reset + diff
    return local_reset


def get_server_weekday():
    """
    Returns:
        int: The server's current day of the week
    """
    diff = server_time_offset()
    server_now = datetime.now() - diff
    result = server_now.weekday()
    return result


def get_server_monthday():
    """
    Returns:
        int: The server's current day of the month
    """
    diff = server_time_offset()
    server_now = datetime.now() - diff
    result = server_now.day
    return result


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


def type_to_str(typ):
    """
    Convert any types or any objects to a string。
    Remove <> to prevent them from being parsed as HTML tags.

    Args:
        typ:

    Returns:
        str: Such as `int`, 'datetime.datetime'.
    """
    if not isinstance(typ, type):
        typ = type(typ).__name__
    return str(typ)


if __name__ == '__main__':
    get_os_reset_remain()
