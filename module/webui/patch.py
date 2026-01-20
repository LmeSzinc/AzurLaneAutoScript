import asyncio
from functools import partial, wraps

from module.logger import logger
from module.webui.setting import cached_class_property


class CachedThreadPoolExecutor:
    @cached_class_property
    def executor(cls):
        from concurrent.futures.thread import ThreadPoolExecutor
        pool = ThreadPoolExecutor(max_workers=5)
        logger.info('Patched ThreadPoolExecutor created')
        return pool


def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        if executor is None:
            executor = CachedThreadPoolExecutor.executor
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def patch_executor():
    """
    Limit pool size in loop.run_in_executor
    so starlette.staticfiles -> aiofiles won't create tons of threads
    """
    try:
        import aiofiles
    except ImportError:
        return

    loop = asyncio.get_event_loop()
    loop.set_default_executor(CachedThreadPoolExecutor.executor)


def patch_mimetype():
    """
    Patch mimetype db to use the builtin table instead of reading from environment.

    By default, mimetype reads user configured mimetype table from environment. It's good for server but bad on our
    side, because we deploy on user's machine which may have polluted environment. To have a consistent behaviour on
    all deployment, we use the builtin mimetype table only.
    """
    import mimetypes
    if mimetypes.inited:
        # ohno mimetypes already inited
        db = mimetypes.MimeTypes()
        mimetypes._db = db
        # override global variable
        mimetypes.encodings_map = db.encodings_map
        mimetypes.suffix_map = db.suffix_map
        mimetypes.types_map = db.types_map[True]
        mimetypes.common_types = db.types_map[False]
    else:
        # init db with the default table
        db = mimetypes.MimeTypes()
        mimetypes._db = db
        mimetypes.inited = True


def fix_py37_subprocess_communicate():
    """
    Monkey patch for subprocess.Popen._communicate on Windows Python 3.7
    Fixes: IndexError: list index out of range

    This bug is fixed on python>=3.8, so we backport the fix

    Ref:
        https://github.com/LmeSzinc/AzurLaneAutoScript/issues/5226
        https://bugs.python.org/issue43423
        https://github.com/python/cpython/pull/24777
    """
    import subprocess
    import sys
    import threading

    if sys.platform != 'win32' or sys.version_info[:2] != (3, 7):
        return

    def _communicate_fixed(self, input, endtime, orig_timeout):
        # Start reader threads feeding into a list hanging off of this
        # object, unless they've already been started.
        if self.stdout and not hasattr(self, "_stdout_buff"):
            self._stdout_buff = []
            self.stdout_thread = \
                threading.Thread(target=self._readerthread,
                                 args=(self.stdout, self._stdout_buff))
            self.stdout_thread.daemon = True
            self.stdout_thread.start()
        if self.stderr and not hasattr(self, "_stderr_buff"):
            self._stderr_buff = []
            self.stderr_thread = \
                threading.Thread(target=self._readerthread,
                                 args=(self.stderr, self._stderr_buff))
            self.stderr_thread.daemon = True
            self.stderr_thread.start()

        if self.stdin:
            self._stdin_write(input)

        # Wait for the reader threads, or time out.  If we time out, the
        # threads remain reading and the fds left open in case the user
        # calls communicate again.
        if self.stdout is not None:
            self.stdout_thread.join(self._remaining_time(endtime))
            if self.stdout_thread.is_alive():
                raise subprocess.TimeoutExpired(self.args, orig_timeout)
        if self.stderr is not None:
            self.stderr_thread.join(self._remaining_time(endtime))
            if self.stderr_thread.is_alive():
                raise subprocess.TimeoutExpired(self.args, orig_timeout)

        # Collect the output from and close both pipes, now that we know
        # both have been read successfully.
        stdout = None
        stderr = None
        if self.stdout:
            stdout = self._stdout_buff
            self.stdout.close()
        if self.stderr:
            stderr = self._stderr_buff
            self.stderr.close()

        # All data exchanged.  Translate lists into strings.

        # --- FIX START ---
        stdout = stdout[0] if stdout else None
        stderr = stderr[0] if stderr else None
        # --- FIX END ---

        return (stdout, stderr)

    subprocess.Popen._communicate = _communicate_fixed
