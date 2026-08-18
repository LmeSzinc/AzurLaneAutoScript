from contextlib import suppress

from module.coalition.coalition import Coalition
from module.config.config import TaskEnd


class CoalitionSP(Coalition):
    def run(self, *args, **kwargs):
        # Catch task switch
        with suppress(TaskEnd):
            super().run(mode="sp", total=1)
        if self.run_count > 0:
            self.config.task_delay(server_update=True)
        else:
            self.config.task_stop()
