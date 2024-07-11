from module.base.button import ButtonGrid
from module.ocr.ocr import Digit
from module.shipyard.assets import *

SHIPYARD_FACE_GRID = ButtonGrid(origin=(188, 607), delta=(181, 0),
                                button_shape=(181, 80), grid_shape=(6, 1),
                                name='SHIPYARD_FACE_GRID')

SHIPYARD_BP_COUNT_GRID = ButtonGrid(origin=(324, 688), delta=(181, 0),
                                    button_shape=(45, 30), grid_shape=(6, 1),
                                    name='SHIPYARD_BP_COUNT_GRID')

SHIPYARD_SERIES_GRID = ButtonGrid(origin=(75, 133), delta=(399, 91),
                                  button_shape=(337, 60), grid_shape=(3, 3),
                                  name='SHIPYARD_SERIES_GRID')

OCR_SHIPYARD_BP_COUNT_GRID = Digit(SHIPYARD_BP_COUNT_GRID.buttons,
                                   letter=(255, 247, 247),
                                   name=f'OCR_BP_COUNT')

OCR_SHIPYARD_TOTAL_DEV = Digit(SHIPYARD_TOTAL_DEV, letter=(255, 247, 247),
                               threshold=64)

OCR_SHIPYARD_TOTAL_FATE = Digit(SHIPYARD_TOTAL_FATE, letter=(255, 247, 247),
                                threshold=64)
