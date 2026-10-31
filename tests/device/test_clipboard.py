import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
from filelock import FileLock, Timeout

import module.device.input as input_module
from module.device.input import Input


@pytest.fixture
def device(monkeypatch, tmp_path):
    monkeypatch.setattr(input_module, '_CLIPBOARD_LOCK_FILE', str(tmp_path / 'clipboard.lock'))
    device = object.__new__(Input)
    device.ensure_clipboard = Mock(return_value=True)
    device.get_clipboard = Mock(return_value='copied text')
    return device


def assert_clipboard_locked():
    with pytest.raises(Timeout):
        with FileLock(input_module._CLIPBOARD_LOCK_FILE, timeout=0):
            pass


def assert_clipboard_released():
    with FileLock(input_module._CLIPBOARD_LOCK_FILE, timeout=0):
        pass


def test_copy_and_read_both_hold_the_clipboard_lock(device):
    def copy():
        assert_clipboard_locked()
        return True

    def read():
        assert_clipboard_locked()
        return 'copied text'

    device.get_clipboard.side_effect = read
    assert device.clipboard_copy(copy) == 'copied text'
    device.ensure_clipboard.assert_called_once_with()
    assert_clipboard_released()


def test_unavailable_clipboard_does_not_copy_or_read(device):
    device.ensure_clipboard.return_value = False
    copy = Mock(return_value=True)

    assert device.clipboard_copy(copy) is None
    copy.assert_not_called()
    device.get_clipboard.assert_not_called()


def test_incomplete_copy_does_not_read_stale_clipboard_and_releases_lock(device):
    assert device.clipboard_copy(lambda: False) is None
    device.get_clipboard.assert_not_called()
    assert_clipboard_released()


def test_busy_clipboard_does_not_copy_or_read(device):
    copy = Mock(return_value=True)
    with FileLock(input_module._CLIPBOARD_LOCK_FILE, timeout=0):
        assert device.clipboard_copy(copy, timeout=0) is None
    copy.assert_not_called()
    device.get_clipboard.assert_not_called()
    assert_clipboard_released()


@pytest.mark.parametrize('stage', ['copy', 'read'])
def test_copy_or_read_error_releases_lock(device, stage):
    copy = Mock(return_value=True)
    (copy if stage == 'copy' else device.get_clipboard).side_effect = RuntimeError('clipboard failed')

    with pytest.raises(RuntimeError, match='clipboard failed'):
        device.clipboard_copy(copy)
    assert_clipboard_released()


def test_separate_processes_and_working_directories_share_the_clipboard_lock(tmp_path):
    root = Path(__file__).resolve().parents[2]
    common = tmp_path / 'shared-temp'
    common.mkdir()
    working_directories = [tmp_path / name for name in ('first', 'second')]
    for directory in working_directories:
        directory.mkdir()
    child = '''
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
tempfile.tempdir = sys.argv[2]
from module.device.input import Input

directory = Path(sys.argv[2])
role = sys.argv[3]
device = object.__new__(Input)
device.serial = role
device.ensure_clipboard = lambda: True
device.get_clipboard = lambda: (directory / 'clipboard.txt').read_text()
copied = False
def copy():
    global copied
    copied = True
    (directory / 'clipboard.txt').write_text(role)
    if role == 'first':
        (directory / 'ready').touch()
        sys.stdin.readline()
    return True
result = device.clipboard_copy(copy, timeout=0)
print('CLIPBOARD_RESULT=' + json.dumps({'copied': copied, 'result': result}), flush=True)
'''
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

    def command(role):
        return [sys.executable, '-B', '-c', child, str(root), str(common), role]

    def result(output):
        return json.loads(next(line[len('CLIPBOARD_RESULT='):] for line in output.splitlines()
                               if line.startswith('CLIPBOARD_RESULT=')))

    def contender():
        process = subprocess.run(command('second'), cwd=str(working_directories[1]), env=environment,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        assert process.returncode == 0, process.stdout + process.stderr
        return result(process.stdout)

    holder = subprocess.Popen(command('first'), cwd=str(working_directories[0]), env=environment,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 20
        while not (common / 'ready').exists():
            if holder.poll() is not None:
                output, errors = holder.communicate()
                pytest.fail('Clipboard holder exited before copying: ' + output + errors)
            if time.monotonic() >= deadline:
                pytest.fail('Clipboard holder did not start copying')
            time.sleep(0.01)

        assert contender() == {'copied': False, 'result': None}
        assert (common / 'clipboard.txt').read_text() == 'first'
        output, errors = holder.communicate(input='release\n', timeout=20)
        assert holder.returncode == 0, output + errors
        assert result(output) == {'copied': True, 'result': 'first'}
        assert contender() == {'copied': True, 'result': 'second'}
    finally:
        if holder.poll() is None:
            holder.kill()
        if not holder.stdout.closed or not holder.stderr.closed:
            holder.communicate()
