import threading

from fastapi import APIRouter

from module.logger import logger
from module.webui.api.helpers import _get_updater
from module.webui.api.models import OkResponse, UpdateHistoryResponse, UpdateStatusResponse

router = APIRouter(tags=["updater"])


@router.get("/update/status", response_model=UpdateStatusResponse)
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


@router.get("/update/history", response_model=UpdateHistoryResponse)
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


@router.post("/update/check", response_model=OkResponse, response_model_exclude_none=True)
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


@router.post("/update/run", response_model=OkResponse, response_model_exclude_none=True)
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
