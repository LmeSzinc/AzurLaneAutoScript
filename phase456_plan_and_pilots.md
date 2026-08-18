# Phase 4/5/6 — 详细方案与试点报告

> 前置状态：Phase 1-3 已在 `refactor/cleanup` 完成并全量验证（ruff/全树 + scoped、pyright scoped、import 冒烟 423/423、结构校验 3 项、pytest 55 通过）。净变更：114 文件，+650/−3149 行；死依赖 5 个；ruff ignore 34→14；死代码 ~180 处。
> 本报告所有测量脚本位于临时目录（`%TEMP%\pilot_*.py`），结论已验证可复现。

---

## Phase 4A — campaign 地图数据化（试点已通过）

### 试点：数据驱动重建等价性验证 ✅ PASSED
用 `%TEMP%\pilot_4a.py` 对 `campaign/campaign_main/campaign_10_1.py` 做了等价性试点：

| 指标 | 结果 |
|---|---|
| 原始 .py 行数 | 72 行 |
| JSON 数据表示 | 42 行 / **826 B** |
| 重建后地图语义一致性 | shape/camera_data/map_data/weight_data/spawn_data 全部相等 |
| 格子展平一致性 | 42 个格子（A1..G6）location 与 is_spawn_point 全部一致 |
| 结论 | `PILOT 4A PASSED` |

试点方法：用 `ast` 从生成文件中提取 `MAP.*` 原始字面量（shape 字符串、camera_data 列表、三个数据块），经 `CampaignMap` 公共 API 重建 + `flatten()`，与正常 import 的模块逐格子比对。**注意点**（已写入方案）：`camera_data`/`shape` 是解析型属性（存的是 Grid 对象/tuple，不含原始字符串），所以数据文件必须存**生成器侧的原始字面量**，而不是实例属性。

### 现状量化（campaign_main 72 文件 / 5695 行）
| 行类别 | 行数 | 占比 | 数据化后去向 |
|---|---|---|---|
| map_data 块 | 602 | 11% | JSON 字段 |
| `MAP.*` 赋值 | 395 | 7% | JSON 字段 |
| weight_data 块 | 376 | 7% | JSON 字段（全 50 的默认省略） |
| Config 属性 | 348 | 6% | 覆盖字典（含生成块 `MAP_SIREN_TEMPLATE=[]` 等 8 项默认值下沉基类） |
| import 头 | 251 | 4% | 加载器统一提供 |
| battle_N 方法 | 171 | 3% | **保留**（这是真正的业务逻辑） |
| Config/Campaign 类声明 | 129 | 2% | 基类 + 覆盖字典 |
| flatten 行+格子行 | 64+ | 1% | 加载器统一生成 |
| road_* 定义 | 55 | 1% | JSON `roads` 字段 |

预计：全库 1423 个地图文件收敛为 1423 个 JSON 数据文件 + 每目录一份薄 .py（仅 `battle_N`/`road_*`/`Config` 覆盖，其中多数目录薄到只剩 `class Campaign(CampaignBase)` 空壳或可整体省略）。

### 实施步骤（分 4 批，每批独立可回滚）
1. **基类改造**：`module/map/map_base.py` 增加 `CampaignMap.from_data(dict)` 类方法（试点已验证路径）；`module/campaign/campaign_base.py` 增加数据文件查找逻辑（`campaign/<dir>/<map>.json`，缺失时回退到旧式模块级 `MAP`，保证灰度安全）。
2. **生成器改造**：`dev_tools/map_extractor.py` 增加 `--emit-json` 输出；`dev_tools/Flatten_generator.py` 的产物不再生成。
3. **批量迁移**：先 `campaign_main`（72 文件）→ 全量跑 `smoke_import_all.py` + 新增的等价性自检（把 pilot_4a 的断言逻辑固化为 `dev_tools/verify_map_data.py`，对全部地图做重建比对）→ 再 `campaign_hard`/`campaign_sos`/`war_archives_*` → 最后 `event_*`（133 目录）。
4. **收敛**：旧式 .py 样板删除；`campaign/` 目录从 ruff `extend-exclude` 移出（F401 噪音随样板消失）。

**风险**：中。灰度期新旧双路径并存；等价性自检脚本是硬门槛（每批必须 100% 通过才合并）。`Config` 生成块与 `battle_N` 是仅存的手写面，改动面最小。

---

## Phase 4B — Button 四服字典去冗余（试点已量化）

### 试点测量（`%TEMP%\pilot_4b.py`，括号深度感知 + 双引号兼容）
| 指标 | 数值 |
|---|---|
| assets.py 文件数（含 Button） | 44 |
| Button 总数 | 1344 |
| area 四服完全相同 | 640（48%） |
| color 四服完全相同 | 638（47%） |
| button 四服完全相同 | 640（48%） |
| file 四服完全相同 | 178（13%） |

### 方案
1. `module/base/button.py` 的 `Button.__init__` 支持单值广播：`area=(x0,y0,x1,y1)`（裸 tuple）自动视作四服相同；四服不同才传 `{'cn':..., 'en':..., 'jp':..., 'tw':...}`。向后兼容：dict 形式照旧解析。
2. `dev_tools/button_extract.py`（assets.py 生成器）改为：四服相同输出裸 tuple，不同输出四元组。
3. 重新生成 44 个 `module/**/assets.py`。**注意**：生成器输出风格会与单行/多行两种历史格式统一为一种，diff 巨大但语义不变——通过 `dev_tools/verify_ui_names.py` + 全树冒烟 + 现有 `PreservedAssets` 正则兼容检查兜底（`resource.py` 里 `get_assets_from_file` 用正则扫 assets.py 行，改格式需同步该正则）。
4. 预计消除 ~48% 的 area/color/button 行冗余；assets.py 总量约 -30%。

**风险**：低-中。行为等价（广播是新增表达形式）；主要风险在生成器重跑引入的意外坐标变化，需对生成的 diff 做人工抽检 + `smoke_import_all`。

---

## Phase 4C — 配置产物单一来源

### 现状（实测）
| 产物 | 大小 | 生成方式 |
|---|---|---|
| `module/config/argument/argument.yaml` | 21 KB | 手写源 |
| `module/config/argument/args.json` | 209 KB | `config_updater.py` 生成 |
| `module/config/config_generated.py` | 23 KB | `config_updater.py` 生成 |
| `module/config/i18n/{zh-CN,en-US,ja-JP,zh-TW}.json` | 100/113/94/100 KB | 生成 |
| `config/template.json` / `config/alas.json` | 各 52 KB | 运行期生成 |

### 方案
1. 生成命令收拢为一个入口 `dev_tools/regenerate_config.py`（调 `ConfigGenerator` 全流程），并新增 `dev_tools/verify_config_generated.py`：重跑生成器 → `git diff` 产物必须为空，否则 CI 失败（防止"改源不改产物"漂移）。
2. `config/alas.json`、`config/template.json` 确认是否已 git-ignore；若未 ignore 则加入 ignore 并从工作区移除（它们是用户态产物）。
3. i18n 四文件保持生成提交（供 webui 前端直接消费），但漂移由上面的 verify 兜底。

**风险**：低。纯流程改进，无行为变化。

---

## Phase 4D — 任务族列表自动推导

`module/config/config_updater.py` 中 `MAINS/EVENTS/RAIDS/WAR_ARCHIVES/COALITIONS/MARITIME_ESCORTS/GEMS_FARMINGS` 手写列表（L32-39）与 `campaign/` 目录、`module/tasks/registry.py` 三方重复维护。
方案：`ConfigGenerator` 增加 `@cached_property task_families`，从 `module/tasks/registry.py` 的 `TaskEntry` 条目 + `campaign/` 目录名推导；`insert_event()` 改用推导结果。验证：`verify_task_registry.py` 的 mapping completeness 与 `insert_event` 输出前后一致。

**风险**：低-中。推导逻辑需覆盖 raid/coalition 的"取最新日期"语义（现状用日期比较选最新 raid/coalition——推导时保留该规则）。

---

## Phase 5 — 业务配置精简

### 5.1 `config_updater.py`（现 825 行）拆分
- `code_generation.py`：`argument/task/default/override/gui` 的 cached_property 与 `args`/`generate_code`。
- `event_table.py`：`Event` 类 + `campaign/Readme.md` 表解析 + `insert_event`。
- `migration.py`：历史键迁移（含 L580-599 的注释块——**直接删除**，迁移已过时效）。
- `deploy_templates.py`：`generate_deploy_template`。
- 验证：跑 `verify_config_generated.py`（见 4C）前后产物零 diff。

### 5.2 任务代码配置分支抽策略映射
试点对象 `module/campaign/gems_farming.py`（~700 行）：
- `ChangeVanguard`/`CommonCV`/`CommonDD` 的"取值→校验→分支"三处合一为 `_OPTIONS = {"ChangeVanguard": {("ship",): fn_ship, ("ship_equip",): fn_ship_equip, ...}}` 策略表。
- 注意：此文件有 ~40 行 docstring 依赖（`logger.attr('ChangeFlagship', self.config.GemsFarming_ChangeFlagship)` 等输出是 webui/日志契约），重构时保持 `logger.attr` 键名不变。
- 风险：中（bot 行为路径）；建议逐选项小步提交，每步跑 `smoke_import_all` + 手动 review diff；无单测覆盖，靠代码评审兜底。

### 5.3 生成产物定位
`config/template.json`/`alas.json` 从"仓库源"降级为"运行期缓存"（见 4C），减少 105 KB 提交面。

---

## Phase 6 — 技术栈减重（决策项 + 数据支撑）

### 6.1 webapp-tauri（Svelte + Tauri 壳）—— 建议裁掉 Rust 壳，保留 SPA
实测：
| 部分 | 提交内容 |
|---|---|
| 全部 | 104 文件 / 6.1 MB |
| Rust 壳 `src-tauri/`（除 target/） | 64 文件 / 5.6 MB（icons/gen/capabilities 占大头，`src/*.rs` 仅 lib.rs/main.rs 数百行） |
| 前端 Svelte 源码 | 40 文件 / 517 KB |
| 本地构建残留 `src-tauri/target/` | 8 GB（git 已忽略，纯本地负担） |

Tauri 壳的实际职责（见 `src-tauri/src/lib.rs` + `webapp-tauri/src/main.ts`）：启动系统浏览器/WebView → 等后端 stderr 的 `"Application startup complete"` 标记 → 导航到 FastAPI 服务。**这是一个可以用 ~30 行 Python（`webbrowser.open` + 轮询健康检查）替代的壳。**

方案 A（推荐）：
1. 删除 `webapp-tauri/src-tauri/`（-64 文件/-5.6 MB），`package.json` 移除 `@tauri-apps/api`/`@tauri-apps/cli` 与 tauri scripts。
2. `gui.py` 增加 `--open-browser`：`uvicorn` 起服后 `webbrowser.open("http://127.0.0.1:22267")`（默认开启，可通过 deploy 配置关闭）。
3. `module/webui/api/__init__.py` 的 dist 挂载路径不变（`webapp-tauri/dist` 由 `pnpm build` 产出）；`deploy/packaging/*.spec` 移除 Tauri sidecar 相关条目。
4. 保留 `pnpm` + Vite 构建（产物 dist 供 FastAPI serve）。
验证：`pnpm build` 后启动 `python gui.py --run`，浏览器直达页面；现有 `tests/test_webui_routing.py` 全绿。

方案 B（更激进，待定）：SPA 也去掉，webui 退回 FastAPI 生成表单。**不建议**——现有 SPA 已是 4062 行迁移成果（UnoCSS），放弃成本高于维护成本。

**决策点留给用户**：是否接受桌面体验从"独立窗口"变为"默认浏览器标签页"。A 方案保留全部功能，仅壳层变化。

### 6.2 scipy（Phase 3 后仅剩 8 个引用点）
`commission`（signal）、`core/geometry`（optimize）、`handler/info_handler`（signal）、`island_handler/production_planner`（linprog）、`map/map_fleet_preparation`（signal）、`map_detection/perspective`（signal）、`map_detection/utils`（optimize 转发门面）、`ui/scroll`（signal.find_peaks）。
- 6 处 `signal` 实际均为 `find_peaks`/`savgol_filter` 类一维信号峰值检测 → 可用 numpy 实现替换（~40 行，语义等价需对比测试；scroll.py 的动量检测有游戏内行为影响，属"独立课题"）。
- 1 处 `linprog` → 需小型 LP 库或手写单纯形，**不划算**；若替换则建议保留 scipy 仅此一处。
- 结论：**不纳入本次清理批次**，单独立项（需要真实游戏回归）。

### 6.3 uiautomator2 —— Phase 3 已明显瘦身
- 删除 login.py 的 XPath 遗留后，uiautomator2 的直接使用只剩 `uiautomator_2.py` 截图通道 + `module/device/method/utils.py` 的运行时 shim（`u2.Device`/`u2.init.Initer` monkey-patch + pkg_resources shim）。
- 由于 shim 是运行时注入给第三方库的（删除会静默破坏 u2 内部调用——Phase 3 中 `show_float_window` 即为此类，已恢复），uiautomator2 依赖**保留**。
- 后续（独立课题）：若 scrcpy/MaaTouch 截图通道稳定覆盖全部场景，再评估整体下线 uiautomator2 通道。

### 6.4 其余
- `inflection`（5 处）、`jellyfish`（5 处）可内联 stdlib 实现；收益 ~几十行，建议随 5.2 顺手做，不单独立项。
- `bin/` 75 MB 多通道截图/控制二进制：3C 已删除对应 uninstall 死方法；通道下线属设备层独立课题（需要真机矩阵回归）。

---

## 试点结论汇总
| 试点 | 结果 | 依据 |
|---|---|---|
| 4A 数据驱动地图等价性 | ✅ PASSED | campaign_10_1 重建与原件 42 格子全等；72 行 → 42 行/826B |
| 4B 四服字典冗余 | ✅ 量化完成 | 1344 按钮中 48% 的 area/button 四服完全相同 |
| 4C/4D 产物与任务族 | ✅ 测量完成 | args.json 209KB/i18n ~410KB/模板 ~105KB；三处手写列表可推导 |
| 6 Tauri 壳减重 | ✅ 测量完成 | 壳 5.6MB/64 文件可由 ~30 行 Python 替代；8GB 本地 target 随删除消失 |

**建议排期**：4C（低风险流程）→ 4D → 4B → 5.1/5.2 → 4A（分批，最大收益）→ 6.1（需用户决策）→ 6.2/6.3（独立课题立项）。
