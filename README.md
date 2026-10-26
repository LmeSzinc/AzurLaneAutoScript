# AzurLaneAutoScript - REST API & MCP Server 扩展版

> 本项目是 [AzurLaneAutoScript (Alas)](https://github.com/LmeSzinc/AzurLaneAutoScript) 的私人定制扩展分支（Fork），由 [ZerowindSE](https://github.com/ZerowindSE) 维护。
> **核心目标**：在**完全不破坏 Alas 原生代码、保持 100% 随时无冲突同步官方上游更新**的前提下，为 Alas 注入现代化的 **RESTful API** 与 **Model Context Protocol (MCP)** 大模型对接能力。

---

## 📖 项目简介与核心用途

原版 Alas 是一个功能强大的 7x24 碧蓝航线自动化脚本，带有基于 PyWebIO 的图形界面，但官方未暴露标准化的程序化控制接口与外部调用能力。

本项目通过增量伴生架构，实现了以下四大核心能力：
1. **游戏运行状态实时透视**：通过状态机实时返回当前状态（`空闲 idle`、`xx任务中 running`、`报错 error`、`已停止 stopped`），任务名严格遵循 Alas 官方标准。
2. **游戏资产（金币/石油）监测与主动刷新**：
   - **被动提取**：零开销实时读取 Alas 日志与 Dashboard 缓存中的石油与金币数值。
   - **主动刷新**：支持一键触发 ADB 截屏并通过底层 OCR 识别主界面顶栏资源（在战斗中自动触发保护跳过，防止意外中断出击）。
3. **任务配置全量读写**：支持通过 API / MCP 动态查询全部 58 个任务的调度时间与配置，并支持在线修改、开关任务及即时生效。
4. **AI Agent / 大模型深度接管 (MCP)**：提供标准 MCP Tools，允许 Claude Code、Cursor、CodeX 等 AI 助手直接“感知港区状态、执行指挥调度、诊断报错日志”。

---

## 🛠️ 新增/修改模块清单与用途说明

为了保证能够永远平滑执行 `git merge upstream/master` 且绝无冲突，本项目严格恪守**“纯增量开发（Zero-Touch Upstream）”**原则：**Alas 官方原有代码 0 修改、0 污染**。

所有新增功能与文件清单如下：

| 文件 / 目录路径 | 类型 | 核心用途与职责说明 |
| :--- | :--- | :--- |
| **`run_api.py`** | 新增入口 | **一体化服务启动器**。统一承载 FastAPI HTTP 服务、Swagger 交互文档、MCP SSE 传输端点，并支持 `--mcp-stdio` 本地命令行管道模式。 |
| **`module/api/service.py`** | 核心服务 | **底层业务适配器**。封装了游戏状态反向推导、OCR 资源主动/被动识别提取、`config/alas.json` 原子读写、任务立即触发及 `ProcessManager` 启停控制。 |
| **`module/api/router.py`** | 接口路由 | **RESTful API 路由定义 (FastAPI)**。对外暴露标准 JSON 端点，包含状态查询、资源刷新、任务配置修改、任务插队触发、进程管控等。 |
| **`module/api/mcp_server.py`** | Agent 协议 | **Model Context Protocol (MCP) 服务端**。为大模型工具调用（Tool Calling）提供 8 个结构化控制工具。 |
| **`AGENTS.md`** | 规范约束 | 针对 **CodeX**、Devin 及通用 Autonomous Agent 的安全红线与开发准则。 |
| **`CLAUDE.md`** | 规范约束 | 针对 **Claude Code** 的专属指令集，**严令禁止擅自发起 Pull Request**。 |
| **`.github/copilot-instructions.md`** | 规范约束 | 针对 **GitHub Copilot / CodeX** 的代码与权限安全指导。 |
| **`.cursorrules`** | 规范约束 | 针对 **Cursor IDE** 的开发行为规范文件。 |
| **`.ssh/`** | 密钥管理 | 本地专用的 GitHub 交互 SSH Key，已配置本地 gitignore，私钥绝不入库。 |
| **`SSH_SETUP.md`** | 说明文档 | 本地 SSH Key 配置与远程仓库推送操作手册。 |
| **`API_README.md`** | 说明文档 | REST API 与 MCP 快速参考卡片。 |

---

## 🚀 快速启动指南

### 1. 启动一体化服务 (REST API + MCP SSE)
在仓库根目录直接运行：
```bash
# 默认启动在 127.0.0.1:8000
python run_api.py

# 自定义监听地址与端口
python run_api.py --host 0.0.0.0 --port 8000
```
启动后终端将输出访问链接：
* **Swagger 交互文档**：`http://127.0.0.1:8000/docs`
* **状态与资源接口**：`http://127.0.0.1:8000/api/status`
* **MCP SSE 传输端点**：`http://127.0.0.1:8000/mcp/sse`

### 2. 本地接入 Claude Desktop / Cursor / Antigravity (stdio 模式)
在你的 MCP 配置文件（例如 `claude_desktop_config.json`）中添加：
```json
{
  "mcpServers": {
    "alas_controller": {
      "command": "python",
      "args": [
        "d:\\Agent\\ALAS_API_MCP\\run_api.py",
        "--mcp-stdio"
      ]
    }
  }
}
```

---

## 📡 REST API 端点手册

| 方法 | 路径 | 描述 | 请求参数 / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/status` | 查询当前运行状态、当前任务名、石油数量、金币数量 | `config_name` (可选，默认 alas) |
| `POST` | `/api/resources/refresh` | 主动进入游戏主页 OCR 刷新石油与金币（遇战斗安全跳过） | `force` (bool，是否强行中断战斗) |
| `GET` | `/api/config/tasks` | 获取所有任务的调度配置（启用状态、下次运行时间） | `config_name` (可选) |
| `GET` | `/api/config/task/{task_name}` | 获取单个指定任务的完整详细配置 | `task_name` (如 Commission, Reward, Main) |
| `POST` | `/api/config/task` | 在线修改任务设置（开关任务、改参数等） | `{"task_name": "...", "settings": {...}}` |
| `POST` | `/api/task/trigger` | 立即触发指定任务执行（设为立即到期并开启） | `{"task_name": "..."}` |
| `POST` | `/api/process/start` | 启动 Alas 调度器后台进程 | `{"config_name": "alas"}` |
| `POST` | `/api/process/stop` | 停止 Alas 调度器后台进程 | `{"config_name": "alas"}` |
| `GET` | `/api/logs` | 读取最新的 Alas 运行控制台日志 | `lines` (读取行数，默认 50) |

---

## 🤖 MCP 工具箱 (Tools) 一览

当接入大模型后，AI Agent 可以直接理解并调用以下工具：

1. `get_alas_status`: 获取当前游戏运行状态（空闲/任务中/报错）、当前任务、金币与石油存量。
2. `refresh_game_resources`: 实时截图并通过 OCR 识别更新金币与石油。
3. `list_all_tasks`: 列出 Alas 中全部 58 个任务的启用情况与下次计划执行时间。
4. `get_task_details`: 查询指定任务的具体运行参数。
5. `configure_task`: 动态开启/关闭指定任务，或修改参数。
6. `trigger_task_now`: 立即将某个任务（如领日常、收委托）插队至队列第一位执行。
7. `control_alas_process`: 启停 Alas 后台调度进程。
8. `read_recent_logs`: 提取最新运行日志，专用于 AI 自动诊断报错与排查问题。

---

## 🚨 安全准则与上游同步工作流

### ⚠️ 绝对红线 (CRITICAL SAFETY RULES)
1. **严禁发起任何 Pull Request (PR)**：本项目为独立私有 Fork，**严禁通过 `gh pr create` 或 API 向官方上游 `LmeSzinc/AzurLaneAutoScript` 发起合并请求**！
2. **严禁向 upstream 推送**：本地配置已将 `upstream` 的 push URL 熔断为 `FORBIDDEN_DO_NOT_PUSH`，并部署了 `.git/hooks/pre-push` 物理拦截。所有推送只能发往 `origin` (`ZerowindSE`)。

### 🔄 同步官方更新的保姆级工作流
当原作者发布新版本或修复游戏 UI 时，在本地执行以下命令即可一键无冲突合并：
```bash
# 1. 抓取官方最新改动
git fetch upstream

# 2. 合并官方 master 分支到你的特性分支 (由于增量代码完全隔离，自动平滑合并)
git merge upstream/master

# 3. 将合并后的最新代码推送到你的 Fork 仓库
git push origin feat/api-mcp
```

---

## 鸣谢与原项目引用
- 原版 AzurLaneAutoScript 仓库：[LmeSzinc/AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript)
- 感谢原作者 **@LmeSzinc** 及其社区贡献者构建的强大自动化生态。
