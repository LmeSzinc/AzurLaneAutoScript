
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import signal

from module.base.mask import Mask
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.map_detection.utils import *
from module.template.assets import *
from module.logger import logger
from module.base.button import ButtonGrid


DETECTING_AREA = (0, 0, 1280, 720)

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
        Because there is no cutting pretreatment, there will always be an invalid value in the return value

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

    def draw(self, lines=None, bg=None, expend=0):
        if bg is None:
            image = self.image.copy()
        else:
            image = bg.copy()
        image = Image.fromarray(image)
        if expend:
            image = ImageOps.expand(image, border=expend, fill=0)
        draw = ImageDraw.Draw(image)
        if lines is None:
            lines = self.horizontal.add(self.vertical)
        for rho, theta in zip(lines.rho, lines.theta):
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 10000 * (-b)) + expend
            y1 = int(y0 + 10000 * a) + expend
            x2 = int(x0 - 10000 * (-b)) + expend
            y2 = int(y0 - 10000 * a) + expend
            draw.line([x1, y1, x2, y2], 'white')

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

        logger.info(self.horizontal)

        # horizontal = Lines(inner_h, 1, self.config)

        # self.draw(horizontal)

        # testLines = horizontal.add(vertical)
        # print(testLines)
        # logger.info(vertical)

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

        return tuple_h[0][0], len(tuple_h)

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

        origin_h, length = self.DivideGrid()

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
        origin_h, length = self.DivideGrid()

        buttonList = ButtonGrid(
            origin=(EQUIPMENT_BASELINE, origin_h), delta=(159, 178), button_shape=(135, 135), grid_shape=(7, length), name='EQUIPMENT')

        areaList = []
        for i in buttonList.buttons():
            if self.Predict_Weapon_Upgrade(i.area):
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

    def Predict_Box_T4(self, area):
        image = self.crop(area=area)
        return TEMPLATE_BOX_T4.match(image, similarity=0.9)
