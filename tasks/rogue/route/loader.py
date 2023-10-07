from typing import Optional

import numpy as np

from module.base.decorator import cached_property
from module.logger import logger
from tasks.base.main_page import MainPage
from tasks.base.page import page_rogue
from tasks.map.keywords import MapPlane
from tasks.map.keywords.plane import (
    Herta_MasterControlZone,
    Herta_ParlorCar,
    Jarilo_AdministrativeDistrict,
    Luofu_AurumAlley,
    Luofu_ExaltingSanctum
)
from tasks.map.minimap.minimap import Minimap
from tasks.map.resource.resource import SPECIAL_PLANES
from tasks.map.route.loader import RouteLoader as RouteLoader_
from tasks.rogue.route.base import RouteBase
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel


def model_from_json(model, file: str):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    data = model.model_validate_json(content)
    return data


class MinimapWrapper:
    @cached_property
    def all_minimap(self) -> dict[str, Minimap]:
        """
        Returns:
            dict: Key: {world}_{plane}_{floor}, e.g. Jarilo_SilvermaneGuardRestrictedZone_F1
                Value: Minimap object
        """
        # No enemy spawn at the followings
        blacklist = [
            Herta_ParlorCar,
            Herta_MasterControlZone,
            Jarilo_AdministrativeDistrict,
            Luofu_ExaltingSanctum,
            Luofu_AurumAlley,
        ]
        maps = {}

        for plane, floor in SPECIAL_PLANES:
            minimap = Minimap()
            minimap.set_plane(plane=plane, floor=floor)
            maps[f'{plane}_{floor}'] = minimap

        for plane in MapPlane.instances.values():
            if plane in blacklist:
                continue
            if not plane.world:
                continue
            for floor in plane.floors:
                minimap = Minimap()
                minimap.set_plane(plane=plane, floor=floor)
                maps[f'{plane.name}_{floor}'] = minimap

        logger.attr('MinimapLoaded', len(maps))
        return maps

    @cached_property
    def all_route(self) -> list[RogueRouteModel]:
        routes = model_from_json(RogueRouteListModel, './route/rogue/route.json').root
        logger.attr('RouteLoaded', len(routes))
        return routes

    def get_minimap(self, route: RogueRouteModel):
        return self.all_minimap[route.plane_floor]


class RouteLoader(MinimapWrapper, RouteLoader_, MainPage):
    def position_find_known(self, image) -> Optional[RogueRouteModel]:
        """
        Try to find from known route spawn point
        """
        logger.info('position_find_known')
        plane = self.get_plane()
        if plane is None:
            logger.warning('Unknown rogue domain')
            return

        visited = []
        for route in self.all_route:
            if plane.rogue_domain and plane.rogue_domain != route.domain:
                if plane.rogue_domain in ['Encounter', 'Transaction'] and route.is_DomainOccurrence:
                    # Treat as "Occurrence"
                    pass
                elif plane.rogue_domain in ['Boss'] and route.is_DomainElite:
                    # Treat as "Elite"
                    pass
                else:
                    continue
            minimap = self.get_minimap(route)
            minimap.init_position(route.position, show_log=False)
            try:
                minimap.update_position(image)
            except FileNotFoundError as e:
                logger.warning(e)
                continue
            visited.append((route, minimap.position_similarity, minimap.position))

        if len(visited) < 3:
            logger.warning('Too few routes to search from, not enough to make a prediction')
            return

        visited = sorted(visited, key=lambda x: x[1], reverse=True)
        logger.info(f'Best 3 prediction: {[(r.name, s, p) for r, s, p in visited[:3]]}')
        nearby = [
            (r, s, p) for r, s, p in visited if np.linalg.norm(np.subtract(r.position, p)) < 5
        ]
        logger.info(f'Best 3 prediction: {[(r.name, s, p) for r, s, p in nearby[:3]]}')
        if len(nearby) == 1:
            if nearby[0][1] > 0.05:
                logger.attr('RoutePredict', nearby[0][0].name)
                return nearby[0][0]
        elif len(nearby) >= 2:
            if nearby[0][1] / nearby[1][1] > 0.75:
                logger.attr('RoutePredict', nearby[0][0].name)
                return nearby[0][0]

        # logger.info(f'Best 3 prediction: {[(r.name, s, p) for r, s, p in visited[:3]]}')
        # if visited[0][1] / visited[1][1] > 0.75:
        #     logger.attr('RoutePredict', visited[0][0].name)
        #     return visited[0][0]

        logger.warning('Similarity too close, not enough to make a prediction')
        return None

    def position_find_bruteforce(self, image) -> Minimap:
        """
        Fallback method to find from all planes and floors
        """
        logger.warning('position_find_bruteforce, this may take a while')
        for name, minimap in self.all_minimap.items():
            if minimap.is_special_plane:
                continue

            minimap.init_position((0, 0), show_log=False)
            try:
                minimap.update_position(image)
            except FileNotFoundError:
                pass

        def get_name(minimap_: Minimap) -> str:
            return f'{minimap_.plane.name}_{minimap_.floor}_X{int(minimap_.position[0])}Y{int(minimap_.position[1])}'

        visited = sorted(self.all_minimap.values(), key=lambda x: x.position_similarity, reverse=True)
        logger.info(f'Best 5 prediction: {[(get_name(m), m.position_similarity) for m in visited[:5]]}')
        if visited[1].position_similarity / visited[0].position_similarity > 0.75:
            logger.warning('Similarity too close, prediction may goes wrong')

        logger.attr('RoutePredict', get_name(visited[0]))
        return visited[0]

    def route_run(self, route=None):
        """
        Run a rogue domain

        Returns:
            bool: True if success, False if route unknown

        Pages:
            in: page_main
            out: page_main, at another domain
                or page_rogue if rogue cleared
        """
        route = self.position_find_known(self.device.image)
        if route is not None:
            super().route_run(route)
            return True
        else:
            self.position_find_bruteforce(self.device.image)
            logger.error('New route detected, please record it')
            return False

    def rogue_run(self, skip_first_screenshot=True):
        """
        Do a complete rogue run, no error handle yet.

        Pages:
            in: page_rogue, LAUNCH_SIMULATED_UNIVERSE
            out: page_rogue, world selecting page
        """
        base = RouteBase(config=self.config, device=self.device, task=self.config.task.command)
        count = 1
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            logger.hr(f'Route run: {count}', level=1)
            base.clear_blessing()
            success = self.route_run()
            if not success:
                # self.device.image_save()
                continue

            # End
            if self.ui_page_appear(page_rogue):
                break

            count += 1


if __name__ == '__main__':
    self = RouteLoader('src', task='Rogue')
    # self.image_file = r''
    # self.device.screenshot()
    # self.position_find_bruteforce(self.device.image)

    self.device.screenshot()
    self.rogue_run()
