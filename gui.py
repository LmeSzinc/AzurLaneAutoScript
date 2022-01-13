import argparse
import os
import socket
import sys
from typing import List, Union

import click
import uvicorn
import uvicorn.config

from module.logger import logger
from module.webui.config import WebuiConfig

# monkey patch Config.bing_socket


def bind(self) -> socket.socket:
    logger = uvicorn.config.logger
    logger_args: List[Union[str, int]]
    if self.uds:  # pragma: py-win32
        path = self.uds
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.bind(path)
            uds_perms = 0o666
            os.chmod(self.uds, uds_perms)
        except OSError as exc:
            logger.error(exc)
            sys.exit(1)

        message = "Uvicorn running on unix socket %s (Press CTRL+C to quit)"
        sock_name_format = "%s"
        color_message = (
            "Uvicorn running on "
            + click.style(sock_name_format, bold=True)
            + " (Press CTRL+C to quit)"
        )
        logger_args = [self.uds]
    elif self.fd:  # pragma: py-win32
        sock = socket.fromfd(self.fd, socket.AF_UNIX, socket.SOCK_STREAM)
        message = "Uvicorn running on socket %s (Press CTRL+C to quit)"
        fd_name_format = "%s"
        color_message = (
            "Uvicorn running on "
            + click.style(fd_name_format, bold=True)
            + " (Press CTRL+C to quit)"
        )
        logger_args = [sock.getsockname()]
    else:
        family = socket.AF_INET
        addr_format = "%s://%s:%d"

        if self.host and ":" in self.host:  # pragma: py-win32
            # It's an IPv6 address.
            family = socket.AF_INET6
            addr_format = "%s://[%s]:%d"

        sock = socket.socket(family=family)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
        except OSError as exc:
            logger.error(exc)
            logger.error(f"Already bind on address ({self.host}, {self.port})")
            sys.exit(1)

        message = f"Uvicorn running on {addr_format} (Press CTRL+C to quit)"
        color_message = (
            "Uvicorn running on "
            + click.style(addr_format, bold=True)
            + " (Press CTRL+C to quit)"
        )
        protocol_name = "https" if self.is_ssl else "http"
        logger_args = [protocol_name, self.host, self.port]
    logger.info(message, *logger_args, extra={"color_message": color_message})
    sock.set_inheritable(True)
    return sock


uvicorn.Config.bind_socket = bind


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
                reload=True, reload_includes=['reloadflag'], reload_excludes=['*.py'])
