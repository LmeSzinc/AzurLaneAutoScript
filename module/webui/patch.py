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
