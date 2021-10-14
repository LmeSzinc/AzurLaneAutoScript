import io
import json
import time

import cv2
import numpy as np
import requests
from requests.adapters import HTTPAdapter

from module.config.config import AzurLaneConfig
from module.logger import logger
from module.statistics.utils import *


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


class DropImage:
    def __init__(self, stat, genre, save, upload):
        """
        Args:
            stat (AzurStats):
            genre:
            save:
            upload:
        """
        self.stat = stat
        self.genre = str(genre)
        self.save = bool(save)
        self.upload = bool(upload)
        self.images = []

    def add(self, image):
        """
        Args:
            image: Pillow image.
        """
        if self:
            self.images.append(image)

    def handle_add(self, main, before=None):
        """
        Handle wait before and after adding screenshot.

        Args:
            main (ModuleBase):
            before (int, float, tuple): Sleep before adding.
        """
        if before is None:
            before = main.config.WAIT_BEFORE_SAVING_SCREEN_SHOT

        if self:
            main.handle_info_bar()
            main.device.sleep(before)
            main.device.screenshot()
            self.add(main.device.image)

    def __bool__(self):
        return self.save or self.upload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self:
            self.stat.commit(images=self.images, genre=self.genre, save=self.save, upload=self.upload)


class AzurStats:
    API = 'https://azurstats.lyoko.io/api/upload/'
    TIMEOUT = 20

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    def _user_agent(self):
        return f'Alas ({str(self.config.DropRecord_AzurStatsID)})'

    def _upload(self, image, genre, timestamp):
        """
        Args:
            image: Image to upload.
            genre (str):
            timestamp (int): Millisecond timestamp.

        Returns:
            bool: If success
        """
        output = io.BytesIO()
        image.save(output, format='png')
        output.seek(0)

        data = {'file': (f'{timestamp}.png', output, 'image/png')}
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

    def _save(self, image, genre, timestamp):
        """
        Args:
            image: Image to save.
            genre (str): Name of sub folder.
            timestamp (int): Millisecond timestamp.

        Returns:
            bool: If success
        """
        try:
            folder = os.path.join(str(self.config.DropRecord_SaveFolder), genre)
            os.makedirs(folder, exist_ok=True)
            file = os.path.join(folder, f'{timestamp}.png')
            image.save(file)
            logger.info(f'Image save success, file: {file}')
            return True
        except Exception as e:
            logger.exception(e)

        return False

    def commit(self, images, genre, save=False, upload=False):
        """
        Args:
            images (list): List of pillow images
            genre (str):
            save (bool): If save image to local file system.
            upload (bool): If upload image to Azur Stats.

        Returns:
            bool: If commit.
        """
        if len(images) == 0:
            return False

        save, upload = bool(save), bool(upload)
        logger.info(f'Drop record commit, genre={genre}, amount={len(images)}, save={save}, upload={upload}')
        image = pack(images)
        now = int(time.time() * 1000)

        if save:
            self._save(image, genre=genre, timestamp=now)
        if upload:
            self._upload(image, genre=genre, timestamp=now)

        return True

    def new(self, genre, save=False, upload=False):
        """
        Args:
            genre (str):
            save (bool): If save image to local file system.
            upload (bool): If upload image to Azur Stats.

        Returns:
            DropImage:
        """
        return DropImage(stat=self, genre=genre, save=save, upload=upload)
