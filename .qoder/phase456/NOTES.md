# Phase456 执行笔记

## S0 基线(2026-08-22)
- ruff (scoped): exit 0
- pyright (scoped): exit 0
- smoke_import_all: Imported 424/424 modules(执行规格写 423/423,实际为 424/424)
- verify_alas_structure: exit 0
- verify_task_registry: exit 0(该脚本对比 master:alas.py,master 已完成 P1.4 注册表重构,
  "old task methods: 1 / registry extras 68 项" 为预期噪音;mapping completeness 68/68)
- verify_task_record: exit 0
- pytest: 55 passed, 10 warnings

## 环境备忘
- 本机禁用 `uv run`(沙箱下触发全量重装),统一用 `.venv\Scripts\python.exe|ruff.exe|pyright.exe`。
- CI 仍用 uv run。
- 基线存档 .qoder/phase456/baseline/(.qoder 被 gitignore,已 `git add -f`)。
