import asyncio
import time

from pypresence import AioPresence

RPC: AioPresence = None


async def run():
    assert RPC is not None
    await RPC.connect()
    await RPC.update(state="Alas is playing Azurlane", start=time.time(), large_image="alas")


def init_discord_rpc():
    global RPC
    RPC = AioPresence("929437173764223057")
    asyncio.create_task(run())


def close_discord_rpc():
    if RPC:
        RPC.send_data(2, {'v': 1, 'client_id': RPC.client_id})
        RPC.sock_writer.close()
