from pathlib import Path
from module.combat.level import LevelOcr
from PIL import Image
from module.base.button import ButtonGrid



# p = Path(r"C:\Users\tang8\Documents\MuMu共享文件夹\MuMu20210725103457.png")

# area = (433,162,476,182)

# level_grid = ButtonGrid(origin=(427, 161), delta=(102, 133), button_shape=(43, 20), grid_shape=(3,2))

# for button in level_grid.buttons:
    

#     level_ocr = LevelOcr(button.area)

#     image = Image.open(p).convert('RGB')

#     image.crop(button.area).show()

#     out = level_ocr.ocr(image)
#     print(out)

class A():
    def p(self):
        print("A")

class B(A):
    def p(self):
        print('B')

class C(A, B):
    pass

c = C()
c.p()