import sys
from types import ModuleType


def import_fake_pil_module():
    fake_pil_module = ModuleType('PIL')
    fake_pil_module.Image = ModuleType('PIL.Image')
    fake_pil_module.Image.Image = type('MockPILImage', (), dict(__init__=None))
    sys.modules['PIL'] = fake_pil_module
    sys.modules['PIL.Image'] = fake_pil_module.Image


def remove_fake_pil_module():
    sys.modules.pop('PIL', None)
    sys.modules.pop('PIL.Image', None)
