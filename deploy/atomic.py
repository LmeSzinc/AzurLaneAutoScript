import os
import random
import re
import string
import time
from typing import Union


def random_id(length=6):
    """
    Args:
        length (int): 6 random letter (62^6 combinations) would be enough

    Returns:
        str: Random ID, like "sTD2kF"
    """
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


def atomic_write(
        file: str,
        data: Union[str, bytes],
        max_attempt=5,
        retry_delay=0.05,
):
    """
    Atomic file write with minimal IO operation
    and handles cases where file might be read by another process.

    os.replace() is an atomic operation among all OS,
    we write to temp file then do os.replace()

    Args:
        file:
        data:
        max_attempt: Max attempt if another process is reading,
            effective only on Windows
        retry_delay: Base time to wait between retries (seconds)
    """
    suffix = random_id(6)
    temp = f'{file}.{suffix}.tmp'
    if isinstance(data, str):
        mode = 'w'
        encoding = 'utf-8'
        newline = ''
    elif isinstance(data, bytes):
        mode = 'wb'
        encoding = None
        newline = None
    else:
        mode = 'w'
        encoding = 'utf-8'
        newline = ''

    try:
        # Write temp file
        with open(temp, mode=mode, encoding=encoding, newline=newline) as f:
            f.write(data)
            # Ensure data flush to disk
            f.flush()
            os.fsync(f.fileno())
    except FileNotFoundError:
        # Create parent directory
        directory = os.path.dirname(file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        # Write again
        with open(temp, mode=mode, encoding=encoding, newline=newline) as f:
            f.write(data)
            # Ensure data flush to disk
            f.flush()
            os.fsync(f.fileno())

    if os.name == 'nt':
        # PermissionError on Windows if another process is reading
        last_error = None
        if max_attempt < 1:
            max_attempt = 1
        for trial in range(max_attempt):
            try:
                # Atomic operation
                os.replace(temp, file)
                # success
                return
            except PermissionError as e:
                last_error = e
                delay = 2 ** trial * retry_delay
                time.sleep(delay)
                continue
            except Exception as e:
                last_error = e
                break
    else:
        # Linux and Mac allow existing reading
        try:
            # Atomic operation
            os.replace(temp, file)
            # success
            return
        except Exception as e:
            last_error = e

    # Clean up temp file on failure
    try:
        os.unlink(temp)
    except:
        pass
    if last_error is not None:
        raise last_error from None


def atomic_read(
        file: str,
        mode: str = 'r',
        errors: str = 'strict',
        max_attempt=5,
        retry_delay=0.05,
):
    """
    Atomic file read with minimal IO operation
    Since os.replace() is atomic, atomic reading is just plain read.

    Args:
        file:
        mode: 'r' or 'rb'
        errors: 'strict', 'ignore', 'replace' and any other errors mode in open()
        max_attempt: Max attempt if another process is reading,
            effective only on Windows
        retry_delay: Base time to wait between retries (seconds)

    Returns:
        str if mode is 'r'
        bytes if mode is 'rb'
    """
    if 'b' in mode:
        encoding = None
        errors = None
    else:
        encoding = 'utf-8'

    if os.name == 'nt':
        # PermissionError on Windows if another process is replacing
        last_error = None
        if max_attempt < 1:
            max_attempt = 1
        for trial in range(max_attempt):
            try:
                with open(file, mode=mode, encoding=encoding, errors=errors) as f:
                    # success
                    return f.read()
            except FileNotFoundError:
                return ''
            except PermissionError as e:
                last_error = e
                delay = 2 ** trial * retry_delay
                time.sleep(delay)
                continue
            except Exception as e:
                last_error = e
                break
        if last_error is not None:
            raise last_error from None
    else:
        # Linux and Mac allow reading while replacing
        try:
            with open(file, mode=mode, encoding=encoding, errors=errors) as f:
                # success
                return f.read()
        except FileNotFoundError:
            return ''


def atomic_failure_cleanup(path: str):
    """
    Cleanup remaining temp file under given path.
    In most cases there should be no remaining temp files unless write process get interrupted.

    This method should only be called at startup
    to avoid deleting temp files that another process is writing.
    """
    with os.scandir(path) as entries:
        for entry in entries:
            if not entry.is_file():
                continue
            # Check suffix first to reduce regex calls
            name = entry.name
            if not name.endswith('.tmp'):
                continue
            # Check temp file format
            res = re.match(r'.*\.[a-zA-Z0-9]{6,}\.tmp$', name)
            if not res:
                continue
            # Delete temp file
            file = f'{path}{os.sep}{name}'
            try:
                os.unlink(file)
            except PermissionError:
                # Another process is reading/writing
                pass
            except:
                pass
