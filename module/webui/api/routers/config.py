import glob
import json as _json
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response

from module.config.utils import filepath_args, filepath_config, read_file, write_file
from module.webui.api.helpers import _save_config, _to_jsonable
from module.webui.api.models import ConfigListItem, ImportConfigRequest, OkResponse, SaveConfigResponse, SetValueRequest
from module.webui.setting import State

router = APIRouter(tags=["config"])


@router.get("/configs", response_model=list[ConfigListItem])
def configs_list():
    out = []
    for f in sorted(glob.glob("./config/*.json")):
        name = os.path.splitext(os.path.basename(f))[0]
        if name.startswith("template"):
            continue
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
        out.append({"name": name, "modified": mtime})
    return out


@router.get("/config/{config_name}", response_model=dict[str, Any])
def get_config(config_name: str):
    config = State.config_updater.read_file(config_name)
    return _to_jsonable(config)


@router.post("/config/{config_name}", response_model=SaveConfigResponse)
def set_config(config_name: str, request: SetValueRequest):
    # request.value: {path.key: value} pairs, path joined by '.'
    modified = request.value
    args_schema = read_file(filepath_args("args", "alas"))
    return _save_config(modified, config_name, args_schema)


@router.post("/config/{config_name}/import", response_model=OkResponse)
def import_config(config_name: str, request: ImportConfigRequest):
    write_file(filepath_config(config_name), request.config)
    return {"ok": True}


@router.get("/config/{config_name}/export")
def export_config(config_name: str):
    config = _to_jsonable(State.config_updater.read_file(config_name))
    content = _json.dumps(config, indent=2, ensure_ascii=False)
    return Response(
        content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{config_name}.json"'},
    )
