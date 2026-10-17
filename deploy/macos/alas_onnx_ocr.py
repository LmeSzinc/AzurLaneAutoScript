"""Native Apple Silicon inference using Alas's original game-trained OCR weights."""
import os
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from convert_models import fingerprint


class MacOcr:
    CNOCR_CONTEXT = 'cpu'

    def __init__(self, model_name='densenet-lite-gru', model_epoch=None,
                 cand_alphabet=None, root=None, context='cpu', name=None):
        if model_name != 'densenet-lite-gru' or root is None or model_epoch is None:
            raise ValueError('This adapter requires the bundled CnOcr DenseNet/GRU models')
        self.name = name or Path(root).name
        self.root = Path(root).resolve()
        bundled = Path(__file__).resolve().parents[2] / 'bin' / 'cnocr_models'
        if self.root.parent != bundled or self.root.name not in ('azur_lane', 'azur_lane_jp', 'cnocr', 'jp', 'tw'):
            raise ValueError('This adapter only loads the five bundled models under bin/cnocr_models')
        self.epoch = model_epoch
        self._cand_alphabet = cand_alphabet
        self._session = None
        self._lock = threading.Lock()
        self._alphabet = [None] + [line.replace('<space>', ' ') for line in
                                  (self.root / 'label_cn.txt').read_text(encoding='utf-8').splitlines()]

    def _load(self):
        if self._session is not None:
            return self._session
        with self._lock:
            if self._session is None:
                import onnxruntime as ort
                path = Path(__file__).parent / 'models' / f'{self.root.name}.onnx'
                if not path.is_file():
                    raise RuntimeError('OCR model missing; run deploy/macos/convert_models.py before starting Alas')
                options = ort.SessionOptions()
                options.intra_op_num_threads = 1
                options.inter_op_num_threads = 1
                session = ort.InferenceSession(str(path), sess_options=options,
                                               providers=['CPUExecutionProvider'])
                if session.get_modelmeta().custom_metadata_map.get('source_sha256') != fingerprint(self.root, self.epoch):
                    raise RuntimeError('OCR source models changed; rerun deploy/macos/convert_models.py')
                from module.logger import logger
                logger.info(f'OCR backend: ONNX Runtime {ort.__version__}, model={self.name}, provider=CPUExecutionProvider')
                self._session = session
        return self._session

    @staticmethod
    def _image(image):
        if isinstance(image, (str, os.PathLike)):
            with Image.open(image) as source:
                return np.asarray(source.convert('L'))
        if isinstance(image, Image.Image):
            return np.asarray(image.convert('L'))
        image = np.asarray(image)
        if image.ndim == 3:
            if image.shape[2] == 1:
                image = image[:, :, 0]
            else:
                image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        if image.ndim != 2 or 0 in image.shape:
            raise ValueError('OCR requires a nonempty grayscale or RGB image')
        return image

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None):
        if not len(img_list):
            return []
        images = [self._image(image) for image in img_list]
        widths = [max(4, int(round(32 / image.shape[0] * image.shape[1]))) for image in images]
        data = np.zeros((len(images), 1, 32, max(widths)), dtype=np.float32)
        for index, (image, width) in enumerate(zip(images, widths)):
            data[index, 0, :, :width] = cv2.resize(image, (width, 32)).astype(np.float32) / 255.0
        probabilities = self._load().run(None, {'data': data})[0]
        # Preserve legacy whitelist and confidence behavior: do not renormalize.
        if cand_alphabet is not None:
            allowed = {0} | {i for i, char in enumerate(self._alphabet) if char is not None and char in cand_alphabet}
            probabilities[:, :, [i for i in range(len(self._alphabet)) if i not in allowed]] = 0
        ids = probabilities.argmax(axis=2)
        ids[probabilities.max(axis=2) <= 0.5] = 0
        results = []
        for index, width in enumerate(widths):
            sequence = ids[:, index].copy()
            if width < max(widths):
                sequence[width // 4:] = 0
            chars, previous = [], 0
            for current in sequence:
                if current and current != previous:
                    chars.append(self._alphabet[current])
                previous = current
            results.append(chars)
        return results

    def atomic_ocr_for_single_line(self, img_fp, cand_alphabet=None):
        return self.atomic_ocr_for_single_lines([img_fp], cand_alphabet)[0]

    def atomic_ocr(self, img_fp, cand_alphabet=None):
        return self.atomic_ocr_for_single_lines([img_fp], cand_alphabet)

    def ocr_for_single_lines(self, img_list):
        return self.atomic_ocr_for_single_lines(img_list, self._cand_alphabet)

    def ocr_for_single_line(self, img_fp):
        return self.atomic_ocr_for_single_line(img_fp, self._cand_alphabet)

    def ocr(self, img_fp):
        return self.atomic_ocr(img_fp, self._cand_alphabet)

    def set_cand_alphabet(self, cand_alphabet):
        self._cand_alphabet = cand_alphabet

    def debug(self, img_list):
        return self.ocr_for_single_lines(img_list)
