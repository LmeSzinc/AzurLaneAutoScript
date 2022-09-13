from pywebio.io_ctrl import Output

import module.config.server as server


class ManualConfig:
    @property
    def SERVER(self):
        return server.server

    SCHEDULER_PRIORITY = """
    MaaStartup
    > MaaRecruit > MaaInfrast
    > MaaVisit > MaaMall > MaaAward
    > MaaAnnihilation > MaaMaterial
    > MaaFight > MaaRoguelike
    """

    """
    module.device
    """
    DEVICE_OVER_HTTP = False
    FORWARD_PORT_RANGE = (20000, 21000)
    REVERSE_SERVER_PORT = 7903
    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'
    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'
    HERMIT_FILEPATH_LOCAL = './bin/hermit/hermit.apk'


class OutputConfig(Output, ManualConfig):
    def __init__(self, spec, on_embed=None):
        super().__init__(spec, on_embed)
