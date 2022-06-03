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

    host = args.host or State.webui_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.webui_config.WebuiPort) or 22267

    uvicorn.run(app, host=host, port=port, factory=True)

if __name__ == "__main__":
    while True:
        event = Event()
        process = Process(target=func, args=(event,))
        process.start()
        event.wait()
        process.kill()
