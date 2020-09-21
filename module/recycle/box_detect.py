
import cv2
import numpy as np
from PIL import Image
from scipy import signal

from module.base.mask import Mask
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.deploy.utils import cached_property
from module.template.assets import *
from module.logger import logger
from module.base.button import ButtonGrid


EQUIP_MASK = Mask(file='./assets/mask/MASK_EQUIPMENT.png')

INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
    'height': (230, 255),
    'width': (0.9, 10),
    'prominence': 10,
    'distance': 35,
}


MATERIAL_BASELINE = 140
EQUIPMENT_BASELINE = 135


class box_detect:
    """

    """
    image: np.ndarray

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    @cached_property
    def ui_mask(self):

        image = Image.fromarray(EQUIP_MASK.image).convert('RGB')
        return np.array(image)

    def find_Y_peaks(self, image, baseLine, param):
        """
        Args:
            image(np.darray): Processed screenshot.
            baseLine(int): base vertical line used for find peaks
            param(dict): Parameters use in scipy.signal.find_peaks.

        Returns:
            peaks(list): a list of peaks

        """
        image = cv2.bitwise_and(image, self.ui_mask)

        image = Image.fromarray(image).convert('RGB')

        bar = np.mean(
            rgb2gray(np.array(image.crop((baseLine, 0, baseLine + 2, 720)))), axis=1)
        peaks, properties = signal.find_peaks(bar, **param)
        return peaks

    def load(self, baseLine):
        image = self.image
        image = np.array(image)

        self.image = image

        # Lines detection
        self.horizontal = self.find_Y_peaks(
            image,
            baseLine,
            param=INTERNAL_LINES_FIND_PEAKS_PARAMETERS
        )

    def crop(self, area, shape=None):
        """Crop image and rescale to target shape. Eliminate the effect of perspective.

        Args:
            area (tuple): upper_left_x, upper_left_y, bottom_right_x, bottom_right_y, such as (-1, -1, 1, 1).
            shape (tuple): Output image shape, (width, height).

        Returns:
            np.ndarray: Shape (height, width, channel).
        """
        area = np.array(area)

        image = crop(self.image, area=np.rint(area).astype(int))
        if shape is not None:
            # Follow the default re-sampling filter in pillow, which is BICUBIC.
            image = cv2.resize(image, shape, interpolation=cv2.INTER_CUBIC)
        return image

    def DivideGrid(self):
        list_h = self.horizontal

        tuple_h = []
        for i in range(0, len(list_h) - 1):
            if(list_h[i + 1] - list_h[i] > 130):
                tuple_h.append((list_h[i], list_h[i + 1]))
        if tuple_h:
            return tuple_h[0][0], len(tuple_h)
        else:
            raise NameError('EmptyList')

        # print(len(self.grid))

    def detectBoxArea(self, image, boxList={'T1': 1, 'T2': 1, 'T3': 1}):
        """
        Args:
            image(PIL.Image, np.ndarray): image used for detected
            boxList(list): filter
        Return value:
            areaList(list): button list
        """
        self.image = image
        self.load(MATERIAL_BASELINE)

        try:
            origin_h, length = self.DivideGrid()
        except NameError('EmptyList'):
            return False

        buttonList = ButtonGrid(
            origin=(MATERIAL_BASELINE, origin_h), delta=(159, 178), button_shape=(135, 135), grid_shape=(7, length), name='EQUIPMENT')

        areaList = []
        for i in buttonList.buttons():
            if boxList['T1'] and self.Predict_Box_T1(i.area):
                areaList.append(i)
                continue

            if boxList['T2'] and self.Predict_Box_T2(i.area):
                areaList.append(i)
                continue

            if boxList['T3'] and self.Predict_Box_T3(i.area):
                areaList.append(i)
                continue

        return areaList

    def detectWeaponArea(self, image):
        """
        Args:
            image(PIL.Image, np.ndarray): image used for detected

        Return value:
            areaList(list): button list 
        """
        self.image = image
        self.load(EQUIPMENT_BASELINE)

        try:
            origin_h, length = self.DivideGrid()
        except NameError('EmptyList'):
            return False

        buttonList = ButtonGrid(
            origin=(EQUIPMENT_BASELINE, origin_h), delta=(159, 178), button_shape=(135, 135), grid_shape=(7, length), name='EQUIPMENT')

        areaList = []
        for i in buttonList.buttons():
            if not self.Predict_Weapon_Upgrade(i.area):
                areaList.append(i)

        # logger.info(areaList)
        return areaList

    def Predict_Weapon_Upgrade(self, area):

        image = self.crop(area=area)

        # logger.info(TEMPLATE_WEAPON_PLUS.match_result(image))
        return TEMPLATE_WEAPON_PLUS.match(image, similarity=0.8)

    def Predict_Box_T1(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T1.match(image, similarity=0.9)

    def Predict_Box_T2(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T2.match(image, similarity=0.9)

    def Predict_Box_T3(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T3.match(image, similarity=0.9)
