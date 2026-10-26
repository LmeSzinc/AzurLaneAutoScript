import json
from typing import Optional, Dict, Any
from mcp.server.mcpserver import MCPServer
from module.api.service import AlasApiService

# 兼容性导入
mcp = MCPServer("Alas Controller MCP")

# 缓存服务实例
_services: Dict[str, AlasApiService] = {}

def get_service(config_name: str = "alas") -> AlasApiService:
    if config_name not in _services:
        _services[config_name] = AlasApiService(config_name=config_name)
    return _services[config_name]

@mcp.tool()
def get_alas_status(config_name: str = "alas") -> str:
    """
    获取碧蓝航线自动化(Alas)当前的游戏状态与资源数量。
    返回信息包括：
    - 当前状态：空闲 (idle) / 运行中 (running) / 报错 (error) / 已停止 (stopped)
    - 当前正在执行的任务名称（如 Commission, Reward, Main 等）
    - 当前持有的石油数量 (Oil)
    - 当前持有的金币数量 (Coin)
    """
    svc = get_service(config_name)
    info = svc.get_game_status()
    return (
        f"【运行状态】: {info['status_text']}\n"
        f"【当前任务】: {info['current_task'] or '无'}\n"
        f"【后台进程】: {'运行中' if info['is_process_alive'] else '已停止'}\n"
        f"【当前石油】: {info['oil']}\n"
        f"【当前金币】: {info['coin']}\n"
        f"【更新时间】: {info['updated_at']}"
    )

@mcp.tool()
def refresh_game_resources(config_name: str = "alas", force: bool = False) -> str:
    """
    主动进入游戏主页进行截图并 OCR 识别最新的石油和金币数量。
    注意：如果 Alas 当前正在战斗出击中，默认会避免强行打断战斗。如需强制打断，可设 force=True。
    """
    svc = get_service(config_name)
    res = svc.refresh_resources_actively(force=force)
    if res.get("refreshed"):
        return f"【主动刷新成功】最新石油: {res['oil']}, 最新金币: {res['coin']} (时间: {res.get('refreshed_at')})"
    else:
        return f"【未执行主动刷新】原因: {res.get('message')}\n记录数据 - 石油: {res.get('oil')}, 金币: {res.get('coin')}"

@mcp.tool()
def list_all_tasks(config_name: str = "alas") -> str:
    """
    获取 Alas 中所有已配置的任务列表、启用状态与下次计划运行时间。
    返回格式示例：
    - [Commission]: 启用=True, 下次运行=2026-10-27 02:30:00
    - [Reward]: 启用=True, 下次运行=2026-10-27 01:20:00
    """
    svc = get_service(config_name)
    tasks = svc.get_tasks_config()
    lines = []
    for name, item in tasks.items():
        enable = "已启用" if item.get("Enable") else "未启用"
        next_run = item.get("NextRun") or "未设置"
        lines.append(f"- [{name}]: {enable}, 下次计划: {next_run}")
    return "\n".join(lines) if lines else "未获取到任何任务配置。"

@mcp.tool()
def get_task_details(task_name: str, config_name: str = "alas") -> str:
    """
    获取指定任务的详细配置内容（如出击关卡、委托筛选条件、日常领取选项等）。
    :param task_name: 任务名称，如 'Commission', 'Reward', 'Main', 'Event', 'Exercise' 等
    """
    svc = get_service(config_name)
    cfg = svc.get_single_task_config(task_name)
    if not cfg:
        return f"未找到名为 '{task_name}' 的任务配置。"
    return json.dumps(cfg, indent=2, ensure_ascii=False)

@mcp.tool()
def configure_task(task_name: str, enable: Optional[bool] = None, settings_json: Optional[str] = None, config_name: str = "alas") -> str:
    """
    修改指定任务的配置（开启/关闭任务，或更新具体参数）。
    :param task_name: 任务名称，如 'Commission', 'Reward', 'Main' 等
    :param enable: 可选，设置为 True 启用该任务，False 禁用该任务
    :param settings_json: 可选，JSON 格式的键值对参数，如 '{"Scheduler": {"NextRun": "2026-10-27 02:00:00"}}'
    """
    svc = get_service(config_name)
    new_settings = {}
    if enable is not None:
        new_settings.setdefault("Scheduler", {})["Enable"] = enable
    if settings_json:
        try:
            extra = json.loads(settings_json)
            new_settings.update(extra)
        except Exception as e:
            return f"参数 settings_json 格式错误: {e}"

    if not new_settings:
        return "未提供任何需要修改的配置项。"

    success = svc.update_task_config(task_name, new_settings)
    if success:
        return f"成功更新任务 [{task_name}] 的配置: {new_settings}"
    return f"更新任务 [{task_name}] 失败。"

@mcp.tool()
def trigger_task_now(task_name: str, config_name: str = "alas") -> str:
    """
    让指定任务立刻进入就绪状态并优先执行。
    通过将该任务的 NextRun 时间设为当前时刻实现。
    :param task_name: 任务名称，如 'Reward'(领日常), 'Commission'(收发委托), 'Exercise'(演习)
    """
    svc = get_service(config_name)
    success = svc.trigger_task_now(task_name)
    if success:
        return f"任务 [{task_name}] 已调度为立刻执行。"
    return f"调度任务 [{task_name}] 失败。"

@mcp.tool()
def control_alas_process(action: str, config_name: str = "alas") -> str:
    """
    控制 Alas 后台调度进程的启停。
    :param action: 'start' (启动后台调度) 或 'stop' (停止后台调度)
    """
    svc = get_service(config_name)
    if action == "start":
        res = svc.start_process()
        return "Alas 后台进程已成功启动。" if res else "Alas 已经在运行中，无需重复启动。"
    elif action == "stop":
        res = svc.stop_process()
        return "Alas 后台进程已停止。" if res else "Alas 当前未在运行。"
    else:
        return f"不支持的操作: {action}，只支持 'start' 或 'stop'。"

@mcp.tool()
def read_recent_logs(lines: int = 50, config_name: str = "alas") -> str:
    """
    读取 Alas 最新的运行日志，用于分析当前任务进度或排查报错堆栈。
    :param lines: 读取行数，默认 50 行
    """
    svc = get_service(config_name)
    log_lines = svc.get_recent_log_lines(count=lines)
    if not log_lines:
        return "未获取到任何运行日志。"
    return "".join(log_lines)
