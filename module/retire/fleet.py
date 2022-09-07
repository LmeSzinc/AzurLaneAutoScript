import time
from typing import List, Tuple, Union

import cv2
import numpy as np

from module.base.utils import crop, float2str
from module.logger import logger
from module.ocr.ocr import Digit, Ocr


def get_features(image) -> Tuple[np.ndarray]:
    center: Tuple[np.ndarray] = (image.shape[0] // 2, image.shape[1] // 2)
    upper_feat: np.ndarray = np.sum(image[:center[0]], axis=0) / center[0]
    lower_feat: np.ndarray = np.sum(image[center[0]:], axis=0) / (image.shape[0] - center[0])
    left_feat: np.ndarray = np.sum(image.T[:center[1]], axis=0) / center[1]
    right_feat: np.ndarray = np.sum(image.T[center[1]:], axis=0) / (image.shape[1] - center[1])
    return upper_feat, lower_feat, left_feat, right_feat


def cosine_similarity(x1, x2) -> float:
    if np.linalg.norm(x1) == 0 or np.linalg.norm(x2) == 0:
        return 0
    cosine: float = np.dot(x1, x2) / (np.linalg.norm(x1) * np.linalg.norm(x2))
    return 0.5 + 0.5 * cosine


class FleetOcr(Digit):
    def __init__(self, buttons, lang='azur_lane', letter=..., threshold=128, alphabet='0123456789', name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)
        self.digit_features = [np.load(f'./bin/fleet_ocr_features/{i}.npy', allow_pickle=True) for i in range(1, 7)]

    def pre_process(self, image):
        # Invert
        image = ~image
        # Use only the green channel
        image[:, :, 0] = image[:, :, 2] = image[:, :, 1]
        # Graying and binarizing
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, image = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)
        # Invert and compress value
        image = ~image / 255

        return image

    def ocr(self, image, direct_ocr=False) -> Union[int, List[int]]:
        """
        This is a very raw override method.
        The fleet index cannot be recognized by Alas's OCR module,
        however, it looks similar to LED segment displays.
        Therefore, a very raw method can be used.

        Consider a digit on LED segment displays,
        it's composed of 7 LEDs like:
        -----           -----
        |                   |
        -----    or     -----
        |   |           |
        -----           -----
        Along the horizontal and vertical central axes, the number is divided
        in four parts: up, bottom, left and right. Calc histogram of each part,
        then we get four feature vectors. Cosine similarity is used to measure
        their similarity. The max one which meets threshold is the answer.
        """
        start_time = time.time()
        if direct_ocr:
            image_list = [self.pre_process(i) for i in image]
        else:
            image_list = [self.pre_process(crop(image, area)) for area in self.buttons]

        result_list = [self.predict(get_features(x)) for x in image_list]

        if len(self.buttons) == 1:
            result_list = result_list[0]
        if Ocr.SHOW_LOG:
            logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                        text=str(result_list))

        return result_list

    def predict(self, x, threshold=0.95):
        sims = [
            np.mean([cosine_similarity(feature[i], x[i]) for i in range(0, 4)])
            for feature in self.digit_features
        ]

        if np.max(sims) >= threshold:
            return np.argmax(sims) + 1

        return 0

    def _feature_extract(self):
        """
        If you need to re-extract features in the future, follow these steps.
        1.  Prepare pics with fleet index, which can be obtained by taking
            screenshots in the dock. However, DO NOT drag the scroll bar because
            area is defined according to the initial positon.
        2.  Crop and pre-process the pics. You can use a code like this:
                cnt = 0
                path = r'XXXX'
                pics = [XXXX]
                for image in pics:
                    image_list = [self.pre_process(crop(image, area)) for area in self.buttons]
                    for img in image_list:
                        cv2.imwrite(f'{path}/{cnt}.png', img * 255)
                        cnt += 1

                Args:
                    pics: pics with fleet index. Use Alas's method to load it
                    path: path to save the image files
        3.  Label and classify the pictures according to the numbers on them.
            You can simply label them by moving the pics with number '1' into folder '1', etc.
            Those which does not contain numbers don't need to do so.
        4.  Calculate the mean value of features and take it as the feature of a certain number.
            Use a code like this:
                pics = [XXXX]
                path = r'XXXX'
                features = []
                for image in pics:
                    image = self.pre_process(image)
                    features.append(get_features(image))
                features = np.array(features)
                features = np.mean(features, axis=0)
                np.save(f'{path}/XXXX.npy', features)

                Args:
                    pics: pics belonging to the same category. Use Alas's method to load it
                    path: path to save the feature file
        """
        pass
