import os
from datetime import datetime

from deploy.atomic import atomic_write
from module.base.base import ModuleBase, cv2, image_channel
from module.logger import logger


class ImageBroken(Exception):
    """
    Raised if image failed to decode/encode
    Raised if image is empty
    """
    pass


class ImageNotSupported(Exception):
    """
    Raised if we can't perform image calculation on this image
    """
    pass


def image_encode(image, ext='png', encode=None):
    """
    Encode image

    Args:
        image (np.ndarray):
        ext:
        encode (list): Extra encode options

    Returns:
        np.ndarray:
    """
    channel = image_channel(image)
    if channel == 3:
        # RGB
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    elif channel == 0:
        # grayscale, keep grayscale unchanged
        pass
    elif channel == 4:
        # RGBA
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
    else:
        raise ImageNotSupported(f'shape={image.shape}')

    # Prepare encode params
    ext = ext.lower()
    if encode is None:
        if ext == 'png':
            # Best compression, 0~9
            encode = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        elif ext == 'jpg' or ext == 'jpeg':
            # Best quality
            encode = [cv2.IMWRITE_JPEG_QUALITY, 100]
        elif ext.lower() == '.webp':
            # Best quality
            encode = [cv2.IMWRITE_WEBP_QUALITY, 100]
        elif ext == 'tiff' or ext == 'tif':
            # LZW compression in TIFF
            encode = [cv2.IMWRITE_TIFF_COMPRESSION, 5]
        else:
            raise ImageNotSupported(f'Unsupported file extension "{ext}"')

    # Encode
    ret, buf = cv2.imencode(f'.{ext}', image, encode)
    if not ret:
        raise ImageBroken('cv2.imencode failed')

    return buf


def image_save(image, file, encode=None):
    """
    Save an image like pillow.

    Args:
        image (np.ndarray):
        file (str):
        encode: (list): Encode params
    """
    _, _, ext = file.rpartition('.')
    data = image_encode(image, ext=ext, encode=encode)
    atomic_write(file, data)


def now():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")


class WatchScreen(ModuleBase):

    def watch(self, similarity=0.98):
        start = now()
        before = self.device.screenshot()
        file = os.path.abspath(f'screenshots/{start}/{start}.png')
        image_save(before, file)
        for image in self.loop():
            res = cv2.matchTemplate(image, before, cv2.TM_CCOEFF_NORMED)
            _, sim, _, loca = cv2.minMaxLoc(res)

            if sim < similarity:
                name = now()
                file = os.path.abspath(f'screenshots/{start}/{name}.png')
                logger.info(f'Save file: {file}')
                image_save(image, file)
                before = image


if __name__ == '__main__':
    self = WatchScreen('alas')
    self.watch()
