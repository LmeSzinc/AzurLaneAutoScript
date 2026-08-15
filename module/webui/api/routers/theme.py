from fastapi import APIRouter

from module.webui.api.models import ThemeRequest, ThemeResponse
from module.webui.setting import State

router = APIRouter(tags=["theme"])


@router.post("/theme", response_model=ThemeResponse)
def set_theme_api(request: ThemeRequest):
    State.theme = request.theme
    State.deploy_config.Theme = request.theme
    return {"theme": request.theme}
