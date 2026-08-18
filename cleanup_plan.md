# AzurLaneAutoScript 完整清理方案

> 配套调研见 `codebase_audit_report.md`。本方案按"风险从低到高、收益从确定性到结构性"排序，每个 Phase 独立可验证、可回滚。
> 所有改动在 git 分支上进行（CI 已对 `refactor/*` 分支触发，见 `.github/workflows/ci.yml`）。

## 0. 总原则与安全网

**分支**：从干净 `master` 拉 `refactor/cleanup`，按 Phase 提交（每 Phase 至少一个 commit），任一 Phase 出问题 `git reset --hard` 即可整体回滚。

**安全网（每 Phase 结束都跑一遍）**：
```powershell
# 1. lint（CI 同款 scoped + 全树）
.\.venv\Scripts\ruff.exe check alas.py module/logger.py module/scheduler module/tasks module/core module/base module/device module/map_detection tests dev_tools/verify_alas_structure.py
.\.venv\Scripts\ruff.exe check .
# 2. 类型（CI 同款 scoped）
.\.venv\Scripts\pyright.exe module/logger.py module/scheduler module/tasks module/core tests
# 3. 全树 import 冒烟（能抓到删错 import / 删活代码）
.\.venv\Scripts\python.exe dev_tools/smoke_import_all.py
# 4. 结构校验
.\.venv\Scripts\python.exe dev_tools/verify_alas_structure.py
.\.venv\Scripts\python.exe dev_tools/verify_task_registry.py
.\.venv\Scripts\python.exe dev_tools/verify_task_record.py
# 5. 测试
.\.venv\Scripts\python.exe -m pytest tests -ra
```

**死代码删除前通用验证**（任何"删函数/删常量"操作前执行）：
```powershell
# name 换成目标符号，refs=1（仅定义处）才可删；>=2 要看是否字符串/注册表引用
$n='<name>'; (Get-ChildItem -Recurse -Filter *.py -File -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\.venv\\|\\.git\\|node_modules|\\.pnpm-store|__pycache__|webapp-tauri|\\.qoder' } |
  Select-String -Pattern ("\b"+[regex]::Escape($n)+"\b") -List | Measure-Object).Count
```

---

## Phase 1 — 依赖减重：删除 0 引用死依赖

**关闭调研项**：1.2「直接依赖中 0 引用的死依赖」。

**删除**（`pyproject.toml` `[project].dependencies`）：
| 包 | 说明 | 删除后是否仍被安装 |
|---|---|---|
| `prettytable>=2.2` | 0 引用，纯直接依赖 | 否（完全移除） |
| `aiofiles` | 0 引用，纯直接依赖 | 否（完全移除） |
| `pycryptodome>=3.9.9` | 0 处 `Crypto.*` | 是（onepush 传递依赖，仍保留） |
| `wrapt>=1.14` | 0 引用 | 是（`deprecated` 传递依赖） |
| `anyio>=1.3` | 仅 `@pytest.mark.anyio` 标记 | 是（starlette 传递依赖） |

**步骤**：
1. 编辑 `pyproject.toml`，删除上表 5 行（`anyio` 若担心测试，可先留到 Phase 2 后再删）。
2. 重新生成锁与导出（注意：需要联网 `uv lock`；CI 注释已说明当前 `uv.lock` 未 pin pytest，联网后顺带 `uv add --dev pytest`）：
   ```powershell
   uv lock
   uv export --no-hashes --no-dev -o requirements.txt --format requirements-txt
   ```
3. 若无网：手工删除 `pyproject.toml` 5 行 + `requirements.txt` 对应 5 个块，`uv.lock` 标注待联网重生成。
4. 验证：跑安全网第 3/5 步（import 冒烟 + pytest），确认 `pytest tests/test_webui_routing.py`（用到 anyio marker）通过。

**风险**：极低（纯声明删除，代码零引用已验证）。

---

## Phase 2 — ruff ignore 解除：修 20 条规则、删 20 个 ignore 项

**关闭调研项**：5.1。合计约 73 处，全部机械可改。

**执行方式**：一条规则一个小提交；先跑 `--select` 拿清单，改完删 ignore 项，再跑全树确认 0 违规。

### 2A. 可自动修（`--fix --unsafe-fixes`，改完务必 `git diff` 复核）
分批执行，逐批复核后提交：
```powershell
# 纯删冗余（去掉多余 list()/int()/双重转换/生成器）
.\.venv\Scripts\ruff.exe check . --select C405,C410,C411,C417,C414,C400,C409,RUF046,RUF015 --fix --unsafe-fixes
# 语义等价改写（bool()/pairwise/元组比较/yield from/any-all）
.\.venv\Scripts\ruff.exe check . --select SIM210,RUF007,SIM109,UP028,SIM110 --fix --unsafe-fixes
```
每批完成 → 从 `ignore` 删除对应规则 → 全树 `ruff check .` 确认。

### 2B. 手工修（单点，给出精确位置）
| 规则 | 位置 | 改法 |
|---|---|---|
| E731 | `dev_tools/ocr_convert/build_onnx.py:263` | lambda 改 `def` |
| B008 | `module/base/base.py:349`（`wait_until_stable` 的 2 个 `Timer()` 默认参） | 默认参改 `None`，函数体内实例化 |
| B005 | `module/os/map_operation.py:119,132` | 多字符 `.strip(...)` 改单字符/`replace` |
| SIM116 | `module/device/platform/emulator_windows.py:111` | 连续 if 改 dict 查表 |
| E722 | `deploy/atomic.py`×4、`dev_tools/item_statistics.py`×2、`dev_tools/slpp.py`、`platform_windows.py`×2、`webui/process_manager.py` | 逐处 `except Exception`（人工确认语义） |
| SIM105 | `deploy/atomic.py`×2、`coalition.py`×2、`coalition_sp.py`、`daemon/uncensored.py`、`event/campaign_sp.py`、`os_ash/ash.py`、`webui/process_manager.py`、`base/decorator.py`、`dev_tools/map_extractor.py` | `try/except X: pass` → `contextlib.suppress(X)` |

### 2C. 收尾
- `ignore` 列表按"结构性（留）"与"已修（删）"重排，重写注释（F405/RUF001 等保留项标注技术债）。
- 删除对应规则后，把 CI scoped lint 目录列表扩一档（下一档：`module/campaign module/config module/map module/handler module/combat`），确认仍绿后提交。

**风险**：低。E722/SIM105 涉及异常语义，需逐个确认（只改 `except: pass` 且明确捕获类型的场景）。

---

## Phase 3 — 死代码清理（按风险分组，逐组提交）

**关闭调研项**：第 4 节。每组删除前跑"死代码删除前通用验证"。

### 3A. 结构性不可达（零风险，先做）
- `module/daemon/daemon.py:65`、`module/daemon/os_daemon.py:68`：删除 `while 1:` 后不可达的 `return True`（`run()` 改为无 return，或改 `return None`）。
- `module/retire/scanner.py:429-511`：`DockScanner` 整类删除（`__init__` 首行 `raise NotImplementedError`，`multi_scan`/`scan_one_fleet`/`scan_whole_dock` 随之删除）。
- `module/logger.py:253`：`rule()` 删除未使用的 `style` 形参及签名默认值。

### 3B. 纯工具层（`module/base` + `module/config` + `deploy`）
- `module/base/timer.py`：`past_time`、`future_time_range`、`time_range_active`、`add_count`。
- `module/base/base.py`：`loop_hierarchy`、`loop_screenshot_hierarchy`、`wait_until_appear_then_click`。
- `module/base/decorator.py`：`set_cached_property`、`function_drop`。
- `module/base/resource.py`：`resource_show`；`module/base/retry.py`：`retry_call`。
- `module/base/button.py`/`template.py`：`match_binary`（两份）、`split_server`（两份）、`show_mask`、`save_mask`。
- `module/config/deep.py`：`deep_get_with_error`、`deep_exist`、`deep_pop`、`deep_iter_depth1`、`deep_iter_depth2`、`deep_values`、`deep_iter_diff`、`deep_iter_patch`。
- `module/config/utils.py`：`alas_template`、`data_to_path`、`type_to_str`。
- `deploy/atomic.py`：`to_nontmp_file`、`atomic_write_stream`、`atomic_read_text_stream`、`atomic_read_bytes_stream`、`atomic_remove`、`atomic_rmtree`。
- 顺带清 noqa：`dev_tools/annotate_star_imports.py` 相关遗留注释同步检查。

### 3C. 设备层（`module/device`）
- `app_control.py`：`hierarchy_timer_set`、`xpath_to_button`；`connection.py:571 adb_exec_out`；`connection_attr.py:195 is_nox_family`；`screenshot.py`：`screenshot_last_save_time_reset`、`image_show`；`platform/emulator_base.py:293 all_adb_binaries`。
- `method/scrcpy/control.py`：`back_or_turn_screen_on`、`expand_notification_panel`、`expand_settings_panel`、`collapse_panels`、`get_clipboard`、`set_clipboard`、`set_screen_power_mode`、`rotate_device`；`scrcpy/options.py:87 command_v125`；`scrcpy/scrcpy.py:109 click_scrcpy`。
- `method/pool.py`：`JobError`、`start_cmd_soon`、`thread_map`、`thread_starmap`、`thread_funcmap`（`run_on_thread`/`gather_jobs` 先 grep 确认）。
- `method/*.py`：`uninstall_ascreencap`、`uninstall_hermit`、`droidcast_uninstall`、`maatouch_uninstall`、`uninstall_uiautomator2`。

### 3D. 业务处理器层（`module/handler` + `module/campaign` + `module/combat`）
- `handler/login.py`：删除 uiautomator2 XPath 遗留——`handle_user_agreement`、`handle_user_login`、`get_cn_xp_hierarchy`、`ensure_no_unfinished_campaign`、`XPS` 类，以及随之而来的 L1-5 模块级 import（`UiObject`/`XPath`/`XPathSelector`/`XPathElementNotFoundError` 与 `scipy.signal.find_peaks`）。**收益**：去掉一处 scipy 引用 + 一组重依赖 import + 若干 F401。
- `handler/info_handler.py`：`handle_guild_popup_confirm`、`handle_mission_popup_go`、`_story_option_buttons`、`handle_map_after_combat_story`（后两者仅剩注释调用，注释一并清）。
- `handler/strategy.py:244 strategy_mob_move_cancel`（注意 `strategy_mob_move_enter`/`strategy_air_strike_enter` 等是活的，别删）。
- `campaign/run.py:134,146`：`_triggered_app_restart`、`handle_app_restart`。
- `combat/combat.py:221 ensure_combat_oil_loaded`；`combat/auto_search_combat.py:144 _wait_until_in_map`。

### 3E. 地图/检测/OS 层
- `map/camera.py:519 convert_local_to_global`；`map/fleet.py:1102 fleet_checked_reset`；`map/map_base.py:535 show_connection`（清注释调用）；`map/map_grids.py:102 left_join`；`map/map.py:307 clear_grids_for_faster`。
- `map_detection/grid_predictor.py`：`predict_mob_move_icon`、`predict_air_strike_icon`；`map_detection/os_grid.py`：`predict_ally`、`predict_akashi`（含注释掉的 `is_ally`）；`map_detection/perspective.py:257 show_array`。
- `os/camera.py`：`grid_is_in_sight`、`_get_map_outside_button`；`os/globe_camera.py:112 globe_wait_until_stable`；`os/fleet.py`：`get_sea_grids`、`_get_goto_expected`；`os/map_operation.py`：`is_meowfficer_searching`、`get_meowfficer_searching_percentage`；`os/radar.py:321 predict_akashi`。
- `os_handler/port.py:42 port_mission_accept`；`os_handler/mission.py:22 get_mission_zone`。

### 3F. 其余业务 + 死资产
- `retire/retirement.py:165 retirement_appear`；`equipment/equipment.py:74 ship_view_prev`、`equipment_code.py:108 _code_exit`；`exercise/exercise.py:177 _get_exercise_reset_remain`、`exercise.py:61 DatedDurationYuv`；`commission/project.py:521 finish_time`、`528 beautify_name`；`shop/shop_medal.py:87 wait_until_medal_appear` + `TEMPLATE_MEDAL_ICON`/`TEMPLATE_MEDAL_ICON_2`、`shop/base.py:167 shop_detect_items`；`storage/storage.py:501 storage_use_box`、`storage/ui.py:90 _storage_enter_equipment`；`statistics/azurstats.py:106 _upload`（清注释调用）、`statistics/get_items.py:13 merge_get_items`；`ocr/al_ocr.py:389,394 atomic_ocr`/`atomic_ocr_for_single_line`、`ocr/ocr.py:200,253 DigitCounterYuv`/`DurationYuv`。
- 死资产/常量：`gacha/gacha_reward.py` 的 `RECORD_GACHA_OPTION`/`RECORD_GACHA_SINCE`；`shop_event/clerk.py` 的 `pt_image`/`urpt_image`；`os_handler/action_point.py` 的 `OCR_ACTION_POINT_REMAIN_OS`；`shop_event/item.py` 的 `GRID_SHAPE`；`island_handler/technology_scanner.py` 的 `TECHNOLOGY_LENGTH`；`island_handler/production_planner.py` 的 `DISH_ITEM_TO_SLOT`；`dorm/dorm.py` 的 `DORM_CAMERA_SWIPE`/`DORM_CAMERA_RANDOM`。

**删除后验证**：`dev_tools/smoke_import_all.py`（会抓删活代码/坏 import）+ `verify_task_registry.py`（抓误删任务类）+ 全树 ruff + pyright scoped。

**风险**：中。风险点在 3D 的 login.py（删除 import 时确认无其它文件 `from module.handler.login import XPS` 等）、3C 的 pool.py（`run_on_thread` 等需逐名 grep）。每一组单独提交。

---

## Phase 4 — 去重复用（campaign / assets / 产物）

**关闭调研项**：第 3 节。

### 4A. campaign 地图样板数据化（收益最大，改动最大）
目标：1423 个文件收敛为"数据 + 单份样板"。
1. 抽公共骨架到基类：`MAP.flatten()` 块、`# ===== Start/End of generated config =====` 布尔/元组默认值，全部下沉到 `module/map/map_base.py` 或一个 `MapConfig` dataclass。
2. 修改生成器 `dev_tools/map_extractor.py` 输出 YAML/JSON 数据（shape/camera_data/map_data/weight_data/spawn_data/Config 覆盖），而非整份 .py。
3. 提供向后兼容加载器：`CampaignBase` 读取数据文件；`battle_N` 这类每个地图不同的手写逻辑仍需保留在 .py（这是真正的业务逻辑，不数据化）。
4. 全 50 无信息量的 `weight_data` 块省略（缺省即全 50）。
5. 分批迁移（按 `campaign_main` → `campaign_hard` → 各 `event_*`），每批跑 `smoke_import_all.py` + `verify_alas_structure.py`。

### 4B. assets.py 按钮定义去四服冗余
- `Button` 支持"服务器值相等时合并"：`area=((17,446,34,461),)` 单值自动广播四服；只有 en/jp/tw 与 cn 不同才写四元组。
- 改生成器 `dev_tools/button_extract.py`，重新生成各 `module/*/assets.py`；`module/campaign/assets.py` 首行注释已声明"由 button_extract.py 生成，勿手改"。

### 4C. 配置产物单一来源
- i18n 四文件、`config/alas.json`/`template.json`、`args.json` 同源于 `argument.yaml`——把生成命令收拢到一个 `dev_tools/` 脚本并加 `verify_*` 检查（产物与源漂移时报错），避免"改一处动五处"的重复。

### 4D. 任务族列表自动推导
- `config_updater.py` 的 `MAINS/EVENTS/RAIDS/WAR_ARCHIVES/COALITIONS/MARITIME_ESCORTS` 由 `campaign/` 目录名推导，消除手工列表与目录的三方重复。

**风险**：中高（4A 涉及加载方式变更）。4A 建议单独成 PR，其余 4B-4D 可独立小步。

---

## Phase 5 — 业务配置精简

**关闭调研项**：第 2 节。

1. `config_updater.py`（825 行）：拆分——代码生成器（`generate_code`/`args`/`insert_event`）与迁移逻辑分文件；把注释掉的迁移块（如 GemsFarming 的 `ChangeVanguard` 旧键迁移 L580-599）清理。
2. `config/template.json`、`config/alas.json`（各 53KB）不再作为"提交的源"——改为运行时生成/缓存（已在 .gitignore 则移除，未 ignore 则改为示例文件）。
3. 任务代码里的配置分支（`gems_farming.py` 的 `ChangeVanguard`/`CommonCV`/`CommonDD` 长链）抽成"选项 → 策略函数"映射，docstring 与取值校验合一。
4. `module/campaign/gems_farming.py` 等 700 行级任务文件按职责拆分（准备/选择/执行）。

**风险**：中。属纯重构，行为不变，靠 `smoke_import_all.py` + 现有 pytest 兜底。

---

## Phase 6 — 技术栈减重（决策项，逐项单独评估，不打包）

**关闭调研项**：1.1 / 1.3 / 1.4。

| 项 | 现状 | 选项与建议 |
|---|---|---|
| Tauri + Node 壳 | `webapp-tauri`（Svelte5+Tauri2+Node 工具链 + 本地 8GB target） | **A（推荐）**：保留 SPA 源码，仅删 Tauri 壳（`src-tauri/`），用 FastAPI 直接 serve dist + 浏览器打开；**B**：整体保留，清理 `.pnpm-store`/`target`/双锁文件（`package-lock.json` 与 `pnpm-lock.yaml` 二选一） |
| scipy | 仅 `find_peaks` + `linprog` + `optimize` | find_peaks 换 numpy 实现（`scipy` 1 处已可随 login.py 死代码删除减少）；`linprog` 若仅一处可换 `pulp`/小型 LP 或手写单纯形。**建议单独评估，非本清理期必做** |
| uiautomator2 | 仅 `login.py`（待删）+ `uiautomator_2.py` 截图法 | 若 3D 删掉 login.py 的 XPath 用法后 uiautomator2 只剩截图通道，评估是否以 scrcpy/MaaTouch 取代 |
| 截图/控制多通道 | bin/ 内 adb/scrcpy/MaaTouch/DroidCast/hermit/ascreencap 75MB | 保留（核心业务），但 3C 删除 uninstall 死方法后，未使用的通道二进制与代码一并评估下线 |
| pypresence / onepush | 各 1 文件 | 保留（可选功能，懒加载，成本低） |
| inflection / jellyfish | 各 5 文件 | 可内联为 stdlib 助手（`levenshtein` 手写、复数规则简单）；**低优先级** |

**风险**：Tauri 壳裁剪是产品决策，需用户拍板；scipy/uiautomator2 替换是独立课题，建议不在本清理批次内强推。

---

## 验收清单（全部 Phase 完成）
- [ ] `ruff check .` 全绿，且 `ignore` 由 33 条降到 13 条（20 条已删）。
- [ ] 删除依赖 5 个，`requirements.txt`/`uv.lock` 重生成且 import 冒烟通过。
- [ ] vulture 复扫 `module dev_tools deploy tests campaign`，报告中的死代码条目清零（资产/动态访问类除外）。
- [ ] `smoke_import_all.py`、`verify_*`（结构/注册表/任务记录）、pytest 全部通过。
- [ ] CI（`refactor/cleanup` 分支）绿灯；scoped lint 目录较现状扩大至少一档。

## 风险总览
| Phase | 风险 | 回滚 |
|---|---|---|
| 1 依赖 | 极低 | 单 commit |
| 2 ruff | 低 | 逐规则 commit |
| 3 死代码 | 中（login/pool 两组重点复核） | 分组 commit |
| 4 去重 | 中高（4A 单独 PR） | 分阶段 |
| 5 配置 | 中 | 纯重构 |
| 6 减重 | 决策项 | 逐项独立 |

**建议执行顺序**：Phase 0 → 1 → 2 → 3（3A→3B→3C→3D→3E→3F）→ 4B → 4C → 4D → 5 → 4A（最后）→ 6（按用户决策）。
