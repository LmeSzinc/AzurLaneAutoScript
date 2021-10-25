from module.base.base import ModuleBase


class DaemonBase(ModuleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device.disable_stuck_detection()
