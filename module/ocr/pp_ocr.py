import math
import os

import cv2
import numpy as np
import onnxruntime as ort
from module.exception import RequestHumanTakeover
from module.logger import logger

logger.info('Loading PP-OCR dependencies')


class PpOcr:
    # cpu only

    def __init__(
            self,
            model_name='ppocrv5',
            cand_alphabet=None,
            root='./bin/ppocr_models/ppocrv5',
            name=None,
    ):
        self._args = (model_name, cand_alphabet, root, name)
        self._model_loaded = False

    def init(
            self,
            model_name='ppocrv5',
            cand_alphabet=None,
            root='./bin/ppocr_models',
            name=None,
    ):
        """
        :param model_name: 模型名称
        :param cand_alphabet: 待识别字符所在的候选集合。默认为 `None`，表示不限定识别字符范围
        :param root: 模型文件所在的根目录
        :param name: 正在初始化的这个实例名称。如果需要同时初始化多个实例，需要为不同的实例指定不同的名称。
        """
        self._model_name = model_name
        self._model_dir = root

        self._assert_and_prepare_model_files()
        self._alphabet = self._read_charset(
            os.path.join(self._model_dir, 'label.txt')
        )

        # Alphabet will be set before calling ocr.
        # self.set_cand_alphabet(cand_alphabet)
        self._cand_alphabet = None

        # Load model
        self._det_model = ort.InferenceSession(os.path.join(self._model_dir, 'det.onnx'))
        self._rec_model = ort.InferenceSession(os.path.join(self._model_dir, 'rec.onnx'))

    def ocr(self, img):
        """
        Only support one line OCR

        :param img: image file path; or color image np.ndarray,
            with shape (height, width, 3), and the channels should be RGB formatted.
        :return: List(Char), such as:
            ['第', '一', '行']
        """
        if not self._model_loaded:
            self.init(*self._args)
            self._model_loaded = True

        image = self._load_image(img)
        image = self._preprocess_image(image)
        preds = self._predict(image)
        result = self._postprocess_text(preds)
        return result

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None, batch_size=10, batch_threshold=20):
        """
        Multi images, one line OCR
        """
        if len(img_list) == 0:
            return []

        if not self._model_loaded:
            self.init(*self._args)
            self._model_loaded = True

        self.set_cand_alphabet(cand_alphabet)

        results = []
        for batch in self._batch_imgs(img_list, batch_size, batch_threshold):
            preds = self._predict(batch)
            results.extend(self._postprocess_text(preds))

        return results

    def detect_then_ocr(self, img, pad=10, threshold=0.6, mode=cv2.RETR_EXTERNAL, batch_size=10, batch_threshold=20,
                        debug=False):
        """
        Detect potential text regions and perform OCR.
        The order of detected text is not guaranteed.

        :param img: image file path; or color image np.ndarray,
            with shape (height, width, 3), and the channels should be RGB formatted.
        :param pad: pad detected text region, both width and height.
        :param threshold: threshold for detect text.
        :param mode: cv2.findCounters(), one of [RETR_EXTERNAL, RETR_LIST, RETR_CCOMP, RETR_TREE, RETR_FLOODFILL].
        :param batch_size: the batch size of text recognition.
        :param batch_threshold: images with width differences less than or equal to batch_threshold are placed in the same batch,
            ensuring similar dimensions within a batch and improving memory and computational efficiency.
        :param debug: debug mode.
        :return: A tuple containing two lists:
            the recognized text and its corresponding region (x, y, w, h).
        """
        if not self._model_loaded:
            self.init(*self._args)
            self._model_loaded = True

        img = self._load_image(img)
        image = img
        image = self._preprocess_image(image, 'det')
        boxes = self._detect(image, pad, threshold, mode)
        boxes.sort(key=lambda box: box[2])

        crops, regions = [], []
        for box in boxes:
            x, y, w, h = box
            crop = img[y:y + h, x:x + w, :]
            crops.append(crop)

        texts, index = [], 0
        for batch in self._batch_imgs(crops, batch_size, batch_threshold):
            preds = self._predict(batch)
            batch_text = self._postprocess_text(preds)
            for chars in batch_text:
                text = ''.join([c.strip() for c in chars])
                if text:
                    texts.append(text)
                    regions.append(boxes[index])

                if debug:
                    x, y, w, h = boxes[index]
                    logger.info(f'[OCR] Text: {text}, Region: ({x}, {y}), ({x + w}, {y + h})')
                    tmp = cv2.rectangle(img.copy(), (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.imshow("ppocr", cv2.cvtColor(tmp, cv2.COLOR_RGB2BGR))
                    cv2.waitKey(0)

                index += 1

        return texts, regions

    def set_cand_alphabet(self, cand_alphabet):
        self._cand_alphabet = [c for c in cand_alphabet] if cand_alphabet else None

    def _assert_and_prepare_model_files(self):
        model_dir = self._model_dir
        model_files = [
            'label.txt',
            'det.onnx',
            'rec.onnx'
        ]
        file_prepared = True
        for f in model_files:
            f = os.path.join(model_dir, f)
            if not os.path.exists(f):
                file_prepared = False
                logger.warning('can not find file %s', f)
                break

        if file_prepared:
            return

        logger.warning(f'Ocr model not prepared: {model_dir}')
        logger.warning(f'Required files: {model_files}')
        logger.critical('Please check if required files of pre-trained OCR model exist')
        raise RequestHumanTakeover

    def _read_charset(self, filename):
        with open(filename, encoding='utf-8') as f:
            alphabet = [line.rstrip('\n') for line in f.readlines()]
        alphabet.append('')
        return np.array(alphabet)

    def _load_image(self, img):
        if isinstance(img, str):
            if not os.path.isfile(img):
                raise FileNotFoundError
            img = cv2.imread(img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif isinstance(img, np.ndarray):
            img = img
        elif isinstance(img, list):
            img = np.array(img[0])
        else:
            raise TypeError
        return img

    def _preprocess_image(self, img, resize_mode='rec'):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        if resize_mode == 'rec':
            if img.shape[0] > img.shape[1] * 1.5:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # Image's height must be 48
            scale = 48 / img.shape[0]
            new_w = int(img.shape[1] * scale)
            img = cv2.resize(img, (new_w, 48))

        elif resize_mode == 'det':
            pad_h = math.ceil(img.shape[0] / 32) * 32 - img.shape[0]
            pad_w = math.ceil(img.shape[1] / 32) * 32 - img.shape[1]
            img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)))

        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        img = img.astype('float32') / 255.0
        img = (img - 0.5) / 0.5
        return img

    def _batch_imgs(self, imgs, batch_size=None, batch_threshold=20):
        def pad_img():
            batch_padded = []
            for b in batch:
                padded = np.pad(b, ((0, 0), (0, 0), (0, 0), (0, max_width - b.shape[3])))
                batch_padded.append(padded)
            return np.vstack(batch_padded)

        batch = []
        min_width, max_width = 1280, 0
        for img in imgs:
            img = self._load_image(img)
            img = self._preprocess_image(img)

            min_width = min(min_width, img.shape[3])
            max_width = max(max_width, img.shape[3])

            if isinstance(batch_threshold, int) and max_width - min_width > batch_threshold:
                yield pad_img()
                batch = []
                min_width, max_width = img.shape[3], img.shape[3]

            batch.append(img)

            if len(batch) == batch_size:
                yield pad_img()
                batch = []
                min_width, max_width = 1280, 0

        if batch:
            yield pad_img()

    def _detect(self, img, pad=10, threshold=0.3, mode=cv2.RETR_EXTERNAL):
        input_name = self._det_model.get_inputs()[0].name
        preds = self._det_model.run(None, {input_name: img})[0][0, 0]
        score_map = (preds > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(score_map, mode, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [self._expand_rect(cv2.boundingRect(cnt), img.shape, pad) for cnt in contours]
        return boxes

    def _expand_rect(self, rect, img_shape, pad=10):
        x, y, w, h = rect
        w, h = min(img_shape[3] - 1, w + pad), min(img_shape[2] - 1, h + pad)
        x, y = max(0, x - pad // 2), max(0, y - pad // 2)
        return x, y, w, h

    def _predict(self, img):
        input_name = self._rec_model.get_inputs()[0].name
        preds = self._rec_model.run(None, {input_name: img})[0]
        preds = preds.argmax(axis=2) - 1
        return preds

    def _postprocess_text(self, preds):
        if len(preds.shape) == 1:
            preds = np.expand_dims(preds, 0)

        result = []
        for pred in preds:
            chars = self._alphabet[pred]
            if self._cand_alphabet:
                mask = np.isin(chars, self._cand_alphabet)
                chars = chars[mask]
            result.append(chars)

        return result
