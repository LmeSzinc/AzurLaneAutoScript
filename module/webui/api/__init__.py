"""FastAPI-based REST + SSE API for the Svelte SPA frontend.

Routes live in the `routers` package, split by domain; request/response
models live in `models.py`; shared helpers in `helpers.py`. The app serves
the production SPA build from webapp-tauri/dist and streams status/log
updates over /sse (server-sent events).
"""

import os
import sys
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from module.logger import logger
from module.webui.api.helpers import _get_updater
from module.webui.api.routers import config, control, events, i18n, remote, scheduler, schema, status, theme, updater
from module.webui.process_manager import ProcessManager
from module.webui.setting import State


def _startup():
    """Initialize backend services, previously done by the pywebio startup."""
    from module.ocr.rpc import start_ocr_server_process
    from module.webui import lang
    from module.webui.discord_presence import init_discord_rpc
    from module.webui.remote_access import RemoteAccess
    from module.webui.tasks import TaskHandler

    lang.reload()
    updater = _get_updater()
    updater.event = State.manager.Event()
    task_handler = TaskHandler()
    # Auto-update loop disabled (2026-08): deployments are git-managed by
    # the user (source) or updated by the shell (packaged), so nothing may
    # self-update in the background. The webui update panel stays available
    # for manual /update/check and /update/run calls.
    # if updater.delay > 0:
    #     task_handler.add(updater.check_update, updater.delay)
    # task_handler.add(updater.schedule_update(), 86400)
    task_handler.start()
    if State.deploy_config.DiscordRichPresence:
        init_discord_rpc()
    if State.deploy_config.StartOcrServer:
        start_ocr_server_process(State.deploy_config.OcrServerPort)
    if State.deploy_config.EnableRemoteAccess and State.deploy_config.Password:
        task_handler.add(RemoteAccess.keep_ssh_alive(), 60)
    ProcessManager.restart_processes()


def _shutdown():
    """Cleanup backend services."""
    from module.ocr.rpc import stop_ocr_server_process
    from module.webui.discord_presence import close_discord_rpc
    from module.webui.remote_access import RemoteAccess

    logger.info("Start clearup")
    RemoteAccess.kill_ssh_process()
    close_discord_rpc()
    stop_ocr_server_process()
    for alas in ProcessManager._processes.values():
        alas.stop()
    State.clearup()


def _add_dev_cors(app: FastAPI):
    """Allow cross-origin requests from the vite dev server (dev only).

    Production serves the SPA from this same process (same origin), so CORS
    is off by default. Set ALAS_CORS_ORIGINS to a comma-separated origin
    list (e.g. "http://localhost:1420") when running the webapp-tauri vite
    dev server against this backend.
    """
    origins = [o.strip() for o in os.environ.get("ALAS_CORS_ORIGINS", "").split(",") if o.strip()]
    if not origins:
        return
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_home_redirect(app: FastAPI):
    """Redirect every unmatched path back to the SPA home page.

    The frontend routes live in the URL hash (#/xxx), which the browser
    never sends to the server, so the only meaningful server paths are the
    registered API routes, the root SPA page, and its static assets.
    Anything else (typos, stale links, stray requests) gets a 302 back to
    "/" instead of the default JSON 404; browsers re-apply the original
    #fragment to the redirect target, so hash routes survive.

    Loop guard: when the SPA build is missing (webapp-tauri/dist not
    built), "/" itself 404s — return the JSON 404 then instead of
    redirecting, to avoid a redirect loop.
    """

    @app.exception_handler(StarletteHTTPException)
    async def unmatched_path_to_home(request, exc):
        if exc.status_code == 404 and request.url.path != "/":
            return RedirectResponse("/", status_code=302)
        # Other HTTP errors (405, ...) and a missing "/" keep FastAPI's
        # default JSON response.
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)


def _add_password_gate(app: FastAPI):
    """Require HTTP Basic auth on every route when a webui password is set.

    Previously the API was unauthenticated even with Password configured
    (any LAN client could trigger /update/run, /run, config writes, ...).
    The browser shows its native credential prompt on the first 401 and
    re-sends the cached credentials on later fetch/EventSource requests, so
    the SPA needs no login UI.
    """
    try:
        password = State.deploy_config.Password
    except Exception:
        password = None
    if not password:
        return

    import base64
    import secrets

    from starlette.middleware.base import BaseHTTPMiddleware

    expected = "Basic " + base64.b64encode(f"alas:{password}".encode()).decode()

    class PasswordGate(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if not secrets.compare_digest(request.headers.get("Authorization", ""), expected):
                return JSONResponse(
                    {"detail": "Unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Alas"'},
                )
            return await call_next(request)

    app.add_middleware(PasswordGate)


def create_api_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # State.init must complete before serving requests (SSE depends on it).
        State.init()
        thread = threading.Thread(target=_startup, daemon=True)
        thread.start()
        # The Tauri shell watches stderr for this marker before showing its
        # window and navigating to this server. Must stay on stderr: logger
        # output goes to stdout, which the shell does not read.
        print("Application startup complete", file=sys.stderr, flush=True)
        yield
        _shutdown()

    app = FastAPI(title="Alas API", lifespan=lifespan)

    _add_password_gate(app)
    _add_dev_cors(app)
    _add_home_redirect(app)

    app.include_router(status.router)
    app.include_router(schema.router)
    app.include_router(config.router)
    app.include_router(i18n.router)
    app.include_router(theme.router)
    app.include_router(control.router)
    app.include_router(updater.router)
    app.include_router(remote.router)
    app.include_router(scheduler.router)
    app.include_router(events.router)

    # ---------- frontend (production build of the Svelte SPA) ----------
    from fastapi.staticfiles import StaticFiles

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    vue_dist = os.path.join(repo_root, "webapp-tauri", "dist")
    if os.path.isdir(vue_dist):
        app.mount("/", StaticFiles(directory=vue_dist, html=True), name="frontend")

    return app
