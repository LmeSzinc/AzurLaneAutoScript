# AzurLaneAutoScript 代码库调研报告

规模基线：1956 个 Python 文件 / ~22.8 万行（其中 `campaign/` 1423 个、`module/` 436 个）；`ruff check .` 当前全绿（靠 ignore 列表）；CI 实际只 lint 一个子集（`alas.py module/logger.py module/scheduler module/tasks module/core module/base module/device module/map_detection tests dev_tools/verify_alas_structure.py`）。

---

## 1. 太重量级的技术栈选择

### 1.1 三套工具链并存，只为做一个"配置编辑器 + 进程管理器"
- Python 侧：**FastAPI + starlette + uvicorn + websockets + pydantic + anyio** 全套异步 Web 栈（`module/webui/api/`，11 个 router），加上 multiprocessing 重启守护（`gui.py`）。
- Node 侧：**webapp-tauri** 是一整套 Svelte 5 + Vite + TypeScript + UnoCSS + Biome + Vitest + pnpm 前端工程（`webapp-tauri/package.json`），连 `package-lock.json` 和 `pnpm-lock.yaml` 两个锁文件并存。
- Rust 侧：**Tauri 2** 桌面壳（`webapp-tauri/src-tauri/`，Cargo 工程 + `capabilities/gen/icons`），仅用于包一层 WebView 并等待后端 stderr 的 "Application startup complete" 标记。
- 结论：同一功能（本地配置编辑）由 Python Web 服务 + SPA + Rust 壳三套技术栈承载；本地 `src-tauri/target/` 残留 **8 GB** Rust 构建产物（git 已忽略，但开发负担真实存在）。

### 1.2 直接依赖中存在 0 代码引用的死依赖（可安全删除）
以下依赖在 `pyproject.toml`/`requirements.txt` 中声明，但**全仓库（含 campaign、deploy、tests）零处代码引用**：

| 依赖 | 说明 |
|---|---|
| `prettytable` | 0 引用 |
| `aiofiles` | 0 引用 |
| `pycryptodome` | 0 引用（无任何 `Crypto.*` 导入） |
| `wrapt` | 0 引用（仅作为 `deprecated` 的传递依赖） |
| `anyio` | 仅 tests 里的 `@pytest.mark.anyio` 标记（pytest 插件用法），代码本身不直接用 |
| `uvicorn` | 仅 `gui.py` 一处 |

### 1.3 小用量换大体积的依赖
- **scipy**（单体最重的依赖之一）：全项目只有 `signal.find_peaks`（`module/ui/scroll.py`、`handler/login.py`、`commission/commission.py` 等 7 处）和 `optimize.linprog`（`island_handler/production_planner.py`）、`optimize`（`core/geometry.py`、`map_detection/utils.py`）。find_peaks 可用 numpy 实现，linprog 可换小型 LP 库。
- **onnxruntime + opencv + numpy + pillow**：核心图像/OCR 栈，合理，但 onnxruntime 连带 flatbuffers/protobuf 等约 10 个包。
- **uiautomator2 + adbutils 传递依赖树**：apkutils2、pyelftools、lxml、logzero、retry、progress、whichcraft、deprecated、deprecation、cigam、xmltodict 等 ~40 个包，大部分只为 APK 安装解析服务。
- **av (PyAV)**：仅 `module/device/method/scrcpy/core.py` 的 `CodecContext` 一处（scrcpy 视频解码），lazy import，属合理但重。
- 可选功能依赖：`pypresence`（Discord RPC，1 文件）、`onepush`（推送，1 文件）。

### 1.4 其它重量级痕迹
- `bin/` 内置 75 MB 第三方二进制：adb、scrcpy、MaaTouch、DroidCast、hermit、ascreencap —— 同一"截图/控制"职责维护了 4~5 条并行通道。
- `config/deploy.template*.yaml` 8 份部署模板 + Docker + PyInstaller 打包（`deploy/packaging`）+ AidLux 手机云部署（`module/config/env.py` 的 `IS_ON_PHONE_CLOUD`）。
- 迁移痕迹：`module/webui/remote_access.py` 是 PyWebIO 的复制件（文件头自述 "Copy from pywebio.platform.remote_access"），当前 FastAPI 版仍通过 SSH 反向隧道提供远程访问。

---

## 2. 太啰嗦的业务逻辑配置

### 2.1 配置系统是一套"生成器 + 巨型产物"管线
- 源头 `module/config/argument/argument.yaml`（21 KB）+ task/override/default/gui.yaml；生成 `args.json`（**214 KB**）、`config_generated.py`（24 KB）、`config_updater.py`（825 行，内含代码生成、事件表解析、迁移逻辑）。
- 产物冗余：`config/alas.json` 与 `template.json` 各 53 KB；i18n 四语言 `en-US/ja-JP/zh-CN/zh-TW.json` 各 ~100 KB（共 ~420 KB），全部由生成器产出但整体提交。
- `config_updater.py` 里手工维护任务族列表：`MAINS`、`EVENTS`、`RAIDS`、`WAR_ARCHIVES`、`COALITIONS`、`MARITIME_ESCORTS`、`GEMS_FARMINGS`（L32-39），以及从 `campaign/Readme.md` 表格解析事件表（L400-417）——本可从 `campaign/` 目录自动推导。

### 2.2 每张地图一份 ~80 行文件，其中一半是样板
`campaign/` 下 133 个事件目录、1423 个地图文件，每个文件固定结构：4 行 import + `MAP = CampaignMap()` + shape/camera_data + map_data 字符串 + weight_data 字符串 + spawn_data 列表 + 格子 flatten 块 + `class Config`。见 `campaign/event_20260226_cn/a1.py` 与 `campaign/campaign_main/campaign_10_1.py`。
- `weight_data` 大量整块全 `50`（无信息量，如 a1.py 的 8×9 全 50 矩阵）。
- `spawn_data` 高度模板化（`{'battle': n, 'enemy': 1}` 序列）。
- flatten 块纯机械（`dev_tools/Flatten_generator.py` 就是为它写的一次性生成器）。
- 每个 event 文件顶部还重复提交 `# ===== Start of generated config =====` 块（`MAP_SIREN_TEMPLATE` 等 8 个布尔/元组配置，同一模板反复粘贴）。

### 2.3 任务代码里配置分支堆叠
`module/campaign/gems_farming.py`（约 700 行）等任务把业务选项以 `if self.config.X == 'disabled'` 的长链堆在类里（如 `ChangeVanguard`、`CommonCV`、`CommonDD` 各配一套分支 + 对应 docstring），同一选项的"取值 → 校验 → 分支"散落多处。

---

## 3. 太重复、可以复用的资源/逻辑

### 3.1 campaign/ 1423 个同构文件
- 2.2 已述；生成器 `dev_tools/map_extractor.py` 存在，但产物全部提交进仓库，任何地图微调都是 1423 份里的重复 diff（示例：`event_20241219_cn/a1.py` vs `event_20260226_cn/a1.py` 仅 17 行实质差异，其余 30+ 行样板逐字相同）。
- 建议：样板（imports、flatten、Config 生成块、全 50 weight_data）改为基类/数据文件（JSON/YAML），只提交差异化数据。

### 3.2 assets.py 按钮定义每份重复 4 次
`module/campaign/assets.py` 每个 Button 把 `area/color/button/file` 四个 dict 各写 `{'cn':..., 'en':..., 'jp':..., 'tw':...}`，一行 400+ 字符；多数按钮四服坐标/颜色完全相同（如 `CHAPTER_20241219_EX`），只有 file 路径不同，却仍展开 4 份。全部 ~7300 个资产文件、41 行内 15+ 个按钮即此模式。Button 类若支持"同值默认合并"可省 2/3 篇幅。

### 3.3 生成产物与源重复维护
- i18n 4 语言文件（~420 KB）与 `argument.yaml` 一一对应，改一个配置项要动 5 个文件。
- `config/alas.json`/`template.json`（各 53 KB）与 `config_generated.py` 同源于 argument.yaml，三份平行产物。
- `module/config/config_updater.py` 的 `MAINS/EVENTS/RAIDS/...` 硬编码任务族与 `campaign/` 目录内容、`module/tasks/registry.py`（130+ 字符串条目）三方各自维护。

### 3.4 其它可复用点
- `module/base/timer.py`、`module/config/deep.py` 等工具模块 API 过剩（见第 4 节），大量未用函数可先删再谈复用。
- `dev_tools/` 存在多代一次性脚本（`relative_record.py` / `relative_record_gif.py` / `relative_record_gif2.py` 三代并存；`verify_*.py` 7 个校验脚本职责重叠）。
- `login.py` 中 `appear_then_click(XXX, offset=(30,30), interval=5)` 的长链（L61-99）是框架惯用法，可抽成"登录页处理列表"驱动。

---

## 4. 无法到达的死代码（均经全仓库引用计数验证，refs=1 即只有定义处）

### 4.1 结构性不可达（vulture 100% 置信度，人工复核确认）
| 位置 | 内容 |
|---|---|
| `module/daemon/daemon.py:65` | `while 1:` 之后的 `return True`，永不执行 |
| `module/daemon/os_daemon.py:68` | 同上 |
| `module/retire/scanner.py:445-446` | `DockScanner.__init__` 首行 `raise NotImplementedError`，其后代码 + 整个类（`multi_scan`/`scan_one_fleet`/`scan_whole_dock`，约 70 行）不可达 |
| `module/logger.py:253` | `rule()` 的 `style` 参数从未使用（100%） |

### 4.2 有定义无调用的死函数/方法（抽样验证 refs=1）
- `module/base/`：`timer.py` 的 `past_time`/`future_time_range`/`time_range_active`/`add_count`；`base.py` 的 `loop_hierarchy`/`loop_screenshot_hierarchy`/`wait_until_appear_then_click`；`decorator.py` 的 `set_cached_property`/`function_drop`；`resource.py` 的 `resource_show`；`retry.py` 的 `retry_call`；`button.py`/`template.py` 的 `match_binary`（双份定义）、`split_server`、`show_mask`/`save_mask`。
- `module/campaign/run.py:134,146`：`_triggered_app_restart`/`handle_app_restart`（仅互相引用）。
- `module/combat/`：`combat.py:221 ensure_combat_oil_loaded`；`auto_search_combat.py:144 _wait_until_in_map`。
- `module/device/`：`app_control.py` 的 `hierarchy_timer_set`/`xpath_to_button`；`connection.py:571 adb_exec_out`；`connection_attr.py:195 is_nox_family`；`screenshot.py` 的 `screenshot_last_save_time_reset`/`image_show`；`platform/emulator_base.py:293 all_adb_binaries`；`method/scrcpy/control.py` 的 `back_or_turn_screen_on`/`expand_notification_panel`/`expand_settings_panel`/`collapse_panels`/`get_clipboard`/`set_clipboard`/`set_screen_power_mode`/`rotate_device`；`scrcpy/options.py:87 command_v125`；`scrcpy/scrcpy.py:109 click_scrcpy`；`method/pool.py` 的 `JobError`/`start_cmd_soon`/`thread_map`/`thread_starmap`/`thread_funcmap`；`method/*.py` 的 `uninstall_ascreencap`/`uninstall_hermit`/`droidcast_uninstall`/`maatouch_uninstall`/`uninstall_uiautomator2`。
- `module/handler/`：`info_handler.py` 的 `handle_guild_popup_confirm`/`handle_mission_popup_go`/`_story_option_buttons`/`handle_map_after_combat_story`（后两者仅剩注释调用）；`strategy.py:244 strategy_mob_move_cancel`；`login.py` 的 `handle_user_agreement`/`handle_user_login`/`get_cn_xp_hierarchy`/`ensure_no_unfinished_campaign` —— uiautomator2 XPath 登录方案的整套遗留（连带 L1-5 的 `XPath`/`XPathSelector`/`UiObject` 等模块级重导入）。
- `module/map/`：`camera.py:519 convert_local_to_global`；`fleet.py:1102 fleet_checked_reset`；`map_base.py:535 show_connection`（仅注释调用）；`map_grids.py:102 left_join`；`map.py:307 clear_grids_for_faster`。
- `module/map_detection/`：`grid_predictor.py` 的 `predict_mob_move_icon`/`predict_air_strike_icon`；`os_grid.py:277,282 predict_ally`/`predict_akashi`（`is_ally` 调用已注释）；`perspective.py:257 show_array`。
- `module/ocr/`：`al_ocr.py:389,394 atomic_ocr`/`atomic_ocr_for_single_line`；`ocr.py:200,253 DigitCounterYuv`/`DurationYuv`（旧 OCR 工具类）。
- `module/os/`：`camera.py` 的 `grid_is_in_sight`/`_get_map_outside_button`；`globe_camera.py:112 globe_wait_until_stable`；`fleet.py` 的 `get_sea_grids`/`_get_goto_expected`；`map_operation.py` 的 `is_meowfficer_searching`/`get_meowfficer_searching_percentage`；`radar.py:321 predict_akashi`。
- `module/os_handler/`：`port.py:42 port_mission_accept`；`mission.py:22 get_mission_zone`。
- `module/retire/retirement.py:165 retirement_appear`；`module/equipment/` 的 `ship_view_prev`/`_code_exit`；`module/exercise/` 的 `_get_exercise_reset_remain`/`DatedDurationYuv`；`module/commission/project.py` 的 `finish_time` property、`beautify_name`；`module/shop/` 的 `wait_until_medal_appear`、`TEMPLATE_MEDAL_ICON`/`TEMPLATE_MEDAL_ICON_2`、`shop_detect_items`；`module/storage/` 的 `storage_use_box`/`_storage_enter_equipment`；`module/statistics/` 的 `azurstats._upload`（仅注释调用）、`get_items.merge_get_items`。
- `module/config/`：`deep.py` 的 `deep_get_with_error`/`deep_exist`/`deep_pop`/`deep_iter_depth1`/`deep_iter_depth2`/`deep_values`/`deep_iter_diff`/`deep_iter_patch`（8 个公共 API 全无调用者）；`utils.py` 的 `alas_template`/`data_to_path`/`type_to_str`。
- `deploy/atomic.py`：`to_nontmp_file`/`atomic_write_stream`/`atomic_read_text_stream`/`atomic_read_bytes_stream`/`atomic_remove`/`atomic_rmtree`（6 个原子 IO 公共函数全部无调用者）。
- 死资源：`gacha_reward.py` 的 `RECORD_GACHA_OPTION`/`RECORD_GACHA_SINCE`；`shop_event/clerk.py` 的 `pt_image`/`urpt_image`；`os_handler/action_point.py` 的 `OCR_ACTION_POINT_REMAIN_OS`；`shop_event/item.py` 的 `GRID_SHAPE`；`island_handler/technology_scanner.py` 的 `TECHNOLOGY_LENGTH`；`production_planner.py` 的 `DISH_ITEM_TO_SLOT`；`dorm.py` 的 `DORM_CAMERA_SWIPE`/`DORM_CAMERA_RANDOM`。

### 4.3 vulture 报告的误报类别（不要照单全收）
- 任务类经 `module/tasks/registry.py` 字符串注册（`GemsFarming`/`OSCampaignRun`/`CoalitionSP`/`RewardCommission`/`Awaken`/`RaidDaily`/`run_frequent` 等均为活代码）。
- assets 数据包经 star import 消费且使用方多在 `campaign/`（`EVENT_20201126_DETAIL` 等 refs≥5，活代码）；跑 vulture 时务必把 `campaign/` 一并纳入，否则全是假阳性。
- `config_generated.py`/`config_manual.py` 的值经 `self.config.X` 动态访问，vulture 不可见。
- 复核方法：全仓库正则 `\b<name>\b` 计数，refs=1 且无字符串/注册表引用的才是真死代码（本次报告所列均已复核）。

---

## 5. 可解除并正面修复的 ruff ignore 条目

现状：`pyproject.toml` 的 `ignore` 共 33 条；用 `--select` 强制统计后，**每条都还有真实违规**（无一可"直接删除"），但按违规数分两档：

### 5.1 可以"先修后删"的 20 条（合计约 73 处，全部机械可改）
| 规则 | 违规数 | 分布（代表位置） | 修复方式 |
|---|---|---|---|
| E731 | 1 | `dev_tools/ocr_convert/build_onnx.py:263` | lambda → def |
| B008 | 2 | `module/base/base.py:349`（`wait_until_stable` 的 `Timer()` 默认参） | Timer 移入函数体 |
| B005 | 2 | `module/os/map_operation.py:119,132` | 单字符 strip |
| C405 | 1 | `module/device/platform/emulator_windows.py:526` | 列表→集合字面量 |
| C410 | 1 | `module/equipment/equipment_code.py:13` | 去掉外层 `list()` |
| C411 | 1 | `module/base/button.py:427` | 去掉 `list()` |
| C417 | 1 | `module/webui/updater.py:59` | map → 列表推导 |
| SIM116 | 1 | `module/device/platform/emulator_windows.py:111` | if 链 → dict |
| SIM210 | 5 | `scrcpy/control.py:236-237`、`map/fleet.py:324`、`tactical_class.py:196,610` | `bool(...)`（有 unsafe-fix） |
| RUF046 | 6 | `island/utils.py:355`、`map/camera.py:43`、`ocr/al_ocr.py:311`、`os/globe_camera.py:93` 等 | 去掉多余 `int()` |
| C414 | 5 | `base/filter.py:18`、`map/map_base.py:191,262`、`dev_tools/research_optimizer.py:340` 等 | 去掉双重转换 |
| SIM110 | 5 | `equipment_code.py:121`、`handler/enemy_searching.py:49`、`map/map_base.py:793` 等 | 改写为 `any()`/`all()` |
| RUF007 | 4 | `map/map_base.py:684,711,719`、`ocr/al_ocr.py:190` | `itertools.pairwise` |
| SIM109 | 4 | `dev_tools/research_optimizer.py:874`、`research/ui.py:87` | 元组比较 |
| UP028 | 4 | `emulator_windows.py:381,410`、`homography.py:414`、`perspective.py:471` | `yield from` |
| C400 | 2 | `base/filter.py:18`、`dev_tools/research_optimizer.py:340` | 生成器→列表推导 |
| C409 | 2 | `tactical_class.py:194,608` | 元组字面量 |
| RUF015 | 2 | `island/season_task.py:241`、`island_handler/shop.py:180` | `next(iter(...))` |
| E722 | 10 | `deploy/atomic.py`×4、`dev_tools/*`×3、`platform_windows.py`×2、`process_manager.py`×1 | 逐处补 `except Exception`（需人工确认语义） |
| SIM105 | 11 | `deploy/atomic.py`×2、`coalition.py`×2、`daemon/uncensored.py`、`webui/process_manager.py` 等 | `contextlib.suppress` |

做法建议：先跑 `ruff check . --select <rule> --output-format concise` 拿到清单 → 逐条修复（多数可 `--fix`/`--unsafe-fixes` 自动化）→ 从 ignore 删除该条 → 最后把 CI 的 scoped lint 扩到全树。

### 5.2 短期不宜动的 13 条（违规量大或需结构性改造）
F405（2778）、RUF001（506）、SIM102（133）、RUF012（88）、SIM103（85）、UP031（84）、B905（65）、RUF003（56）、E501（52）、SIM108（46）、B904（44）、RUF002（35）、E402（30）、F811（24）。
其中 F405/RUF001 是 star-import 数据包与游戏文本的固有问题（pyproject 注释已说明）；E501/E402 属历史代码风格债；B904 需逐处审查异常链语义。这些可以维持 ignore 并标注"技术债台账"，但**建议把 ignore 列表按"可修"与"结构性"分节注释**，避免后续误判。

### 5.3 其它 lint 卫生
- 全树 205 处 `# noqa`：F403×164（star import 数据包）、F401×36、RUF005×3、SIM112×1、F722×1 —— F401 的 36 处与 F722 等属于"已选中规则但局部豁免"，与 ignore 列表无关，可在清理死代码时顺带消化（例如 `login.py` 删掉 XPath 遗留后其 import 即可清理）。
- `pyproject.toml` 的 `extend-exclude` 注释里明确写着 `config`/`campaign`/`submodule` "Lint them explicitly once cleaned" —— 与 CI 注释（"widen them as the legacy codebase goes green"）是同一份待办。

---

## 附：调研方法
- 依赖使用：`pyproject.toml`/`requirements.txt` 逐项 × 全仓库 import 扫描。
- ruff：`ruff check . --select <rule> --statistics`（CLI `--select` 可越过配置文件 ignore 得到真实违规数）。
- 死代码：vulture 2.16 全树扫描（60% 置信度起）→ 对每个候选做全仓库 `\bname\b` 引用计数 → 排除注册表字符串/star-import/动态属性三类误报 → 对 100% 置信度项人工读码复核。
- 本报告未修改任何代码；临时分析文件已清理。
