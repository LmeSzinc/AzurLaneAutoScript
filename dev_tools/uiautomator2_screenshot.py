from module.device.screenshot import Screenshot
from module.config.config import AzurLaneConfig
from datetime import datetime

import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

s = Screenshot(AzurLaneConfig())
i = s._screenshot_uiautomator2()
filename = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
i.save(f'./screenshots/' + filename + ".png")