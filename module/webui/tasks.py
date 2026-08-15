"""
Background task scheduling, extracted from the legacy pywebio utils module.
"""

import datetime
import operator
import threading
import time
from collections.abc import Callable, Generator

from module.logger import logger


def get_next_time(t: datetime.time):
    now = datetime.datetime.today().time()
    second = (t.hour - now.hour) * 3600 + (t.minute - now.minute) * 60 + (t.second - now.second)
    if second < 0:
        second += 86400
    return second


class Task:
    def __init__(self, g: Generator, delay: float, next_run: float | None = None, name: str | None = None) -> None:
        self.g = g
        g.send(None)
        self.delay = delay
        self.next_run = next_run if next_run else time.time()
        self.name = name if name is not None else self.g.__name__

    def __str__(self) -> str:
        return f"<{self.name} (delay={self.delay})>"

    def __next__(self) -> None:
        return next(self.g)

    def send(self, obj) -> None:
        return self.g.send(obj)

    __repr__ = __str__


def get_generator(func: Callable):
    def _g():
        yield
        while True:
            yield func()

    g = _g()
    g.__name__ = func.__name__
    return g


class TaskHandler:
    def __init__(self) -> None:
        # List of background running task
        self.tasks: list[Task] = []
        # List of task name to be removed
        self.pending_remove_tasks: list[Task] = []
        # Running task
        self._task = None
        # Task running thread
        self._thread: threading.Thread = None
        self._alive = False
        self._lock = threading.Lock()

    def add(self, func, delay: float, pending_delete: bool = False) -> None:
        """
        Add a task running background.
        Another way of `self.add_task()`.
        func: Callable or Generator
        """
        if isinstance(func, Callable):
            g = get_generator(func)
        elif isinstance(func, Generator):
            g = func
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
            logger.warning(f"Failed to remove task {task}. Current tasks list: {self.tasks}")

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

    def remove_current_task(self) -> None:
        self.remove_task(self._task, nowait=True)

    def get_task(self, name) -> Task:
        with self._lock:
            for task in self.tasks:
                if task.name == name:
                    return task
            return None

    def loop(self) -> None:
        """
        Start task loop.
        You **should** run this function in an individual thread.
        """
        self._alive = True
        while self._alive:
            if self.tasks:
                with self._lock:
                    self.tasks.sort(key=operator.attrgetter("next_run"))
                    task = self.tasks[0]
                if task.next_run < time.time():
                    start_time = time.time()
                    try:
                        self._task = task
                        task.send(self)
                    except Exception as e:
                        logger.exception(e)
                        self.remove_task(task, nowait=True)
                    finally:
                        self._task = None
                    end_time = time.time()
                    task.next_run += task.delay
                    with self._lock:
                        for task in self.tasks:
                            task.next_run += end_time - start_time
                else:
                    time.sleep(0.05)
            else:
                time.sleep(0.5)
        logger.info("End of task handler loop")

    def _get_thread(self) -> threading.Thread:
        thread = threading.Thread(target=self.loop, daemon=True)
        return thread

    def start(self) -> None:
        """
        Start task handler.
        """
        logger.info("Start task handler")
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Task handler already running!")
            return
        self._thread = self._get_thread()
        self._thread.start()

    def stop(self) -> None:
        self.remove_pending_task()
        self._alive = False
        self._thread.join(timeout=2)
        if not self._thread.is_alive():
            logger.info("Finish task handler")
        else:
            logger.warning("Task handler does not stop within 2 seconds")
