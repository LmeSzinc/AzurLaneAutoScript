import abc
import ctypes
import subprocess
from collections import deque
from functools import wraps
from itertools import count
from threading import Lock, Thread
from typing import Generic, NoReturn, TypeVar

from module.logger import logger

ValueT = TypeVar("ValueT", covariant=True)
ResultT = TypeVar("ResultT")


def remove_tb_frames(exc, n: int):
    """
    Args:
        exc (BaseException):
        n:

    Returns:
        BaseException:
    """
    tb = exc.__traceback__
    for _ in range(n):
        assert tb is not None
        tb = tb.tb_next
    return exc.with_traceback(tb)


class Outcome(abc.ABC, Generic[ValueT]):
    @abc.abstractmethod
    def unwrap(self) -> ValueT:
        """Return or raise the contained value or exception.

        These two lines of code are equivalent::

           x = fn(*args)
           x = outcome.capture(fn, *args).unwrap()

        """
        pass


class Value(Outcome[ValueT], Generic[ValueT]):
    """Concrete :class:`Outcome` subclass representing a regular value.

    """
    __slots__ = ('value',)

    def __init__(self, value: ValueT):
        self.value: ValueT = value

    def __repr__(self) -> str:
        return f'Value({self.value!r})'

    def unwrap(self) -> ValueT:
        return self.value


class Error(Outcome[NoReturn]):
    """Concrete :class:`Outcome` subclass representing a raised exception.

    """
    __slots__ = ('error',)

    def __init__(self, error: BaseException):
        self.error: BaseException = error

    def __repr__(self) -> str:
        return f'Error({self.error!r})'

    def unwrap(self):
        # Tracebacks show the 'raise' line below out of context, so let's give
        # this variable a name that makes sense out of context.
        captured_error = self.error
        try:
            raise captured_error
        finally:
            # We want to avoid creating a reference cycle here. Python does
            # collect cycles just fine, so it wouldn't be the end of the world
            # if we did create a cycle, but the cyclic garbage collector adds
            # latency to Python programs, and the more cycles you create, the
            # more often it runs, so it's nicer to avoid creating them in the
            # first place. For more details see:
            #
            #    https://github.com/python-trio/trio/issues/1770
            #
            # In particular, by deleting this local variables from the 'unwrap'
            # methods frame, we avoid the 'captured_error' object's
            # __traceback__ from indirectly referencing 'captured_error'.
            del captured_error, self


def capture(sync_fn, *args, **kwargs):
    """
    Run ``sync_fn(*args, **kwargs)`` and capture the result.

    Args:
        sync_fn (Callable[..., ResultT]):

    Returns:
        Value[ResultT] | Error:
    """
    try:
        return Value(sync_fn(*args, **kwargs))
    except BaseException as exc:
        exc = remove_tb_frames(exc, 1)
        return Error(exc)


class JobError(Exception):
    pass


class JobTimeout(Exception):
    pass


class _JobKill(Exception):
    pass


class Job(Generic[ResultT]):
    """
    A simple queue, copied from queue.Queue()
    Faster but can only put() once and get() once.
    """

    # __slots__ = ('worker', 'func_args_kwargs', 'queue', 'mutex', 'finished')

    def __init__(self, worker, func_args_kwargs):
        # Having attribute "worker" means job is ongoing
        # Not having attribute "worker" means job is finished or killed
        self.worker = worker
        self.func_args_kwargs = func_args_kwargs

        self.queue: "deque[Outcome[ResultT]]" = deque()
        self.put_lock = Lock()
        self.notify_get = Lock()
        self.notify_get.acquire()

    def __repr__(self):
        return f'Job({self.func_args_kwargs})'

    def get(self) -> ResultT:
        """
        Get job result or job error
        """
        self.notify_get.acquire()

        # Return job result or raise job error
        item = self.queue.popleft()
        return item.unwrap()

    def get_or_kill(self, timeout) -> ResultT:
        """
        Try to get result within given seconds,
        if success, return job result or job error
        if failed, kill job and raise JobTimeout

        Note that JobTimeout may not raises immediately if POOL_SIZE reached
        """
        if self.notify_get.acquire(timeout=timeout):
            # Return job result or raise job error
            item = self.queue.popleft()
            return item.unwrap()
        else:
            self._kill()
            raise JobTimeout

    def _kill(self):
        with self.put_lock:
            try:
                worker = self.worker
            except AttributeError:
                # Trying to kill a finished job, do nothing
                return
            worker.kill()
            del self.worker


name_counter = count()


class WorkerThread:
    def __init__(self, thread_pool):
        """
        Args:
            thread_pool (WorkerPool):
        """
        self.job: "Job | None" = None
        self.thread_pool = thread_pool
        # This Lock is used in an unconventional way.
        #
        # "Unlocked" means we have a pending job that's been assigned to us;
        # "locked" means that we don't.
        #
        # Initially we have no job, so it starts out in locked state.
        self.worker_lock = Lock()
        self.worker_lock.acquire()
        self.default_name = f"Alasio thread {next(name_counter)}"

        self.thread = Thread(target=self._work, name=self.default_name, daemon=True)
        self.thread.start()

    def __repr__(self):
        return f'{self.__class__.__name__}({self.default_name})'

    def _handle_job(self) -> None:
        # Convert to local variable, `self.job` will be another
        # value if new job is assigned
        job = self.job
        del self.job
        func, args, kwargs = job.func_args_kwargs

        result = capture(func, *args, **kwargs)

        # Tell the cache that we're available to be assigned a new
        # job. We do this *before* calling 'deliver', so that if
        # 'deliver' triggers a new job, it can be assigned to us
        # instead of spawning a new thread.
        self.thread_pool.idle_workers[self] = None
        self.thread_pool.release_full_lock()

        # Deliver
        if isinstance(result, Error) and isinstance(result.error, _JobKill):
            # Job killed
            pass
        else:
            # Job finished, putin result and notify
            with job.put_lock:
                job.queue.append(result)
                del job.worker
                job.notify_get.release()

    def _work(self) -> None:
        while True:
            if self.worker_lock.acquire(timeout=WorkerPool.IDLE_TIMEOUT):
                # We got a job
                self._handle_job()
            else:
                # Timeout acquiring lock, so we can probably exit. But,
                # there's a race condition: we might be assigned a job *just*
                # as we're about to exit. So we have to check.
                try:
                    del self.thread_pool.idle_workers[self]
                except KeyError:
                    # Someone else removed us from the idle worker queue, so
                    # they must be in the process of assigning us a job - loop
                    # around and wait for it.
                    self.thread_pool.release_full_lock()
                    continue
                else:
                    # We successfully removed ourselves from the idle
                    # worker queue, so no more jobs are incoming; it's safe to
                    # exit.
                    del self.thread_pool.all_workers[self]
                    self.thread_pool.release_full_lock()
                    return

    def kill(self):
        """
        Yes, it's unsafe to kill a thread, but what else can you do
        if a single job function get blocked.
        This method should be protected by `job.put_lock` to prevent
        race condition with `_handle_job()`.

        Returns:
            bool: If success to kill the thread
        """
        # Send SystemExit to thread
        thread_id = ctypes.c_long(self.thread.ident)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(_JobKill))
        if res <= 1:
            self.thread_pool.all_workers.pop(self, None)
            self.thread_pool.release_full_lock()
            return True
        else:
            try:
                job = self.job
            except AttributeError:
                job = None
            logger.error(f'Failed to kill thread {self.thread.ident} from job {job}')
            # Failed to send SystemExit, reset it
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            return False


class WorkerPool:
    """
    A thread pool imitating trio.to_thread.start_thread_soon()
    https://github.com/python-trio/trio/issues/6
    """

    # Thread exits after 10s idling.
    IDLE_TIMEOUT = 10

    def __init__(self, pool_size: int = 8):
        # Pool has 8 threads at max.
        # Alasio is for local low-frequency access so default pool size is small
        self.pool_size = pool_size

        self.idle_workers: "dict[WorkerThread, None]" = {}
        self.all_workers: "dict[WorkerThread, None]" = {}

        self.notify_worker = Lock()
        self.notify_worker.acquire()
        self.notify_pool = Lock()
        self.notify_pool.acquire()

    def release_full_lock(self):
        """
        Call this method if worker finished any job, or exited, or get killed.

        When pool full,
        Pool tells all workers: any worker finishes his job notify me.
        `self.notify_worker.release()`
        Then the pool blocks himself.
        `self.notify_pool.acquire()`
        The fastest worker, and also the only worker, receives the message,
        `if self.notify_worker.acquire(blocking=False):`
        Worker tells the pool, new pool slot is ready, you are ready to go.
        `self.notify_pool.release()`
        """
        if self.notify_worker.acquire(blocking=False):
            self.notify_pool.release()

    def _get_thread_worker(self) -> WorkerThread:
        try:
            worker, _ = self.idle_workers.popitem()
            return worker
        except KeyError:
            pass

        # Wait if reached max thread
        if len(self.all_workers) >= self.pool_size:
            # See release_full_lock()
            self.notify_worker.release()
            self.notify_pool.acquire()
            # A worker just idle
            try:
                worker, _ = self.idle_workers.popitem()
                return worker
            except KeyError:
                pass
            # A worker just exited
            # if len(self.all_workers) < WorkerPool.MAX_WORKER:
            #     break

        # Create new worker
        worker = WorkerThread(self)
        # logger.info(f'New worker thread: {worker.default_name}')
        self.all_workers[worker] = None
        return worker

    def start_thread_soon(self, func, *args, **kwargs):
        """
        Run a function on thread,
        result can be got from `job` object

        Args:
            func (Callable[..., ResultT]):
            *args:
            **kwargs:

        Returns:
            Job[ResultT]:

        Examples:
            job = WORKER_POOL.start_thread_soon(func, *args)
            result = job.get()
        """
        worker = self._get_thread_worker()
        job = Job(worker=worker, func_args_kwargs=(func, args, kwargs))

        worker.job = job
        worker.worker_lock.release()
        return job

    def run_on_thread(self, func):
        """
        Decorate a function to run on thread,
        result can be got from `job` object

        Args:
            func (Callable[..., ResultT]):

        Returns:
            Job[ResultT]:

        Examples:
            @run_on_thread
            def function(...):
                pass
            job = function(...)
            result = job.get()
        """
        @wraps(func)
        def thread_wrapper(*args, **kwargs) -> "Job[ResultT]":
            return self.start_thread_soon(func, *args, **kwargs)

        return thread_wrapper

    @staticmethod
    def _subprocess_execute(cmd, timeout=10):
        """
        Helper function to run cmd in subprocess

        Args:
            cmd (list[str]):
            timeout:

        Returns:
            bytes:
        """
        logger.info(f'Execute: {cmd}')

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)

        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.warning(f'TimeoutExpired when calling {cmd}, stdout={stdout}, stderr={stderr}')
        return stdout

    def start_cmd_soon(self, cmd, timeout=10):
        """
        Run cmd on subprocess and communicate it on another thread,
        result can be got from `job` object

        Args:
            cmd (list[str]):
            timeout:

        Returns:
            Job[bytes]:
        """
        worker = self._get_thread_worker()
        job = Job(worker=worker, func_args_kwargs=(
            self._subprocess_execute, (cmd,), {'timeout': timeout}
        ))

        worker.job = job
        worker.worker_lock.release()
        return job

    def wait_jobs(self) -> "WaitJobsWrapper":
        """
        Auto wait all jobs finished

        Examples:
            with WORKER_POOL.wait_jobs() as pool:
                pool.start_thread_soon(...)
        """
        return WaitJobsWrapper(self)

    def gather_jobs(self) -> "GatherJobsWrapper":
        """
        Auto wait all jobs finished and gather results

        Examples:
            pool = WORKER_POOL.gather_jobs()
            with pool:
                pool.start_thread_soon(...)
            # Get results
            print(pool.results)
        """
        return GatherJobsWrapper(self)

    def thread_map(self, func, iterables):
        """
        Alternative to ThreadPoolExecutor.map(func, iterables)

        Args:
            func (Callable[..., ResultT]):
            iterables:

        Returns:
            list[ResultT]:
        """
        jobs = [self.start_thread_soon(func, arg) for arg in iterables]
        results = [job.get() for job in jobs]
        return results

    def thread_starmap(self, func, iterables):
        """
        Alternative to multiprocessing.pool.Pool().starmap(func, iterables) but on threads

        Args:
            func (Callable[..., ResultT]):
            iterables:

        Returns:
            list[ResultT]:
        """
        jobs = [self.start_thread_soon(func, *arg) for arg in iterables]
        results = [job.get() for job in jobs]
        return results

    def thread_funcmap(self, func_iterables):
        """
        Run a list of functions on threads

        Args:
            func_iterables (Iterable[Callable[..., ResultT]]):

        Returns:
            list[ResultT]:
        """
        jobs = [self.start_thread_soon(func) for func in func_iterables]
        results = [job.get() for job in jobs]
        return results


class WaitJobsWrapper:
    """
    Wrapper class to wait all jobs
    """

    def __init__(self, pool: "WorkerPool"):
        self.pool: "WorkerPool" = pool
        self.jobs: "list[Job[ResultT]]" = []

    def get(self):
        for job in self.jobs:
            job.get()
        self.jobs.clear()

    def __enter__(self):
        self.jobs.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.get()

    def start_thread_soon(self, func, *args, **kwargs):
        """
        Run a function on thread,
        result can be got from `job` object

        Args:
            func (Callable[..., ResultT]):
            *args:
            **kwargs:

        Returns:
            Job[ResultT]:
        """
        job = self.pool.start_thread_soon(func, *args, **kwargs)
        self.jobs.append(job)
        return job


class GatherJobsWrapper(WaitJobsWrapper):
    """
    Wrapper class to gather all jobs
    """

    def __init__(self, pool: "WorkerPool"):
        super().__init__(pool)
        self.results: "list[ResultT]" = []

    def get(self):
        for job in self.jobs:
            result = job.get()
            self.results.append(result)
        self.jobs.clear()

    def __enter__(self):
        self.jobs.clear()
        self.results.clear()
        return self


WORKER_POOL = WorkerPool()
