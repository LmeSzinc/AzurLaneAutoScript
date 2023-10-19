import time

from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.logger import logger
from module.map_detection.homography import Homography
from module.map_detection.perspective import Perspective
from module.map_detection.utils import *

GLOBE_MAP = './assets/map_detection/os_globe_map.png'
GLOBE_MAP_SHAPE = (2570, 1696)


class GlobeDetection:
    """
    Detect globe map in Operation Siren.

    Examples:
        globe = GlobeDetection(AzurLaneConfig('template'))
        globe.load(image)

    Logs:
                  globe_center: (1305, 325)
        0.062s      similarity: 0.354
    """
    globe = None
    homo_center: tuple
    center_loca: tuple

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.perspective = Perspective(config)
        self.homography = Homography(config)
        self._globe_map_loaded = False

    def load_globe_map(self):
        """
        Call this method before doing anything.
        """
        if self._globe_map_loaded:
            return False

        logger.info('Loading OS globe map')

        # Load GLOBE_MAP
        image = load_image(GLOBE_MAP)
        image = self.find_peaks(image, para=self.config.OS_GLOBE_FIND_PEAKS_PARAMETERS)
        pad = self.config.OS_GLOBE_IMAGE_PAD
        image = np.pad(image, ((pad, pad), (pad, pad)), mode='constant', constant_values=0)
        image = image.astype(np.uint8)
        image = cv2.resize(image, None, fx=self.config.OS_GLOBE_IMAGE_RESIZE, fy=self.config.OS_GLOBE_IMAGE_RESIZE)
        self.globe = image

        # Load homography
        backup = self.config.temporary(
            HOMO_STORAGE=self.config.OS_GLOBE_HOMO_STORAGE, DETECTING_AREA=self.config.OS_GLOBE_DETECTING_AREA)
        self.homography.find_homography(*self.config.HOMO_STORAGE, overflow=False)
        self.homo_center = self.screen2globe([self.config.SCREEN_CENTER])[0].astype(int)
        backup.recover()

        self._globe_map_loaded = True
        return True

    def screen2globe(self, points):
        return perspective_transform(points, data=self.homography.homo_data)

    def globe2screen(self, points):
        return perspective_transform(points, data=self.homography.homo_invt)

    def find_peaks(self, image, para):
        """
        Args:
            image (np.ndarray): Screenshot.
            para (dict): Parameters use in scipy.signal.find_peaks.

        Returns:
            np.ndarray: Image in monochrome, map borders in white, others in black.
        """
        r, g, b = cv2.split(image)
        b = cv2.add(cv2.multiply(g, 0.6), cv2.multiply(b, 0.4))
        image = cv2.subtract(b, r)

        hori = self.perspective.find_peaks(image, is_horizontal=True, param=para, mask=None)
        vert = self.perspective.find_peaks(image, is_horizontal=False, param=para, mask=None)
        image = cv2.bitwise_or(hori, vert)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        image = cv2.dilate(image, kernel)

        return image

    def perspective_transform(self, image):
        """
        Args:
            image (np.ndarray): Screenshot with perspective.

        Returns:
            np.ndarray: Image without perspective, like normal 2D maps.
        """
        image = cv2.warpPerspective(image, self.homography.homo_data, self.homography.homo_size)
        return image

    def load(self, image):
        """
        Args:
            image (np.ndarray):
        """
        self.load_globe_map()
        start_time = time.time()

        local = self.find_peaks(self.perspective_transform(image), para=self.config.OS_LOCAL_FIND_PEAKS_PARAMETERS)
        local = local.astype(np.uint8)
        local = cv2.resize(local, None, fx=self.config.OS_GLOBE_IMAGE_RESIZE, fy=self.config.OS_GLOBE_IMAGE_RESIZE)

        result = cv2.matchTemplate(self.globe, local, cv2.TM_CCOEFF_NORMED)
        _, similarity, _, loca = cv2.minMaxLoc(result)
        loca = np.array(loca) / self.config.OS_GLOBE_IMAGE_RESIZE
        loca = tuple(self.homo_center + loca - self.config.OS_GLOBE_IMAGE_PAD)
        self.center_loca = loca

        time_cost = round(time.time() - start_time, 3)
        logger.attr_align('globe_center', loca)
        logger.attr_align('similarity', float2str(similarity), front=float2str(time_cost) + 's')
        if similarity < 0.1:
            logger.warning('Low similarity when matching OS globe')
