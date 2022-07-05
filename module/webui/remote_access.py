"""
Copy from pywebio.platform.remote_access

* Implementation of remote access
Use https://github.com/wang0618/localshare service by running a ssh subprocess in PyWebIO application.

The stdout of ssh process is the connection info.


"""

import json
import shlex
import threading
import time
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING

from module.logger import logger
from module.config.utils import random_id
from module.webui.setting import State

if TYPE_CHECKING:
    from module.webui.utils import TaskHandler

_ssh_process: Popen = None
_ssh_thread: threading.Thread = None
_ssh_notfound: bool = False
address: str = None


def am_i_the_only_thread() -> bool:
    """Whether the current thread is the only non-Daemon threads in the process"""
    alive_none_daemonic_thread_cnt = sum(
        1
        for t in threading.enumerate()
        if t.is_alive() and not t.isDaemon() or t is threading.current_thread()
    )
    return alive_none_daemonic_thread_cnt == 1


def remote_access_service(
    local_host="127.0.0.1",
    local_port=22267,
    server="app.pywebio.online",
    server_port=1022,
    remote_port="/",
    setup_timeout=60,
):
    """
    Wait at most one minute to get the ssh output, if it gets a normal out, the connection is successfully established.
    Otherwise report error and kill ssh process.

    :param local_port: ssh local listen port
    :param server: ssh server domain
    :param server_port: ssh server port
    :param setup_timeout: If the service can't setup successfully in `setup_timeout` seconds, then exit.
    """
    global _ssh_process, _ssh_notfound

    bin = State.deploy_config.SSHExecutable
    cmd = f"{bin} -oStrictHostKeyChecking=no -R {remote_port}:{local_host}:{local_port} -p {server_port} {server} -- --output json"
    args = shlex.split(cmd)
    logger.debug(f"remote access service command: {cmd}")

    if _ssh_process is not None and _ssh_process.poll() is None:
        logger.warning(f"Kill previous ssh process [{_ssh_process.pid}]")
        _ssh_process.kill()
    try:
        _ssh_process = Popen(args, stdout=PIPE, stderr=PIPE)
    except FileNotFoundError as e:
        logger.critical(
            f"Cannot find SSH executable {bin}, please install OpenSSH or specify SSHExecutable in deploy.yaml"
        )
        _ssh_notfound = True
        return
    logger.info(f"remote access process pid: {_ssh_process.pid}")
    success = False

    def timeout_killer(wait_sec):
        time.sleep(wait_sec)
        if not success and _ssh_process.poll() is None:
            logger.info("Connection timeout, kill ssh process")
            _ssh_process.kill()

    threading.Thread(
        target=timeout_killer, kwargs=dict(wait_sec=setup_timeout), daemon=True
    ).start()

    stdout = _ssh_process.stdout.readline().decode("utf8")
    logger.info(f"ssh server stdout: {stdout}")
    connection_info = {}
    try:
        connection_info = json.loads(stdout)
        success = True
    except json.decoder.JSONDecodeError:
        if not success and _ssh_process.poll() is None:
            _ssh_process.kill()

    if success:
        if connection_info.get("status", "fail") != "success":
            logger.info(
                f"Failed to establish remote access, this is the error message from service provider: {connection_info.get('message', '')}"
            )
        else:
            global address
            address = connection_info["address"]
            logger.debug(f"Remote access url: {address}")

    # wait ssh or main thread exit
    while not am_i_the_only_thread() and _ssh_process.poll() is None:
        # while _ssh_process.poll() is None:
        time.sleep(1)

    if _ssh_process.poll() is None:  # main thread exit, kill ssh process
        logger.info("App process exit, killing ssh process")
        _ssh_process.kill()
    else:  # ssh process exit by itself or by timeout killer
        stderr = _ssh_process.stderr.read().decode("utf8")
        if stderr:
            logger.error(f"PyWebIO application remote access service error: {stderr}")
        else:
            logger.info("PyWebIO application remote access service exit.")
    address = None


def start_remote_access_service_(**kwargs):
    logger.info("Start remote access service")
    try:
        remote_access_service(**kwargs)
    except KeyboardInterrupt:  # ignore KeyboardInterrupt
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        if _ssh_process:
            logger.info("Exception occurred, killing ssh process")
            _ssh_process.kill()
    logger.info("Exit remote access service thread")


class ParseError(Exception):
    pass


def start_remote_access_service(**kwagrs):
    global _ssh_thread

    try:
        server, server_port = State.deploy_config.SSHServer.split(":")
    except (ValueError, AttributeError):
        raise ParseError(
            f"Failed to parse SSH server [{State.deploy_config.SSHServer}]"
        )
    if State.deploy_config.WebuiHost == "0.0.0.0":
        local_host = "127.0.0.1"
    elif State.deploy_config.WebuiHost == "::":
        local_host = "[::1]"
    else:
        local_host = State.deploy_config.WebuiHost

    if State.deploy_config.SSHUser is None:
        logger.info("SSHUser is not set, generate a random one")
        State.deploy_config.SSHUser = random_id(24)

    server = f"{State.deploy_config.SSHUser}@{server}"
    kwagrs.setdefault("server", server)
    kwagrs.setdefault("server_port", server_port)
    kwagrs.setdefault("local_host", local_host)
    kwagrs.setdefault("local_port", State.deploy_config.WebuiPort)

    _ssh_thread = threading.Thread(
        target=start_remote_access_service_,
        kwargs=kwagrs,
        daemon=False,
    )
    _ssh_thread.start()
    return _ssh_thread


class RemoteAccess:
    @staticmethod
    def keep_ssh_alive():
        task_handler: TaskHandler
        task_handler = yield
        while True:
            if _ssh_thread is not None and _ssh_thread.is_alive():
                yield
                continue
            logger.info("Remote access service is not running, starting now")
            try:
                start_remote_access_service()
            except ParseError as e:
                logger.exception(e)
                task_handler.remove_current_task()
            yield

    @staticmethod
    def kill_ssh_process():
        if RemoteAccess.is_alive():
            _ssh_process.kill()

    @staticmethod
    def is_alive():
        return (
            _ssh_thread is not None
            and _ssh_thread.is_alive()
            and _ssh_process is not None
            and _ssh_process.poll() is None
        )

    @staticmethod
    def get_state():
        if RemoteAccess.is_alive():
            if address is not None:
                return 1
            else:
                return 2
        elif _ssh_notfound:
            return 3
        else:
            return 0

    @staticmethod
    def get_entry_point():
        return address if RemoteAccess.is_alive() else None
