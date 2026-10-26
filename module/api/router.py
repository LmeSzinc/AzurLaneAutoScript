from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from module.api.service import AlasApiService

router = APIRouter(prefix="/api", tags=["Alas Management API"])

# 单例缓存
_services: Dict[str, AlasApiService] = {}

def get_service(config_name: str = "alas") -> AlasApiService:
    if config_name not in _services:
        _services[config_name] = AlasApiService(config_name=config_name)
    return _services[config_name]

# Request Models
class UpdateTaskRequest(BaseModel):
    config_name: str = Field(default="alas", description="Alas 配置文件名称")
    task_name: str = Field(..., description="任务名称，如 Commission, Reward, Main 等")
    settings: Dict[str, Any] = Field(..., description="要更新的设置项")

class TriggerTaskRequest(BaseModel):
    config_name: str = Field(default="alas", description="Alas 配置文件名称")
    task_name: str = Field(..., description="要立即执行的任务名称")

class ProcessControlRequest(BaseModel):
    config_name: str = Field(default="alas", description="Alas 配置文件名称")

# Endpoints
@router.get("/status")
def get_status(config_name: str = Query(default="alas", description="配置文件名")):
    """
    获取 Alas 当前状态与资源信息：
    - 状态：空闲 (idle) / 运行中 (running) / 报错 (error) / 已停止 (stopped)
    - 当前任务名称（严格按 Alas 官方列表）
    - 石油数量
    - 金币数量
    """
    svc = get_service(config_name)
    return svc.get_game_status()

@router.post("/resources/refresh")
def refresh_resources(
    config_name: str = Query(default="alas", description="配置文件名"),
    force: bool = Query(default=False, description="是否强制打断当前任务刷新")
):
    """
    主动刷新石油与金币数量：
    通过 ADB 截图并进行 OCR 识别，更新最新资源存量。
    若 Alas 正在战斗中，默认会安全跳过以防退战扣心情。
    """
    svc = get_service(config_name)
    return svc.refresh_resources_actively(force=force)

@router.get("/config/tasks")
def get_all_tasks_config(config_name: str = Query(default="alas", description="配置文件名")):
    """
    获取所有任务的调度配置（是否启用、下次执行时间及参数）
    """
    svc = get_service(config_name)
    return svc.get_tasks_config()

@router.get("/config/task/{task_name}")
def get_task_config(
    task_name: str,
    config_name: str = Query(default="alas", description="配置文件名")
):
    """
    获取指定任务的详细配置
    """
    svc = get_service(config_name)
    cfg = svc.get_single_task_config(task_name)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    return cfg

@router.post("/config/task")
def update_task_config(req: UpdateTaskRequest):
    """
    修改指定任务的配置（如开启/关闭、修改下次执行时间、修改参数）
    """
    svc = get_service(req.config_name)
    success = svc.update_task_config(req.task_name, req.settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save task configuration")
    return {"success": True, "task": req.task_name}

@router.post("/task/trigger")
def trigger_task(req: TriggerTaskRequest):
    """
    立即触发执行指定任务（将该任务启用并将下次运行时间设置为当前）
    """
    svc = get_service(req.config_name)
    success = svc.trigger_task_now(req.task_name)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to trigger task '{req.task_name}'")
    return {"success": True, "message": f"Task '{req.task_name}' has been scheduled to run immediately"}

@router.post("/process/start")
def start_process(req: ProcessControlRequest):
    """
    启动 Alas 调度主循环进程
    """
    svc = get_service(req.config_name)
    started = svc.start_process()
    return {"started": started, "message": "Process started" if started else "Process already running"}

@router.post("/process/stop")
def stop_process(req: ProcessControlRequest):
    """
    停止 Alas 调度主循环进程
    """
    svc = get_service(req.config_name)
    stopped = svc.stop_process()
    return {"stopped": stopped, "message": "Process stopped" if stopped else "Process not running"}

@router.get("/logs")
def get_logs(
    config_name: str = Query(default="alas", description="配置文件名"),
    lines: int = Query(default=50, description="读取最近日志行数")
):
    """
    获取最新的 Alas 运行日志
    """
    svc = get_service(config_name)
    return {"lines": svc.get_recent_log_lines(count=lines)}
