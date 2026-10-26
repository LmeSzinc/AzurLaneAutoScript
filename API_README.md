# Alas REST API & MCP Server 接入指南

本项目基于官方原版 `LmeSzinc/AzurLaneAutoScript`，采用**纯增量架构（Additive Only）**开发，**零侵入、零修改** Alas 官方原有代码，随时可以无冲突同步官方上游最新更新。

---

## 快速启动

在仓库根目录下运行一体化服务：

```bash
# 启动 HTTP 服务（同时提供 REST API 与 MCP SSE 端点）
python run_api.py

# 自定义监听主机与端口（默认 127.0.0.1:8000）
python run_api.py --host 0.0.0.0 --port 8000

# 以 stdio 管道模式运行 MCP Server（供 Claude Desktop / Cursor 本地子进程启动）
python run_api.py --mcp-stdio
```

---

## 一、 REST API 端点概览

服务启动后，可在浏览器访问 Swagger 交互文档：`http://127.0.0.1:8000/docs`

| HTTP 方法 | 路径 | 功能说明 |
| :--- | :--- | :--- |
| `GET` | `/api/status` | 获取当前状态（空闲/运行中/报错/已停止）、当前任务名、石油数量、金币数量 |
| `POST` | `/api/resources/refresh` | 主动刷新石油与金币（进入游戏主页 OCR 顶栏，战斗中自动保护跳过） |
| `GET` | `/api/config/tasks` | 获取全部任务的调度配置（开启状态、下次执行时间） |
| `GET` | `/api/config/task/{task_name}` | 获取指定任务的详细参数与配置（如 Commission, Reward, Main） |
| `POST` | `/api/config/task` | 修改任务设置（如开关任务、修改参数） |
| `POST` | `/api/task/trigger` | 立即触发指定任务执行（将 NextRun 设为当前时间） |
| `POST` | `/api/process/start` | 启动 Alas 调度器后台进程 |
| `POST` | `/api/process/stop` | 停止 Alas 调度器后台进程 |
| `GET` | `/api/logs` | 获取最新的 Alas 运行日志（支持指定行数） |

---

## 二、 MCP (Model Context Protocol) 接入

### 1. 本地 stdio 模式（推荐配合 Claude Desktop / Cursor / Antigravity）

在 MCP 配置文件（如 `claude_desktop_config.json`）中添加：

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

### 2. HTTP / SSE 远程传输模式

服务默认暴露 SSE 端点：`http://127.0.0.1:8000/mcp/sse`，支持跨网络、跨主机的 AI Agent 远程挂接。

### 3. MCP 工具箱一览

- `get_alas_status`: 获取当前游戏运行状态与金币、石油
- `refresh_game_resources`: 主动截图 OCR 刷新游戏资源
- `list_all_tasks`: 列出所有任务的调度时间与开启状态
- `get_task_details`: 查询指定任务的详细配置
- `configure_task`: 修改任务参数或开关任务
- `trigger_task_now`: 立刻插队执行指定任务
- `control_alas_process`: 启停 Alas 后台调度进程
- `read_recent_logs`: 读取最新运行日志分析报错

---

## 三、 同步官方上游更新（永不冲突工作流）

当官方发布新版本或游戏 UI 补丁时，执行：

```bash
# 1. 获取官方最新 commit
git fetch upstream

# 2. 合并官方 master 分支
git merge upstream/master

# 3. 推送到你自己的分支
git push origin feat/api-mcp
```
