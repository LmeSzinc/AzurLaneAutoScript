"""Scheduler mixin integration tests (P2.3 refactor).

Exercise `Scheduler.run / wait_until / get_next_task / loop` against a fake
app shell: no emulator, no real config instance, no file or network side
effects. This is the offline runtime proof for the loop extracted from
alas.py — the same behavior the webui child process executes.
"""

import threading
import typing as t
from datetime import datetime, timedelta

import pytest

import module.scheduler.scheduler as scheduler_module
from module.base.decorator import cached_property
from module.config.config import AzurLaneConfig, TaskEnd
from module.exception import (
    GameBugError,
    GameNotRunningError,
    GamePageUnknownError,
    GameStuckError,
    RequestHumanTakeover,
    ScriptError,
)
from module.scheduler.scheduler import Scheduler
from module.scheduler.task_record import TaskRecord


class FakeDevice:
    """Minimal device surface; unknown methods are recorded no-ops."""

    def __init__(self):
        self.package = "com.example.game"
        self.config = None
        self.calls: list[str] = []

    def __getattr__(self, item: str) -> t.Callable[..., None]:
        def _noop(*args, **kwargs):
            self.calls.append(item)

        return _noop


class FakeChecker:
    def __init__(self):
        self.recovered = False
        self.available = True
        self.available_calls = 0
        self.check_calls = 0

    def wait_until_available(self):
        self.available_calls += 1

    def is_recovered(self) -> bool:
        return self.recovered

    def check_now(self):
        self.check_calls += 1

    def is_available(self) -> bool:
        return self.available


class FakeTask:
    def __init__(self, command: str, next_run: datetime | None = None):
        self.command = command
        self.next_run = next_run or (datetime.now() - timedelta(seconds=1))


class FakeConfig:
    """AzurLaneConfig-like surface used by the Scheduler methods."""

    def __init__(self, tasks: list[FakeTask], when_task_queue_empty: str = "stay_there"):
        self._tasks = list(tasks)
        self.task: FakeTask | None = None
        self.Optimization_WhenTaskQueueEmpty = when_task_queue_empty
        self.Error_HandleError = False
        self.Error_OnePushConfig = "provider: null"
        self.calls: list[tuple] = []

    def get_next(self) -> FakeTask:
        return self._tasks.pop(0)

    def bind(self, task):
        self.task = task

    def task_call(self, name):
        self.calls.append(("task_call", name))

    def task_delay(self, server_update=False):
        self.calls.append(("task_delay", server_update))

    def start_watching(self):
        self.calls.append(("start_watching",))

    def should_reload(self) -> bool:
        return False

    def publish_scheduler_state(self, current=None):
        self.calls.append(("publish_scheduler_state", current))


class FakeShell(Scheduler):
    """App-shell stand-in: cached config/device/checker like alas.py's."""

    def __init__(
        self,
        tasks: list[FakeTask] | None = None,
        stop_event: threading.Event | None = None,
        handle_error: bool = False,
        task_func: t.Callable[[], None] | None = None,
    ):
        self.config_name = "scheduler_test"
        self.is_first_task = True
        self.task_record = TaskRecord()
        self.stop_event = stop_event
        self.task_func = task_func
        self.saved_error_log = False
        self.config_instance = FakeConfig(tasks or [])
        self.config_instance.Error_HandleError = handle_error

    @cached_property
    def config(self):
        return self.config_instance

    @cached_property
    def device(self):
        return FakeDevice()

    @cached_property
    def checker(self):
        return FakeChecker()

    def _resolve_task(self, command):
        if self.task_func is None:
            return lambda: None
        return self.task_func

    def save_error_log(self):
        self.saved_error_log = True


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch):
    """Neutralize the scheduler's external side effects.

    - handle_notify: no push provider in tests.
    - logger.set_file_logger: keep test runs out of ./log.
    - release_resources: would import OCR/webui layers and walk real assets.
    """
    monkeypatch.setattr(scheduler_module, "handle_notify", lambda *a, **k: None)
    monkeypatch.setattr(scheduler_module.logger, "set_file_logger", lambda *a, **k: None)
    import module.base.resource as resource_module

    monkeypatch.setattr(resource_module, "release_resources", lambda *a, **k: None)


@pytest.fixture
def hoarding_restored():
    """get_next_task resets AzurLaneConfig.is_hoarding_task; restore it."""
    original = AzurLaneConfig.is_hoarding_task
    yield
    AzurLaneConfig.is_hoarding_task = original


# ---------------------------------------------------------------- run()


def test_run_success():
    calls: list[str] = []
    shell = FakeShell(task_func=lambda: calls.append("task"))
    assert shell.run("some_task") is True
    assert calls == ["task"]


def test_run_skip_first_screenshot():
    calls: list[str] = []
    shell = FakeShell(task_func=lambda: calls.append("task"))
    assert shell.run("some_task", skip_first_screenshot=True) is True
    assert calls == ["task"]
    assert "screenshot" not in shell.device.calls


def test_run_task_end_returns_true():
    def task():
        raise TaskEnd

    shell = FakeShell(task_func=task)
    assert shell.run("x") is True


def test_run_game_not_running_requests_restart():
    def task():
        raise GameNotRunningError("game not running")

    shell = FakeShell(task_func=task)
    assert shell.run("x") is False
    assert ("task_call", "Restart") in shell.config.calls
    assert not shell.saved_error_log


def test_run_game_stuck_saves_error_and_restarts():
    def task():
        raise GameStuckError("stuck")

    shell = FakeShell(task_func=task)
    assert shell.run("x") is False
    assert shell.saved_error_log
    assert ("task_call", "Restart") in shell.config.calls


def test_run_game_bug_requests_restart():
    def task():
        raise GameBugError("game bug")

    shell = FakeShell(task_func=task)
    assert shell.run("x") is False
    assert shell.saved_error_log
    assert ("task_call", "Restart") in shell.config.calls


def test_run_game_page_unknown_exits_when_available():
    def task():
        raise GamePageUnknownError

    shell = FakeShell(task_func=task)
    with pytest.raises(SystemExit) as excinfo:
        shell.run("x")
    assert excinfo.value.code == 1
    assert shell.checker.check_calls == 1


def test_run_game_page_unknown_waits_when_unavailable():
    def task():
        raise GamePageUnknownError

    shell = FakeShell(task_func=task)
    shell.checker.available = False
    assert shell.run("x") is False


def test_run_script_error_exits():
    def task():
        raise ScriptError("dev mistake")

    shell = FakeShell(task_func=task)
    with pytest.raises(SystemExit) as excinfo:
        shell.run("x")
    assert excinfo.value.code == 1


def test_run_request_human_takeover_exits():
    def task():
        raise RequestHumanTakeover

    shell = FakeShell(task_func=task)
    with pytest.raises(SystemExit) as excinfo:
        shell.run("x")
    assert excinfo.value.code == 1


def test_run_unexpected_exception_saves_log_and_exits():
    def task():
        raise ValueError("unexpected")

    shell = FakeShell(task_func=task)
    with pytest.raises(SystemExit) as excinfo:
        shell.run("x")
    assert excinfo.value.code == 1
    assert shell.saved_error_log


# ---------------------------------------------------------- wait_until()


def test_wait_until_past_time_returns_true():
    shell = FakeShell()
    assert shell.wait_until(datetime.now() - timedelta(seconds=10)) is True


def test_wait_until_stop_event_exits(monkeypatch):
    event = threading.Event()
    shell = FakeShell(stop_event=event)
    event.set()
    monkeypatch.setattr(scheduler_module.time, "sleep", lambda *a, **k: None)
    with pytest.raises(SystemExit) as excinfo:
        shell.wait_until(datetime.now() + timedelta(hours=1))
    assert excinfo.value.code == 0


def test_wait_until_config_reload_returns_false(monkeypatch):
    shell = FakeShell()
    shell.config.should_reload = lambda: True  # type: ignore[method-assign]
    monkeypatch.setattr(scheduler_module.time, "sleep", lambda *a, **k: None)
    assert shell.wait_until(datetime.now() + timedelta(hours=1)) is False


# ------------------------------------------------------- get_next_task()


def test_get_next_task_returns_due_task(hoarding_restored):
    shell = FakeShell(tasks=[FakeTask("Commission")])
    assert shell.get_next_task() == "Commission"
    assert shell.config.task is not None
    assert shell.config.task.command == "Commission"


def test_get_next_task_alas_command(hoarding_restored):
    shell = FakeShell(tasks=[FakeTask("Alas")])
    assert shell.get_next_task() == "Alas"


def test_get_next_task_resets_hoarding_flag(hoarding_restored):
    AzurLaneConfig.is_hoarding_task = True
    shell = FakeShell(tasks=[FakeTask("Commission")])
    shell.get_next_task()
    assert AzurLaneConfig.is_hoarding_task is False


# ----------------------------------------------------------------- loop()


def test_run_binds_task_context(no_side_effects):
    # L3: every record logged during run() carries extra["task"], so logs
    # can be filtered per task.
    from module.logger import logger

    records = []
    sink_id = logger.add(  # type: ignore[attr-defined] (loguru ships no py.typed)
        lambda m: records.append(m.record), level="TRACE", enqueue=False
    )
    try:
        shell = FakeShell(task_func=lambda: logger.info("task body log"))
        shell.run("Commission")
    finally:
        logger.remove(sink_id)  # type: ignore[attr-defined] (loguru ships no py.typed)
    assert records, "no records captured"
    assert any(r["extra"].get("task") == "Commission" for r in records)


def test_loop_stop_event_breaks_immediately():
    event = threading.Event()
    shell = FakeShell(stop_event=event)
    event.set()
    shell.loop()
    assert shell.checker.available_calls == 0


def test_loop_skips_first_restart_then_runs_and_breaks():
    def fail_task():
        raise GameNotRunningError("not running")

    shell = FakeShell(tasks=[FakeTask("Restart"), FakeTask("Commission")], task_func=fail_task)
    shell.loop()
    assert ("task_delay", True) in shell.config.calls
    assert ("publish_scheduler_state", "Commission") in shell.config.calls
    assert shell.task_record.failure_count("Commission") == 1


def test_loop_too_many_failures_requests_takeover():
    def fail_task():
        raise GameNotRunningError("not running")

    tasks = [FakeTask("Commission") for _ in range(3)]
    shell = FakeShell(tasks=tasks, task_func=fail_task, handle_error=True)
    with pytest.raises(SystemExit) as excinfo:
        shell.loop()
    assert excinfo.value.code == 1
    assert shell.checker.check_calls == 2  # two recoverable failures before exit
    assert shell.task_record.failure_count("Commission") == 3
