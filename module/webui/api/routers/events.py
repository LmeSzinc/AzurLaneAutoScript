import asyncio
import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from module.logger import logger
from module.webui.api.helpers import build_status, render_log
from module.webui.process_manager import ProcessManager

router = APIRouter(tags=["events"])


def _sse_message(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _render_logs(renderables) -> list[str]:
    return [render_log(r) for r in renderables]


async def _sse_stream():
    """Yield status/log updates as server-sent events.

    Mirrors the old /ws push loop: status is pushed on change, logs are
    pushed once per new renderable (per-connection cursor), plus a
    keepalive comment every ~25s so idle proxies don't drop the stream.
    """
    last_status = None
    log_cursor: dict[str, int] = {}
    idle = 0
    try:
        while True:
            status = await asyncio.to_thread(build_status)
            if status != last_status:
                yield _sse_message("status", status)
                last_status = status
            for name, manager in list(ProcessManager._processes.items()):
                total = len(manager.renderables)
                cursor = log_cursor.get(name, 0)
                reset = False
                if total < cursor:
                    # renderables buffer was trimmed or replaced; re-send all
                    cursor = 0
                    reset = True
                new_renderables = manager.renderables[cursor:]
                log_cursor[name] = total
                if new_renderables:
                    logs = await asyncio.to_thread(_render_logs, new_renderables)
                    yield _sse_message("log", {"instance": name, "logs": logs, "reset": reset})
            idle += 1
            if idle >= 25:
                idle = 0
                yield ": keepalive\n\n"
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(e)


@router.get("/sse")
async def sse_endpoint():
    return StreamingResponse(
        _sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
