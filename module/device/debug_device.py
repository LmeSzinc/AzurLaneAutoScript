import os
from queue import Queue

from module.base.utils import load_image, random_rectangle_point, ensure_int, point2str
from module.config.server import set_server
from module.device.device import Device
from module.logger import logger


class DebugDevice(Device):

    def __init__(self, server='cn', image_folder=None):
        logger.hr('DebugDevice', level=1)
        logger.info('You are debugging, No need device')

        set_server(server)

        # init objects
        self.image_queue = Queue()
        self.image = None

        # if image_folder is not empty, load their fileNames which end with '.PNG' or '.png' into image_queue
        if len(image_folder) > 0:
            for file_name in os.listdir(image_folder):
                if file_name.endswith('.PNG') or file_name.endswith('.png'):
                    image_absolute_location = image_folder + '\\' + file_name
                    self.image_queue.put(image_absolute_location)

        if self.image_queue.empty():
            logger.error('Can not find any valid picture')
        else:
            # load the first image as default screenshot
            self.screenshot()

    # if you want simulate a delay of several seconds, you can sleep here?
    def screenshot(self):
        logger.info('A screenshot call')
        if self.image_queue.empty():
            logger.error('No enough images, check your code!')
            return None
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
