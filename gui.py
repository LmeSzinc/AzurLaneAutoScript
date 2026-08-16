import multiprocessing
import threading
from multiprocessing import Event, Process

from module.logger import logger
from module.webui.setting import State


def func(ev: threading.Event):
    import argparse
    import asyncio
    import sys

    import uvicorn

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    State.restart_event = ev

    parser = argparse.ArgumentParser(description="Alas web service")
    parser.add_argument(
        "--host",
        type=str,
        help="Host to listen. Default to WebuiHost in deploy setting",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to listen. Default to WebuiPort in deploy setting",
    )
    parser.add_argument("-k", "--key", type=str, help="Password of alas. No password by default")
    parser.add_argument("--ssl-key", dest="ssl_key", type=str, help="SSL key file path for HTTPS support")
    parser.add_argument("--ssl-cert", type=str, help="SSL certificate file path for HTTPS support")
    parser.add_argument(
        "--run",
        nargs="+",
        type=str,
        help="Run alas by config names on startup",
    )
    args, _ = parser.parse_known_args()

    host = args.host or State.deploy_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.deploy_config.WebuiPort) or 22267
    ssl_key = args.ssl_key or State.deploy_config.WebuiSSLKey
    ssl_cert = args.ssl_cert or State.deploy_config.WebuiSSLCert
    ssl = ssl_key is not None and ssl_cert is not None

    logger.hr("Launcher config")
    logger.attr("Host", host)
    logger.attr("Port", port)
    logger.attr("SSL", ssl)
    logger.attr("Reload", ev is not None)

    if ssl_cert is None and ssl_key is not None:
        logger.error("SSL key provided without certificate. Please provide both SSL key and certificate.")
    elif ssl_key is None and ssl_cert is not None:
        logger.error("SSL certificate provided without key. Please provide both SSL key and certificate.")

    from module.webui.api import create_api_app

    app = create_api_app()

    if ssl:
        uvicorn.run(app, host=host, port=port, ssl_keyfile=ssl_key, ssl_certfile=ssl_cert)
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Required when running frozen (PyInstaller sidecar): EnableReload
    # spawns a child process of this module on Windows.
    multiprocessing.freeze_support()

    if State.deploy_config.EnableReload:
        process = None
        try:
            should_exit = False
            while not should_exit:
                event = Event()
                process = Process(target=func, args=(event,))
                process.start()
                while not should_exit:
                    try:
                        b = event.wait(1)
                    except KeyboardInterrupt:
                        should_exit = True
                        break
                    else:
                        if b:
                            # Reload requested (updater): stop the child and
                            # start a fresh one.
                            process.terminate()
                            process.join()
                            break
                        elif not process.is_alive():
                            # Backend died unexpectedly; no point waiting for
                            # a reload event that will never come.
                            logger.critical("Webui backend exited unexpectedly")
                            should_exit = True
                            break
        finally:
            # Ctrl+C or any other exit path must not leave the uvicorn
            # child orphaned (previously Ctrl+C only exited the parent and
            # the backend kept running unreachable).
            if process is not None and process.is_alive():
                process.terminate()
                process.join()
    else:
        func(ev=None)
