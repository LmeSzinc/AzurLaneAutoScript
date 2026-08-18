"""Task execution record: failure counting and execution-rate limiting.

Extracted from the scheduler loop in alas.py (P2.3 refactor). Replaces the
inline `failure_record` dict + deep_get/deep_set bookkeeping with a small
dedicated class, mirroring Alasio's TaskRecord.

Semantics kept identical to the legacy behavior:
- mark_result(task, success): success resets the count, failure increments.
- too_many_failures(task, limit=3): True once a task failed `limit` times
  in a row (the scheduler then requests human takeover).
"""

from __future__ import annotations

from collections import defaultdict


class TaskRecord:
    def __init__(self):
        # Key: str, task name; value: int, consecutive failure count
        self._failure_count: dict[str, int] = defaultdict(int)

    def mark_result(self, task: str, success: bool) -> int:
        """
        Record one task run result and return the current failure count.

        Args:
            task (str): Task name.
            success (bool): Whether the run succeeded.

        Returns:
            int: Current consecutive failure count of the task.
        """
        if success:
            self._failure_count[task] = 0
        else:
            self._failure_count[task] += 1
        return self._failure_count[task]

    def failure_count(self, task: str) -> int:
        """Current consecutive failure count of a task."""
        return self._failure_count[task]

    def too_many_failures(self, task: str, limit: int = 3) -> bool:
        """
        Whether a task has failed `limit` or more times in a row.

        Args:
            task (str): Task name.
            limit (int): Failure threshold, default 3.

        Returns:
            bool:
        """
        return self._failure_count[task] >= limit

    def reset(self, task: str | None = None) -> None:
        """
        Reset failure counts.

        Args:
            task (str | None): Reset one task, or all tasks if None.
        """
        if task is None:
            self._failure_count.clear()
        else:
            self._failure_count.pop(task, None)
