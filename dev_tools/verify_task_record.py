"""Verify TaskRecord matches the legacy failure_record semantics (P2.3)."""

import sys

sys.path.insert(0, ".")

from module.scheduler.task_record import TaskRecord


def legacy_behavior(sequence):
    """Replicate old alas.py inline logic: deep_get/deep_set on a dict."""
    record = {}
    out = []
    for task, success in sequence:
        failed = record.get(task, 0)
        failed = 0 if success else failed + 1
        record[task] = failed
        out.append((failed, failed >= 3))
    return out


def new_behavior(sequence):
    tr = TaskRecord()
    out = []
    for task, success in sequence:
        failed = tr.mark_result(task, success=success)
        out.append((failed, tr.too_many_failures(task, limit=3)))
    return out


cases = [
    [("A", False), ("A", False), ("A", False), ("A", True), ("A", False)],
    [("A", True), ("A", True), ("B", False), ("B", False), ("B", False), ("B", True)],
    [("X", False), ("Y", False), ("X", False), ("Y", False), ("X", False)],
    [],
]
for i, seq in enumerate(cases):
    old = legacy_behavior(seq)
    new = new_behavior(seq)
    assert old == new, f"case {i}: legacy={old} new={new}"
    print(f"case {i}: {len(seq)} runs -> equivalent")

# reset semantics
tr = TaskRecord()
tr.mark_result("A", False)
tr.mark_result("A", False)
tr.reset("A")
assert tr.failure_count("A") == 0
tr.mark_result("A", False)
tr.reset()
assert tr.failure_count("A") == 0
print("reset semantics OK")
print("TASK RECORD VERIFICATION PASSED")
