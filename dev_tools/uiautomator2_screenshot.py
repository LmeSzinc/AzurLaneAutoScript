from datetime import datetime

import module.config.server as server
from module.config.config import AzurLaneConfig
from module.device.screenshot import Screenshot

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

s = Screenshot(AzurLaneConfig(config_name="alas"))
s.image = s.screenshot_uiautomator2()
filename = datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")
s.image_save(f"./screenshots/{filename}.png")