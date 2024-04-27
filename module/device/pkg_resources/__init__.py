import os
import re
import sys

from module.base.decorator import cached_property
from module.logger import logger

"""
Importing pkg_resources is so slow, like 0.4 ~ 1.0s, just google it you will find it indeed really slow.
Since it was some kind of standard library there is no way to modify it or speed it up.
So here's a poor but fast implementation of pkg_resources returning the things in need.

To patch:
```
# Patch pkg_resources before importing adbutils and uiautomator2
from module.device.pkg_resources import get_distribution
# Just avoid being removed by import optimization
_ = get_distribution
```
"""
# Inject sys.modules, pretend we have pkg_resources imported
try:
    sys.modules['pkg_resources'] = sys.modules['module.device.pkg_resources']
except KeyError:
    logger.error('Patch pkg_resources failed, patch module does not exists')


def remove_suffix(s, suffix):
    """
    Remove suffix of a string or bytes like `string.removesuffix(suffix)`, which is on Python3.9+

    Args:
        s (str, bytes):
        suffix (str, bytes):

    Returns:
        str, bytes:
    """
    return s[:-len(suffix)] if s.endswith(suffix) else s


class FakeDistributionObject:
    def __init__(self, dist, version):
        self.dist = dist
        self.version = version

    def __str__(self):
        return f'{self.__class__.__name__}({self.dist}={self.version})'

    __repr__ = __str__


class PackageCache:
    @cached_property
    def site_packages(self):
        # Just whatever library to locate the `site-packages` directory
        import requests
        path = os.path.abspath(os.path.join(requests.__file__, '../../'))
        return path

    @cached_property
    def dict_installed_packages(self):
        """
        Returns:
            dict: Key: str, package name
                Value: FakeDistributionObject
        """
        dic = {}
        for file in os.listdir(self.site_packages):
            # mxnet_cu101-1.6.0.dist-info
            # adbutils-0.11.0-py3.7.egg-info
            res = re.match(r'^([a-zA-Z0-9._]+)-([a-zA-Z0-9._]+)-', file)
            if res:
                version = remove_suffix(res.group(2), '.dist')
                # version = res.group(2)
                obj = FakeDistributionObject(
                    dist=res.group(1),
                    version=version,
                )
                dic[obj.dist] = obj

        return dic


PACKAGE_CACHE = PackageCache()


def resource_filename(*args):
    if args == ("adbutils", "binaries"):
        path = os.path.abspath(os.path.join(PACKAGE_CACHE.site_packages, *args))
        return path


def get_distribution(dist):
    """Return a current distribution object for a Requirement or string"""
    if dist == 'adbutils':
        return PACKAGE_CACHE.dict_installed_packages.get(
            'adbutils',
            FakeDistributionObject('adbutils', '0.11.0'),
        )
    if dist == 'uiautomator2':
        return PACKAGE_CACHE.dict_installed_packages.get(
            'uiautomator2',
            FakeDistributionObject('uiautomator2', '2.16.17'),
        )


class DistributionNotFound(Exception):
    pass
