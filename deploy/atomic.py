import os
import random
import re
import string
import time
from typing import Union

# Max attempt if another process is reading/writing, effective only on Windows
WINDOWS_MAX_ATTEMPT = 5
# Base time to wait between retries (seconds)
WINDOWS_RETRY_DELAY = 0.05


def random_id(length: int = 6) -> str:
    """
    Args:
        length (int): 6 random letter (62^6 combinations) would be enough

    Returns:
        str: Random ID, like "sTD2kF"
    """
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


def is_tmp_file(filename: str) -> bool:
    """
    Check if a filename is tmp file
    """
    # Check suffix first to reduce regex calls
    if not filename.endswith('.tmp'):
        return False
    # Check temp file format
    res = re.match(r'.*\.[a-zA-Z0-9]{6,}\.tmp$', filename)
    if not res:
        return False
    return True


def to_tmp_file(filename: str) -> str:
    """
    Convert a filename or directory name to tmp
    """
    suffix = random_id(6)
    return f'{filename}.{suffix}.tmp'


def windows_attempt_delay(attempt: int) -> float:
    """
    Exponential Backoff if file is in use on Windows

    Args:
        attempt: Current attempt, starting from 0

    Returns:
        float: Seconds to wait
    """
    return 2 ** attempt * WINDOWS_RETRY_DELAY


def atomic_write(
        file: str,
        data: Union[str, bytes],
):
    """
    Atomic file write with minimal IO operation
    and handles cases where file might be read by another process.

    os.replace() is an atomic operation among all OS,
    we write to temp file then do os.replace()

    Args:
        file:
        data:
    """
    temp = to_tmp_file(file)
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
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                # Atomic operation
                os.replace(temp, file)
                # success
                return
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
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


def atomic_stream_write(
        file: str,
        data_generator,
):
    """
    Atomic file write with streaming data support.
    Handles cases where file might be read by another process.
    os.replace() is an atomic operation among all OS,
    we write to temp file then do os.replace()

    Only creates a file if the generator yields at least one data chunk.
    Automatically determines write mode based on the type of first chunk.

    Args:
        file: Target file path
        data_generator: An iterable that yields data chunks (str or bytes)
    """
    # Convert generator to iterator to ensure we can peek at first chunk
    data_iter = iter(data_generator)

    # Try to get the first chunk
    try:
        first_chunk = next(data_iter)
    except StopIteration:
        # Generator is empty, no file will be created
        return

    # Create temp file path
    temp = to_tmp_file(file)

    # Determine mode, encoding and newline from first chunk
    if isinstance(first_chunk, str):
        mode = 'w'
        encoding = 'utf-8'
        newline = ''
    elif isinstance(first_chunk, bytes):
        mode = 'wb'
        encoding = None
        newline = None
    else:
        # Default to text mode for other types
        mode = 'w'
        encoding = 'utf-8'
        newline = ''

    try:
        # Write temp file
        with open(temp, mode=mode, encoding=encoding, newline=newline) as f:
            f.write(first_chunk)
            for chunk in data_iter:
                f.write(chunk)
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
            f.write(first_chunk)
            for chunk in data_iter:
                f.write(chunk)
            # Ensure data flush to disk
            f.flush()
            os.fsync(f.fileno())

    last_error = None
    if os.name == 'nt':
        # PermissionError on Windows if another process is reading
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                # Atomic operation
                os.replace(temp, file)
                # success
                return
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
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
):
    """
    Atomic file read with minimal IO operation
    Since os.replace() is atomic, atomic reading is just plain read.

    Args:
        file:
        mode: 'r' or 'rb'
        errors: 'strict', 'ignore', 'replace' and any other errors mode in open()

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
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                with open(file, mode=mode, encoding=encoding, errors=errors) as f:
                    # success
                    return f.read()
            except FileNotFoundError:
                return ''
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
                time.sleep(delay)
                continue
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


def atomic_remove(file: str):
    """
    Atomic file remove

    Args:
        file:
    """
    if os.name == 'nt':
        # PermissionError on Windows if another process is replacing
        last_error = None
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                os.unlink(file)
            except FileNotFoundError:
                return
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
                time.sleep(delay)
                continue
        if last_error is not None:
            raise last_error from None
    else:
        # Linux and Mac allow deleting while another process is reading
        # The directory entry is removed but the storage allocated to the file is not made available
        # until the original file is no longer in use.
        try:
            os.unlink(file)
        except FileNotFoundError:
            return


def atomic_failure_cleanup(directory: str, recursive: bool = False):
    """
    Cleanup remaining temp file under given path.
    In most cases there should be no remaining temp files unless write process get interrupted.

    This method should only be called at startup
    to avoid deleting temp files that another process is writing.
    """
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if is_tmp_file(entry.name):
                    # Delete temp file or directory
                    if entry.is_dir(follow_symlinks=False):
                        import shutil
                        shutil.rmtree(entry.path, ignore_errors=True)
                    else:
                        try:
                            os.unlink(entry.path)
                        except PermissionError:
                            # Another process is reading/writing
                            pass
                        except FileNotFoundError:
                            # Another process removed current file while iterating
                            pass
                        except:
                            pass
                else:
                    if entry.is_dir(follow_symlinks=False):
                        # Normal directory
                        if recursive:
                            atomic_failure_cleanup(entry.path, recursive=True)
                    # Normal file
                    # else:
                    #     pass
    except FileNotFoundError:
        # directory to clean up does not exist, no need to clean up
        pass
