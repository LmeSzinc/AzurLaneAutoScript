import time

import cv2
import numpy as np
from PIL import Image
from cnocr import CnOcr

from module.base.button import Button
from module.base.utils import extract_letters
from module.logger import logger

# OCR_MODELS = {
#     # Font: Impact, AgencyFB
#     # Charset: 0123456789
#     'digit': CnOcr(root='./bin/cnocr_models/digit', model_epoch=60),
#     # Font: Impact
#     # Charset: 0123456789ABCDEFSP-:/
#     'stage': CnOcr(root='./bin/cnocr_models/stage', model_epoch=56),
#
#     'cnocr': CnOcr(root='./bin/cnocr_models/cnocr', model_epoch=20)
# }
image_shape = (280, 32)
width_range = (0.6, 1.4)
text_length = (1, 6)
text_interval = (0, 10)
y_range = (-2, 2)


class Ocr:
    def __init__(self, buttons, lang, letter=(255, 255, 255), back=(0, 0, 0), mid_process_height=70, threshold=127,
                 additional_preprocess=None, use_binary=True, length=None, white_list=None, name='OCR'):
        """
        Args:
            lang (str): OCR model. in ['digit', 'cnocr'].
            letter (tuple(int)): Letter RGB.
            back (tuple(int)): Background RGB.
            mid_process_height (int): 70
            additional_preprocess (callable):
            use_binary (bool):
            length (int, tuple(int)): Expected length.
            white_list (str): Expected str.
            buttons (Button, List[Button]): Button or list of Button instance.
        """
        self.lang = lang
        # self.cnocr = OCR_MODELS[lang]
        self.letter = letter
        self.back = back
        self.mid_process_height = mid_process_height
        self.threshold = threshold
        self.additional_preprocess = additional_preprocess
        self.use_binary = use_binary
        self.length = (length, length) if isinstance(length, int) else length
        self.white_list = white_list
        self.buttons = buttons if isinstance(buttons, list) else [buttons]
        self.name = str(buttons) if isinstance(buttons, Button) else name

    def additional_preprocess_example(self, image):
        """
        Args:
            image (np.ndarray): data range: [0, 255], dtype: float. shape: [?, 70]

        Returns:
            np.ndarray: data range: [0, 255], dtype: float.
        """
        pass

    def pre_process(self, image):
        """
        Args:
            image: A cropped screenshot.

        Returns:
            np.ndarray: shape: [70, 280]. data range: [0, 1]
        """
        # Resize to height=70.
        size = (int(image.size[0] / image.size[1] * self.mid_process_height), self.mid_process_height)
        image = image.resize(size, Image.BILINEAR)

        # Set letter color to black, set background color to white.
        image = extract_letters(image, letter=self.letter, back=self.back)

        # Additional preprocess.
        if self.additional_preprocess is not None:
            image = self.additional_preprocess(image)

        # Binarization.
        if self.use_binary:
            _, image = cv2.threshold(image, self.threshold, 255, cv2.THRESH_BINARY)

        # Resize to input size.
        size = (int(image.shape[1] / image.shape[0] * image_shape[1]), image_shape[1])
        image = cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)

        # Left align
        x = np.where(np.mean(image, axis=0) < 220)[0]
        if len(x):
            x = x[0] - 2 if x[0] - 2 >= 2 else 0
            image = image[:, x:]

        # Pad to image_shape=(280, 32)
        diff_x = image_shape[0] - image.shape[1]
        if diff_x > 0:
            image = np.pad(image, ((0, 0), (0, diff_x)), mode='constant', constant_values=255)
        else:
            image = image[:, :image_shape[0]]

        # Image.fromarray(image.astype('uint8')).show()

        return image / 255.0

    def after_process(self, result):
        """
        Args:
            result (list[str]): ['第', '二', '行']

        Returns:
            str:
        """
        result = ''.join(result)

        if self.length is not None:
            if len(result) > self.length[1] or len(result) < self.length[0]:
                logger.warning(f'OCR result length unexpected. Expect: {self.length}. Result: {len(result)}')
        if self.white_list:
            for letter in result:
                if letter not in self.white_list:
                    logger.warning(f'OCR letter unexpected. Letter: {letter}. White_list: {self.white_list}')

        return result

    def ocr(self, image):
        start_time = time.time()

        image_list = [self.pre_process(image.crop(button.area)) for button in self.buttons]
        result_list = self.cnocr.ocr_for_single_lines(image_list)
        result_list = [self.after_process(result) for result in result_list]

        if len(self.buttons) == 1:
            result_list = result_list[0]
        logger.attr(name='%s %ss' % (self.name, str(round(time.time() - start_time, 3)).ljust(5, '0')),
                    text=str(result_list))

        return result_list


class Digit(Ocr):
    def __init__(self, buttons, letter=(255, 255, 255), back=(0, 0, 0), mid_process_height=70, threshold=127,
                 additional_preprocess=None, length=None, white_list=None, limit=None, name='OCR'):
        super().__init__(buttons=buttons, lang='digit', letter=letter, back=back, mid_process_height=mid_process_height,
                         threshold=threshold,
                         additional_preprocess=additional_preprocess, length=length, white_list=white_list, name=name)
        self.limit = (0, limit) if isinstance(limit, int) else limit

    def after_process(self, raw):
        """
        Returns:
            int:
        """
        raw = super().after_process(raw)
        if not raw:
            result = 0
        else:
            result = int(raw)

        if self.limit:
            if result < self.limit[0]:
                logger.info(f'OCR result smaller than expected. Expect: {self.limit}. Raw: {raw}. Treat as: {result}')
                result = self.limit[0]
            if result > self.limit[1]:
                logger.info(f'OCR result bigger than expected. Expect: {self.limit}. Raw: {raw}. Treat as: {result}')
                result = self.limit[1]

        return result
