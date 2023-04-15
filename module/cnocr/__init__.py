"""
Copy from CnOCR (https://github.com/breezedeus/CnOCR) version 1.2.2 under Apache License 2.0

Modifications:
    - data_utils is deleted
    - logging setting in utils.py is deleted
"""
from .cn_ocr import CnOcr
from .consts import MODEL_VERSION, AVAILABLE_MODELS, NUMBERS, ENG_LETTERS
