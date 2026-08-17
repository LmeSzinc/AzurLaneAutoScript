"""Verify refactored alas.py structure (P1.4)."""

import sys

sys.path.insert(0, ".")

import alas  # noqa: F401
from alas import AzurLaneAutoScript

alas_obj = AzurLaneAutoScript.__new__(AzurLaneAutoScript)
for infra in ["restart", "start", "goto_main", "wait_until", "get_next_task", "loop", "save_error_log"]:
    assert hasattr(alas_obj, infra), f"missing infra: {infra}"
for gone in ["research", "commission", "opsi_explore", "main", "gems_farming"]:
    assert not hasattr(alas_obj, gone), f"legacy method should be gone: {gone}"
# Infra commands exercise the _resolve_task fallback path; they resolve to
# bound methods without instantiating anything.
for cmd in ["goto_main", "restart", "start"]:
    fn = alas_obj._resolve_task(cmd)
    assert callable(fn), f"not callable: {cmd}"
# Registered tasks resolve through the declarative registry. Their entries
# instantiate the task class with a live config/device (this script builds
# the object via __new__ without __init__), so verify the registry mapping
# instead of calling _resolve_task; registry completeness is checked by
# dev_tools/verify_task_registry.py.
from module.tasks.registry import TASK_BY_COMMAND

for cmd in ["research", "opsi_explore", "main"]:
    assert TASK_BY_COMMAND.get(cmd), f"unregistered command: {cmd}"
print("alas.py STRUCTURE VERIFICATION PASSED")
with open("alas.py", encoding="utf-8") as f:
    print(f"alas.py lines: {len(f.readlines())}")
