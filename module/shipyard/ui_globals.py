from module.base.button import ButtonGrid
from module.shipyard.assets import *
from module.ocr.ocr import Ocr, Digit, DigitCounter

SHIPYARD_FACE_GRID = ButtonGrid(origin=(255, 610), delta=(180, 0),
                                button_shape=(55, 55), grid_shape=(6, 1),
                                name='SHIPYARD_FACE_GRID')

SHIPYARD_BP_COUNT_GRID = ButtonGrid(origin=(324, 688), delta=(181, 0),
                                    button_shape=(45, 30), grid_shape=(6, 1),
                                    name='SHIPYARD_BP_COUNT_GRID')

SHIPYARD_SERIES_GRID = ButtonGrid(origin=(449, 286), delta=(280, 121),
                                  button_shape=(166, 58), grid_shape=(2, 2),
                                  name='SHIPYARD_SERIES_GRID')

OCR_SHIPYARD_BP_COUNT_GRID = Digit(SHIPYARD_BP_COUNT_GRID.buttons,
                                   letter=(255, 247, 247),
                                   name=f'OCR_BP_COUNT')

OCR_SHIPYARD_TOTAL_DEV = Digit(SHIPYARD_TOTAL_DEV, letter=(255, 247, 247),
                               threshold=64)

OCR_SHIPYARD_TOTAL_FATE = Digit(SHIPYARD_TOTAL_FATE, letter=(255, 247, 247),
                                threshold=64)
