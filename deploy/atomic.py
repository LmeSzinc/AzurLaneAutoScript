import os
import random
import string
import time
from contextlib import suppress

IS_WINDOWS = os.name == "nt"
# Max attempt if another process is reading/writing, effective only on Windows
WINDOWS_MAX_ATTEMPT = 5
# Base time to wait between retries (seconds)
WINDOWS_RETRY_DELAY = 0.05


def random_id():
    """
    Returns:
        str: Random ID, like "sTD2kF"
    """
    # 6 random letter (62^6 combinations) would be enough
    return "".join(random.sample(string.ascii_letters + string.digits, 6))


def is_tmp_file(file: str) -> bool:
    """
    Check if a filename is tmp file
    """
    # Check suffix first to reduce regex calls
    if not file.endswith(".tmp"):
        return False
    # Check temp file format
    dot = file[-11:-10]
    if not dot:
        return False
    rid = file[-10:-4]
    return rid.isalnum()


def to_tmp_file(file: str) -> str:
    """
    Convert a filename or directory name to tmp
    filename -> filename.sTD2kF.tmp
    """
    suffix = random_id()
    return f"{file}.{suffix}.tmp"


def windows_attempt_delay(attempt: int) -> float:
    """
    Exponential Backoff if file is in use on Windows

    Args:
        attempt: Current attempt, starting from 0

    Returns:
        float: Seconds to wait
    """
    return 2**attempt * WINDOWS_RETRY_DELAY


def replace_tmp(tmp: str, file: str):
    """
    Replace temp file to file

    Raises:
        PermissionError: (Windows only) If another process is still reading the file and all retries failed
        FileNotFoundError: If tmp file gets deleted unexpectedly
    """
    if IS_WINDOWS:
        # PermissionError on Windows if another process is reading
        last_error = None
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                # Atomic operation
                os.replace(tmp, file)
                # success
                return
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
                time.sleep(delay)
                continue
            except FileNotFoundError:
                # tmp file gets deleted unexpectedly
                raise
            except Exception as e:
                last_error = e
                break
    else:
        # Linux and Mac allow existing reading
        try:
            # Atomic operation
            os.replace(tmp, file)
            # success
            return
        except FileNotFoundError:
            raise
        except Exception as e:
            last_error = e

    # Clean up tmp file on failure (both FileNotFoundError -- tmp file
    # already deleted -- and any other failure are swallowed).
    with suppress(Exception):
        os.unlink(tmp)
    if last_error is not None:
        raise last_error from None


def file_write(file: str, data: str | bytes):
    """
    Write data into file, auto create directory
    Auto determines write mode based on the type of data.
    """
    if isinstance(data, str):
        mode = "w"
        encoding = "utf-8"
        newline = ""
    elif isinstance(data, bytes):
        mode = "wb"
        encoding = None
        newline = None
        # Create memoryview as Pathlib do
        data = memoryview(data)
    else:
        typename = str(type(data))
        if typename == "<class 'numpy.ndarray'>":
            mode = "wb"
            encoding = None
            newline = None
        else:
            mode = "w"
            encoding = "utf-8"
            newline = ""

    try:
        # Write temp file
        with open(file, mode=mode, encoding=encoding, newline=newline) as f:
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
        with open(file, mode=mode, encoding=encoding, newline=newline) as f:
            f.write(data)
            # Ensure data flush to disk
            f.flush()
            os.fsync(f.fileno())


def atomic_write(
    file: str,
    data: str | bytes,
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
    file_write(temp, data)
    replace_tmp(temp, file)


def file_read_text(file: str, encoding: str = "utf-8", errors: str = "strict") -> str:
    """
    Args:
        file:
        encoding:
        errors: 'strict', 'ignore', 'replace' and any other errors mode in open()
    """
    try:
        with open(file, encoding=encoding, errors=errors) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def file_read_bytes(file: str) -> bytes:
    """
    Args:
        file:
    """
    try:
        # No python-side buffering when reading the entire file to speedup reading
        # https://github.com/python/cpython/pull/122111
        with open(file, mode="rb", buffering=0) as f:
            return f.read()
    except FileNotFoundError:
        return b""


def atomic_read_text(file: str, encoding: str = "utf-8", errors: str = "strict") -> str:
    """
    Atomic file read with minimal IO operation

    Args:
        file:
        encoding:
        errors: 'strict', 'ignore', 'replace' and any other errors mode in open()
    """
    if IS_WINDOWS:
        # PermissionError on Windows if another process is replacing
        last_error = None
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                return file_read_text(file, encoding=encoding, errors=errors)
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
                time.sleep(delay)
                continue
        if last_error is not None:
            raise last_error from None
    else:
        # Linux and Mac allow reading while replacing
        return file_read_text(file, encoding=encoding, errors=errors)


def atomic_read_bytes(file: str) -> bytes:
    """
    Atomic file read with minimal IO operation
    """
    if IS_WINDOWS:
        # PermissionError on Windows if another process is replacing
        last_error = None
        for attempt in range(WINDOWS_MAX_ATTEMPT):
            try:
                return file_read_bytes(file)
            except PermissionError as e:
                last_error = e
                delay = windows_attempt_delay(attempt)
                time.sleep(delay)
                continue
        if last_error is not None:
            raise last_error from None
    else:
        # Linux and Mac allow reading while replacing
        return file_read_bytes(file)


def file_remove(file: str):
    """
    Remove a file non-atomic
    """
    with suppress(FileNotFoundError):
        # If file not exist, just no need to remove
        os.unlink(file)


def folder_rmtree(folder, may_symlinks=True):
    """
    Recursively remove a folder and its content

    Args:
        folder:
        may_symlinks: Default to True
            False if you already know it's not a symlink

    Returns:
        bool: If success
    """
    try:
        # If it's a symlinks, unlink it
        if may_symlinks and os.path.islink(folder):
            file_remove(folder)
            return True
        # Iter folder
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    folder_rmtree(entry.path, may_symlinks=False)
                else:
                    # File or symlink
                    # Just remove the symlink, not what it points to.
                    # PermissionError: another process is reading/writing.
                    with suppress(PermissionError):
                        file_remove(entry.path)

    except FileNotFoundError:
        # directory to clean up does not exist, no need to clean up
        return True
    except NotADirectoryError:
        file_remove(folder)
        return True

    # Remove empty folder
    # May raise OSError if it's still not empty
    try:
        os.rmdir(folder)
        return True
    except FileNotFoundError:
        return True
    except NotADirectoryError:
        file_remove(folder)
        return True
    except OSError:
        return False


def atomic_failure_cleanup(folder: str, recursive: bool = False):
    """
    Cleanup remaining temp file under given path.
    In most cases there should be no remaining temp files unless write process get interrupted.

    This method should only be called at startup
    to avoid deleting temp files that another process is writing.
    """
    try:
        with os.scandir(folder) as entries:
            for entry in entries:
                if is_tmp_file(entry.name):
                    # Delete temp file or directory. Swallow all failures:
                    # another process may be reading/writing.
                    with suppress(Exception):
                        if entry.is_dir(follow_symlinks=False):
                            folder_rmtree(entry.path, may_symlinks=False)
                        else:
                            file_remove(entry.path)
                else:
                    if recursive:
                        with suppress(Exception):
                            if entry.is_dir(follow_symlinks=False):
                                # Normal directory
                                atomic_failure_cleanup(entry.path, recursive=True)

    except FileNotFoundError:
        # directory to clean up does not exist, no need to clean up
        pass
    except NotADirectoryError:
        file_remove(folder)
    except Exception:
        # Ignore all failures, it doesn't matter if tmp files still exist
        pass
