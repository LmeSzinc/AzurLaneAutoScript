import argparse
import os

import uvicorn

from module.logger import logger
from module.webui.config import WebuiConfig

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Alas web service')
    parser.add_argument('--host', type=str,
                        help='Host to listen. Default to WebuiHost in deploy setting')
    parser.add_argument('-p', '--port', type=int,
                        help='Port to listen. Default to WebuiPort in deploy setting')
    args, _ = parser.parse_known_args()

    webui_config = WebuiConfig()
    host = args.host or webui_config.WebuiHost or '0.0.0.0'
    port = args.port or int(webui_config.WebuiPort) or 22267

    logger.hr('Server config')
    logger.attr('Host', host)
    logger.attr('Port', port)

    try:
        os.remove('./reloadflag')
    except:
        pass

    uvicorn.run('module.webui.app:app', host=host, port=port, factory=True,
                reload=True, reload_includes=['reloadflag', '.*'], reload_excludes=['*.py'])
