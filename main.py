import logging
import platform

import uvicorn

from app import app


def main():
    logging.info('App started')
    logging.debug(f'Machine: {platform.machine()}')
    logging.debug(f'version: {platform.version()}')
    logging.debug(f'platform: {platform.platform()}')
    logging.debug(f'uname: {platform.machine()}')
    logging.debug(f'system: {platform.system()}')

    config_server = uvicorn.Config(app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(config=config_server)
    server.install_signal_handlers = lambda: None
    server.run()


if __name__ == '__main__':
    main()

