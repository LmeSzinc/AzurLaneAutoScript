"""Verify P1.4 registry completeness against the pre-refactor alas.py (git HEAD)."""

import ast
import subprocess
import sys

sys.path.insert(0, ".")

import inflection

from module.tasks.registry import TASK_BY_COMMAND, TASK_REGISTRY

# 1) Mapping completeness: every task name's underscore form resolves back
mismatch = []
for name in TASK_REGISTRY:
    cmd = inflection.underscore(name)
    back = TASK_BY_COMMAND.get(cmd)
    if back != name:
        mismatch.append(f"{name}: cmd={cmd} -> {back}")
print(f"mapping completeness: {len(TASK_REGISTRY) - len(mismatch)}/{len(TASK_REGISTRY)}")
for m in mismatch:
    print(" ", m)

# 2) Registry covers every old task method (except infra)
old = subprocess.run(["git", "show", "HEAD:alas.py"], capture_output=True, text=True, check=True).stdout
tree = ast.parse(old)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
old_methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
infra = {
    "__init__",
    "config",
    "device",
    "checker",
    "run",
    "save_error_log",
    "restart",
    "start",
    "goto_main",
    "wait_until",
    "get_next_task",
    "loop",
}
old_tasks = old_methods - infra
reg_commands = set(TASK_BY_COMMAND)
missing = old_tasks - reg_commands
extra = reg_commands - old_tasks
print(f"old task methods: {len(old_tasks)}, registry commands: {len(reg_commands)}")
print(f"old methods NOT in registry: {sorted(missing) if missing else 'NONE'}")
print(f"registry extras (should be none): {sorted(extra) if extra else 'NONE'}")
