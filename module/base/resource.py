import re

import module.config.server as server
from module.base.decorator import cached_property


def del_cached_property(obj, name):
    """
    Delete a cached property safely.

    Args:
        obj:
        name (str):
    """
    if name in obj.__dict__:
        del obj.__dict__[name]


def get_assets_from_file(file, regex):
    assets = set()
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
            file='./module/ui/assets.py',
            regex=re.compile(r'^([A-Za-z][A-Za-z0-9_]+) = ')
        )
        assets |= get_assets_from_file(
            file='./module/ui/ui.py',
            regex=re.compile(r'\(([A-Z][A-Z0-9_]+),')
        )
        assets |= get_assets_from_file(
            file='./module/handler/info_handler.py',
            regex=re.compile(r'\(([A-Z][A-Z0-9_]+),')
        )
        # MAIN_CHECK == MAIN_GOTO_CAMPAIGN
        assets.add('MAIN_GOTO_CAMPAIGN')
        return assets


_preserved_assets = PreservedAssets()


class Resource:
    # Class property, record all button and templates
    instances = {}
    # Instance property, record cached properties of instance
    cached = []

    def resource_add(self, key):
        Resource.instances[key] = self

    def resource_release(self):
        for cache in self.cached:
            del_cached_property(self, cache)

    @classmethod
    def is_loaded(cls, obj):
        if hasattr(obj, '_image') and obj._image is None:
            return False
        elif hasattr(obj, 'image') and obj.image is None:
            return False
        return True

    @classmethod
    def resource_show(cls):
        from module.logger import logger
        logger.hr('Show resource')
        for key, obj in cls.instances.items():
            if cls.is_loaded(obj):
                continue
            logger.info(f'{obj}: {key}')

    @staticmethod
    def parse_property(data):
        """
        Parse properties of Button or Template object input.
        Such as `area`, `color` and `button`.

        Args:
            data: Dict or str
        """
        if isinstance(data, dict):
            return data[server.server]
        else:
            return data


def release_resources(next_task=''):
    # Release all OCR models
    # Usually to have 2 models loaded and each model takes about 20MB
    # This will release 20-40MB
    from module.ocr.ocr import OCR_MODEL
    if 'Opsi' in next_task or 'commission' in next_task:
        # OCR models will be used soon, don't release
        models = []
    elif next_task:
        # Release OCR models except 'azur_lane'
        models = ['cnocr', 'jp', 'tw']
    else:
        models = ['azur_lane', 'cnocr', 'jp', 'tw']
    for model in models:
        del_cached_property(OCR_MODEL, model)

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

    # Release cached images for map detection
    from module.map_detection.utils_assets import ASSETS
    attr_list = [
        'ui_mask',
        'ui_mask_os',
        'ui_mask_stroke',
        'ui_mask_in_map',
        'ui_mask_os_in_map',
        'tile_center_image',
        'tile_corner_image',
        'tile_corner_image_list'
    ]
    for attr in attr_list:
        del_cached_property(ASSETS, attr)

    # Useless in most cases, but just call it
    # gc.collect()
