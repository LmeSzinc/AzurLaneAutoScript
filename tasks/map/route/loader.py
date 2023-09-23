import importlib
import os

from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.ui import UI
from tasks.map.route.base import RouteBase


class RouteLoader(UI):
    route: RouteBase

    def route_run(self, route: str):
        """
        Args:
            route: .py module path such as `daily.forgotten_hall.stage1`
                which will load `./route/daily/forgotten_hall/stage1.py`
        """
        folder, name = route.rsplit('.', maxsplit=1)
        path = f'./route/{route.replace(".", "/")}.py'
        try:
            module = importlib.import_module(f'route.{folder}.{name}')
        except ModuleNotFoundError:
            logger.critical(f'Route file not found: {route} ({path})')
            if not os.path.exists(path):
                logger.critical(f'Route file not exists: {path}')
            raise RequestHumanTakeover

        # config = copy.deepcopy(self.config).merge(module.Config())
        config = self.config
        device = self.device
        try:
            self.route = module.Route(config=config, device=device)
            return self.route.route()
        except AttributeError as e:
            logger.critical(e)
            logger.critical(f'Route file {route} ({path}) must define Route.route()')
            raise RequestHumanTakeover
