from fastapi import APIRouter

from module.webui.api.helpers import build_status
from module.webui.api.models import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def get_status():
    return build_status()
