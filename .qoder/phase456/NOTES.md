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

## S1 历史陈旧产物刷新(S1.2 commit)
首次运行 regenerate_config 暴露的历史漂移(4C 零漂移门的首次清扫):
- config/deploy.template*.yaml ×8:源 deploy/utils.py DEPLOY_TEMPLATE 文案已更新,产物未重生成。
- module/config/i18n/*.json ×4:gui.yaml 已删除的 webui updater 旧键残留在产物中
  (Modified/CurrentVersion/Repo/Refresh/Install/Installing/NoReleases/InstallHint),重生成后移除,
  与近期 webui updater 重写提交一致。
- args.json/menu.json/config_generated.py/campaign/Readme.md 无漂移。
