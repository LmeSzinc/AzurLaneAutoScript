# Alas 技术栈换新方案（Tech Stack Migration）

> 调研日期：2026-08-14
> 状态：阶段 1（OCR 引擎替换）与阶段 6（uv + ruff）已执行完成，待冒烟测试

## 一、项目现状

| 维度 | 现状 |
|---|---|
| 定位 | 碧蓝航线自动化脚本，7×24 无人值守运行 |
| 规模 | 1847 个 Python 文件、约 18.7 万行，另有 Electron 前端（alas-webapp 独立包） |
| 活跃度 | 持续活跃开发中（2026-08） |
| 运行架构 | `alas.py`（调度核心）→ `module/`（50+ 业务模块）→ `module/device`（设备控制）→ `gui.py`（uvicorn WebUI 入口） |

## 二、现有技术栈盘点（含问题）

### 1. Python 运行时与核心库 —— 被"死依赖"钉死在 2019 年
- Python 3.7（2023-06 已 EOL）
- numpy 1.16.6 / scipy 1.4.1 / pillow 8.3 / opencv 4.5.3：均为 2021 年前版本，无法升级的根因是被 mxnet 钉死

### 2. OCR 引擎 —— 最大的技术债
- cnocr 1.2.2 + mxnet 1.6.0（Apache MXNet 已于 2023-09 移入 Attic、2023-11 GitHub 归档，彻底无人维护）
- 连带死依赖：gluoncv、graphviz、portalocker 等
- 核心资产：`bin/cnocr_models/` 下 5 个自训练 densenet-lite-gru 模型（azur_lane 39 类字符集，验证精度 99.43%；azur_lane_jp、cnocr 6426 类、jp、tw），均为 MXNet 格式
- 已有解耦设计：`module/ocr/ocr.py` 的 `Ocr` 封装类 + `UseOcrServer` 配置项（OCR 可跑独立进程，经 zerorpc 通信），为引擎替换预留了接口

### 3. 进程间通信 —— zerorpc 已多年不维护
- zerorpc 0.6.3（基于 gevent，2019 年后基本停更），用于 OCR server 通信（`module/ocr/rpc.py`，pickle + tcp）
- gevent 21.12 不兼容 Python 3.11，是运行时升级的硬障碍

### 4. Web 层 —— 同步框架 + 2021 年版全家桶
- pywebio 1.6.2（同步阻塞模型）+ starlette 0.14.2 + uvicorn 0.17.6
- 前端：Electron 15 + Vue 3.2.19 + Vite 2.6.2 + TS 4.4（alas-webapp 0.3.7 独立仓库）

### 5. 设备控制层 —— 相对健康
- uiautomator2 2.16.17 + adbutils 0.11.0，外加自研多控制方案（minitouch/MaaTouch/scrcpy/nemu_ipc/hermit/ascreencap/ldopengl/wsa），`module/device/method/` 按方法解耦，结构良好
- 视频流：av 10.0（scrcpy 解码）

### 6. 配置与工程化
- pydantic 1.10.2 + pyyaml，配置经 `config_generated.py` 代码生成
- pip-compile 管理依赖；Windows 一键安装包 / Docker / headless / AidLux(ARM) 多部署形态

## 三、换新方案：分阶段渐进升级（不重写）

核心策略：优先消灭"死依赖"，按依赖链自下而上推进；每阶段可独立合入，18 万行业务代码零改动或微调。

### 阶段 1：替换 OCR 引擎（最高优先级）✅ 执行中
- **采用 onnxruntime 后端**：cnocr 2.x 已官方迁移 PyTorch 架构且重训了模型，无 1.x→2.x 模型转换工具；因此将本地 5 个自训练 mxnet 模型（symbol.json + params + label_cn.txt）经 mxnet ONNX 导出器转换为 ONNX 格式，用 onnxruntime 实现推理
- 权重 100% 保留 → 识别精度与行为逐字一致，无需重训
- `module/ocr/al_ocr.py` 重写为 ONNX 后端，保持公共 API 不变（`ocr` / `ocr_for_single_line` / `ocr_for_single_lines` / `atomic_*` / `set_cand_alphabet`），业务侧 50+ 模块零改动
- 附带收益：移除 mxnet/gluoncv/graphviz/portalocker 死依赖；numpy 解绑可升级
- 同步处理 OCR server 通信（`module/ocr/rpc.py`）：zerorpc/gevent 替换为标准库 socket + pickle，接口不变

### 阶段 2：Python 运行时与基础库升级 ✅ 部分执行（随阶段 1 进行）
- Python 3.7 → 3.11；numpy → 1.26；pillow → 10.x；opencv → 4.10+
- pydantic 1.10 → 2.x 迁移面大，单独成阶段；v1 仍在维护可暂留

### 阶段 3：通信层去 zerorpc（OCR server 部分随阶段 1 完成）
- 其余 zerorpc 用法（如存在）同步清理，统一为 socket/msgpack

### 阶段 4：Web 层现代化
- pywebio 1.6.2 → 最新版（原生 FastAPI 集成）；starlette → FastAPI 0.11x + uvicorn 0.30+
- 前端：Electron 15 → 30+；Vite 2.6 → 5.x；Vue 3.2 → 3.5；TS 4.4 → 5.x

### 阶段 5：设备层与部署
- uiautomator2 2.16 → 3.x；adbutils → 2.x；av → 12+
- pyinstaller 升级；评估 Nuitka；CI workflows 切 Python 3.11

### 阶段 6：工程化 ✅ 执行中
- 依赖管理：pip-compile → uv（pyproject.toml + uv.lock；requirements.txt 经 `uv pip compile` 生成，保持 deploy/install 兼容）
- lint：ruff 替换 flake8

## 四、工作量与风险

| 阶段 | 预估工作量 | 风险等级 | 说明 |
|---|---|---|---|
| 1 OCR 替换 | 2~4 周 | 高 | 权重无损迁移后风险主要来自推理行为差异，需逐字对比验证；接口已解耦，业务零改动 |
| 2 运行时升级 | 1~2 周 | 低 | 紧随阶段 1 |
| 3 去 zerorpc | 1 周 | 低 | 改动集中在 `module/ocr/rpc.py` |
| 4 Web 层升级 | 2~3 周 | 中 | pywebio API 变动 + 前端工具链升级 |
| 5 设备/部署 | 持续 | 中 | u2 3.x 行为差异需真机验证 |
| 6 工程化 | 持续 | 低 | 可随时穿插 |

## 五、关键决策记录

| 决策 | 结论 | 理由 |
|---|---|---|
| OCR 后端选型 | onnxruntime（自研推理封装） | cnocr 2.x 无 1.x 模型转换工具且已重训；ONNX 格式稳定、免 torch 运行时、对 Windows 打包与 ARM 部署友好 |
| 模型转换方式 | 手写 ONNX 构造器（解析 symbol.json 逐节点翻译，GRU 用 Scan 忠实实现 cuDNN 变体公式） | mxnet 1.6 exporter 不支持 RNN 与 -3 维度标记；mxnet gluon GRU（cuDNN 变体）与 ONNX GRU 公式不等价，必须逐步实现 |
| 工具链 | uv + ruff | 已安装 uv 0.11.26；requirements.txt 保留生成流程以兼容 deploy/install |

## 六、执行记录（2026-08-14）

### 已完成
1. **OCR 引擎替换**：5 个自训练模型（azur_lane/azur_lane_jp/cnocr/jp/tw）全部转换为 ONNX（bin/cnocr_models/<name>/<name>.onnx），动态 batch 与宽度；新旧推理逐元素对比 max_diff < 3.1e-5 且 argmax 完全一致（单图与 batch 均验证）
2. `module/ocr/al_ocr.py` 重写为 onnxruntime 后端，公共 API 与推理行为（预处理、置信度过滤、宽度截断、CTC 解码、cand_alphabet）与原实现一致
3. `module/ocr/rpc.py` 通信层 zerorpc/gevent → 标准库 socket + pickle，OCR server 进程模式验证通过
4. 依赖：移除 mxnet/cnocr/gluoncv/graphviz/portalocker/zerorpc/gevent 等死依赖；Python 3.11 + numpy 1.26 + opencv 4.11 + onnxruntime 1.28
5. 工具链：pyproject.toml + uv.lock（uv 0.11），requirements.txt 经 `uv export` 生成；ruff 已配置（E/F/W/B 规则集），改动文件全部通过
6. opencv 4.11 适配：`cv2.copyTo` 3 参形式与 4 元素标量 subtract 已修复

### 冒烟测试（.venv，Python 3.11）
- `dev_tools/ocr_convert/smoke_ocr.py`：AlOcr 单图/批量推理 OK
- `dev_tools/ocr_convert/smoke_rpc.py`：OCR server 进程 + RPC 通信 OK
- `dev_tools/ocr_convert/smoke_business.py`：业务层 Digit/DigitYuv/Ocr 多按钮链路 OK
- `dev_tools/ocr_convert/compare_mxnet_onnx.py`：新旧模型对照（需 .venv-mxnet 环境）

### 遗留
- 全仓 ruff 存量错误 4456 个（旧代码遗留，非本次引入），可用 `ruff check --fix` 渐进清理
- pydantic 仍为 v1（迁移面大，单独成阶段）
- 阶段 4（Web 层）、阶段 5（设备/部署）未开始

## 七、前端现代化执行记录（2026-08-14 第二阶段）

### 已完成
1. **后端 API 化**：`module/webui/api/` FastAPI（status/schema/config/i18n/language/theme/run/stop/instance/update/remote 端点 + /ws 状态与日志推送），lifespan 承载原 pywebio startup（State.init/updater 调度/OCR server/Discord/远程访问）
2. **Tauri 2 外壳**：`webapp-tauri/`（Rust 1.97）：PyShell 拉起 gui.py、stderr 就绪监听、无边框窗口、托盘、单实例、窗口控制命令；cargo 编译通过（13.9MB）
3. **Vue 3 SPA**：Vite 8 + Vue 3.5 + TS 6 + vue-router + Biome；主界面（实例/状态/日志流）、schema 驱动设置表单（8 种控件类型，i18n 中文翻译）、DevTools（更新器/实例管理/远程访问）
4. **样式保留**：pywebio 5 个 bootstrap 主题 + alas 自定义 CSS 移植到前端，主题动态加载
5. **阶段 7 切换**：pywebio/Electron 完全移除（module/webui 旧页面、webapp/、pywebio/alas-webapp 依赖）；gui.py 直接启动 FastAPI + Vue 静态服务
6. **验证**：浏览器实测三页（首页 Connected/实例/日志、设置页任务列表+表单、DevTools commit 信息）全部联通

### 依赖变化
- 新增：fastapi、tauri（Rust）、vue/vite/typescript（前端）
- 移除：pywebio、alas-webapp、tornado、user-agents 等 pywebio 系
- 升级：starlette 0.4x、uvicorn 0.52、websockets 17
