"""
Copy from pywebio.platform.fastapi
"""
import asyncio
import os

import uvicorn
from pywebio.platform.fastapi import (STATIC_PATH, Session, cdn_validation,
                                      get_free_port,
                                      open_webbrowser_on_server_started,
                                      start_remote_access_service,
                                      webio_routes)
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from module.config.config import AzurLaneConfig
from module.config.utils import alas_instance
from module.webui.process_manager import ProcessManager
from module.webui.setting import State


STATE_MAP = {
    1: "running",
    2: "stopped",
    3: "crashed",
    4: "updating",
}

def _check_auth(request) -> JSONResponse:
    """
    Returns a 401 JSONResponse if authentication fails, or None if authorised.
    Password is read live from deploy config so runtime changes take effect.
    """
    password = State.deploy_config.Password
    if not password:
        return None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == password:
        return None
    return JSONResponse(
        {"error": "Unauthorized", "message": "Invalid or missing password"},
        status_code=401,
    )


class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache"
        return response


async def api_scheduler_list(request):
    """
    GET /api/scheduler/list
    Return all created config instances with their current status.
    """
    resp = _check_auth(request)
    if resp:
        return resp
    instances = []
    for name in alas_instance():
        pm = ProcessManager.get_manager(name)
        instances.append({
            "config_name": name,
            "alive": pm.alive,
            "state": STATE_MAP.get(pm.state, "unknown"),
        })
    return JSONResponse({"instances": instances})


async def api_scheduler_start(request):
    """
    POST /api/scheduler/start
    Start the scheduler for the given config_name.

    Request body (JSON):
        {"config_name": "alas"}  (optional, defaults to "alas")
    """
    resp = _check_auth(request)
    if resp:
        return resp
    body = await request.json()
    config_name = body.get("config_name", "alas")
    pm = ProcessManager.get_manager(config_name)
    if pm.alive:
        return JSONResponse({
            "config_name": config_name,
            "status": "already_running",
        })
    pm.start(func=None)
    return JSONResponse({
        "config_name": config_name,
        "status": "started",
    })


async def api_scheduler_stop(request):
    """
    POST /api/scheduler/stop
    Stop the scheduler for the given config_name.

    Request body (JSON):
        {"config_name": "alas"}  (optional, defaults to "alas")
    """
    resp = _check_auth(request)
    if resp:
        return resp
    body = await request.json()
    config_name = body.get("config_name", "alas")
    pm = ProcessManager.get_manager(config_name)
    if not pm.alive:
        return JSONResponse({
            "config_name": config_name,
            "status": "already_stopped",
        })
    pm.stop()
    return JSONResponse({
        "config_name": config_name,
        "status": "stopped",
    })


async def api_scheduler_status(request):
    """
    GET /api/scheduler/status?config_name=alas
    Query detailed status of the specified instance.
    """
    resp = _check_auth(request)
    if resp:
        return resp
    config_name = request.query_params.get("config_name", "alas")
    pm = ProcessManager.get_manager(config_name)
    return JSONResponse({
        "config_name": config_name,
        "alive": pm.alive,
        "state": STATE_MAP.get(pm.state, "unknown"),
    })


async def api_scheduler_tasks(request):
    """
    GET /api/scheduler/tasks?config_name=alas
    Return the task queue of the specified instance.

    Scheduler process status is reported via the `alive` field separately;
    the caller may interpret pending[0] as "running" when alive is true.
    """
    resp = _check_auth(request)
    if resp:
        return resp
    config_name = request.query_params.get("config_name", "alas")
    config = AzurLaneConfig(config_name=config_name)
    config.load()
    config.get_next_task()
    pm = ProcessManager.get_manager(config_name)

    # pending = tasks past their scheduled time (ready to run)
    # waiting = tasks not yet due (scheduled in the future)
    pending = config.pending_task
    waiting = config.waiting_task

    def serialize(func):
        return {
            "command": func.command,
            "enable": func.enable,
            "next_run": func.next_run.isoformat() if func.next_run else None,
        }

    return JSONResponse({
        "config_name": config_name,
        "alive": pm.alive,
        "tasks": {
            "pending": [serialize(t) for t in pending],
            "waiting": [serialize(t) for t in waiting],
        },
    })


API_ROUTES = [
    Route("/api/scheduler/list", endpoint=api_scheduler_list, methods=["GET"]),
    Route("/api/scheduler/start", endpoint=api_scheduler_start, methods=["POST"]),
    Route("/api/scheduler/stop", endpoint=api_scheduler_stop, methods=["POST"]),
    Route("/api/scheduler/status", endpoint=api_scheduler_status, methods=["GET"]),
    Route("/api/scheduler/tasks", endpoint=api_scheduler_tasks, methods=["GET"]),
]


def asgi_app(
    applications,
    cdn=True,
    static_dir=None,
    debug=False,
    allowed_origins=None,
    check_origin=None,
    **starlette_settings
):
    debug = Session.debug = os.environ.get("PYWEBIO_DEBUG", debug)
    cdn = cdn_validation(cdn, "warn")
    if cdn is False:
        cdn = "pywebio_static"
    routes = webio_routes(
        applications,
        cdn=cdn,
        allowed_origins=allowed_origins,
        check_origin=check_origin,
    )
    if static_dir:
        routes.append(
            Mount("/static", app=StaticFiles(directory=static_dir), name="static")
        )
    routes.append(
        Mount(
            "/pywebio_static",
            app=StaticFiles(directory=STATIC_PATH),
            name="pywebio_static",
        )
    )
    routes.extend(API_ROUTES)
    middleware = [Middleware(HeaderMiddleware)]
    return Starlette(
        routes=routes, middleware=middleware, debug=debug, **starlette_settings,
    )


def start_server(
    applications,
    port=0,
    host="",
    cdn=True,
    static_dir=None,
    remote_access=False,
    debug=False,
    allowed_origins=None,
    check_origin=None,
    auto_open_webbrowser=False,
    **uvicorn_settings
):

    app = asgi_app(
        applications,
        cdn=cdn,
        static_dir=static_dir,
        debug=debug,
        allowed_origins=allowed_origins,
        check_origin=check_origin,
    )

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(
            open_webbrowser_on_server_started("localhost", port)
        )

    if not host:
        host = "0.0.0.0"

    if port == 0:
        port = get_free_port()

    if remote_access:
        start_remote_access_service(local_port=port)

    uvicorn.run(app, host=host, port=port, **uvicorn_settings)
