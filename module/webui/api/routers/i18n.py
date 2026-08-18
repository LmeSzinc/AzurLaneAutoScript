from fastapi import APIRouter

from module.webui.api.models import LanguageRequest, LanguageResponse
from module.webui.lang import dic_lang, set_language

router = APIRouter(tags=["i18n"])


@router.get("/i18n/{lang}", response_model=dict[str, str])
def get_i18n(lang: str):
    return dic_lang.get(lang, dic_lang.get("en-US", {}))


@router.post("/language", response_model=LanguageResponse)
def set_language_api(request: LanguageRequest):
    from module.webui import lang

    set_language(request.language)
    return {"language": lang.LANG}
