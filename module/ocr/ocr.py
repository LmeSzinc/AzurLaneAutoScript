import time

from PIL import Image

from module.base.button import Button
from module.base.utils import *
from module.exception import ScriptError
from module.logger import logger
from module.ocr.al_ocr import AlOcr

OCR_MODEL = {
    # Folder: ./bin/cnocr_models/azur_lane
    # Size: 3.25MB
    # Model: densenet-lite-gru
    # Epoch: 15
    # Validation accuracy: 99.43%
    # Font: Impact, AgencyFB-Regular, MStiffHeiHK-UltraBold
    # Charset: 0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ:/- (Letter 'O' and <space> is not included)
    # _num_classes: 39
    'azur_lane': AlOcr(model_name='densenet-lite-gru', model_epoch=15, root='./bin/cnocr_models/azur_lane', name='azur_lane'),

    # Folder: ./bin/cnocr_models/cnocr
    # Size: 9.51MB
    # Model: densenet-lite-gru
    # Epoch: 39
    # Validation accuracy: 99.04%
    # Font: Various
    # Charset: Number, English character, Chinese character, symbols, <space>
    # _num_classes: 6426
    'cnocr': AlOcr(model_name='densenet-lite-gru', model_epoch=39, root='./bin/cnocr_models/cnocr', name='cnocr'),

    'jp': AlOcr(model_name='densenet-lite-gru', model_epoch=125, root='./bin/cnocr_models/jp', name='jp'),
}


class Ocr:
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet=None, name=None):
        """
        Args:
            buttons (Button, tuple, list[Button], list[tuple]): OCR area.
            lang (str): 'azur_lane' or 'cnocr'.
            letter (tuple(int)): Letter RGB.
            threshold (int):
            alphabet: Alphabet white list.
            name (str):
        """
        self.name = str(buttons) if isinstance(buttons, Button) else name
        self.buttons = buttons if isinstance(buttons, list) else [buttons]
        self.buttons = [button.area if isinstance(button, Button) else button for button in self.buttons]
        self.letter = letter
        self.threshold = threshold
        self.alphabet = alphabet
        self.cnocr = OCR_MODEL[lang]

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)

        return image.astype(np.uint8)

    def after_process(self, result):
        """
        Args:
            result (list[str]): ['第', '二', '行']

        Returns:
            str:
        """
        result = ''.join(result)

        return result

    def ocr(self, image, direct_ocr=False):
        start_time = time.time()

        self.cnocr.set_cand_alphabet(self.alphabet)
        if direct_ocr:
            image_list = [self.pre_process(np.array(i)) for i in image]
        else:
            image_list = [self.pre_process(np.array(image.crop(area))) for area in self.buttons]

        # This will show the images feed to OCR model
        # self.cnocr.debug(image_list)

        result_list = self.cnocr.ocr_for_single_lines(image_list)
        result_list = [self.after_process(result) for result in result_list]

        if len(self.buttons) == 1:
            result_list = result_list[0]
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str(result_list))

        return result_list


class Digit(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = int(result) if result else 0

        return result


class DigitCounter(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789/',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def ocr(self, image, direct_ocr=False):
        """
        DigitCounter only support doing OCR on one button.

        Args:
            image:
            direct_ocr:

        Returns:
            int, int, int: current, remain, total.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        result = result_list[0] if isinstance(result_list, list) else result_list

        try:
            current, total = result.split('/')
            current, total = int(current), int(total)
            current = min(current, total)
            return current, total - current, total
        except (IndexError, ValueError):
            logger.warning(f'Unexpected ocr result: {result_list}')
            return 0, 0, 0
