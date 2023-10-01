from typing import Optional

from module.base.decorator import cached_property
from module.logger import logger
from tasks.base.main_page import MainPage
from tasks.map.keywords import MapPlane
from tasks.map.keywords.plane import (
    Herta_MasterControlZone,
    Herta_ParlorCar,
    Jarilo_AdministrativeDistrict,
    Luofu_AurumAlley,
    Luofu_ExaltingSanctum
)
from tasks.map.minimap.minimap import Minimap
from tasks.map.route.loader import RouteLoader as RouteLoader_
from tasks.rogue.route.base import RouteBase
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel


def model_from_json(model, file: str):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    data = model.model_validate_json(content)
    return data


class RouteLoader(RouteLoader_, MainPage):
    @cached_property
    def all_minimap(self) -> dict[(str, str), Minimap]:
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
        for plane in MapPlane.instances.values():
            if plane in blacklist:
                continue
            if not plane.world:
                continue
            for floor in plane.floors:
                minimap = Minimap()
                minimap.set_plane(plane=plane, floor=floor)
                maps[f'{plane.name}_{floor}'] = minimap
        return maps

    @cached_property
    def all_route(self) -> list[RogueRouteModel]:
        return model_from_json(RogueRouteListModel, './route/rogue/route.json').root

    def get_minimap(self, route: RogueRouteModel):
        return self.all_minimap[route.plane_floor]

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
                if plane.rogue_domain == 'Transaction' and route.is_DomainOccurrence:
                    # Treat "Transaction" as "Occurrence"
                    pass
                elif plane.rogue_domain == 'Encounter' and route.is_DomainOccurrence:
                    # Treat "Encounter" as "Occurrence"
                    pass
                else:
                    continue
            minimap = self.get_minimap(route)
            minimap.init_position(route.position, show_log=False)
            try:
                minimap.update_position(image)
            except FileNotFoundError:
                continue
            visited.append((route, minimap.position_similarity))

        if len(visited) < 3:
            logger.warning('Too few routes to search from, not enough to make a prediction')
            return

        visited = sorted(visited, key=lambda x: x[1], reverse=True)
        logger.info(f'Best 3 prediction: {[(r.name, s) for r, s in visited[:3]]}')
        if visited[1][1] / visited[0][1] > 0.75:
            logger.warning('Similarity too close, not enough to make a prediction')
            return

        logger.attr('RoutePredict', visited[0][0].name)
        return visited[0][0]

    def position_find_bruteforce(self, image) -> Minimap:
        """
        Fallback method to find from all planes and floors
        """
        logger.warning('position_find_bruteforce, this may take a while')
        for name, minimap in self.all_minimap.items():
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

        Pages:
            in: page_main
            out: page_main, at another domain
        """
        route = self.position_find_known(self.device.image)
        if route is not None:
            super().route_run(route)
        else:
            self.position_find_bruteforce(self.device.image)
            logger.error('New route detected, please record it')


if __name__ == '__main__':
    self = RouteLoader('src', task='Rogue')
    # self.image_file = r''
    # self.position_find_bruteforce(self.device.image)

    self.device.screenshot()
    base = RouteBase(config=self.config, device=self.device, task='Rogue')
    base.clear_blessing()
    self.route_run()
