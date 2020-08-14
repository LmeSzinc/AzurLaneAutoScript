import module.config.server as server
server.server = 'en'  # Change server here

from module.base.base import ModuleBase
from module.retire.assets import *
from module.config.config import AzurLaneConfig
from PIL import Image
az = ModuleBase(AzurLaneConfig('template'))

file = 'C:\\Users\\David\\Desktop\\take_2\\raw\\Screenshot_2020-08-13-17-30-27.png'  # Put your file here.
#file = 'C:\\Users\\David\\Desktop\\take_2\\blue_stack_raw\\Azur Lane_Screenshot_2020.08.13_17.17.10.jpg'  # Put your file here.

image = Image.open(file).convert('RGB')
az.device.image = image
self = az

filter_list = ["ALL", "CLEAR", "DD", "SS", "OTHERS", "CV", "CL", "CA", "BB"]
for item in filter_list:
    ON = globals()[f'FILTER_INDEX_{item}_ON']
    OFF = globals()[f'FILTER_INDEX_{item}_OFF']
    print(item)
    print(self.appear(OFF, offset=(30, 30)), self.appear(ON, offset=(30, 30)))
    print(self.appear(OFF), self.appear(ON))