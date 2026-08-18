"""Logging stack tests (L1 loguru rewrite).

Pin the public contract of module.logger: hr separator lines (consumed by
alas.save_error_log's split regex), attr/error/exception semantics, lazy
{}-formatting, the file sink behavior, and the func-stream renderable
contract used by the webui parent process.
"""

import os
import re
import time

import pytest
from rich.console import Console

import module.logger as log_module
from module.logger import logger


@pytest.fixture
def capture_logs():
    lines = []
    sink_id = logger.add(  # type: ignore[attr-defined] (loguru ships no py.typed)
        lambda m: lines.append(str(m).rstrip("\n")), format="{message}", level="TRACE", enqueue=False
    )
    yield lines
    logger.remove(sink_id)  # type: ignore[attr-defined] (loguru ships no py.typed)


def test_hr_level3(capture_logs):
    logger.hr("Test", level=3)
    assert capture_logs == ["<<< TEST >>>"]


def test_hr_level2(capture_logs):
    logger.hr("Test", level=2)
    assert len(capture_logs) == 2
    assert capture_logs[0].startswith("─")
    assert capture_logs[1] == "TEST"


def test_hr_level0_separator_lines(capture_logs):
    logger.hr("Start", level=0)
    assert len(capture_logs) == 3
    # First and last lines must match ^═{15,}$ - the pattern
    # alas.save_error_log() uses to split the error log file.
    assert re.fullmatch(r"═{15,}", capture_logs[0])
    assert re.fullmatch(r"═{15,}", capture_logs[-1])
    assert "START" in capture_logs[1]


def test_attr(capture_logs):
    logger.attr("Key", "value")
    assert capture_logs == ["[Key] value"]


def test_attr_align(capture_logs):
    logger.attr_align("Key", "value", align=10)
    assert capture_logs[0].endswith("Key: value")


def test_error_converts_exception(capture_logs):
    logger.error(ValueError("boom"))
    assert capture_logs[0].startswith("ValueError: boom")


def test_exception_logs_once_with_traceback(capture_logs):
    try:
        raise RuntimeError("trace me")
    except RuntimeError as e:
        logger.exception(e)
    text = "\n".join(capture_logs)
    assert text.startswith("trace me")
    assert text.count("Traceback (most recent call last)") == 1
    assert "RuntimeError: trace me" in text


def test_lazy_braces_formatting(capture_logs):
    logger.info("value={} other={}", 1, 2)
    assert capture_logs == ["value=1 other=2"]


def test_func_stream_delivers_renderable():
    received = []
    log_module.set_func_logger(received.append)
    try:
        logger.info("hello stream")
        assert received, "func sink did not receive a renderable"
        console = Console(no_color=True, force_terminal=False, width=120)
        with console.capture() as capture:
            console.print(received[-1])
        text = capture.get()
        assert "hello stream" in text
        assert "INFO" in text
    finally:
        log_module._logger.remove(log_module._func_sink_id)  # type: ignore[attr-defined]
        log_module._func_sink_id = None  # type: ignore[attr-defined]


def test_cleanup_old_logs_removes_only_old_top_level_files(tmp_path):
    # L3 retention policy: old files removed, fresh files and directories kept
    old_file = tmp_path / "old.txt"
    new_file = tmp_path / "new.txt"
    subdir = tmp_path / "error"
    subdir.mkdir()
    old_file.write_text("old", encoding="utf-8")
    new_file.write_text("new", encoding="utf-8")
    old_time = time.time() - 40 * 86400
    os.utime(old_file, (old_time, old_time))

    log_module.cleanup_old_logs(directory=str(tmp_path), days=30)  # type: ignore[attr-defined]

    assert not old_file.exists()
    assert new_file.exists()
    assert subdir.exists()


def test_file_logger_writes_and_tracks_path(tmp_path, monkeypatch):
    target = tmp_path / "test_log.txt"
    monkeypatch.setattr(log_module, "_file_log_path", lambda name: str(target))
    try:
        log_module.set_file_logger("unittest")
        logger.info("written to file")
        assert log_module._log_file == str(target)  # type: ignore[attr-defined]
        # enqueue=True writes on a worker thread: poll briefly
        for _ in range(20):
            if target.exists():
                break
            time.sleep(0.05)
        assert target.exists()
    finally:
        # Restore the default file sink so module state stays consistent
        log_module.set_file_logger()
