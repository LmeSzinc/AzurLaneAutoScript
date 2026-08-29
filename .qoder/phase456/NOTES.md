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

## P1(S1-S3)完成记录
- 提交链:S1.1 4a22f8d23 → S1.2 842304a71 → S2.1 9308c927b → S2.2 deacc862d → S3 2dee1af31 → style e10dc162c。
- 全门禁绿:verify_config_generated ZERO DRIFT / verify_task_families OK / bridges ok / pytest 55 / smoke 427(424+3 新模块)。
- 执行方式偏离说明:原计划由 subagent 执行,但本环境 subagent 连续 3 次卡死(无进程活动),改由主代理按同一规格小步执行。
- S3 拆分方式:AST 脚本搬移 + mixin 组合;`event` 方法整体搬移(未做 parse_readme/normalize_readme 拆分,
  与规格偏差已记录:该拆分仅为可测性,行为等价)。
- S2.2 曾因 PowerShell -replace 大小写不敏感误替换局部变量 `events` 与注释,已修复(教训:替换常量引用用逐处 edit,不用全局 replace)。

## P2-P6 完成记录(2026-08-29)
- P2(S4):8d0f3859c 语义快照+校验器 / 6413f5567 四服广播重生成(assets -28,996 行)。运行时零改动。
- P3(S5):5291d1a80 策略表(CV/DD/FLEET_SLOTS)/ 6f860d109 换角色骨架 ROLES。
- P4(S6):4d302cc42 stage_meta.py + 27 个 meta.json + handle_stage_name 表驱动(verify 1982 例全等)。
- P5(S7):42ab4f087 加载器 / f52a91a19 转换器硬化 / 4e4a3d211 格值标记 / 1502819d9 B2 /
  3619529a9+8c7023532 B3 / e1d786b4c 垫片注册 / 7e6383749 B4 终转。
  **最终:1348/1348 地图等价通过,12 跳过(0.9%)**。
- P6(S8):CI equivalence job;S9 终验全绿,报告见 FINAL.md。

## 4A 遗留(12 个 legacy 跳过文件)
- 自定义 Grid 类:t4.py(EventGrid,war_archives_20190321_en/a1 等 4-5 个)
- 历史损坏 import(assets 中不存在的 C2/D3/EVENT_20200312CN_SP3):legacy 下同样 ImportError,行为不变
- actions 字典 sp.py(复杂格名字典,1 个)
- ttl1.py `if __name__ == '__main__':` 调试块(1 个)
可在后续逐个支持;当前全部走 legacy 路径,行为与重构前完全一致。

## 加载器关键设计(供后续维护)
- JSON 优先、legacy 回退;片段无 import,全部名字由 ns 注入。
- legacy 兄弟文件导入已转换图:早期 shim 注册 + _inflight/_loading 守卫解决循环。
- campaign 内引用一律走 _legacy_import(先垫片预载);module.* 引用走 importlib 前缀循环。
- from_data 依赖字段顺序(shape 先于 map_data 等),转换器按源文件顺序保序。

