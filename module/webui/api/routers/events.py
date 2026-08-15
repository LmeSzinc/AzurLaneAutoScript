import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from module.logger import logger
from module.webui.api.helpers import build_status, render_log
from module.webui.process_manager import ProcessManager

router = APIRouter(tags=["events"])


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_status = None
    # Per-instance render cursor: only render and send NEW renderables.
    log_cursor: dict[str, int] = {}
    try:
        while True:
            # Drain incoming messages (keepalive / commands, ignored for now)
            try:
                while True:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
            except TimeoutError:
                pass
            status = build_status()
            if status != last_status:
                await websocket.send_json({"type": "status", "data": status})
                last_status = status
            for name, manager in ProcessManager._processes.items():
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
                    logs = [render_log(r) for r in new_renderables]
                    await websocket.send_json(
                        {
                            "type": "log",
                            "data": {"instance": name, "logs": logs, "reset": reset},
                        }
                    )
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(e)
