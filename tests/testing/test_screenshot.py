"""File reference lookup tests; these do not decode or recognize images."""
import hashlib
from types import SimpleNamespace

import pytest

import module.testing.screenshot as screenshot_module
from module.testing.screenshot import (
    ScreenshotAmbiguous,
    ScreenshotNotFound,
    ScreenshotTestError,
    image,
    screenshot_of,
)


def _item(root, function):
    return SimpleNamespace(
        function=function,
        fspath=str(root / 'tests' / 'test_screenshot.py'),
        name='test_resolver',
    )


def _resolve(root, path, monkeypatch):
    monkeypatch.setattr(
        screenshot_module.PROJECT_ROOT_MANAGER,
        'get_project_root',
        lambda test_file: root,
    )

    @image(path)
    def test_function():
        pass

    return screenshot_of(_item(root, test_function))


def test_named_png_and_webp_paths(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'named'
    collection.mkdir(parents=True)
    for suffix in ('png', 'webp'):
        path = collection / ('named-frame.' + suffix)
        path.write_bytes(('named-' + suffix).encode('ascii'))

        assert _resolve(tmp_path, 'named/' + path.name, monkeypatch) == path.resolve()


def test_content_hash_survives_rename_and_accepts_uppercase(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'renamed'
    collection.mkdir(parents=True)
    content = b'encoded screenshot bytes'
    original = collection / 'first.webp'
    original.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    renamed = collection / 'nested' / 'second.webp'
    renamed.parent.mkdir()
    original.rename(renamed)

    assert _resolve(tmp_path, 'renamed/' + digest.upper(), monkeypatch) == renamed.resolve()


def test_hash_lookup_ignores_digest_in_filename(tmp_path, monkeypatch):
    collection = tmp_path / 'collection'
    collection.mkdir()
    content = b'expected encoded bytes'
    digest = hashlib.sha256(content).hexdigest()
    (collection / (digest + '.webp')).write_bytes(b'different encoded bytes')
    expected = collection / 'meaningful.webp'
    expected.write_bytes(content)

    assert _resolve(tmp_path, digest[:8], monkeypatch) == expected.resolve()


def test_hash_looking_named_file_uses_its_path(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'named'
    collection.mkdir(parents=True)
    path = collection / 'deadbeef'
    path.write_bytes(b'content does not start with deadbeef')

    assert _resolve(tmp_path, 'named/deadbeef', monkeypatch) == path.resolve()


def test_identical_content_copies_have_one_hash_identity(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'copies'
    collection.mkdir(parents=True)
    content = b'the same encoded screenshot'
    first = collection / 'first.png'
    second = collection / 'second.webp'
    first.write_bytes(content)
    second.write_bytes(content)
    prefix = hashlib.sha256(content).hexdigest()[:12]

    assert _resolve(tmp_path, 'copies/' + prefix, monkeypatch) == first.resolve()


def test_hash_search_stays_in_requested_folder(tmp_path, monkeypatch):
    collection = tmp_path / 'collection'
    source = collection / 'source' / 'image.webp'
    source.parent.mkdir(parents=True)
    content = b'only in source folder'
    source.write_bytes(content)
    prefix = hashlib.sha256(content).hexdigest()[:12]

    with pytest.raises(ScreenshotNotFound):
        _resolve(tmp_path, 'other/' + prefix, monkeypatch)


def test_hash_search_rejects_symlink_outside_collection(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'inside'
    collection.mkdir(parents=True)
    outside = tmp_path / 'outside.webp'
    content = b'outside collection'
    outside.write_bytes(content)
    (collection / 'escape.webp').symlink_to(outside)
    prefix = hashlib.sha256(content).hexdigest()[:12]

    with pytest.raises(ScreenshotNotFound):
        _resolve(tmp_path, 'inside/' + prefix, monkeypatch)


def test_named_symlink_outside_collection_is_rejected(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'inside'
    collection.mkdir(parents=True)
    outside = tmp_path / 'outside.webp'
    outside.write_bytes(b'outside collection')
    (collection / 'escape.webp').symlink_to(outside)

    with pytest.raises(ScreenshotTestError):
        _resolve(tmp_path, 'inside/escape.webp', monkeypatch)


def test_eight_character_prefix_ambiguity_is_reported(tmp_path, monkeypatch):
    collection = tmp_path / 'collection' / 'ambiguous'
    collection.mkdir(parents=True)
    first = b'collision-55045'
    second = b'collision-70885'
    assert hashlib.sha256(first).hexdigest().startswith('45560c60')
    assert hashlib.sha256(second).hexdigest().startswith('45560c60')
    (collection / 'first.png').write_bytes(first)
    (collection / 'second.webp').write_bytes(second)

    with pytest.raises(ScreenshotAmbiguous):
        _resolve(tmp_path, 'ambiguous/45560c60', monkeypatch)

    assert _resolve(tmp_path, 'ambiguous/' + hashlib.sha256(first).hexdigest(), monkeypatch) == \
        (collection / 'first.png').resolve()
