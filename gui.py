import threading

from multiprocessing import Process, Event


def func(ev: threading.Event):
    import argparse
    import uvicorn
    from module.webui.app import app
    from module.webui.setting import State

    State.researt_event = ev

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
    args, _ = parser.parse_known_args()

    host = args.host or State.deploy_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.deploy_config.WebuiPort) or 22267

    uvicorn.run(app, host=host, port=port, factory=True)


if __name__ == "__main__":
    should_exit = False
    while not should_exit:
        event = Event()
        process = Process(target=func, args=(event,))
        process.start()
        while not should_exit:
            if event.wait(5):
                process.kill()
                break
            elif process.is_alive():
                continue
            else:
                should_exit = True
