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
- YAML 优先、legacy 回退;片段无 import,全部名字由 ns 注入。
- 网格文本块(map_data/weight_data/map_data_loop)以**行数组**存 YAML,loader join 还原
  (CampaignMap._parse_text 逐行 strip,语义全等)。
- legacy 兄弟文件导入已转换图:早期 shim 注册 + _inflight/_loading 守卫解决循环。
- campaign 内引用优先取垫片(yaml 存在时),否则 _legacy_import;module.* 引用走 importlib 前缀循环。
- from_data 依赖字段顺序(shape 先于 map_data 等),转换器按源文件顺序保序。

## Followup(2026-08-29)完成记录
- **followup-2**(YAML+行数组):1ea13c46b。1348 地图 json→yaml;迁移时发现并修复 **MAP.name 丢失 bug**
  (转换器从未捕获 `CampaignMap('10-1')` 位置参数,自 4A 起全部地图 name=None;已从基线 git 树恢复,
  后续转换器已修)。
- **followup-1a**(转换器模式扩展):6920f9984。片段允许前置类/顶层函数、globals 字段、__main__ 块丢弃;
  跳过从 12 → 3(仅剩死导入地图,资产确实缺失,legacy 同样 ImportError)。
- **followup-1b**(OCR 入 meta):04879b688。campaign_ocr._get_stage_name 应用 ocr_rewrite 规则;
  2 个事件覆盖删除。
- **followup-1c**(D2 事件入口流):3c8179125。campaign_event 新增 event_entrance_ensure/click/from_main;
  5 个事件 ui_goto_event 收敛(war_archives 滚动搜索保留专用)。
- **followup-1d**(C5 战斗助手):cffbe168f。battle_clear_roadblocks 助手;32 处精确模式 AST 重写(6 简单+26 potential);
  其余混杂模式未动(需真机逐个验证)。
- **merge**:a2b4bce57 合并 qoder/master(上游 5 提交 + 2 游戏更新提交)。冲突仅 4 个 assets.py(取对方→广播重生成)。
  gems_farming/fast_forward 自动合并成功,双方改动均在。island 全面守护:diff 中 0 个 island 路径。
  **注意**:对方 args.json/i18n 中的 raid_20260827 选项与事件名("大人物的预告信")因上游未提供
  campaign/Readme.md 源行,按零漂移原则被 regenerate 归一丢弃;raid 按钮/raid.py/地图模块改动均已保留。
  待上游补 Readme 行 + raid 地图目录后可自然恢复。
- **followup-1e**(声明式战斗模式):battle_patterns.py 模式库(11 种:clear_filter/boss/clear_siren/
  default/clear_mode_filter/protect_siren/mystery/clear_scale/bouncing_filter/roadblocks)。
  转换器+变换器双通道提取;**2472 个方法**从片段移入 YAML `battles` 字段,loader 按模式合成方法;
  片段 15,638 → 6,725 行(-57%),battle_N 定义 2990 → 450。
  等价硬门:快照 `battle_bodies` 记录提取前方法体,verify 逐方法断言"规范源码 == 原方法体"
  (canonical_source 与 match_body 共用同一 AST 构建器,匹配时即断言)。
  未匹配模式的手写方法(~450)保留在片段,含全部真机差异策略。



