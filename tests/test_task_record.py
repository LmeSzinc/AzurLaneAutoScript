"""Unit tests for module.scheduler.task_record.TaskRecord (P2.3 refactor).

Mirrors the semantics verified by dev_tools/verify_task_record.py.
"""

from module.scheduler.task_record import TaskRecord


def test_failure_counting_resets_on_success():
    record = TaskRecord()
    assert record.mark_result("task", success=False) == 1
    assert record.mark_result("task", success=False) == 2
    assert record.mark_result("task", success=True) == 0
    assert record.failure_count("task") == 0


def test_too_many_failures_threshold():
    record = TaskRecord()
    record.mark_result("a", success=False)
    record.mark_result("a", success=False)
    assert not record.too_many_failures("a", limit=3)
    record.mark_result("a", success=False)
    assert record.too_many_failures("a", limit=3)
    # Tasks are counted independently
    assert not record.too_many_failures("b", limit=3)
    record.mark_result("a", success=True)
    assert not record.too_many_failures("a", limit=3)


def test_reset_single_and_all():
    record = TaskRecord()
    record.mark_result("a", success=False)
    record.mark_result("b", success=False)
    record.reset("a")
    assert record.failure_count("a") == 0
    assert record.failure_count("b") == 1
    record.reset()
    assert record.failure_count("b") == 0


def test_unknown_task_failure_count():
    record = TaskRecord()
    # defaultdict semantics: unknown task starts at 0
    assert record.failure_count("never_seen") == 0
