"""Registry integrity tests (P1.4 refactor).

Verify the declarative TASK_REGISTRY maps every task name to a resolvable
module/symbol. No task class is instantiated here: constructing one needs a
live config/device (that path is covered by the Scheduler mixin tests with
fakes, and by dev_tools/verify_task_registry.py against the pre-refactor
master snapshot).
"""

import importlib
import inspect
from types import SimpleNamespace
from typing import Any, cast

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
        assert (
            entry.method_kwargs is None
            or isinstance(entry.method_kwargs, dict)
            or callable(entry.method_kwargs)
        ), name


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


def _signature_accepts(sig, keys):
    params = sig.parameters
    return all(key in params for key in keys) or any(p.kind is p.VAR_KEYWORD for p in params.values())


def test_declared_kwargs_match_call_targets():
    """Regression: kwargs must be accepted by the constructor, method_kwargs
    by the method (ModuleBase.__init__ took name/folder/mode and crashed
    every campaign task - see 2026-08-18 alas log)."""
    cfg: Any = SimpleNamespace(Campaign_Name="D1", Campaign_Event="event_20260813_cn", Campaign_Mode="normal")
    for name, entry in TASK_REGISTRY.items():
        if entry.class_name is None:
            continue
        module = importlib.import_module(entry.module)
        cls = getattr(module, entry.class_name)
        if entry.kwargs is not None:
            keys = entry.kwargs(cfg) if callable(entry.kwargs) else entry.kwargs
            assert _signature_accepts(inspect.signature(cls.__init__), keys), (
                f"{name}: constructor does not accept kwargs {keys}"
            )
        if entry.method_kwargs is not None:
            keys = entry.method_kwargs(cfg) if callable(entry.method_kwargs) else entry.method_kwargs
            method = getattr(cls, entry.method)
            assert _signature_accepts(inspect.signature(method), keys), (
                f"{name}: {entry.method} does not accept method kwargs {keys}"
            )
        if entry.task_arg:
            assert _signature_accepts(inspect.signature(cls.__init__), {"task"}), (
                f"{name}: constructor does not accept task="
            )


def test_resolution_passes_method_kwargs_to_method(monkeypatch):
    """End-to-end: ctor gets kwargs, the run call gets method_kwargs."""
    import alas
    import module.tasks.registry as reg

    calls = {}

    class FakeTask:
        def __init__(self, config, device, **kwargs):
            calls["ctor"] = (config, device, kwargs)

        def run(self, **kwargs):
            calls["run"] = kwargs

    entry = TaskEntry(
        module="module.tasks.registry",
        class_name="FakeTask",
        kwargs={"ctor_extra": 1},
        method_kwargs=lambda c: {"name": c.Campaign_Name},
    )
    monkeypatch.setattr(reg, "TASK_REGISTRY", {"Fake": entry})
    monkeypatch.setattr(reg, "TASK_BY_COMMAND", {"fake": "Fake"})
    monkeypatch.setattr(reg, "FakeTask", FakeTask, raising=False)

    az = cast(Any, alas.AzurLaneAutoScript.__new__(alas.AzurLaneAutoScript))
    az.config = SimpleNamespace(Campaign_Name="D1")
    az.device = object()

    fn = az._resolve_task("fake")
    fn()

    assert calls["ctor"][0] is az.config
    assert calls["ctor"][1] is az.device
    assert calls["ctor"][2] == {"ctor_extra": 1}
    assert calls["run"] == {"name": "D1"}
