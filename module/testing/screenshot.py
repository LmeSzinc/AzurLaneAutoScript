"""Pytest support for golden tests backed by real game screenshots.

This is a local adaptation of Alasio's screenshot helper.  The repository uses
``module`` as its application package, and its modules all inherit the local
``ModuleBase``/``AzurLaneConfig`` pair, so the adapter deliberately avoids the
Alasio-only annotation and path dependencies.

Source: LmeSzinc/Alasio, commit c47c861194285b1adfd0baa12d20abf549be8adc,
alasio/testing/screenshot.py. See test/README.md for the migration workflow.
"""

from __future__ import absolute_import

import hashlib
import inspect
import json
import os
import re
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import get_type_hints

import pytest
from PIL import Image, ImageDraw

from module.testing.screenshot_device import ScreenshotDevice, ScreenshotNotProvided, ScreenshotTestError


ATTR_SCREENSHOT = '__screenshot__'
ATTR_SCREENSHOT_SERVER = '__screenshot_server__'
ATTR_SCREENSHOT_METADATA = '__screenshot_metadata__'
COLLECTION = 'collection'
CONFIG_NAME = 'template'
HASH_PREFIX = re.compile(r'[0-9a-fA-F]{8,64}\Z')


class ScreenshotNotFound(ScreenshotTestError):
    """Raised if the screenshot bound to a test cannot be loaded."""


class ScreenshotAmbiguous(ScreenshotTestError):
    """Raised when a hash prefix identifies more than one screenshot."""


class ModuleRequest(object):
    """Placeholder parametrized into a screenshot test module argument."""

    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.cls.__name__)


def _validate_relative_path(path):
    if not isinstance(path, (str, bytes, os.PathLike)):
        raise TypeError('Screenshot path must be a relative filesystem path')
    path = os.fspath(path)
    if isinstance(path, bytes):
        path = os.fsdecode(path)
    if not path or os.path.isabs(path):
        raise ValueError('Screenshot path must be relative to the collection folder')
    # pathlib treats a Windows drive as a normal name on POSIX, so explicitly
    # reject drive-qualified paths as well.
    if os.path.splitdrive(path)[0]:
        raise ValueError('Screenshot path must be relative to the collection folder')
    parts = Path(path).parts
    if '..' in parts:
        raise ValueError('Screenshot path must stay under the collection folder')
    return path


def image(path, server='cn'):
    """Bind one collected screenshot to a test function.

    ``path`` may be a named path relative to ``collection``, such as
    ``"island/order/regular_and_cooldown_orders_jp.webp"``, or a prefix of
    the actual PNG/WebP file-content SHA-256 (8 to 64 hexadecimal characters).
    ``"captures/e2e401e9"`` searches only that folder and its subfolders; a
    bare prefix searches the whole collection. An ambiguous prefix must be
    extended or scoped to a narrower folder. ``server`` selects ``cn``, ``jp``,
    ``en`` or ``tw``.
    """
    path = _validate_relative_path(path)
    from module.config.server import VALID_SERVER
    if server not in VALID_SERVER:
        raise ValueError('Unknown screenshot server {!r}; expected one of {}'.format(
            server, ', '.join(VALID_SERVER)))

    def decorator(func):
        setattr(func, ATTR_SCREENSHOT, path)
        setattr(func, ATTR_SCREENSHOT_SERVER, server)
        setattr(func, ATTR_SCREENSHOT_METADATA, {'path': path, 'server': server})
        return func

    return decorator


class ProjectRootManager(object):
    """Find and cache project roots for test files."""

    def __init__(self):
        self.roots = []

    @staticmethod
    def _contains(root, path):
        try:
            return os.path.commonpath([str(root), str(path)]) == str(root)
        except ValueError:
            return False

    def get_known_root(self, path):
        path = Path(os.path.abspath(os.fspath(path)))
        matches = [root for root in self.roots if self._contains(root, path)]
        return max(matches, key=lambda item: len(str(item))) if matches else None

    def get_project_root(self, test_file):
        path = Path(os.path.abspath(os.fspath(test_file)))
        known = self.get_known_root(path)
        if known is not None:
            return known
        root = self.find_root(path, test_file)
        self.roots.append(root)
        return root

    @staticmethod
    def find_root(path, test_file=None):
        path = Path(os.path.abspath(os.fspath(path)))
        folder = path.parent if path.is_file() else path
        while True:
            # ``const.py`` is the marker used by Alasio mods.  This checkout
            # has the equivalent generated config.py instead.
            if (folder / 'module' / 'config' / 'const.py').is_file() or \
                    (folder / 'module' / 'config' / 'config.py').is_file():
                return folder
            parent = folder.parent
            if parent == folder:
                break
            folder = parent
        raise ScreenshotTestError(
            'No project root above the test file "{}", a project root is a folder '
            'holding "module/config/const.py" or "module/config/config.py"'.format(
                test_file or path)
        )


PROJECT_ROOT_MANAGER = ProjectRootManager()


def test_name(item):
    node = getattr(item, 'node', item)
    return node.name


def _screenshot_server_of(item):
    return getattr(item.function, ATTR_SCREENSHOT_SERVER, 'cn')


def _is_within(root, path):
    try:
        return os.path.commonpath([str(root), str(path)]) == str(root)
    except ValueError:
        return False


def _screenshot_by_hash(collection, prefix, name):
    """Resolve a hash prefix within the supplied folder and its subfolders."""
    collection = collection.resolve()
    prefix = prefix.lower()
    matches = {}
    for file in sorted(collection.rglob('*')):
        if file.suffix.lower() not in ('.webp', '.png') or not file.is_file():
            continue
        resolved = file.resolve()
        if not _is_within(collection, resolved) or not resolved.is_file():
            continue
        try:
            with resolved.open('rb') as stream:
                digest = hashlib.sha256(stream.read()).hexdigest()
        except OSError:
            continue
        if digest.startswith(prefix):
            # Copies of the same content on different pages have one identity.
            matches.setdefault(digest, resolved)
    if not matches:
        raise ScreenshotNotFound(
            'No screenshot matches SHA-256 prefix "{}" for "{}" under {}'.format(
                prefix, name, collection)
        )
    if len(matches) > 1:
        raise ScreenshotAmbiguous(
            'Screenshot SHA-256 prefix "{}" for "{}" is ambiguous under {}. Use a longer '
            'prefix or a narrower folder. Matching hashes: {}'.format(
                prefix, name, collection, ', '.join(sorted(matches)))
        )
    return next(iter(matches.values())).resolve()


def screenshot_of(item):
    path = getattr(item.function, ATTR_SCREENSHOT, None)
    if path is None:
        raise ScreenshotNotFound(
            '"{}" has no screenshot, decorate the test with @image("<screenshot>") '
            'to bind one from the collection folder'.format(test_name(item))
        )
    root = PROJECT_ROOT_MANAGER.get_project_root(str(item.fspath))
    collection = (root / COLLECTION).resolve()
    reference = Path(path)
    file = (collection / path).resolve()
    if not _is_within(collection, file):
        raise ScreenshotTestError(
            'Screenshot path for "{}" must stay under the collection folder: {}'.format(
                test_name(item), path)
        )
    if file.is_file():
        return file
    if HASH_PREFIX.fullmatch(reference.name):
        folder = (collection / reference.parent).resolve()
        if not _is_within(collection, folder):
            raise ScreenshotTestError(
                'Screenshot search folder for "{}" must stay under the collection folder: {}'.format(
                    test_name(item), reference.parent)
            )
        file = _screenshot_by_hash(folder, reference.name, test_name(item))
    return file


def load_screenshot(item):
    file = screenshot_of(item)
    if not file.is_file():
        raise ScreenshotNotFound('Screenshot of "{}" does not exist: {}'.format(
            test_name(item), file))
    try:
        # Alas modules consume RGB arrays, matching module.base.utils.load_image.
        # Do not use cv2.imread here: it returns BGR and silently changes every
        # colour based detector in the module under test.
        from module.base.utils import load_image
        image = load_image(str(file))
    except (OSError, IOError) as exc:
        raise ScreenshotNotFound(
            'Screenshot of "{}" could not be read: {} ({})'.format(
                test_name(item), file, exc)
        ) from None
    return file, image


def _class_annotations(cls):
    try:
        return get_type_hints(cls)
    except (NameError, TypeError):
        annotations = {}
        for parent in reversed(getattr(cls, '__mro__', (cls,))):
            annotations.update(getattr(parent, '__annotations__', {}))
        return annotations


def _config_class(cls):
    annotation = _class_annotations(cls).get('config')
    return annotation if isinstance(annotation, type) else None


def config_of(cls):
    config_cls = _config_class(cls)
    if config_cls is None:
        raise ScreenshotTestError(
            '"{}" has no usable "config" annotation; annotate it like the '
            'module does: "config: AzurLaneConfig"'.format(cls.__name__)
        )
    # The template name makes AzurLaneConfig read-only and avoids all user
    # config file/database IO.  Custom config classes used by tests follow the
    # same one-argument constructor contract.
    return config_cls(CONFIG_NAME)


def build_main(cls, device, **kwargs):
    return cls(config_of(cls), device=device, **kwargs)


def module_parameters(function):
    try:
        annotations = get_type_hints(function)
    except (NameError, TypeError):
        annotations = getattr(function, '__annotations__', {})
    out = {}
    for name, annotation in annotations.items():
        if name in ('self', 'return') or not isinstance(annotation, type):
            continue
        if _config_class(annotation) is not None:
            out[name] = annotation
    return out


def pytest_addoption(parser):
    parser.addoption(
        '--screenshot-review-dir',
        action='store',
        default=None,
        metavar='PATH',
        help='write optional screenshot review JSON, overlays and index under PATH',
    )


def pytest_configure(config):
    # Review reports are intentionally scoped to one pytest session.  Keeping
    # this mapping in memory avoids reparsing Markdown links from an older run.
    config._screenshot_review_entries = {}


def pytest_generate_tests(metafunc):
    if getattr(metafunc.function, ATTR_SCREENSHOT, None) is None:
        return
    for name, cls in module_parameters(metafunc.function).items():
        metafunc.parametrize(name, [ModuleRequest(cls)], ids=[cls.__name__])


@contextmanager
def _resource_server_context(server_name):
    import module.config.server as server_module
    from module.base.resource import Resource

    original_server = server_module.server
    original_instances = dict(Resource.instances)
    original_state = [(obj, dict(obj.__dict__)) for obj in original_instances.values()]
    try:
        server_module.server = server_name
        for obj in original_instances.values():
            try:
                obj.resource_release()
            except (AttributeError, KeyError):
                pass
        yield
    finally:
        server_module.server = original_server
        Resource.instances.clear()
        Resource.instances.update(original_instances)
        for obj, state in original_state:
            obj.__dict__.clear()
            obj.__dict__.update(state)


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, timedelta):
        return value.total_seconds()
    try:
        import numpy as np
        if isinstance(value, np.generic):
            return _jsonable(value.item())
        if isinstance(value, np.ndarray):
            return _jsonable(value.tolist())
    except ImportError:
        pass
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, '_asdict'):
        return _jsonable(value._asdict())
    if hasattr(value, '__dict__'):
        return {str(key): _jsonable(item) for key, item in value.__dict__.items()
                if not key.startswith('__')}
    return repr(value)


def _region_area(region):
    label = ''
    area = region
    if isinstance(region, dict):
        area = region.get('area', ())
        label = region.get('label', '')
    elif isinstance(region, (list, tuple)) and len(region) == 2 and \
            isinstance(region[1], str):
        area, label = region
    elif hasattr(region, 'area'):
        area = region.area
        label = getattr(region, 'name', '')
    try:
        coords = tuple(int(float(value)) for value in area)
    except (TypeError, ValueError):
        return None, label
    if len(coords) != 4:
        return None, label
    return coords, label


def _review_paths(review_dir, source):
    source = Path(source)
    root = PROJECT_ROOT_MANAGER.get_project_root(str(source))
    collection = root / COLLECTION
    relative = source.resolve().relative_to(collection.resolve())
    # Replacing the final suffix directly preserves earlier dots, e.g.
    # ``page.v2.webp`` becomes ``page.v2.json`` rather than ``page.json``.
    return root, relative, Path(review_dir).resolve() / relative.with_suffix('.json'), \
        Path(review_dir).resolve() / relative.with_suffix('.png')


def _write_review_reports(item, device, review_dir):
    if not device or not device.reviews:
        return
    source = Path(device.file)
    root, relative, json_file, overlay_file = _review_paths(review_dir, source)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    overlay_file.parent.mkdir(parents=True, exist_ok=True)

    records = [_jsonable(record) for record in device.reviews]
    payload = {
        'status': 'unreviewed machine output; compare the full result with the screenshot by hand',
        'nodeid': item.nodeid,
        'source': (Path(COLLECTION) / relative).as_posix(),
        'result': records[0]['result'] if len(records) == 1 else [record['result'] for record in records],
        'regions': records[0]['regions'] if len(records) == 1 else [record['regions'] for record in records],
        'reviews': records,
    }
    with open(str(json_file), 'w', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)

    if isinstance(device.image, Image.Image):
        overlay = device.image.convert('RGB').copy()
    else:
        overlay = Image.fromarray(device.image).convert('RGB')
    draw = ImageDraw.Draw(overlay)
    for record in device.reviews:
        for region in record['regions']:
            area, label = _region_area(region)
            if area is None:
                continue
            draw.rectangle(area, outline='red', width=3)
            if label:
                try:
                    draw.text((area[0], area[1]), str(label), fill='red')
                except UnicodeError:
                    # A default PIL font may not contain a human supplied
                    # label; retaining the rectangle still makes the region
                    # reviewable and must not fail the test report.
                    draw.text((area[0], area[1]), '?', fill='red')
    overlay.save(str(overlay_file), format='PNG')

    review_root = Path(review_dir).resolve()
    review_root.mkdir(parents=True, exist_ok=True)
    index_file = review_root / 'index.md'
    source_link = os.path.relpath(str(source), str(review_root)).replace(os.sep, '/')
    overlay_link = os.path.relpath(str(overlay_file), str(review_root)).replace(os.sep, '/')
    report_link = os.path.relpath(str(json_file), str(review_root)).replace(os.sep, '/')
    entries = getattr(item.config, '_screenshot_review_entries', None)
    if entries is None:
        entries = item.config._screenshot_review_entries = {}
    entries[item.nodeid] = {
        'source': source_link,
        'overlay': overlay_link,
        'report': report_link,
        'status': 'unreviewed machine output',
    }
    with open(str(index_file), 'w', encoding='utf-8') as stream:
        stream.write('# Screenshot review\n\n')
        stream.write('Machine generated outputs are unreviewed; compare each full result with its source screenshot.\n\n')
        stream.write('| nodeid | source | overlay | report | status |\n')
        stream.write('|---|---|---|---|---|\n')
        for nodeid in sorted(entries):
            value = entries[nodeid]
            stream.write('| {} | [source]({}) | [overlay]({}) | [report]({}) | {} |\n'.format(
                nodeid.replace('|', '\\|'), value['source'], value['overlay'],
                value['report'], value['status']))


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if getattr(pyfuncitem.function, ATTR_SCREENSHOT, None) is None:
        return None

    if inspect.iscoroutinefunction(pyfuncitem.function):
        raise ScreenshotTestError('"{}" is async, a screenshot test is sync'.format(pyfuncitem.name))

    # Resolve the source before looking for module parameters.  This means a
    # decorated test with no module arguments still fails clearly for a missing
    # screenshot while ordinary tests remain entirely under pytest's hooks.
    file, screenshot = load_screenshot(pyfuncitem)
    requests = {
        name: pyfuncitem.funcargs[name]
        for name in module_parameters(pyfuncitem.function)
        if isinstance(pyfuncitem.funcargs.get(name), ModuleRequest)
    }
    device = None
    modules = {}
    server_name = _screenshot_server_of(pyfuncitem)
    try:
        with _resource_server_context(server_name):
            if requests:
                device = ScreenshotDevice(image=screenshot, file=file)
                for name, request in requests.items():
                    modules[name] = build_main(request.cls, device)

            names = set(inspect.signature(pyfuncitem.function).parameters) - {'self'}
            kwargs = {name: value for name, value in pyfuncitem.funcargs.items() if name in names}
            kwargs.update(modules)
            pyfuncitem.obj(**kwargs)
    finally:
        review_dir = pyfuncitem.config.getoption('screenshot_review_dir')
        if review_dir and device is not None:
            _write_review_reports(pyfuncitem, device, review_dir)
    return True
