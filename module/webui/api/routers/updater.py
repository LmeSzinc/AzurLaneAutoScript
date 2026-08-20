import threading

from fastapi import APIRouter

from module.logger import logger
from module.webui.api.helpers import _get_updater
from module.webui.api.models import OkResponse, UpdateInstallRequest

router = APIRouter(tags=["updater"])


@router.get("/update/status")
def update_status():
    return _get_updater().status()


@router.post("/update/refresh", response_model=OkResponse, response_model_exclude_none=True)
def update_refresh():
    def worker():
        try:
            _get_updater().refresh()
        except Exception as e:
            logger.exception(e)

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True}


@router.post("/update/install", response_model=OkResponse, response_model_exclude_none=True)
def update_install(body: UpdateInstallRequest):
    error = _get_updater().start_install(body.version)
    return {"ok": error is None, "error": error}
