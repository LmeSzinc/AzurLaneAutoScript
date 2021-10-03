import ctypes

from module.webui.widgets import *
import threading

from pywebio.output import *
from pywebio.pin import *
from pywebio.session import run_js

class QueueHandler:
    def __init__(self, q) -> None:
        self.queue = q

    def write(self, s:str):
        if s.endswith('\n'):
            s = s[:-1]

        # reduce log length by cutting off the date.
        self.queue.put(s[11:] + '\n')

class thread_with_exception(threading.Thread):
    # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)

    def _get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self._get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

def filepath_css(filename):
    return f'./assets/gui/css/{filename}.css'

def filepath_icon(filename):
    return f'./assets/gui/icon/{filename}.svg'

def add_css(filepath):
    with open(filepath, "r") as f:
        css = f.read().replace('\n', '')
        run_js(f"""$('head').append('<style>{css}</style>')""")

def _read(path):
    with open(path, 'r') as f:
        return f.read()

class Icon:
    """
    Storage html of icon.
    """
    ALAS = _read(filepath_icon('alas'))
    SETTING = _read(filepath_icon('setting'))
    INSTALL = _read(filepath_icon('install'))
    RUN = _read(filepath_icon('run'))
    DEVELOP = _read(filepath_icon('develop'))
    PERFORMANCE =_read(filepath_icon('performance'))


def get_output(type, name, title, help=None, value=None, options=None, width="12rem"):
    if type == 'input':
        return put_input_(name, title, help, value, width)
    elif type == 'select':
        return put_select_(name, title, help, options, width)
    elif type == 'textarea':
        return put_textarea_(name, title, help, value)
    elif type == 'checkbox':
        return put_checkbox_(name, title, help, value, width)
    elif type == 'disable':
        return put_input_(name, title, help, value, width, readonly=True)

def parse_pin_value(val):
    """
    input, textarea return str
    select return its option (str or int)
    checkbox return [] or [True] (define in put_checkbox_)
    """
    if isinstance(val, list):
        if len(val) == 0:
            return False
        else:
            return True
    elif isinstance(val, (int, float)):
        return val
    else:
        try:
            v = float(val)
        except:
            return val
        if v.is_integer():
            return int(v)
        else:
            return v