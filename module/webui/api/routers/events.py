import asyncio
import json
import time
from queue import Empty
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from module.logger import logger
from module.webui.api.helpers import build_status, render_log
from module.webui.process_manager import ProcessManager

router = APIRouter(tags=["events"])

# Latest scheduler snapshot per instance, so freshly connected SSE clients
# get the current three-column state immediately (same mechanism as the
# status first frame).
_scheduler_cache: dict[str, dict] = {}

# Wall-clock of the last live recompute per instance. The bot process only
# publishes scheduler snapshots while it runs (on task transitions); while
# the scheduler is stopped/paused the overview would otherwise freeze on the
# stale snapshot even though pending/waiting are plain functions of the
# config file. Recompute those instances periodically.
_last_recompute: dict[str, float] = {}
_RECOMPUTE_INTERVAL = 30.0


def _recompute_scheduler(name: str) -> dict | None:
    """Compute the current pending/waiting split straight from the config
    file, mirroring the REST /scheduler/{name} route (shared shape with
    publish_scheduler_state: current/pending/waiting).

    Only called while the bot process is NOT alive, so nothing is running:
    `current` stays None and `pending` keeps its full list (the bot's own
    snapshots keep the running task inside pending, so the shapes match).
    Splitting pending[:1] off as a fake "running" task here made the overview
    show a phantom running task with an empty time row after the first
    30-second recompute of a stopped instance.
    """
    try:
        from module.config.config import AzurLaneConfig

        config = AzurLaneConfig(name)
        config.load()
        config.get_next_task()
        pending = config.pending_task
        fmt = lambda f: {"command": f.command, "next_run": str(f.next_run)}  # noqa: E731
        return {
            "current": None,
            "pending": [fmt(f) for f in pending],
            "waiting": [fmt(f) for f in config.waiting_task],
        }
    except Exception:
        # Config may be mid-write or half-renamed; skip this round.
        return None


def _render_logs(renderables) -> list[str]:
    return [render_log(r) for r in renderables]


def _drain_scheduler_queue(manager) -> list[dict]:
    """Non-blocking drain of an instance's live scheduler snapshots."""
    out = []
    try:
        while True:
            out.append(manager._scheduler_queue.get_nowait())
    except Empty:
        pass
    except Exception as e:
        # Manager proxy may be gone while the child is being torn down.
        logger.exception(e)
    return out


async def _event_updates():
    """Yield (kind, payload) tuples for status changes and new log lines.

    Status is pushed on change, logs are pushed once per new renderable
    (per-connection cursor).
    """
    last_status = None
    log_cursor: dict[str, int] = {}
    sent_scheduler: set[str] = set()
    idle = 0
    try:
        while True:
            status = await asyncio.to_thread(build_status)
            if status != last_status:
                yield "status", status
                last_status = status
            for name, manager in list(ProcessManager._processes.items()):
                total = len(manager.renderables)
                cursor = log_cursor.get(name, 0)
                first_frame = name not in log_cursor
                reset = False
                if total < cursor:
                    # renderables buffer was trimmed or replaced; re-send all
                    cursor = 0
                    reset = True
                if first_frame:
                    # Pre-push the whole accumulated buffer for a fresh
                    # connection (page refresh) so the log view fills
                    # immediately instead of appearing cleared and re-fetching.
                    cursor = 0
                    reset = True
                new_renderables = manager.renderables[cursor:]
                log_cursor[name] = total
                if new_renderables:
                    logs = await asyncio.to_thread(_render_logs, new_renderables)
                    yield "log", {"instance": name, "logs": logs, "reset": reset}
                for snapshot in _drain_scheduler_queue(manager):
                    _scheduler_cache[name] = snapshot
                    sent_scheduler.add(name)
                    yield "scheduler", {"instance": name, **snapshot}
                if name not in sent_scheduler:
                    # First frame for this connection: replay the latest
                    # snapshot so the overview has data before the bot's
                    # next publish.
                    cached = _scheduler_cache.get(name)
                    if cached is not None:
                        sent_scheduler.add(name)
                        yield "scheduler", {"instance": name, **cached}
                if not manager.alive:
                    # Scheduler stopped/paused: the bot publishes nothing,
                    # so keep the overview honest by recomputing the
                    # pending/waiting split from the config file.
                    now = time.monotonic()
                    if now - _last_recompute.get(name, 0) >= _RECOMPUTE_INTERVAL:
                        _last_recompute[name] = now
                        snapshot = _recompute_scheduler(name)
                        if snapshot is not None:
                            _scheduler_cache[name] = snapshot
                            yield "scheduler", {"instance": name, **snapshot}
            idle += 1
            if idle >= 25:
                idle = 0
                yield "keepalive", None
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(e)


def _sse_message(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _sse_stream():
    """Format _event_updates as a server-sent event stream.

    Keepalive comments keep idle proxies from dropping the stream.
    """
    async for kind, data in _event_updates():
        if kind == "keepalive":
            yield ": keepalive\n\n"
        else:
            yield _sse_message(kind, data)


@router.get("/sse")
async def sse_endpoint():
    return StreamingResponse(
        _sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
