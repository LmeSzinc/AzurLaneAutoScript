"""Registry integrity tests (P1.4 refactor).

Verify the declarative TASK_REGISTRY maps every task name to a resolvable
module/symbol. No task class is instantiated here: constructing one needs a
live config/device (that path is covered by the Scheduler mixin tests with
fakes, and by dev_tools/verify_task_registry.py against the pre-refactor
master snapshot).
"""

import importlib

import inflection

from module.tasks.registry import TASK_BY_COMMAND, TASK_REGISTRY, TaskEntry


def test_command_map_round_trip():
    """Every PascalCase task name round-trips through its snake_case command."""
    for name in TASK_REGISTRY:
        cmd = inflection.underscore(name)
        assert TASK_BY_COMMAND.get(cmd) == name, f"{name}: cmd={cmd} -> {TASK_BY_COMMAND.get(cmd)!r}"


def test_command_map_has_no_collisions():
    commands = [inflection.underscore(name) for name in TASK_REGISTRY]
    assert len(commands) == len(set(commands)), "duplicate snake_case commands in TASK_REGISTRY"


def test_entry_shape():
    for name, entry in TASK_REGISTRY.items():
        assert isinstance(entry, TaskEntry), name
        assert entry.class_name is not None or entry.function is not None, f"{name}: no class or function"
        assert entry.kwargs is None or isinstance(entry.kwargs, dict) or callable(entry.kwargs), name


def test_all_entry_modules_importable():
    """Every registry module imports; each entry's class/function exists."""
    modules = {entry.module for entry in TASK_REGISTRY.values()}
    for module_name in sorted(modules):
        module = importlib.import_module(module_name)
        for _name, entry in TASK_REGISTRY.items():
            if entry.module != module_name:
                continue
            if entry.class_name is not None:
                assert hasattr(module, entry.class_name), f"{module_name} missing class {entry.class_name}"
            if entry.function is not None:
                assert hasattr(module, entry.function), f"{module_name} missing function {entry.function}"
