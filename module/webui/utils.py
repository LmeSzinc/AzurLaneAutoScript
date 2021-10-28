import ctypes
import operator
import threading
import time
from typing import Generator

from module.logger import logger
from module.webui.widgets import *
from pywebio.input import PASSWORD, input
from pywebio.session import register_thread, run_js


class QueueHandler:
    def __init__(self, q) -> None:
        self.queue = q

    def write(self, s: str):
        if s.endswith('\n'):
            s = s[:-1]

        # reduce log length by cutting off the date.
        self.queue.put(s[11:] + '\n')


class Thread(threading.Thread):
    # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    def __init__(self, target=..., *args, **kwargs):
        threading.Thread.__init__(self, target=target, *args, **kwargs)

    def _get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for thd_id, thread in threading._active.items():
            if thread is self:
                return thd_id

    def stop(self):
        thread_id = self._get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


class Task:
    def __init__(self, g: Generator, delay: float, next_run: float = None) -> None:
        self.g = g
        self.delay = delay
        self.next_run = next_run if next_run else time.time()

    def __str__(self) -> str:
        return f'<{self.g.__name__} (delay={self.delay})>'

    def __next__(self) -> None:
        return next(self.g)

    __repr__ = __str__


class TaskHandler:
    def __init__(self) -> None:
        # List of background running task
        self.tasks: List[Task] = []
        # List of task name to be removed
        self.pending_remove_tasks: List[Task] = []
        # Task running thread
        self._thread = Thread()
        self._lock = threading.Lock()

    def add(self, g: Generator, delay: float, pending_delete: bool = False) -> None:
        """
        Add a task running background.
        Another way of `self.add_task()`.
        """
        self.add_task(Task(g, delay), pending_delete=pending_delete)

    def add_task(self, task: Task, pending_delete: bool = False) -> None:
        """
        Add a task running background.
        """
        if task in self.tasks:
            logger.warning(f"Task {task} already in tasks list.")
            return
        logger.info(f"Add task {task}")
        with self._lock:
            self.tasks.append(task)
        if pending_delete:
            self.pending_remove_tasks.append(task)

    def _remove_task(self, task: Task) -> None:
        if task in self.tasks:
            self.tasks.remove(task)
            logger.info(f"Task {task} removed.")
        else:
            logger.warning(
                f"Failed to remove task {task}. Current tasks list: {self.tasks}")

    def remove_task(self, task: Task, nowait: bool = False) -> None:
        """
        Remove a task in `self.tasks`.
        Args:
            task:
            nowait: if True, remove it right now, 
                    otherwise remove when call `self.remove_pending_task`
        """
        if nowait:
            with self._lock:
                self._remove_task(task)
        else:
            self.pending_remove_tasks.append(task)

    def remove_pending_task(self) -> None:
        """
        Remove all pending remove tasks.
        """
        with self._lock:
            for task in self.pending_remove_tasks:
                self._remove_task(task)
            self.pending_remove_tasks = []

    def loop(self) -> None:
        """
        Start task loop.
        You **should** run this function in an individual thread.
        """
        while True:
            if self.tasks:
                with self._lock:
                    self.tasks.sort(key=operator.attrgetter('next_run'))
                    task = self.tasks[0]
                if task.next_run < time.time():
                    start_time = time.time()
                    try:
                        next(task)
                    except Exception as e:
                        logger.exception(e)
                        self.remove_task(task, nowait=True)
                    end_time = time.time()
                    task.next_run += task.delay
                    with self._lock:
                        for task in self.tasks:
                            task.next_run += end_time - start_time
                else:
                    time.sleep(0.05)
            else:
                time.sleep(0.5)

    def start(self) -> None:
        """
        Start task handler.
        """
        logger.info("Start task handler")
        if self._thread.is_alive():
            logger.warning("Task handler already running!")
            return
        self._thread = Thread(target=self.loop)
        register_thread(self._thread)
        self._thread.start()

    def stop(self) -> None:
        self.remove_pending_task()
        if self._thread.is_alive():
            self._thread.stop()
        logger.info("Finish task handler")


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
    RUN = _read(filepath_icon('run'))
    DEVELOP = _read(filepath_icon('develop'))
    PERFORMANCE = _read(filepath_icon('performance'))
    ADD = _read(filepath_icon('add'))


def get_output(arg_type, name, title, arg_help=None, value=None, options=None, width="12rem"):
    if arg_type == 'input':
        return put_input_(name, title, arg_help, value, width)
    elif arg_type == 'select':
        return put_select_(name, title, arg_help, options, width)
    elif arg_type == 'textarea':
        return put_textarea_(name, title, arg_help, value)
    elif arg_type == 'checkbox':
        return put_checkbox_(name, title, arg_help, value, width)
    elif arg_type == 'disable':
        return put_input_(name, title, arg_help, value, width, readonly=True)


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
        except ValueError:
            return val
        if v.is_integer():
            return int(v)
        else:
            return v


def login(password):
    pwd = input(label='Please login below.', type=PASSWORD, placeholder='PASSWORD')
    if pwd == password:
        return True
    else:
        toast('Wrong password!', color='error')
        return False


if __name__ == '__main__':
    def gen(x):
        n = 0
        while True:
            n += x
            print(n)
            yield n

    th = TaskHandler()
    th.start()

    t1 = Task(gen(1), delay=1)
    t2 = Task(gen(-2), delay=3)

    th.add_task(t1)
    th.add_task(t2)

    time.sleep(5)
    th.remove_task(t2, nowait=True)
    time.sleep(5)
    th.stop()
