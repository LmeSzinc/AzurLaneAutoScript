from module.base.template import Template
from module.base.utils import crop


class BulinRetireTemplate(Template):
    def __init__(self, file, area):
        self.area = area
        super().__init__(file=file)

    def pre_process(self, image):
        return crop(image, self.area)


BULIN_RETIRE_TEMPLATES = {
    'purple_bulin': [
        BulinRetireTemplate(file='./assets/shop/medal/BulinT1.png', area=(8, 18, 48, 58)),
        BulinRetireTemplate(file='./assets/shop/merit/BulinT1.png', area=(8, 18, 48, 58)),
    ],
    'gold_bulin': [
        BulinRetireTemplate(file='./assets/shop/medal/BulinT2.png', area=(16, 18, 56, 58)),
        BulinRetireTemplate(file='./assets/shop/merit/BulinT2.png', area=(16, 18, 56, 58)),
    ],
}
