"""
FastAPI-based REST + WebSocket API for the Vue SPA frontend.

This module coexists with the legacy pywebio GUI during the migration
(dual-stack). The Vue frontend consumes REST endpoints for configuration
and control, and the /ws endpoint for status and log streaming.
"""

import asyncio
import re
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from rich.console import Console

from module.config.deep import deep_get, deep_iter, deep_set
from module.config.utils import alas_instance, filepath_args, filepath_config, read_file, write_file
from module.logger import logger
from module.webui.lang import dic_lang, set_language
from module.webui.process_manager import ProcessManager
from module.webui.setting import State


class SetValueRequest(BaseModel):
    value: Any


class RunRequest(BaseModel):
    instance: str
    func: str | None = None


class StopRequest(BaseModel):
    instance: str


class LanguageRequest(BaseModel):
    language: str


class ThemeRequest(BaseModel):
    theme: str


class NewInstanceRequest(BaseModel):
    name: str
    origin: str | None = None


class DeleteInstanceRequest(BaseModel):
    name: str


class ImportConfigRequest(BaseModel):
    config: dict[str, Any]


_update_singleton = None


def _get_updater():
    """Module-level updater singleton so state survives across requests."""
    global _update_singleton
    if _update_singleton is None:
        from module.webui.updater import Updater

        _update_singleton = Updater()
    return _update_singleton


def render_log(renderable) -> str:
    """Render a rich renderable to a plain string."""
    try:
        console = Console(no_color=True)
        with console.capture() as capture:
            console.print(renderable)
        return capture.get().rstrip("\n")
    except Exception:
        return str(renderable)


def build_status() -> dict[str, Any]:
    from module.webui import lang

    instances = []
    for name in alas_instance():
        manager = ProcessManager.get_manager(name)
        instances.append(
            {
                "name": name,
                "state": manager.state,
                "alive": manager.alive,
            }
        )
    return {
        "instances": instances,
        "theme": State.theme,
        "language": lang.LANG,
    }


def _parse_value(value: Any, valuetype: str) -> Any:
    """Convert a frontend value to the python type defined by valuetype."""
    if value is None:
        return value
    if valuetype == "int":
        return int(value)
    elif valuetype == "float":
        return float(value)
    elif valuetype == "bool":
        return bool(value)
    elif valuetype == "datetime":
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    elif valuetype == "str":
        return str(value)
    elif valuetype == "list":
        return value if isinstance(value, list) else [value]
    elif valuetype == "dict":
        return value if isinstance(value, dict) else {}
    return value


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def _save_config(modified: dict[str, Any], config_name: str, args_schema: dict[str, Any]) -> dict[str, Any]:
    """Validate and save modified config keys.

    Returns:
        {valid: [...], invalid: [...]}
    """
    valid = []
    invalid = []
    config_updater = State.config_updater
    config = config_updater.read_file(config_name)
    n = datetime.now()
    for p, v in deep_iter(config, depth=3):
        if p[-1].endswith("un") and not isinstance(v, bool):
            if (v - n).days >= 31:
                deep_set(config, p, "")
    for k, v in modified.items():
        valuetype = deep_get(args_schema, k + ".valuetype")
        v = _parse_value(v, valuetype)
        validate = deep_get(args_schema, k + ".validate")
        if not len(str(v)):
            default = deep_get(args_schema, k + ".value")
            deep_set(config, k, default)
            valid.append(k)
        elif not validate or re.fullmatch(validate, str(v)):
            deep_set(config, k, v)
            valid.append(k)
            for set_key, set_value in config_updater.save_callback(k, v):
                deep_set(config, set_key, set_value)
                valid.append(set_key)
        else:
            invalid.append(k)

    if valid:
        write_file(filepath_config(config_name), config)
    return {"valid": valid, "invalid": invalid}


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
    if updater.delay > 0:
        task_handler.add(updater.check_update, updater.delay)
    task_handler.add(updater.schedule_update(), 86400)
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


def create_api_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # State.init must complete before serving requests (WS depends on it).
        State.init()
        thread = threading.Thread(target=_startup, daemon=True)
        thread.start()
        yield
        _shutdown()

    app = FastAPI(title="Alas API", lifespan=lifespan)

    # ---------- status ----------
    @app.get("/status")
    def get_status():
        return build_status()

    # ---------- schema ----------
    @app.get("/schema/{mod_name}")
    def get_schema(mod_name: str = "alas"):
        from module.config.server import to_server

        menu = read_file(filepath_args("menu", mod_name))
        args = read_file(filepath_args("args", mod_name))
        # Resolve server-specific select options, mirroring the legacy
        # AlasGUI.set_group() behavior.
        server = to_server("cn")
        for _task, groups in args.items():
            for _group_name, argv in groups.items():
                for _arg_name, arg_dict in argv.items():
                    if arg_dict.get("type") != "select":
                        continue
                    options = arg_dict.get("option", [])
                    server_options = arg_dict.get(f"option_{server}")
                    if isinstance(server_options, list) and server_options:
                        options = server_options
                    arg_dict["option"] = options
                    if len(options) == 1:
                        only = options[0]
                        if only in arg_dict.get("option_bold", []):
                            arg_dict["type"] = "state"
        return {"menu": menu, "args": args}

    # ---------- config ----------
    @app.get("/config/{config_name}")
    def get_config(config_name: str):
        config = State.config_updater.read_file(config_name)
        return _to_jsonable(config)

    @app.post("/config/{config_name}")
    def set_config(config_name: str, request: SetValueRequest):
        # request.value: {path.key: value} pairs, path joined by '.'
        modified = request.value
        args_schema = read_file(filepath_args("args", "alas"))
        return _save_config(modified, config_name, args_schema)

    # ---------- i18n ----------
    @app.get("/i18n/{lang}")
    def get_i18n(lang: str):
        return dic_lang.get(lang, dic_lang.get("en-US", {}))

    @app.post("/language")
    def set_language_api(request: LanguageRequest):
        from module.webui import lang

        set_language(request.language)
        return {"language": lang.LANG}

    # ---------- theme ----------
    @app.post("/theme")
    def set_theme_api(request: ThemeRequest):
        State.theme = request.theme
        State.deploy_config.Theme = request.theme
        return {"theme": request.theme}

    # ---------- control ----------
    @app.post("/run")
    def run_alas(request: RunRequest):
        manager = ProcessManager.get_manager(request.instance)
        if manager.alive:
            return {"ok": False, "error": f"{request.instance} is already running"}
        manager.start(func=request.func)
        return {"ok": True}

    @app.post("/stop")
    def stop_alas(request: StopRequest):
        manager = ProcessManager.get_manager(request.instance)
        manager.stop()
        return {"ok": True}

    # ---------- instances management ----------
    @app.post("/instance/new")
    def new_instance(request: NewInstanceRequest):
        from module.config.utils import filepath_config

        name = request.name.strip()
        if not name:
            return {"ok": False, "error": "Empty name"}
        if name in alas_instance() or name == "template":
            return {"ok": False, "error": f"Instance {name} already exists"}
        origin = request.origin or "template"
        origin_config = State.config_updater.read_file(origin)
        deep_set(origin_config, "Alas.Emulator.Serial", "")
        write_file(filepath_config(name), origin_config)
        return {"ok": True}

    @app.post("/instance/delete")
    def delete_instance(request: DeleteInstanceRequest):
        import os

        from module.config.utils import filepath_config

        name = request.name
        if name == "template" or name not in alas_instance():
            return {"ok": False, "error": f"Cannot delete {name}"}
        manager = ProcessManager.get_manager(name)
        if manager.alive:
            manager.stop()
        os.remove(filepath_config(name))
        return {"ok": True}

    @app.post("/config/{config_name}/import")
    def import_config(config_name: str, request: ImportConfigRequest):
        write_file(filepath_config(config_name), request.config)
        return {"ok": True}

    # ---------- updater ----------
    @app.get("/update/status")
    def update_status():
        updater = _get_updater()
        raw = getattr(updater, "state", 0)
        # NOTE: False hashes to 0, so {0: "idle", False: "none"} collides;
        # map the three real states explicitly instead.
        if raw is False:
            state = "none"
        elif raw is True:
            state = "available"
        elif raw == 0:
            state = "idle"
        else:
            state = str(raw)
        try:
            sha, _author, _isotime, message = updater.get_commit(short_sha1=True)
            current = {"sha": sha, "message": message}
        except Exception:
            current = None
        return {"state": state, "current": current}

    @app.get("/update/history")
    def update_history():
        updater = _get_updater()
        try:
            local = list(updater.get_commit(short_sha1=True))
        except Exception:
            local = None
        try:
            upstream = list(updater.get_commit(f"origin/{updater.Branch}", short_sha1=True))
        except Exception:
            upstream = None
        try:
            history = [list(c) for c in updater.get_commit(f"origin/{updater.Branch}", n=20, short_sha1=True)]
        except Exception:
            history = []
        return {"local": local, "upstream": upstream, "history": history}

    @app.post("/update/check")
    def update_check():
        updater = _get_updater()

        def worker():
            try:
                updater.check_update()
            except Exception as e:
                logger.exception(e)
                updater.state = "failed"

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True}

    @app.post("/update/run")
    def update_run():
        updater = _get_updater()

        def worker():
            try:
                updater.run_update()
            except Exception as e:
                logger.exception(e)
                updater.state = "failed"

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True}

    # ---------- remote access ----------
    @app.get("/remote/status")
    def remote_status():
        from module.webui.remote_access import RemoteAccess

        return {
            "alive": RemoteAccess.is_alive(),
            "state": RemoteAccess.get_state(),
            "entry_point": RemoteAccess.get_entry_point(),
        }

    @app.post("/remote/start")
    def remote_start():
        from module.webui.remote_access import start_remote_access_service

        start_remote_access_service()
        return {"ok": True}

    @app.post("/remote/stop")
    def remote_stop():
        from module.webui.remote_access import RemoteAccess

        RemoteAccess.kill_ssh_process()
        return {"ok": True}

    # ---------- config files ----------
    @app.get("/configs")
    def configs_list():
        import glob
        import os

        out = []
        for f in sorted(glob.glob("./config/*.json")):
            name = os.path.splitext(os.path.basename(f))[0]
            if name.startswith("template"):
                continue
            mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            out.append({"name": name, "modified": mtime})
        return out

    @app.get("/config/{config_name}/export")
    def export_config(config_name: str):
        import json as _json

        from fastapi.responses import Response

        config = _to_jsonable(State.config_updater.read_file(config_name))
        content = _json.dumps(config, indent=2, ensure_ascii=False)
        return Response(
            content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{config_name}.json"'},
        )

    # ---------- scheduler ----------
    @app.get("/scheduler/{config_name}")
    def scheduler(config_name: str):
        from module.config.config import AzurLaneConfig

        config = AzurLaneConfig(config_name)
        config.load()
        config.get_next_task()
        alive = ProcessManager.get_manager(config_name).alive
        pending = config.pending_task
        if alive and len(pending) >= 1:
            running = pending[:1]
            pending = pending[1:]
        else:
            running = []

        def dump(func):
            return {"command": func.command, "next_run": str(func.next_run)}

        return {
            "alive": alive,
            "running": [dump(f) for f in running],
            "pending": [dump(f) for f in pending],
            "waiting": [dump(f) for f in config.waiting_task],
        }

    # ---------- websocket ----------
    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()
        last_status = None
        last_log_len: dict[str, int] = {}
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
                    logs = [render_log(r) for r in manager.renderables]
                    prev_len = last_log_len.get(name, 0)
                    if len(logs) > prev_len:
                        await websocket.send_json(
                            {
                                "type": "log",
                                "data": {"instance": name, "logs": logs[prev_len:]},
                            }
                        )
                    last_log_len[name] = len(logs)
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.exception(e)

    # ---------- frontend (production build of the Vue SPA) ----------
    import os

    from fastapi.staticfiles import StaticFiles

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    vue_dist = os.path.join(repo_root, "webapp-tauri", "dist")
    if os.path.isdir(vue_dist):
        app.mount("/", StaticFiles(directory=vue_dist, html=True), name="frontend")

    return app
