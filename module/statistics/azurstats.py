import threading
import io
import json
import os
import time

import requests
from PIL import Image
from requests.adapters import HTTPAdapter

from module.base.utils import save_image
from module.config.config import AzurLaneConfig
from module.config.deep import deep_get
from module.exception import ScriptError
from module.logger import logger
from module.statistics.utils import pack


class DropImage:
    def __init__(self, stat, genre, save, upload, info=''):
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
        self.info = info
        self.images = []

    def add(self, image):
        """
        Args:
            image (np.ndarray):
        """
        if self:
            self.images.append(image)
            logger.info(
                f'Drop record added, genre={self.genre}, amount={self.count}')

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

    def clear(self):
        self.images = []

    @property
    def count(self):
        return len(self.images)

    def __bool__(self):
        # Uncomment these if stats service re-run in the future
        # return self.save or self.upload

        return self.save

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self:
            self.stat.commit(images=self.images, genre=self.genre,
                             save=self.save, upload=self.upload, info=self.info)


class AzurStats:
    TIMEOUT = 20

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    @property
    def _api(self):
        method = self.config.DropRecord_API
        if method == 'default':
            return 'https://azurstats.lyoko.io/api/upload/'
        elif method == 'cn_gz_reverse_proxy':
            return 'https://image.tyy.akagiyui.com/api/upload'
        elif method == 'cn_sh_reverse_proxy':
            return 'https://image.tyy.akagiyui.com/api/upload'
        else:
            logger.critical('Invalid upload API, please check your settings')
            raise ScriptError('Invalid upload API')

    @property
    def _user_agent(self):
        return f'Alas ({str(self.config.DropRecord_AzurStatsID)})'

    def _upload(self, image, genre, filename):
        """
        Args:
            image: Image to upload.
            genre (str):
            filename (str): 'xxx.png'

        Returns:
            bool: If success
        """
        output = io.BytesIO()
        Image.fromarray(image, mode='RGB').save(output, format='png')
        output.seek(0)

        data = {'file': (filename, output, 'image/png')}
        headers = {'user-agent': self._user_agent}
        session = requests.Session()
        session.trust_env = False
        session.mount('http://', HTTPAdapter(max_retries=5))
        session.mount('https://', HTTPAdapter(max_retries=5))
        try:
            resp = session.post(self._api, files=data,
                                headers=headers, timeout=self.TIMEOUT)
        except Exception as e:
            logger.warning(f'Image upload failed, {e}')
            return False

        if resp.status_code == 200:
            # print(resp.text)
            info = json.loads(resp.text)

            # Lsky response
            status = deep_get(info, keys='status', default=None)
            if status is not None:
                if status:
                    md5 = deep_get(info, keys='data.md5', default='')
                    logger.info(f'Image upload success, md5: {md5}')
                    return True
                else:
                    message = deep_get(info, keys='message', default='')
                    logger.warning(f'Image upload failed, message: {message}')
                    return False

            # Imgurl response
            code = deep_get(info, keys='code', default=None)
            if code is not None:
                if code == 200:
                    imgid = deep_get(info, keys='imgid', default='')
                    logger.info(f'Image upload success, imgid: {imgid}')
                    return True
                elif code == 0:
                    msg = deep_get(info, keys='msg', default='')
                    logger.warning(f'Image upload failed, msg: {msg}')
                    return False

        logger.warning(f'Image upload failed, unexpected server returns, '
                       f'status_code: {resp.status_code}, returns: {resp.text[:500]}')
        return False

    def _save(self, image, genre, filename):
        """
        Args:
            image: Image to save.
            genre (str): Name of sub folder.
            filename (str): 'xxx.png'

        Returns:
            bool: If success
        """
        try:
            folder = os.path.join(
                str(self.config.DropRecord_SaveFolder), genre)
            os.makedirs(folder, exist_ok=True)
            file = os.path.join(folder, filename)
            save_image(image, file)
            logger.info(f'Image save success, file: {file}')
            return True
        except Exception as e:
            logger.exception(e)

        return False

    def commit(self, images, genre, save=False, upload=False, info=''):
        """
        Args:
            images (list): List of images in numpy array.
            genre (str):
            save (bool): If save image to local file system.
            upload (bool): If upload image to Azur Stats.
            info (str): Extra info append to filename.

        Returns:
            bool: If commit.
        """
        if len(images) == 0:
            return False

        save, upload = bool(save), bool(upload)
        logger.info(
            f'Drop record commit, genre={genre}, amount={len(images)}, save={save}, upload={upload}')
        image = pack(images)
        now = int(time.time() * 1000)

        if info:
            filename = f'{now}_{info}.png'
        else:
            filename = f'{now}.png'

        if save:
            save_thread = threading.Thread(
                target=self._save, args=(image, genre, filename))
            save_thread.start()

        # Uncomment these if stats service re-run in the future
        # if upload:
        #     upload_thread = threading.Thread(
        #         target=self._upload, args=(image, genre, filename))
        #     upload_thread.start()

        return True

    def new(self, genre, method='do_not', info=''):
        """
        Args:
            genre (str):
            method (str): The method about save and upload image.
            info (str): Extra info append to filename.

        Returns:
            DropImage:
        """
        save = 'save' in method
        upload = 'upload' in method
        return DropImage(stat=self, genre=genre, save=save, upload=upload, info=info)
