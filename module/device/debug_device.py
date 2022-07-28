import os
from queue import Queue

from module.base.utils import load_image, random_rectangle_point, ensure_int, point2str
from module.config.server import set_server
from module.device.device import Device
from module.logger import logger


class DebugDevice(Device):

    def __init__(self, server='cn', image_location=None):
        logger.hr('DebugDevice', level=1)
        logger.info('You are debugging, No need device')

        set_server(server)

        # init objects
        self.image_queue = Queue()
        self.image = None

        if len(image_location) <= 0:
            logger.warning('Your image location is empty, ignore')
            return

        if isinstance(image_location, list):
            logger.debug('You select multi images debug mode, and you specified the order of pictures.')
            for file_name in image_location:
                if file_name.endswith('.PNG') or file_name.endswith('.png'):
                    self.image_queue.put(file_name)
        elif image_location.endswith('.PNG') or image_location.endswith('.png'):
            logger.debug('You select single image debug mode, only use this image from beginning to end.')
            self.image_queue.put(image_location)
        elif image_location.endswith('/') or image_location.endswith('//'):
            logger.debug('You select multi images debug mode, will use the picture ine the folder in order.')
            for file_name in os.listdir(image_location):
                if file_name.endswith('.PNG') or file_name.endswith('.png'):
                    image_absolute_location = image_location + '\\' + file_name
                    self.image_queue.put(image_absolute_location)
        else:
            logger.warning('Please check your image location')

        if self.image_queue.empty():
            logger.error('Can not find any valid picture')
        else:
            # load the first image as default screenshot
            self.screenshot()

    # if you want simulate a delay of several seconds, you can sleep here?
    def screenshot(self):
        logger.info('A screenshot call')
        if self.image_queue.empty():
            logger.warning('No enough images, also use current image!')
        else:
            current_image = self.image_queue.get()
            logger.info('Load ' + current_image + ' as your screenshot')
            self.image = load_image(current_image)
        return self.image

    def click(self, button, control_check=True):
        logger.info('A click call')
        x, y = random_rectangle_point(button.button)
        x, y = ensure_int(x, y)
        logger.info(
            'Click %s @ %s' % (point2str(x, y), button)
        )

    def swipe(self, p1, p2, duration=(0.1, 0.2), name='SWIPE', distance_check=True):
        logger.info('A swipe call')
