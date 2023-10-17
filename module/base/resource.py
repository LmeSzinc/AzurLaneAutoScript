import re

from module.base.decorator import cached_property


def get_assets_from_file(file):
    assets = set()
    regex = re.compile(r"file='(.*?)'")
    with open(file, 'r', encoding='utf-8') as f:
        for row in f.readlines():
            result = regex.search(row)
            if result:
                assets.add(result.group(1))
    return assets


class PreservedAssets:
    @cached_property
    def ui(self):
        assets = set()
        assets |= get_assets_from_file(
            file='./tasks/base/assets/assets_base_page.py',
        )
        assets |= get_assets_from_file(
            file='./tasks/base/assets/assets_base_popup.py',
        )
        assets |= get_assets_from_file(
            file='./tasks/base/assets/assets_base_main_page.py',
        )
        return assets


_preserved_assets = PreservedAssets()


class Resource:
    # Class property, record all button and templates
    instances = {}

    def resource_add(self, key):
        Resource.instances[key] = self

    def resource_release(self):
        pass

    @classmethod
    def is_loaded(cls, obj):
        if hasattr(obj, '_image') and obj._image is not None:
            return True
        if hasattr(obj, 'image') and obj.image is not None:
            return True
        if hasattr(obj, 'buttons') and obj.buttons is not None:
            return True
        return False

    @classmethod
    def resource_show(cls):
        from module.logger import logger
        logger.hr('Show resource')
        for key, obj in cls.instances.items():
            if cls.is_loaded(obj):
                logger.info(f'{obj}: {key}')


def release_resources(next_task=''):
    # Release all OCR models
    # det models take 400MB
    if not next_task:
        from module.ocr.models import OCR_MODEL
        OCR_MODEL.resource_release()

    # Release assets cache
    # module.ui has about 80 assets and takes about 3MB
    # Alas has about 800 assets, but they are not all loaded.
    # Template images take more, about 6MB each
    for key, obj in Resource.instances.items():
        # Preserve assets for ui switching
        if next_task and str(obj) in _preserved_assets.ui:
            continue
        # if Resource.is_loaded(obj):
        #     logger.info(f'Release {obj}')
        obj.resource_release()

    # Useless in most cases, but just call it
    # gc.collect()
