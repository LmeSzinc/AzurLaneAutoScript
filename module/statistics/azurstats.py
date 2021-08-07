import io
import json
import time

import cv2
import numpy as np
import requests

from module.config.config import AzurLaneConfig
from module.logger import logger
from module.statistics.utils import *
from requests.adapters import HTTPAdapter



def pack(img_list):
    """
    Stack images vertically.

    Args:
        img_list (list): List of pillow image

    Returns:
        Pillow image
    """
    img_list = [np.array(i) for i in img_list]
    image = cv2.vconcat(img_list)
    image = Image.fromarray(image, mode='RGB')
    return image


class AzurStats:
    API = 'https://azurstats.lyoko.io/api/upload/'
    TIMEOUT = 20

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.images = []

    def add(self, image):
        """
        Args:
            image: Pillow image.

        Returns:
            bool: If added.
        """
        if self.config.ENABLE_AZURSTAT:
            self.images.append(image)
            return True
        else:
            return False

    def clear(self):
        self.images = []

    @property
    def count(self):
        return len(self.images)

    def _user_agent(self):
        return f'Alas ({self.config.AZURSTAT_ID})'

    def _upload(self):
        """
        Returns:
            bool: If success
        """
        amount = len(self.images)
        logger.info(f'Uploading screenshots to AzurStat, amount: {amount}')
        if amount == 0:
            # logger.warning(f'Image upload failed, no images to upload')
            return False
        image = pack(self.images)
        output = io.BytesIO()
        image.save(output, format='png')
        output.seek(0)

        now = int(time.time() * 1000)
        data = {'file': (f'{now}.png', output, 'image/png')}
        headers = {'user-agent': self._user_agent()}
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=5))
        session.mount('https://', HTTPAdapter(max_retries=5))
        try:
            resp = session.post(self.API, files=data, headers=headers, timeout=self.TIMEOUT)
        except Exception as e:
            logger.warning(f'Image upload failed, {e}')
            return False

        if resp.status_code == 200:
            # print(resp.text)
            info = json.loads(resp.text)
            code = info.get("code", 500)
            if code == 200:
                logger.info(f'Image upload success, imgid: {info.get("imgid", "")}')
                return True
            elif code == 0:
                logger.warning(f'Image upload failed, msg: {info.get("msg", "")}')
                return False

        logger.warning(f'Image upload failed, unexpected server returns, '
                       f'status_code: {resp.status_code}, returns: {resp.text}')
        return False

    def upload(self):
        """
        Returns:
            bool: If success
        """
        if not self.config.ENABLE_AZURSTAT:
            return False

        self._upload()
        self.clear()
        return True
