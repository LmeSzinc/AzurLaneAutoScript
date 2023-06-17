import re

import module.config.server as server
from module.base.decorator import cached_property, del_cached_property


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
            file='./tasks/base/assets/assets_base_page.py',
            regex=re.compile(r'^([A-Za-z][A-Za-z0-9_]+) = ')
        )
        assets |= get_assets_from_file(
            file='./tasks/base/assets/assets_base_popup.py',
            regex=re.compile(r'^([A-Za-z][A-Za-z0-9_]+) = ')
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


def release_resources(next_task=''):
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
