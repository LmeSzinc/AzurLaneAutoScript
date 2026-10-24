"""An offline device for screenshot based tests.

The production device classes initialise emulator transports as part of their
constructor.  Screenshot tests must never do that, so this intentionally small
device implements the part of the device protocol used by modules while
keeping the image and every attempted action in memory.

Adapted from LmeSzinc/Alasio, commit
c47c861194285b1adfd0baa12d20abf549be8adc, alasio/testing/screenshot_device.py.
"""

from __future__ import absolute_import

import os

from PIL import Image


class ScreenshotTestError(Exception):
    """Raised when a screenshot test is not set up correctly."""


class ScreenshotNotProvided(ScreenshotTestError):
    """Raised whenever code under test asks for another screenshot."""


class ScreenshotDevice(object):
    """A no-connection device holding one screenshot for a test."""

    def __init__(self, image, file=None):
        self.file = os.fspath(file) if file is not None else None
        self.clicks = []
        self.drags = []
        self.swipes = []
        self.sleeps = []
        self._click_record = []
        self.reviews = []
        # These aliases make the recorded data convenient for callers while
        # retaining the simple records used by the upstream helper.
        self.review_results = []
        self.review_regions = []
        self.package = None
        self.set_image(image)

    def set_image(self, image):
        if isinstance(image, Image.Image):
            image = image.copy()
        self.image = image

    @property
    def has_cached_image(self):
        return getattr(self, 'image', None) is not None

    def screenshot(self):
        raise ScreenshotNotProvided(
            '"{}" is the only screenshot of this test, but the module under '
            'test asked for another screenshot. Add a screenshot of that page '
            'to the test, or reuse the first screenshot '
            '(skip_first_screenshot).'.format(self.file)
        )

    def click(self, button, *args, **kwargs):
        self.clicks.append(button)
        self.click_record_add(button)

    def stuck_record_add(self, button):
        # Stuck detection is meaningful only for a connected device.
        return None

    def drag(self, p1, p2, *args, **kwargs):
        self.drags.append((p1, p2))

    def swipe(self, p1, p2, *args, **kwargs):
        self.swipes.append((p1, p2))
        self.drags.append((p1, p2))

    def swipe_vector(self, vector, box=(123, 159, 1175, 628), padding=15,
                     *args, **kwargs):
        """Record the endpoint pair produced by a common vector swipe call."""
        left, top, right, bottom = box
        center = ((left + right) // 2, (top + bottom) // 2)
        p1 = (center[0], center[1])
        p2 = (center[0] + vector[0], center[1] + vector[1])
        self.swipe(p1, p2, *args, **kwargs)

    def sleep(self, second):
        self.sleeps.append(second)

    # The production device has a click record used for stuck detection.  A
    # few modules clear or inspect it around an action, so provide the harmless
    # in-memory equivalent as well.
    @property
    def click_record(self):
        return list(self._click_record)

    def click_record_add(self, button):
        if not hasattr(self, '_click_record'):
            self._click_record = []
        self._click_record.append(button)

    def click_record_clear(self):
        self._click_record = []

    def click_record_remove(self, button):
        if not hasattr(self, '_click_record'):
            return
        self._click_record = [item for item in self._click_record if item != button]

    def click_record_check(self):
        return False

    def image_save(self, file=None):
        if file is None:
            raise ValueError('A destination file is required for a screenshot test')
        image = self.image
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)
        image.save(file)

    def save_screenshot(self, *args, **kwargs):
        return False

    def review(self, result, regions=()):
        """Record a machine result and regions for optional human review."""
        region_list = list(regions or ())
        record = {'result': result, 'regions': region_list}
        self.reviews.append(record)
        self.review_results.append(result)
        self.review_regions.append(region_list)
        return result
