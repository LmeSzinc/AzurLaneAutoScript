from ctypes import windll
import win32gui
import win32ui
import win32con
import cv2
import numpy as np

import module.config.server as server

from module.exception import GameNotRunningError

from module.device.method.utils import ImageTruncated


class Winapiutils:
    hwnd = None
    # Need other server player support
    windowname = {'jp': 'アズールレーン'}
    def __init__(self):
        self.windowposx = 0
        self.windowposy = 0
        self.windowwidth = 0
        self.windowheight = 0


    def find_window(self):
        """
        Args:
            winname (str): window name

        """

        try:
            winname = self.windowname[server.server]
        except KeyError:
            winname = '碧蓝航线'

        self.hwnd = win32gui.FindWindow(None, winname)
        if not self.hwnd:
            raise GameNotRunningError

        self.resize_window()

    def resize_window(self):
        # ignore the effect of dpi scaling
        windll.user32.SetProcessDPIAware()

        # get application window information
        winpos = win32gui.GetWindowRect(self.hwnd)
        self.windowposx = winpos[0]
        self.windowposy = winpos[1]
        self.windowwidth = winpos[2] - winpos[0]
        self.windowheight = winpos[3] - winpos[1]
        if (self.windowposx != 0 and self.windowposy != 0) or (self.windowwidth != 1280 and self.windowheight != 720):
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, win32con.WS_SYSMENU)
            win32gui.SetWindowPos(self.hwnd, None, 0, 0, 1280, 720,
                                  win32con.SWP_NOSENDCHANGING | win32con.SWP_SHOWWINDOW)

    def get_frame(self):
        """

        return:
            image (numpy)

        """

        self.resize_window()

        # return window handle
        hwndc = win32gui.GetWindowDC(self.hwnd)

        # create device description table
        mfcdc = win32ui.CreateDCFromHandle(hwndc)

        # create memory device description table
        savedc = mfcdc.CreateCompatibleDC()

        # create bitmap instance
        savebitmap = win32ui.CreateBitmap()

        # malloc for bitmap
        savebitmap.CreateCompatibleBitmap(mfcdc, self.windowwidth, self.windowheight)

        # save screenshot to bitmap
        savedc.SelectObject(savebitmap)

        # save bitmap to memory
        windll.user32.PrintWindow(self.hwnd, savedc.GetSafeHdc(), 2)

        # get bitmap information
        image = savebitmap.GetBitmapBits(True)

        # free memory
        win32gui.DeleteObject(savebitmap.GetHandle())
        savedc.DeleteDC()
        mfcdc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndc)

        # process image to numpy array
        image = np.frombuffer(image, dtype = 'uint8')
        image.shape = (self.windowheight, self.windowwidth, 4)
        if image is None:
            raise ImageTruncated('Empty image after reading from buffer')

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if image is None:
            raise ImageTruncated('Empty image after cv2.cvtColor')

        return image
