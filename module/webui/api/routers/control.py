import os
import re

from fastapi import APIRouter

from module.config.deep import deep_set
from module.config.utils import alas_instance, filepath_config, write_file
from module.webui.api.models import (
    DeleteInstanceRequest,
    NewInstanceRequest,
    OkResponse,
    RenameInstanceRequest,
    RunRequest,
    StopRequest,
)
from module.webui.process_manager import ProcessManager
from module.webui.setting import State

router = APIRouter(tags=["control"])

_INVALID_NAME_CHARS = re.compile(r'[\\/:*?"<>|]')


@router.post("/run", response_model=OkResponse, response_model_exclude_none=True)
def run_alas(request: RunRequest):
    manager = ProcessManager.get_manager(request.instance)
    if manager.alive:
        return {"ok": False, "error": f"{request.instance} is already running"}
    manager.start(func=request.func)
    return {"ok": True}


@router.post("/stop", response_model=OkResponse, response_model_exclude_none=True)
def stop_alas(request: StopRequest):
    manager = ProcessManager.get_manager(request.instance)
    manager.stop()
    return {"ok": True}


@router.post("/instance/new", response_model=OkResponse, response_model_exclude_none=True)
def new_instance(request: NewInstanceRequest):
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


@router.post("/instance/delete", response_model=OkResponse, response_model_exclude_none=True)
def delete_instance(request: DeleteInstanceRequest):
    name = request.name
    if name == "template" or name not in alas_instance():
        return {"ok": False, "error": f"Cannot delete {name}"}
    manager = ProcessManager.get_manager(name)
    if manager.alive:
        manager.stop()
    os.remove(filepath_config(name))
    return {"ok": True}


@router.post("/instance/rename", response_model=OkResponse, response_model_exclude_none=True)
def rename_instance(request: RenameInstanceRequest):
    name = request.name
    new_name = request.new_name.strip()
    if name == "template":
        return {"ok": False, "error": "Cannot rename template"}
    if name not in alas_instance():
        return {"ok": False, "error": f"Instance {name} not found"}
    if not new_name:
        return {"ok": False, "error": "Empty name"}
    if new_name == "template" or new_name in alas_instance():
        return {"ok": False, "error": f"Instance {new_name} already exists"}
    if _INVALID_NAME_CHARS.search(new_name):
        return {"ok": False, "error": f"Invalid characters in name: {new_name}"}
    manager = ProcessManager.get_manager(name)
    if manager.alive:
        manager.stop()
    os.rename(filepath_config(name), filepath_config(new_name))
    # Drop the stale manager entry so the renamed instance starts fresh and
    # the old name stops appearing in process bookkeeping.
    ProcessManager._processes.pop(name, None)
    return {"ok": True}
