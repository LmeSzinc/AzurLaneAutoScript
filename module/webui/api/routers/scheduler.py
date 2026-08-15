from fastapi import APIRouter

from module.webui.api.models import SchedulerResponse
from module.webui.process_manager import ProcessManager

router = APIRouter(tags=["scheduler"])


@router.get("/scheduler/{config_name}", response_model=SchedulerResponse)
def scheduler(config_name: str):
    from module.config.config import AzurLaneConfig

    config = AzurLaneConfig(config_name)
    config.load()
    config.get_next_task()
    alive = ProcessManager.get_manager(config_name).alive
    pending = config.pending_task
    if alive and len(pending) >= 1:
        running = pending[:1]
        pending = pending[1:]
    else:
        running = []

    def dump(func):
        return {"command": func.command, "next_run": str(func.next_run)}

    return {
        "alive": alive,
        "running": [dump(f) for f in running],
        "pending": [dump(f) for f in pending],
        "waiting": [dump(f) for f in config.waiting_task],
    }
