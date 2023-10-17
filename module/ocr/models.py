from pponnxcr import TextSystem as TextSystem_

from module.base.decorator import cached_property, del_cached_property
from module.exception import ScriptError

DIC_LANG_TO_MODEL = {
    'cn': 'zhs',
    'en': 'en',
    'jp': 'ja',
    'tw': 'zht',
}


def lang2model(lang: str) -> str:
    """
    Args:
        lang: In-game language name, defined in VALID_LANG

    Returns:
        str: Model name, defined in pponnxcr.utility
    """
    return DIC_LANG_TO_MODEL.get(lang, lang)


def model2lang(model: str) -> str:
    """
    Args:
        model: Model name, defined in pponnxcr.utility

    Returns:
        str: In-game language name, defined in VALID_LANG
    """
    for k, v in DIC_LANG_TO_MODEL.items():
        if model == v:
            return k
    return model


class TextSystem(TextSystem_):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_recognizer.rec_batch_num = 1


class OcrModel:
    def get_by_model(self, model: str) -> TextSystem:
        try:
            return self.__getattribute__(model)
        except AttributeError:
            raise ScriptError(f'OCR model "{model}" does not exists')

    def get_by_lang(self, lang: str) -> TextSystem:
        try:
            model = lang2model(lang)
            return self.__getattribute__(model)
        except AttributeError:
            raise ScriptError(f'OCR model under lang "{lang}" does not exists')

    def resource_release(self):
        del_cached_property(self, 'zhs')
        del_cached_property(self, 'en')
        del_cached_property(self, 'ja')
        del_cached_property(self, 'zht')

    @cached_property
    def zhs(self):
        return TextSystem('zhs')

    @cached_property
    def en(self):
        return TextSystem('en')

    @cached_property
    def ja(self):
        return TextSystem('ja')

    @cached_property
    def zht(self):
        return TextSystem('zht')


OCR_MODEL = OcrModel()
