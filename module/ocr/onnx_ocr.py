import os

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

from module.exception import RequestHumanTakeover
from module.logger import logger
from module.webui.setting import State


class OnnxOcr:
    def __init__(
            self,
            model_name='densenet-lite-gru',
            model_epoch=None,
            cand_alphabet=None,
            root=None,
            context='cpu',
            name=None,
    ):
        self._args = (model_name, model_epoch, cand_alphabet, root, context, name)
        self._model_loaded = False

    def init(
            self,
            model_name='densenet-lite-gru',
            model_epoch=None,
            cand_alphabet=None,
            root=None,
            context='cpu',
            name=None,
    ):
        self._model_name = model_name
        self._model_epoch = model_epoch
        self._model_dir = root
        self._assert_and_prepare_model_files()
        self._alphabet, self._inv_alph_dict = self._read_charset(
            os.path.join(self._model_dir, 'label_cn.txt')
        )
        self._cand_alph_idx = None

        options = ort.SessionOptions()
        threads = State.deploy_config.OnnxIntraOpThreads
        if isinstance(threads, int) and threads > 0:
            options.intra_op_num_threads = threads

        logger.info('Loading OCR model: %s' % self._model_dir)
        model = os.path.join(self._model_dir, 'model.onnx')
        self._session = ort.InferenceSession(
            model,
            sess_options=options,
            providers=['CPUExecutionProvider'],
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name

    @staticmethod
    def _read_charset(charset_fp):
        alphabet = [None]
        with open(charset_fp, encoding='utf-8') as fp:
            for line in fp:
                alphabet.append(line.rstrip('\n'))
        try:
            alphabet[alphabet.index('<space>')] = ' '
        except ValueError:
            pass
        inv_alph_dict = {_char: idx for idx, _char in enumerate(alphabet)}
        return alphabet, inv_alph_dict

    def _assert_and_prepare_model_files(self):
        model_files = ['label_cn.txt', 'model.onnx']
        for file in model_files:
            if not os.path.exists(os.path.join(self._model_dir, file)):
                logger.warning(f'Ocr model not prepared: {self._model_dir}')
                logger.warning(f'Required files: {model_files}')
                logger.critical('Please check if required files of pre-trained OCR model exist')
                raise RequestHumanTakeover

    def _ensure_loaded(self):
        if not self._model_loaded:
            self.init(*self._args)
            self._model_loaded = True

    def set_cand_alphabet(self, cand_alphabet):
        self._ensure_loaded()
        if cand_alphabet is None:
            self._cand_alph_idx = None
        else:
            self._cand_alph_idx = [0] + [self._inv_alph_dict[word] for word in cand_alphabet]
            self._cand_alph_idx.sort()

    def ocr(self, img_fp):
        self._ensure_loaded()
        if isinstance(img_fp, str):
            if not os.path.isfile(img_fp):
                raise FileNotFoundError(img_fp)
            img = np.array(Image.open(img_fp).convert('RGB'))
        elif isinstance(img_fp, np.ndarray):
            img = img_fp
        else:
            raise TypeError('Inappropriate argument type.')
        if min(img.shape[0], img.shape[1]) < 2:
            return ''
        if img.mean() < 145:
            img = 255 - img
        line_imgs = self._line_split(img)
        return self.ocr_for_single_lines(line_imgs)

    def ocr_for_single_line(self, img_fp):
        self._ensure_loaded()
        if isinstance(img_fp, str):
            if not os.path.isfile(img_fp):
                raise FileNotFoundError(img_fp)
            img = np.array(Image.open(img_fp).convert('L'))
        elif isinstance(img_fp, np.ndarray):
            img = img_fp
        else:
            raise TypeError('Inappropriate argument type.')
        return self.ocr_for_single_lines([img])[0]

    def ocr_for_single_lines(self, img_list):
        self._ensure_loaded()
        if len(img_list) == 0:
            return []
        img_list = [self._preprocess_img_array(img) for img in img_list]
        batch_size = len(img_list)
        img_list, img_widths = self._pad_arrays(img_list)

        prob = self._predict(np.array(img_list, dtype=np.float32))
        prob = np.reshape(prob, (-1, batch_size, prob.shape[1]))
        if self._cand_alph_idx is not None:
            prob = prob * self._gen_mask(prob.shape)

        max_width = max(img_widths)
        res = []
        for i in range(batch_size):
            res.append(self._gen_line_pred_chars(prob[:, i, :], img_widths[i], max_width))
        return res

    def atomic_ocr(self, img_fp, cand_alphabet=None):
        self.set_cand_alphabet(cand_alphabet)
        return self.ocr(img_fp)

    def atomic_ocr_for_single_line(self, img_fp, cand_alphabet=None):
        self.set_cand_alphabet(cand_alphabet)
        return self.ocr_for_single_line(img_fp)

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None):
        self.set_cand_alphabet(cand_alphabet)
        return self.ocr_for_single_lines(img_list)

    @staticmethod
    def _preprocess_img_array(img):
        if len(img.shape) == 3 and img.shape[2] == 3:
            if img.dtype != np.dtype('uint8'):
                img = img.astype('uint8')
            img = np.array(Image.fromarray(img).convert('L'))
        new_width = int(round(32 / img.shape[0] * img.shape[1]))
        img = cv2.resize(img, (new_width, 32))
        img = np.expand_dims(img, 0).astype('float32') / 255.0
        return img

    @staticmethod
    def _pad_arrays(img_list):
        img_widths = [img.shape[2] for img in img_list]
        if len(img_list) <= 1:
            return img_list, img_widths
        max_width = max(img_widths)
        pad_width = [(0, 0), (0, 0), (0, 0)]
        padded_img_list = []
        for img in img_list:
            if img.shape[2] < max_width:
                pad_width[2] = (0, max_width - img.shape[2])
                img = np.pad(img, pad_width, 'constant', constant_values=0.0)
            padded_img_list.append(img)
        return padded_img_list, img_widths

    def _predict(self, sample):
        return self._session.run([self._output_name], {self._input_name: sample})[0]

    def _gen_mask(self, prob_shape):
        mask_shape = list(prob_shape)
        mask_shape[1] = 1
        mask = np.zeros(mask_shape, dtype='int8')
        mask[:, :, self._cand_alph_idx] = 1
        return mask

    def _gen_line_pred_chars(self, line_prob, img_width, max_img_width):
        class_ids = np.argmax(line_prob, axis=-1)
        class_ids *= np.max(line_prob, axis=-1) > 0.5
        if img_width < max_img_width:
            end_idx = img_width // 4
            if end_idx < len(class_ids):
                class_ids[end_idx:] = 0
        prediction = self._ctc_label(class_ids.tolist())
        return [self._alphabet[p] for p in prediction]

    @staticmethod
    def _ctc_label(class_ids):
        prediction = []
        previous = 0
        for current in class_ids:
            if current != 0 and current != previous:
                prediction.append(current)
            previous = current
        return prediction

    @staticmethod
    def _line_split(img):
        image = Image.fromarray(img)
        gray = np.array(image.convert('L'))
        binary = gray < 145
        project = np.sum(binary, axis=1)
        blank = np.where(project == 0)[0]
        if len(blank) == 0:
            return [np.array(image)]

        borders = np.concatenate(([-1], blank, [gray.shape[0]]))
        spans = []
        for start, end in zip(borders[:-1], borders[1:]):
            if end - start > 10:
                spans.append((start + 1, end))
        if not spans:
            return [np.array(image)]

        result = []
        for start, end in spans:
            start = max(0, start - 2)
            end = min(gray.shape[0], end + 2)
            result.append(np.array(image.crop((0, start, gray.shape[1], end))))
        return result

    def debug(self, img_list):
        self._ensure_loaded()
        img_list = [(self._preprocess_img_array(img) * 255.0).astype(np.uint8) for img in img_list]
        img_list, _ = self._pad_arrays(img_list)
        image = cv2.hconcat(img_list)[0, :, :]
        Image.fromarray(image).show()
