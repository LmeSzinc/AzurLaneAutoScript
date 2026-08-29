# Phase456 终验报告(FINAL)

日期:2026-08-29
分支:`refactor/phase456`(基线 master @ afcab3d13)

## 全部等价/门禁结果(终验)

| 门禁 | 结果 |
|---|---|
| ruff(scoped,基线范围) | exit 0 |
| pyright(scoped) | 0 errors |
| smoke_import_all | 427/427(基线 424 + 3 新模块:code_generation/event_table/deploy_templates) |
| verify_alas_structure | pass |
| verify_task_registry | exit 0(master 已重构,"extras" 为预期噪音) |
| verify_task_record | PASSED |
| verify_config_generated | CONFIG GENERATED: ZERO DRIFT |
| verify_task_families | FAMILIES: OK(8 族 18 任务) |
| verify_stage_meta | OK(1982 cases;27 meta.json) |
| verify_map_data --all | **1348/1348 maps OK,12 skipped** |
| verify_assets check | OK(1334 buttons / 437 templates) |
| pytest | 55 passed |
| 桥接导入(AlasMaa/AlasFpy) | ok |

## 规模变化

- campaign 树:1423 个 .py / 102,420 行 → **1348 个 .json + 片段 .py(纯逻辑)+ 12 个 legacy 跳过文件**
- assets.py:48 文件 **-28,996 行** 四服冗余(area/button 相同者广播为裸值)
- config_updater.py:825 行 → 4 模块 mixin 组合(225 行门面)
- 任务族:3 处手写列表 → registry family 标签单一来源
- 阶段名特判:~120 行 if 链 → 27 个 meta.json 规则表

## 用户真机自动化测试清单

1. 主线:Main 跑 12-4(或 2-4 快速图),确认地图加载/格子识别正常
2. 困难模式:Hard 任务(hard.py 走新 load_map)
3. 战争档案:WarArchives 任一(map_files 含 .json)
4. 活动图:任一 event(含 vsp/esp 别名事件,确认 stage 名规范化)
5. GemsFarming:一轮换船流程(确认 ChangeFlagship/ChangeVanguard 日志键与换船成功)
6. 配置重生成:`dev_tools/regenerate_config.py` 后 git 干净
7. 回滚演练:`git revert <4A 任一 batch commit>` 恢复旧路径

## 已知遗留(全部在 NOTES.md)

- 12 个跳过文件保持 legacy(自定义 Grid 类 / 历史损坏 import / actions 字典 / __main__ 块),占比 0.9%
- module/campaign/run.py 有 1 处既有 SIM105 lint(非本次改动面)
- OCR 结果重写(event_20240425_cn / event_20260417_cn)仍为事件级覆盖,未并入 meta.json(基类为 staticmethod 无 config 访问,需签名改造)
- 事件入口流(ui_goto_event)的 D2 抽取、battle_clear_roadblocks 助手(C5)未做,见 refined_plan 后续项
