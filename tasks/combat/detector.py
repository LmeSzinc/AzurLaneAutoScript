import os
import cv2
import numpy as np


class Detector:
    def __init__(self):
        """
        A detector to detect the circle mark of enemy and item.
        """
        self.ui_mask = cv2.imread(os.path.join(os.path.dirname(__file__), "mask.png"), 0)

    def update(self, frame):
        # apply a mask to every frame to block the UI from interfering detection
        frame_masked = cv2.bitwise_and(frame, frame, mask=self.ui_mask)
        # update the detector with current frame before detection
        self.hsv = cv2.cvtColor(frame_masked, cv2.COLOR_BGR2HSV)

    def detect_item(self):
        filter_params = {
            'lowerb': np.array([0, 0, 215]),
            'upperb': np.array([108, 53, 255]),
        }
        hough_params = {
            'minDist': 8,
            'param1': 200,
            'param2': 8,
            'minRadius': 2,
            'maxRadius': 4,
        }

        # augment the target marker through mask based on HSV color space
        mask = cv2.inRange(self.hsv, **filter_params)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)), iterations=1)

        # resize the mask to reduce computational complexity of hough operation
        mask = cv2.resize(mask, None, fx=0.25, fy=0.25)
        mask = cv2.GaussianBlur(mask, (3, 3), 0, 0)

        circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, **hough_params)

        # if any target exists, return the center coordinates
        return self.get_coordinates(circles) if circles is not None else None

    def detect_enemy(self):
        filter_params = {
            'lowerb': np.array([0, 62, 213]),
            'upperb': np.array([180, 198, 255]),
        }
        hough_params = {
            'minDist': 18,
            'param1': 200,
            'param2': 10,
            'minRadius': 5,
            'maxRadius': 9,
        }

        mask = cv2.inRange(self.hsv, **filter_params)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)), iterations=1)

        mask = cv2.resize(mask, None, fx=0.25, fy=0.25)
        mask = cv2.GaussianBlur(mask, (3, 3), 0, 0)
        circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, **hough_params)

        return self.get_coordinates(circles) if circles is not None else None

    @staticmethod
    def get_coordinates(circles):
        # convert coordinates to original scale
        circles = np.asarray(np.around(circles * 4), dtype=np.uint16).squeeze(0)
        return [circle[:2] for circle in circles]


def generate_ui_mask():
    """
    code to generate ui mask
    """
    mask = np.ones([720, 1280]) * 255
    mask[34:81, 21:61] = 0
    mask[179:220, 21:51] = 0
    mask[35:84, 183:218] = 0
    mask[0:61, 780:1280] = 0
    mask[145:435, 1153:1240] = 0
    cv2.circle(mask, (907, 614), 55, 0, -1)
    cv2.circle(mask, (1033, 542), 67, 0, -1)
    cv2.imwrite("mask.png", mask)


if __name__ == '__main__':
    # how to use
    class YourClass:
        def __init__(self, stream):
            self.stream = stream
            self.detector = Detector()  # initiate a detector, recommend to set scale=0.25

            self.run()

        def run(self):
            while True:
                # update the detector with current frame before detection
                self.frame = cv2.cvtColor(self.stream.capture(), cv2.COLOR_RGB2BGR)
                self.detector.update(self.frame)

                # return a list of coordinates of corresponding target
                enemies = self.detector.detect_enemy()
                if enemies is not None:
                    self.plot_points(enemies)

                items = self.detector.detect_item()
                if items is not None:
                    self.plot_points(items)

                cv2.imshow("frame", self.frame)
                if cv2.waitKey(1) == ord('q'):
                    cv2.destroyAllWindows()
                    break

        def plot_points(self, points):
            for point in points:
                cv2.circle(self.frame, (point[0], point[1]), 3, (255, 255, 255), -1)
