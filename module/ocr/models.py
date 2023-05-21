from module.base.decorator import cached_property
from module.ocr.ppocr import TextSystem


class OcrModel:
    @cached_property
    def ch(self):
        return TextSystem()


OCR_MODEL = OcrModel()
