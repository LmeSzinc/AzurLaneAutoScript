import os
import re
from typing import Iterator

import numpy as np
from tqdm import tqdm

from module.base.code_generator import CodeGenerator, MarkdownGenerator
from module.base.decorator import cached_property
from module.base.utils import SelectedGrids, load_image
from module.config.utils import iter_folder
from tasks.map.route.model import RouteModel
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel, RogueWaypointListModel, RogueWaypointModel


class RouteExtract:
    def __init__(self, folder):
        self.folder = folder

    def iter_files(self) -> Iterator[str]:
        for path, folders, files in os.walk(self.folder):
            path = path.replace('\\', '/')
            for file in files:
                if file.endswith('.py'):
                    yield f'{path}/{file}'

    def extract_route(self, file) -> Iterator[RouteModel]:
        print(f'Extract {file}')
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        """
        def route_item_enemy(self):
            self.enter_himeko_trial()
            self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))
        """
        regex = re.compile(
            r'def (?P<func>[a-zA-Z0-9_]*?)\(self\):.*?'
            r'self\.map_init\((.*?)\)',
            re.DOTALL)
        file = file.replace(self.folder, '').replace('.py', '').replace('/', '_').strip('_')
        module = f"{self.folder.strip('./').replace('/', '.')}.{file}"

        for result in regex.findall(content):
            func, data = result

            res = re.search(r'plane=([a-zA-Z_]*)', data)
            if res:
                plane = res.group(1)
            else:
                # Must contain plane
                continue
            res = re.search(r'floor=([\'"a-zA-Z0-9_]*)', data)
            if res:
                floor = res.group(1).strip('"\'')
            else:
                floor = 'F1'
            res = re.search(r'position=\(([0-9.]*)[, ]+([0-9.]*)', data)
            if res:
                position = (float(res.group(1)), float(res.group(2)))
            else:
                position = None

            name = f'{file}__{func}'
            yield RouteModel(
                name=name,
                route=f'{module}:{func}',
                plane=plane,
                floor=floor,
                position=position,
            )

    def iter_route(self):
        """
        Yields:
            RouteData
        """
        for f in self.iter_files():
            for row in self.extract_route(f):
                yield row

    def write(self, file):
        gen = CodeGenerator()
        gen.Import("""
        from tasks.map.route.model import RouteModel
        """)
        gen.CommentAutoGenerage('dev_tools.route_extract')

        for row in self.iter_route():
            with gen.Object(key=row.name, object_class='RouteModel'):
                for key, value in row.__iter__():
                    gen.ObjectAttr(key, value)
        gen.write(file)


def model_to_json(model, file):
    content = model.model_dump_json(indent=2)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)


regex_posi = re.compile(r'_?X(\d+)Y(\d+)')


def get_position_from_name(name):
    res = regex_posi.search(name)
    if res:
        position = int(res.group(1)), int(res.group(2))
    else:
        position = (0, 0)
    return position


class RouteDetect:
    GEN_END = '===== End of generated waypoints ====='

    def __init__(self, folder):
        self.folder = os.path.abspath(folder)
        print(self.folder)
        self.waypoints = SelectedGrids(list(self.iter_image()))

    @cached_property
    def detector(self):
        from tasks.rogue.route.loader import MinimapWrapper
        return MinimapWrapper()

    def get_minimap(self, route: RogueWaypointModel):
        return self.detector.all_minimap[route.plane_floor]

    def iter_image(self) -> Iterator[RogueWaypointModel]:
        for domain_folder in iter_folder(self.folder, is_dir=True):
            domain = os.path.basename(domain_folder)
            for route_folder in iter_folder(domain_folder, is_dir=True):
                route = os.path.basename(route_folder)
                try:
                    for image_file in iter_folder(os.path.join(route_folder, 'route'), ext='.png'):
                        waypoint = os.path.basename(image_file[:-4])

                        parts = route.split('_', maxsplit=3)
                        if len(parts) == 4:
                            world, plane, floor, position = parts
                            position = get_position_from_name(position)
                        elif len(parts) == 3:
                            world, plane, floor = parts
                            position = (0, 0)
                        elif len(parts) == 2:
                            world, plane = parts
                            floor = 'F1'
                            position = (0, 0)
                        else:
                            continue

                        file = f'{self.folder}/{domain}/{route}/route/{waypoint}.png'
                        file_position = get_position_from_name(waypoint)
                        if file_position != (0, 0):
                            position = file_position
                            # waypoint = regex_posi.sub('', waypoint)
                        elif waypoint != 'spawn':
                            position = (0, 0)
                        model = RogueWaypointModel(
                            domain=domain,
                            route=route,
                            waypoint=waypoint,
                            index=0,
                            file=file,
                            plane=f'{world}_{plane}',
                            floor=floor,
                            position=position,
                            direction=0.,
                            rotation=0,
                        )
                        yield model
                        # deep_set(out, keys=[image.route, image.waypoint], value=image)
                except FileNotFoundError:
                    pass

    def predict(self):
        for waypoint in tqdm(self.waypoints.grids):
            waypoint: RogueWaypointModel = waypoint
            minimap = self.get_minimap(waypoint)
            im = load_image(waypoint.file)

            prev = waypoint.position
            minimap.init_position(waypoint.position, show_log=False)
            minimap.update(im, show_log=False)
            waypoint.position = minimap.position
            waypoint.direction = minimap.direction
            waypoint.rotation = minimap.rotation
            if prev != (0, 0) and np.linalg.norm(np.subtract(waypoint.position, prev)) > 1.5:
                if waypoint.is_spawn:
                    print(f'Position changed: {self.folder}/{waypoint.domain}/{waypoint.route}'
                          f' -> {waypoint.plane}_{waypoint.floor}_{waypoint.positionXY}')
                else:
                    name = regex_posi.sub('', waypoint.waypoint)
                    print(f'Position changed: {waypoint.file}'
                          f' -> {name}_{waypoint.positionXY}')

        self.waypoints.create_index('route')
        # Sort by distance
        for waypoints in self.waypoints.indexes.values():
            waypoints = self.sort_waypoints(waypoints.grids)
            for index, waypoint in enumerate(waypoints):
                waypoint.index = index
        self.waypoints = self.waypoints.sort('route', 'index')

    @staticmethod
    def sort_waypoints(waypoints: list[RogueWaypointModel]) -> list[RogueWaypointModel]:
        waypoints = sorted(waypoints, key=lambda point: point.waypoint, reverse=True)
        middle = [point for point in waypoints if not point.is_spawn and not point.is_exit]
        if not middle:
            return waypoints

        try:
            spawn: RogueWaypointModel = [point for point in waypoints if point.is_spawn][0]
        except IndexError:
            return waypoints

        prev = spawn.position
        if prev == (0, 0):
            return waypoints

        sorted_middle = []
        while len(middle):
            distance = np.array([point.position for point in middle]) - prev
            distance = np.linalg.norm(distance, axis=1)
            index = np.argmin(distance)
            sorted_middle.append(middle[index])
            middle.pop(index)

        end = [point for point in waypoints if point.is_exit]
        waypoints = [spawn] + sorted_middle + end
        return waypoints

    def write(self):
        waypoints = RogueWaypointListModel(self.waypoints.grids)
        model_to_json(waypoints, f'{self.folder}/data.json')

    def gen_route(self, waypoints: SelectedGrids):
        gen = CodeGenerator()

        spawn: RogueWaypointModel = waypoints.select(is_spawn=True).first_or_none()
        exit_: RogueWaypointModel = waypoints.select(is_exit=True).first_or_none()
        if spawn is None or exit_ is None:
            return

        class WaypointRepr:
            def __init__(self, position):
                if isinstance(position, RogueWaypointModel):
                    position = position.position
                self.position = tuple(position)

            def __repr__(self):
                return f'Waypoint({self.position})'

            __str__ = __repr__

        def call(func, name):
            ws = waypoints.filter(lambda x: x.waypoint.startswith(name)).get('waypoint')
            ws = ['exit_' if w == 'exit' else w for w in ws]
            if ws:
                ws = ', '.join(ws)
                gen.add(f'self.{func}({ws})')

        with gen.tab():
            with gen.Def(name=spawn.route, args='self'):
                table = MarkdownGenerator(['Waypoint', 'Position', 'Direction', 'Rotation'])
                for waypoint in waypoints:
                    table.add_row([
                        waypoint.waypoint,
                        f'{WaypointRepr(waypoint)},',
                        waypoint.direction,
                        waypoint.rotation
                    ])
                gen.add('"""')
                for row in table.generate():
                    gen.add(row)
                gen.add('"""')
                position = tuple(spawn.position)
                gen.add(f'self.map_init(plane={spawn.plane}, floor="{spawn.floor}", position={position})')
                if spawn.is_DomainBoss or spawn.is_DomainElite or spawn.is_DomainRespite:
                    # Domain has only 1 exit
                    pass
                else:
                    gen.add(f'self.register_domain_exit({WaypointRepr(exit_)}, end_rotation={exit_.rotation})')
                # Waypoint attributes
                for waypoint in waypoints:
                    if waypoint.is_spawn:
                        continue
                    if waypoint.is_exit and not (spawn.is_DomainBoss or spawn.is_DomainElite or spawn.is_DomainRespite):
                        continue
                    name = waypoint.waypoint
                    if name == 'exit':
                        name = 'exit_'
                    gen.Value(key=name, value=WaypointRepr(waypoint))

                # Domain specific
                if spawn.is_DomainBoss or spawn.is_DomainElite:
                    gen.Empty()
                    call('clear_elite', 'enemy')
                    call('domain_reward', 'reward')
                if spawn.is_DomainRespite:
                    gen.Empty()
                    call('clear_item', 'item')
                    call('domain_herta', 'herta')
                if spawn.is_DomainOccurrence or spawn.is_DomainTransaction:
                    gen.Empty()
                    call('clear_item', 'item')
                    call('clear_event', 'event')
                if spawn.is_DomainBoss or spawn.is_DomainElite or spawn.is_DomainRespite:
                    # Domain has only 1 exit
                    call('domain_single_exit', 'exit')

                gen.Comment(self.GEN_END)

        return gen.generate()

    def insert(self, folder, base='tasks.map.route.base'):
        # Create folder
        self.waypoints.create_index('domain')
        for index, waypoints in self.waypoints.indexes.items():
            domain = index[0]
            os.makedirs(f'{folder}/{domain}', exist_ok=True)

        # Create file
        self.waypoints.create_index('domain', 'plane', 'floor')
        for index, waypoints in self.waypoints.indexes.items():
            domain, plane, floor = index
            file = f'{folder}/{domain}/{plane}_{floor}.py'
            if not os.path.exists(file):
                gen = CodeGenerator()
                gen.Import(f"""
                from {base} import RouteBase
                """)
                with gen.Class('Route', inherit='RouteBase'):
                    pass
                    # gen.Pass()
                gen.write(file)

        for index, routes in self.waypoints.indexes.items():
            domain, plane, floor = index
            file = f'{folder}/{domain}/{plane}_{floor}.py'
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Add import
            if base != 'tasks.map.route.base':
                content = content.replace('tasks.map.route.base', base)
            p = '_'.join(plane.split('_', maxsplit=2)[:2])
            imp = [
                      'from tasks.map.control.waypoint import Waypoint',
                      f'from tasks.map.keywords.plane import {p}',
                      f'from {base} import RouteBase',
                  ][::-1]
            res = re.search(r'^(.*?)class Route', content, re.DOTALL)
            if res:
                head = res.group(1)
                for row in imp:
                    if row not in head:
                        content = row + '\n' + content
            content = content.replace(
                'from tasks.rogue.route.base import locked',
                'from tasks.map.route.base import locked')
            # Replace or add routes
            routes.create_index('route')
            for waypoints in routes.indexes.values():
                spawn = waypoints.select(is_spawn=True).first_or_none()
                if spawn is None:
                    continue
                regex = re.compile(rf'def {spawn.route}.*?{self.GEN_END}', re.DOTALL)
                res = regex.search(content)
                if res:
                    before = res.group(0).strip()
                    after = self.gen_route(waypoints).strip()
                    content = content.replace(before, after)
                else:
                    content += '\n' + self.gen_route(waypoints)

            # Sort routes
            regex = re.compile(
                r'(?=(\n    def ([a-zA-Z0-9_]+)\(.*?\n    def|\n    def ([a-zA-Z0-9_]+)\(.*?$))', re.DOTALL)
            funcs = regex.findall(content)

            known_routes = [route[0] for route in routes.indexes.keys()]
            routes = []
            for code, route1, route2 in funcs:
                if route1:
                    route = route1
                elif route2:
                    route = route2
                else:
                    continue
                if route not in known_routes:
                    continue
                code = code.removesuffix('\n    def').removeprefix('\n')
                routes.append((route, code))

            sorted_routes = sorted(routes, key=lambda x: get_position_from_name(x[0]))
            routes = [route[1] for route in routes]
            sorted_routes = [route[1] for route in sorted_routes]
            new = ''
            for before, after in zip(routes, sorted_routes):
                left = content.index(before)
                right = left + len(before)
                new += content[:left]
                new += after
                content = content[right:]
            new += content
            content = new

            # Format
            content = re.sub(r'[\n ]+    def', '\n\n    def', content)
            content = content.rstrip('\n') + '\n'
            content = re.sub(r'    (@[a-zA-Z0-9_().]+)[\n ]+    def', r'    \1\n    def', content)
            # Write
            with open(file, 'w', encoding='utf-8', newline='') as f:
                f.write(content)


def rogue_extract(folder):
    print('rogue_extract')

    def iter_route():
        for row in RouteExtract(f'{folder}').iter_route():
            domain = row.name.split('_', maxsplit=1)[0]
            row = RogueRouteModel(domain=domain, **row.model_dump())
            row.name = f'{row.domain}_{row.route.split(":")[1]}'
            row.route = row.route.replace('_', '.', 1)
            yield row

    routes = RogueRouteListModel(list(iter_route()))
    model_to_json(routes, f'{folder}/route.json')


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '../'))
    RouteExtract('./route/daily').write('./tasks/map/route/route/daily.py')

    self = RouteDetect('../SrcRoute/rogue')
    self.predict()
    self.write()
    self.insert('./route/rogue', base='tasks.rogue.route.base')

    rogue_extract('./route/rogue')
