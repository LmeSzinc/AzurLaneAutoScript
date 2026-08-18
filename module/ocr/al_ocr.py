import itertools
import os

import cv2
import numpy as np
import onnxruntime
from PIL import Image

from module.exception import RequestHumanTakeover
from module.logger import logger

# The OCR models are small (3-9MB); spawning one thread per core (24 here)
# for every inference call creates a thread-creation storm that contends with
# the desktop/emulator. Two threads are faster AND smoother (measured ~18%).
cv2.setNumThreads(2)

IMG_HEIGHT = 32
SEQ_LEN_CMPR_RATIO = 4  # densenet-lite downsamples width by 4x


class AlOcr:
    """
    OCR engine backed by onnxruntime, API-compatible with the previous
    cnocr 1.2.2 (mxnet replaced by onnxruntime).

    Models are converted from the original self-trained mxnet checkpoints,
    see dev_tools/ocr_convert/build_onnx.py. The model directory must
    contain:
        <name>.onnx    ONNX model, input 'data' (N, 1, 32, W), output 'probs'
        label_cn.txt   charset, one char per line (first entry is the blank)

    Inference behavior is identical to cnocr 1.2.2 + Alas patches:
        - preprocess: resize to height 32, normalize to [0, 1]
        - decode: argmax with confidence filter (prob > 0.5), width truncation,
          CTC label collapse
        - cand_alphabet: mask applied on softmax probabilities
    """

    def __init__(
        self,
        model_name="densenet-lite-gru",
        model_epoch=None,
        cand_alphabet=None,
        root="./bin/cnocr_models/azur_lane",
        context="cpu",
        name=None,
    ):
        self._args = (model_name, model_epoch, cand_alphabet, root, context, name)
        self._model_loaded = False
        self._session = None
        self._alphabet = None
        self._inv_alph_dict = None
        self._cand_alph_idx = None
        self._net_prefix = None if name == "" else name

    def init(
        self,
        model_name="densenet-lite-gru",
        model_epoch=None,
        cand_alphabet=None,
        root="./bin/cnocr_models/azur_lane",
        context="cpu",
        name=None,
    ):
        """
        :param model_name: model file name without extension
        :param model_epoch: kept for API compatibility, unused
        :param cand_alphabet: candidate character set, None for unrestricted
        :param root: directory containing <name>.onnx and label_cn.txt
        :param context: 'cpu' or 'gpu' (onnxruntime provider)
        :param name: instance name, also the model file name
        """
        model_name = name or model_name
        model_dir = root
        onnx_path = os.path.join(model_dir, f"{model_name}.onnx")
        label_path = os.path.join(model_dir, "label_cn.txt")
        self._assert_and_prepare_model_files(onnx_path, label_path)

        self._alphabet, self._inv_alph_dict = self._read_charset(label_path)
        self._cand_alph_idx = None
        # Alphabet will be set before calling ocr via atomic_ocr_* methods.
        # self.set_cand_alphabet(cand_alphabet)

        providers = ["CPUExecutionProvider"]
        if context == "gpu" and "CUDAExecutionProvider" in onnxruntime.get_available_providers():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        logger.info(f"Loading OCR model: {model_dir}")
        sess_options = onnxruntime.SessionOptions()
        # Cap intra-op threads: the default (one per core) is slower and floods
        # the scheduler with short-lived threads on many-core machines.
        sess_options.intra_op_num_threads = 2
        self._session = onnxruntime.InferenceSession(onnx_path, providers=providers, sess_options=sess_options)

    @staticmethod
    def _read_charset(charset_fp):
        alphabet = [None]
        # The 0-th element is reserved for the CTC blank.
        with open(charset_fp, encoding="utf-8") as fp:
            for line in fp:
                alphabet.append(line.rstrip("\n"))
        try:
            space_idx = alphabet.index("<space>")
            alphabet[space_idx] = " "
        except ValueError:
            pass
        inv_alph_dict = {_char: idx for idx, _char in enumerate(alphabet)}
        return alphabet, inv_alph_dict

    @staticmethod
    def _assert_and_prepare_model_files(onnx_path, label_path):
        missing = [f for f in (onnx_path, label_path) if not os.path.exists(f)]
        if missing:
            logger.warning(f"Ocr model not prepared: {missing}")
            logger.critical("Please check if required files of pre-trained OCR model exist")
            raise RequestHumanTakeover

    def set_cand_alphabet(self, cand_alphabet):
        """
        Set the candidate character set. None means unrestricted.

        :param cand_alphabet: candidate characters
        """
        if cand_alphabet is None:
            self._cand_alph_idx = None
        else:
            self._cand_alph_idx = [0] + [self._inv_alph_dict[word] for word in cand_alphabet]
            self._cand_alph_idx.sort()

    def _ensure_loaded(self):
        if not self._model_loaded:
            self.init(*self._args)
            self._model_loaded = True

    def ocr(self, img_fp):
        self._ensure_loaded()
        return self._ocr(img_fp)

    def _ocr(self, img_fp):
        """
        :param img_fp: image file path, or color image np.ndarray with shape
            (height, width, 3). Multi-line images are split into lines.
        :return: list of list of chars, such as [['第', '一', '行'], ['第', '二', '行']]
        """
        if isinstance(img_fp, str):
            if not os.path.isfile(img_fp):
                raise FileNotFoundError(img_fp)
            img = cv2.imread(img_fp, cv2.IMREAD_COLOR)
        elif isinstance(img_fp, np.ndarray):
            img = img_fp
        else:
            raise TypeError("Inappropriate argument type.")
        if min(img.shape[0], img.shape[1]) < 2:
            return ""
        if img.mean() < 145:  # Invert dark-background images to white background
            img = 255 - img
        line_imgs = self._line_split(img)
        line_img_list = [line_img for line_img, _ in line_imgs]
        return self.ocr_for_single_lines(line_img_list)

    @staticmethod
    def _line_split(image, blank=True):
        """Split an image into text lines by horizontal projection.

        Ported from cnocr 1.2.2 line_split.

        :param image: PIL.Image or np.ndarray
        :param blank: keep margin above/below each line
        :return: list of [sub_image, (x1, y1, x2, y2)]
        """
        threshold = 145
        table = [1] * threshold + [0] * (256 - threshold)
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)

        image_ = image.convert("L")
        bn = image_.point(table, "1")
        bn_mat = np.array(bn)
        h, pic_len = bn_mat.shape
        project = np.sum(bn_mat, 1)
        pos = np.where(project <= 0)[0]
        if len(pos) == 0 or pos[0] != 0:
            pos = np.insert(pos, 0, 0)
        if pos[-1] != len(project):
            pos = np.append(pos, len(project))
        diff = np.diff(pos)

        if len(diff) == 0:
            return [[np.array(image), (0, 0, pic_len, h)]]

        width = np.max(diff)
        coordinate = list(itertools.pairwise(pos))
        info = list(zip(diff, coordinate, strict=False))
        info = list(filter(lambda x: x[0] > 10, info))

        split_pos = []
        temp = []
        for pos_info in info:
            if width - 2 <= pos_info[0] <= width:
                if temp:
                    split_pos.append(temp.pop(0))
                split_pos.append(pos_info)
            elif pos_info[0] < width - 2:
                temp.append(pos_info)
                if len(temp) > 1:
                    s, e = temp[0][1][0], temp[1][1][1]
                    if e - s <= width + 2:
                        temp = [(e - s, (s, e))]
                    else:
                        split_pos.append(temp.pop(0))

        if temp:
            split_pos.append(temp[0])

        # crop images with split_pos
        line_res = []
        if blank:
            if len(split_pos) == 1:
                pos_info = split_pos[0][1]
                ymin, ymax = max(0, pos_info[0] - 2), min(h, pos_info[1] + 2)
                return [[np.array(image.crop((0, ymin, pic_len, ymax))), (0, ymin, pic_len, ymax)]]

            length = len(split_pos)
            for i in range(length):
                if i == 0:
                    next_info = split_pos[i + 1]
                    margin = min(next_info[1][0] - split_pos[i][1][1], 2)
                    ymin, ymax = max(0, split_pos[i][1][0] - margin), split_pos[i][1][1] + margin
                    sub = image.crop((0, ymin, pic_len, ymax))
                elif i == length - 1:
                    pre_info = split_pos[i - 1]
                    margin = min(split_pos[i][1][0] - pre_info[1][1], 2)
                    ymin, ymax = split_pos[i][1][0] - margin, min(h, split_pos[i][1][1] + margin)
                    sub = image.crop((0, ymin, pic_len, ymax))
                else:
                    next_info = split_pos[i + 1]
                    pre_info = split_pos[i - 1]
                    margin = min(split_pos[i][1][0] - pre_info[1][1], next_info[1][0] - split_pos[i][1][0], 2)
                    ymin, ymax = split_pos[i][1][0] - margin, split_pos[i][1][1] + margin
                    sub = image.crop((0, ymin, pic_len, ymax))
                line_res.append([np.array(sub), (0, ymin, pic_len, ymax)])
        else:
            for pos_info in split_pos:
                sub = image.crop((0, pos_info[1][0], pic_len, pos_info[1][1]))
                line_res.append([np.array(sub), (0, pos_info[1][0], pic_len, pos_info[1][1])])

        return line_res

    def ocr_for_single_line(self, img_fp):
        self._ensure_loaded()
        if isinstance(img_fp, str):
            if not os.path.isfile(img_fp):
                raise FileNotFoundError(img_fp)
            img = cv2.imread(img_fp, cv2.IMREAD_GRAYSCALE)
        elif isinstance(img_fp, np.ndarray):
            img = img_fp
        else:
            raise TypeError("Inappropriate argument type.")
        res = self.ocr_for_single_lines([img])
        return res[0]

    def ocr_for_single_lines(self, img_list):
        """
        Batch recognize characters from a list of one-line images.

        :param img_list: list of images, each with shape [height, width] or
            [height, width, channel], values ranging from 0 to 255.
        :return: list of list of chars, such as [['第', '一', '行'], ...]
        """
        self._ensure_loaded()
        if len(img_list) == 0:
            return []
        img_list = [self._preprocess_img_array(img) for img in img_list]

        batch_size = len(img_list)
        img_list, img_widths = self._pad_arrays(img_list)

        prob = self._predict(np.ascontiguousarray(np.array(img_list, dtype="float32")))
        # [T*batch_size, num_classes] -> [T, batch_size, num_classes]
        prob = np.reshape(prob, (-1, batch_size, prob.shape[1]))

        if self._cand_alph_idx is not None:
            prob = prob * self._gen_mask(prob.shape)

        max_width = max(img_widths)
        res = []
        for i in range(batch_size):
            res.append(self._gen_line_pred_chars(prob[:, i, :], img_widths[i], max_width))
        return res

    def _predict(self, batch):
        return self._session.run(["probs"], {"data": batch})[0]

    def _gen_mask(self, prob_shape):
        mask_shape = list(prob_shape)
        mask_shape[1] = 1
        mask = np.zeros(mask_shape, dtype="int8")
        mask[:, :, self._cand_alph_idx] = 1
        return mask

    def _preprocess_img_array(self, img):
        """
        :param img: np.ndarray with shape [height, width] or
            [height, width, channel], channel 1 or 3.
        :return: np.ndarray with shape (1, height, width), float32 in [0, 1]
        """
        if len(img.shape) == 3 and img.shape[2] == 3:
            if img.dtype != np.dtype("uint8"):
                img = img.astype("uint8")
            # color to gray
            img = np.array(Image.fromarray(img).convert("L"))
        # Resize image using cv2.resize (same as the previous implementation)
        new_width = round(IMG_HEIGHT / img.shape[0] * img.shape[1])
        img = cv2.resize(img, (new_width, IMG_HEIGHT))
        img = np.expand_dims(img, 0).astype("float32") / 255.0
        return img

    @staticmethod
    def _pad_arrays(img_list):
        """Padding to make sure all the elements have the same width."""
        img_widths = [img.shape[2] for img in img_list]
        if len(img_list) <= 1:
            return img_list, img_widths
        max_width = max(img_widths)
        pad_width = [(0, 0), (0, 0), (0, 0)]
        padded_img_list = []
        for img in img_list:
            if img.shape[2] < max_width:
                pad_width[2] = (0, max_width - img.shape[2])
                img = np.pad(img, pad_width, "constant", constant_values=0.0)
            padded_img_list.append(img)
        return padded_img_list, img_widths

    def _gen_line_pred_chars(self, line_prob, img_width, max_img_width):
        """
        Get the predicted characters.

        :param line_prob: with shape of [seq_length, num_classes]
        :param img_width:
        :param max_img_width:
        """
        class_ids = np.argmax(line_prob, axis=-1)

        class_ids *= np.max(line_prob, axis=-1) > 0.5  # Delete low confidence result

        if img_width < max_img_width:
            comp_ratio = SEQ_LEN_CMPR_RATIO
            end_idx = img_width // comp_ratio
            if end_idx < len(class_ids):
                class_ids[end_idx:] = 0
        prediction, _ = self._ctc_label(class_ids.tolist())
        alphabet = self._alphabet
        res = [alphabet[p] if alphabet[p] != "<space>" else " " for p in prediction]

        return res

    @staticmethod
    def _ctc_label(p):
        """
        Iterates through p, identifying non-zero and non-repeating values,
        and returns them in a list.

        :param p: list of int
        :return: list of int, list of (start_idx, end_idx)
        """
        ret = []  # each element consists of [label_id, start_idx, end_idx]
        p1 = [0, *p]
        for i, _ in enumerate(p):
            c1 = p1[i]
            c2 = p1[i + 1]
            if (c2 == 0 or c2 != c1) and c1 != 0 and len(ret) > 0:
                ret[-1][-1] = i
            if c2 == 0 or c2 == c1:
                continue
            ret.append([c2, i, -1])

        if len(ret) == 0:
            return [], []
        if ret[-1][-1] < 0:
            ret[-1][-1] = len(p)

        label_ids = [ele[0] for ele in ret]
        start_end_idx = [(ele[1], ele[2]) for ele in ret]
        return label_ids, start_end_idx

    """
    Atomic version of the OCR methods above
    handling set_cand_alphabet inside
    """

    def atomic_ocr(self, img_fp, cand_alphabet=None):
        self._ensure_loaded()
        self.set_cand_alphabet(cand_alphabet)
        return self._ocr(img_fp)

    def atomic_ocr_for_single_line(self, img_fp, cand_alphabet=None):
        self._ensure_loaded()
        self.set_cand_alphabet(cand_alphabet)
        return self.ocr_for_single_line(img_fp)

    def atomic_ocr_for_single_lines(self, img_list, cand_alphabet=None):
        self._ensure_loaded()
        self.set_cand_alphabet(cand_alphabet)
        return self.ocr_for_single_lines(img_list)

    def debug(self, img_list):
        """
        Show the images feed to the OCR model.

        :param img_list: list of numpy array, (height, width)
        """
        self._ensure_loaded()
        img_list = [(self._preprocess_img_array(img) * 255.0).astype(np.uint8) for img in img_list]
        img_list, _img_widths = self._pad_arrays(img_list)
        image = cv2.hconcat(img_list)[0, :, :]
        Image.fromarray(image).show()
