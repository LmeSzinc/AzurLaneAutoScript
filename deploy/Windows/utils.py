import os
import re
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")

DEPLOY_CONFIG = './config/deploy.yaml'
DEPLOY_TEMPLATE = './deploy/Windows/template.yaml'


class cached_property(Generic[T]):
    """
    cached-property from https://github.com/pydanny/cached-property
    Add typing support

    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func: Callable[..., T]):
        self.func = func

    def __get__(self, obj, cls) -> T:
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


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


def poor_yaml_read(file):
    """
    Poor implementation to load yaml without pyyaml dependency, but with re

    Args:
        file (str):

    Returns:
        dict:
    """
    if not os.path.exists(file):
        return {}

    data = {}
    regex = re.compile(r'^(.*?):(.*?)$')
    with open(file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip('\n\r\t ').replace('\\', '/')
            if line.startswith('#'):
                continue
            result = re.match(regex, line)
            if result:
                k, v = result.group(1), result.group(2).strip('\n\r\t\' ')
                if v:
                    if v.lower() == 'null':
                        v = None
                    elif v.lower() == 'false':
                        v = False
                    elif v.lower() == 'true':
                        v = True
                    elif v.isdigit():
                        v = int(v)
                    data[k] = v

    return data


def poor_yaml_write(data, file, template_file=DEPLOY_TEMPLATE):
    """
    Args:
        data (dict):
        file (str):
        template_file (str):
    """
    with open(template_file, 'r', encoding='utf-8') as f:
        text = f.read().replace('\\', '/')

    for key, value in data.items():
        if value is None:
            value = 'null'
        elif value is True:
            value = "true"
        elif value is False:
            value = "false"
        text = re.sub(f'{key}:.*?\n', f'{key}: {value}\n', text)

    with open(file, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


@dataclass
class DataProcessInfo:
    proc: object  # psutil.Process or psutil._pswindows.Process
    pid: int

    @cached_property
    def name(self):
        try:
            name = self.proc.name()
        except:
            name = ''
        return name

    @cached_property
    def cmdline(self):
        try:
            cmdline = self.proc.cmdline()
        except:
            # psutil.AccessDenied
            # # NoSuchProcess: process no longer exists (pid=xxx)
            cmdline = []
        cmdline = ' '.join(cmdline).replace(r'\\', '/').replace('\\', '/')
        return cmdline

    def __str__(self):
        # Don't print `proc`, it will take some time to get process properties
        return f'DataProcessInfo(name="{self.name}", pid={self.pid}, cmdline="{self.cmdline}")'

    __repr__ = __str__


def iter_process() -> Iterable[DataProcessInfo]:
    try:
        import psutil
    except ModuleNotFoundError:
        return

    if psutil.WINDOWS:
        # Since this is a one-time-usage, we access psutil._psplatform.Process directly
        # to bypass the call of psutil.Process.is_running().
        # This only costs about 0.017s.
        for pid in psutil.pids():
            proc = psutil._psplatform.Process(pid)
            yield DataProcessInfo(
                proc=proc,
                pid=proc.pid,
            )
    else:
        # This will cost about 0.45s, even `attr` is given.
        for proc in psutil.process_iter():
            yield DataProcessInfo(
                proc=proc,
                pid=proc.pid,
            )
