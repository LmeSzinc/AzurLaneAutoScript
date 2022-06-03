import asyncio
import time

from pypresence import AioPresence

RPC = AioPresence("929437173764223057")


async def run():
    await RPC.connect()
    await RPC.update(state="Alas is playing Azurlane", start=time.time(), large_image="alas")


def init_discord_rpc():
    asyncio.create_task(run())


def close_discord_rpc():
    RPC.close()


if __name__ == "__main__":
    init_discord_rpc()
