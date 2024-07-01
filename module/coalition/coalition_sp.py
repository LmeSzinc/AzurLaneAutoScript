from module.coalition.coalition import Coalition
from module.config.config import TaskEnd


class CoalitionSP(Coalition):
    def run(self, *args, **kwargs):
        try:
            super().run(mode='sp', total=1)
        except TaskEnd:
            # Catch task switch
            pass
        if self.run_count > 0:
            self.config.task_delay(server_update=True)
        else:
            self.config.task_stop()
