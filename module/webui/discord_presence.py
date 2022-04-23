import time
from multiprocessing import Process

from pypresence import Presence

process: Process = None


def run():
    APPLICATION_ID = "929437173764223057"
    RPC = Presence(APPLICATION_ID)
    RPC.connect()
    RPC.update(state="Alas is playing Azurlane", start=time.time(), large_image="alas")


def init_discord_rpc():
    global process
    if process is None:
        process = Process(target=run)
        process.start()


def close_discord_rpc():
    global process
    if process is not None:
        process.terminate()
        process = None


if __name__ == "__main__":
    init_discord_rpc()
